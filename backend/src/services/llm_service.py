from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import openai
from utils.logger import setup_logger
from utils.exceptions import (
    LLMError, ModelInitializationError, ModelInferenceError,
    HardwareError, wrap_exception
)

logger = setup_logger(__name__)

class LLMService:
    def __init__(self, config):
        self.config = config.get('llm', {})
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        self._initialize_model()

    def _initialize_model(self):
        try:
            # モデル名を指定
            model_name = "huggingface.co/elyza/Llama-3-ELYZA-JP-8B-GGUF:latest"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16,
                device_map=self.device
            )
            logger.info(f"LLM initialized on device: {self.device}")
        except Exception as e:
            llm_init_error = wrap_exception(
                e, ModelInitializationError,
                "Error initializing LLM model",
                details={
                    'model_name': model_name,
                    'device': self.device,
                    'torch_dtype': 'float16',
                    'mps_available': torch.backends.mps.is_available()
                }
            )
            logger.error(f"LLM initialization error: {llm_init_error.to_dict()}")
            raise llm_init_error

    def generate_response(self, context):
        try:
            # プロンプトの作成
            prompt = self._create_prompt(context)
            
            # トークナイズと生成
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            outputs = self.model.generate(
                input_ids=inputs.input_ids, 
                attention_mask=inputs.attention_mask,
                max_new_tokens=100,
                temperature=0.7,
                do_sample=True
            )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return self._extract_response(response)
        except Exception as e:
            llm_inference_error = wrap_exception(
                e, ModelInferenceError,
                "Error generating LLM response",
                details={
                    'context_length': len(context) if context else 0,
                    'device': self.device,
                    'model_loaded': hasattr(self, 'model') and self.model is not None
                }
            )
            logger.error(f"LLM inference error: {llm_inference_error.to_dict()}")
            return "申し訳ありません。応答の生成に失敗しました。"

    def _create_prompt(self, context):
        return f"""<|system|>
あなたは勉強を監視する助手です。ユーザーの行動に応じて適切なアドバイスをしてください。

<|user|>
{context}

<|assistant|>"""

    def _extract_response(self, response):
        # システムプロンプトと入力を除去して応答のみを抽出
        try:
            return response.split("<|assistant|>")[-1].strip()
        except Exception as e:
            extract_error = wrap_exception(
                e, LLMError,
                "Error extracting LLM response",
                details={'response_length': len(response) if response else 0}
            )
            logger.warning(f"Response extraction error: {extract_error.to_dict()}")
            return response 
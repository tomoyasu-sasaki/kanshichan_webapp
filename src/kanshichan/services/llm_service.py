from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from src.kanshichan.utils.logger import setup_logger

logger = setup_logger(__name__)

class LLMService:
    def __init__(self, config):
        self.config = config.get('llm', {})
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        self._initialize_model()

    def _initialize_model(self):
        try:
            # TinyLlama-1.1B-Chatを使用
            model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16,
                device_map=self.device
            )
            logger.info(f"LLM initialized on device: {self.device}")
        except Exception as e:
            logger.error(f"Error initializing LLM: {e}")
            raise

    def generate_response(self, context):
        try:
            # プロンプトの作成
            prompt = self._create_prompt(context)
            
            # トークナイズと生成
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=100,
                temperature=0.7,
                do_sample=True
            )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return self._extract_response(response)
        except Exception as e:
            logger.error(f"Error generating response: {e}")
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
        except:
            return response 
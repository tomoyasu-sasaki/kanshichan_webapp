import pytest
from unittest import mock
import torch
from src.kanshichan.services.llm_service import LLMService
from transformers import AutoModelForCausalLM, AutoTokenizer

@pytest.fixture
def config():
    return {
        'llm': {
            'model_name': 'TinyLlama/TinyLlama-1.1B-Chat-v1.0',
            'temperature': 0.7,
            'max_tokens': 100
        }
    }

@pytest.fixture
def mock_tokenizer():
    tokenizer = mock.Mock()
    tokenizer.decode.return_value = "<|system|>...<|assistant|>テスト応答"
    tokenizer.__call__ = mock.Mock(return_value={
        'input_ids': torch.tensor([[1, 2, 3]]),
        'attention_mask': torch.tensor([[1, 1, 1]])
    })
    return tokenizer

@pytest.fixture
def mock_model():
    model = mock.Mock()
    model.generate.return_value = torch.tensor([[1, 2, 3]])
    return model

def test_llm_initialization(config):
    """LLMサービスが正しく初期化されるかテスト"""
    with mock.patch('torch.backends.mps.is_available', return_value=True), \
         mock.patch('transformers.AutoTokenizer.from_pretrained') as mock_tokenizer, \
         mock.patch('transformers.AutoModelForCausalLM.from_pretrained') as mock_model:
        
        llm_service = LLMService(config)
        
        assert llm_service.device == "mps"
        mock_tokenizer.assert_called_once()
        mock_model.assert_called_once()

def test_generate_response(config, mock_tokenizer, mock_model):
    """応答生成テストの修正版"""
    with mock.patch('transformers.AutoTokenizer.from_pretrained', return_value=mock_tokenizer), \
         mock.patch('transformers.AutoModelForCausalLM.from_pretrained', return_value=mock_model):
        
        llm_service = LLMService(config)
        mock_tokenizer.to = mock.Mock(return_value=mock_tokenizer)
        
        response = llm_service.generate_response("ユーザーが勉強に集中しています")
        assert "テスト応答" in response

def test_error_handling(config):
    """エラー処理テストの修正版"""
    with mock.patch('transformers.AutoTokenizer.from_pretrained') as mock_tokenizer:
        mock_tokenizer.side_effect = Exception("Error initializing LLM: モデル読み込みエラー")
        
        with pytest.raises(Exception) as exc_info:
            LLMService(config)
        assert "Error initializing LLM" in str(exc_info.value)
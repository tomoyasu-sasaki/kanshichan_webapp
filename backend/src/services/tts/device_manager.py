"""
Device Manager - シンプル化されたデバイス管理

PyTorchデバイス選択とモデル最適化を管理
"""

import torch
from typing import Dict, Any, Optional, Tuple
from .tts_config import TTSConfig
from utils.logger import setup_logger
from utils.exceptions import ServiceUnavailableError
from .device_utils import get_optimal_device, configure_device_env, cleanup_device_memory, get_device_info, ensure_tensor_device

logger = setup_logger(__name__)


class DeviceManager:
    """シンプル化されたデバイス管理クラス
    
    PyTorchデバイス選択とモデル最適化
    """
    
    def __init__(self, tts_config: 'TTSConfig'):
        """デバイス管理初期化
        
        Args:
            tts_config: TTS設定インスタンス
        """
        self.tts_config = tts_config
        self.device = get_optimal_device(self.tts_config.enable_mps)
        
        # デバイス環境設定
        configure_device_env(self.device)
        
        logger.info(f"Device initialized: {self.device}")
    
    def optimize_model_for_device(self, model: Any) -> Any:
        """モデルをデバイス用に最適化（シンプル版）
        
        Args:
            model: 最適化するモデル
            
        Returns:
            Any: 最適化されたモデル
        """
        try:
            # デバイスに移動（MPSの場合は型も統一）
            if self.device == 'mps':
                # MPSではBF16とF16の混在問題を避けるためF16に統一
                logger.info("🍎 MPS detected: Converting model to float16 for compatibility")
                model = model.to(self.device, torch.float16)
            else:
                model = model.to(self.device)
            
            # 推論モードに設定
            model.eval()
            for param in model.parameters():
                param.requires_grad = False
            
            # デバイス固有の最適化
            if self.device == 'mps' and self.tts_config.mps_half_precision and hasattr(model, 'half'):
                try:
                    # すでにfloat16に変換済みなので追加処理は不要
                    logger.info("🔢 MPS using float16")
                except Exception as half_error:
                    logger.warning(f"MPS half precision failed: {half_error}")
            
            elif self.device == 'cuda' and hasattr(model, 'half'):
                try:
                    model = model.half()
                    logger.info("🔢 CUDA half precision enabled")
                except Exception:
                    logger.debug("CUDA half precision not supported")
            
            logger.info(f"Model optimized for {self.device.upper()}")
            return model
            
        except Exception as e:
            logger.error(f"Model optimization failed: {e}")
            if self.device != 'cpu':
                logger.warning(f"Falling back to CPU")
                self.device = 'cpu'
                return self.optimize_model_for_device(model)
            return model
    
    def handle_device_error(self, error: Exception, model: Any = None) -> Tuple[str, Any]:
        """デバイスエラーのシンプルなハンドリング
        
        Args:
            error: 発生したエラー
            model: エラーが発生したモデル（オプション）
            
        Returns:
            tuple[str, Any]: (新しいデバイス, フォールバック後のモデル)
        """
        # MPSまたはCUDAエラーの場合はCPUにフォールバック
        if self.device != 'cpu':
            logger.warning(f"🔧 Device error detected, falling back to CPU: {error}")
            
            # デバイス変更
            self.device = 'cpu'
            configure_device_env(self.device)
            
            # モデルがある場合はCPUに移動
            if model is not None:
                try:
                    model = model.to('cpu')
                    model.eval()
                except Exception as model_error:
                    logger.error(f"Model CPU migration error: {model_error}")
            
            return self.device, model
        
        # すでにCPUの場合は再発生
        raise error
    
    def ensure_tensor_device_consistency(self, tensor: torch.Tensor, model: Any = None) -> torch.Tensor:
        """テンソルのデバイス一貫性を確保（シンプル版）
        
        Args:
            tensor: 処理するテンソル
            model: 参照モデル（オプション）
            
        Returns:
            torch.Tensor: デバイス一貫性が確保されたテンソル
        """
        return ensure_tensor_device(tensor, self.device)
    
    def cleanup_device_memory(self) -> None:
        """デバイスメモリのクリーンアップ"""
        cleanup_device_memory(self.device)
    
    def get_device_info(self) -> Dict[str, Any]:
        """デバイス情報を取得
        
        Returns:
            Dict[str, Any]: デバイス情報
        """
        return get_device_info(
            self.device, 
            self.tts_config.enable_mps,
            self.tts_config.mps_memory_fraction
        ) 
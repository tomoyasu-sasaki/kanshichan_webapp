"""
Device Manager - デバイス管理とMPS最適化

PyTorchデバイス選択、MPS最適化、フォールバック処理を管理
"""

import os
import torch
from typing import Dict, Any, Optional
from utils.logger import setup_logger
from utils.exceptions import ServiceUnavailableError, wrap_exception

logger = setup_logger(__name__)


class DeviceManager:
    """デバイス管理クラス
    
    PyTorchデバイス選択、MPS最適化、GPU/CPUフォールバック処理
    """
    
    def __init__(self, tts_config: 'TTSConfig'):
        """デバイス管理初期化
        
        Args:
            tts_config: TTS設定インスタンス
        """
        self.tts_config = tts_config
        self.device = self._get_optimal_device()
        self.original_device = self.device
        
        logger.info(f"Device initialized: {self.device}")
    
    def _get_optimal_device(self) -> str:
        """最適な実行デバイスを決定
        
        Returns:
            str: 使用デバイス ('cuda', 'mps', 'cpu')
        """
        if torch.cuda.is_available():
            logger.info("🚀 CUDA GPU detected")
            return 'cuda'
        
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            if self.tts_config.enable_mps:
                logger.info("🍎 Apple Silicon MPS detected - attempting acceleration")
                return 'mps'
            else:
                logger.info("MPS available but disabled by configuration, using CPU")
                return 'cpu'
        else:
            logger.info("Using CPU device")
            return 'cpu'
    
    def configure_device_optimizations(self) -> None:
        """デバイス固有の最適化設定"""
        if self.device == 'mps':
            self._configure_mps_optimizations()
        elif self.device == 'cuda':
            self._configure_cuda_optimizations()
        else:
            self._configure_cpu_optimizations()
    
    def _configure_mps_optimizations(self) -> None:
        """MPS最適化設定"""
        try:
            # MPS環境変数設定（強化版）
            os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
            os.environ['MPS_GRAPH_CACHE_DEPTH'] = '5'
            os.environ['PYTORCH_MPS_HIGH_WATERMARK_RATIO'] = '0.75'
            os.environ['PYTORCH_MPS_LOW_WATERMARK_RATIO'] = '0.70'
            os.environ['PYTORCH_MPS_PREFER_CPU_FALLBACK'] = '1'
            os.environ['PYTORCH_ENABLE_MPS_CPU_FALLBACK'] = '1'
            
            # デバッグ設定
            if self.tts_config.debug_mps:
                os.environ['PYTORCH_VERBOSE'] = '1'
                os.environ['PYTORCH_MPS_LOG_LEVEL'] = '1'
            
            # メモリ最適化
            if hasattr(torch.mps, 'set_per_process_memory_fraction'):
                torch.mps.set_per_process_memory_fraction(self.tts_config.mps_memory_fraction)
                logger.info(f"🧠 MPS memory fraction: {self.tts_config.mps_memory_fraction}")
            
            # 最適化フラグ
            if hasattr(torch.backends.mps, 'is_available'):
                torch.backends.mps.enable_all_optimizations = True
            
            logger.info("🍎 MPS optimizations configured with CPU fallback")
            
        except Exception as e:
            logger.warning(f"MPS optimization failed: {e}")
    
    def _configure_cuda_optimizations(self) -> None:
        """CUDA最適化設定"""
        try:
            # cuDNN最適化
            torch.backends.cudnn.benchmark = True
            torch.backends.cudnn.deterministic = False
            
            # メモリ効率化
            if self.tts_config.gpu_memory_optimization:
                torch.cuda.empty_cache()
            
            logger.info("🚀 CUDA optimizations configured")
            
        except Exception as e:
            logger.warning(f"CUDA optimization failed: {e}")
    
    def _configure_cpu_optimizations(self) -> None:
        """CPU最適化設定"""
        try:
            # CPU最適化
            torch.set_num_threads(self.tts_config.max_worker_threads)
            
            # 推論最適化
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
            
            logger.info("💻 CPU optimizations configured")
            
        except Exception as e:
            logger.warning(f"CPU optimization failed: {e}")
    
    def optimize_model_for_device(self, model: Any) -> Any:
        """モデルをデバイス用に最適化
        
        Args:
            model: 最適化するモデル
            
        Returns:
            Any: 最適化されたモデル
        """
        try:
            # デバイスに移動
            model = model.to(self.device)
            
            # デバイス固有の最適化
            if self.device == 'mps':
                model = self._optimize_model_for_mps(model)
            elif self.device == 'cuda':
                model = self._optimize_model_for_cuda(model)
            else:
                model = self._optimize_model_for_cpu(model)
            
            # 推論モードに設定
            model.eval()
            for param in model.parameters():
                param.requires_grad = False
            
            logger.info(f"Model optimized for {self.device.upper()}")
            return model
            
        except Exception as e:
            logger.error(f"Model optimization failed: {e}")
            return model
    
    def _optimize_model_for_mps(self, model: Any) -> Any:
        """MPS用モデル最適化"""
        try:
            # 半精度設定
            if self.tts_config.mps_half_precision and hasattr(model, 'half'):
                try:
                    model = model.half()
                    logger.info("🔢 MPS half precision enabled")
                except Exception as half_error:
                    logger.warning(f"MPS half precision failed: {half_error}")
            
            # 推論最適化
            try:
                model = torch.jit.optimize_for_inference(model)
                logger.info("🔧 MPS inference optimization applied")
            except Exception as opt_error:
                logger.debug(f"MPS inference optimization skipped: {opt_error}")
            
            return model
            
        except Exception as e:
            logger.warning(f"MPS model optimization failed: {e}")
            return model
    
    def _optimize_model_for_cuda(self, model: Any) -> Any:
        """CUDA用モデル最適化"""
        try:
            # GPU最適化
            if hasattr(model, 'half'):
                try:
                    model = model.half()
                    logger.info("🔢 CUDA half precision enabled")
                except Exception:
                    logger.debug("CUDA half precision not supported")
            
            return model
            
        except Exception as e:
            logger.warning(f"CUDA model optimization failed: {e}")
            return model
    
    def _optimize_model_for_cpu(self, model: Any) -> Any:
        """CPU用モデル最適化"""
        try:
            # CPU推論最適化
            logger.info("💻 CPU model optimization applied")
            return model
            
        except Exception as e:
            logger.warning(f"CPU model optimization failed: {e}")
            return model
    
    def handle_device_error(self, error: Exception, model: Any = None) -> tuple[str, Any]:
        """デバイスエラーのハンドリングとフォールバック
        
        Args:
            error: 発生したエラー
            model: エラーが発生したモデル（オプション）
            
        Returns:
            tuple[str, Any]: (新しいデバイス, フォールバック後のモデル)
        """
        error_str = str(error).lower()
        
        # MPS エラーのフォールバック
        if self.device == 'mps' and ('scatter_reduce' in error_str or 'aten::' in error_str or 'mps' in error_str):
            logger.warning(f"🔧 MPS error detected, falling back to CPU: {error}")
            
            # 特定エラータイプの詳細ログ
            if 'scatter_reduce' in error_str:
                logger.info("📝 エラー発生箇所: Zonos sampling.py の repetition penalty 処理中")
                logger.info("📝 具体的操作: torch.scatter_reduce() がMPSで未実装")
                logger.info("📝 発生タイミング: model.generate() 実行中の音声コード生成処理")
            
            # 完全なCPUフォールバック処理
            fallback_model = self._perform_complete_cpu_fallback(model)
            
            return self.device, fallback_model
        
        # その他のエラーは再発生
        raise error
    
    def _perform_complete_cpu_fallback(self, model: Any = None) -> Any:
        """完全なCPUフォールバック処理
        
        MPSエラー発生時に、モデル全体を確実にCPUに移行
        
        Args:
            model: フォールバック対象モデル
            
        Returns:
            Any: CPU移行後のモデル（参照更新のため）
        """
        try:
            logger.info("🔄 Starting complete CPU fallback process...")
            
            # デバイス設定変更
            self.device = 'cpu'
            self._configure_cpu_optimizations()
            
            # モデルの完全CPU移行
            if model is not None:
                # 1. メイン部分をCPUに移動
                logger.debug("Moving main model to CPU...")
                model = model.to('cpu')
                
                # 2. Autoencoder部分の安全な移行
                if hasattr(model, 'autoencoder') and model.autoencoder is not None:
                    logger.debug("Processing autoencoder components...")
                    
                    # autoencoderのto()メソッド有無を確認
                    if hasattr(model.autoencoder, 'to'):
                        logger.debug("Moving autoencoder to CPU...")
                        model.autoencoder = model.autoencoder.to('cpu')
                    
                    # 3. DAC部分の安全な移行
                    if hasattr(model.autoencoder, 'dac') and model.autoencoder.dac is not None:
                        logger.debug("Processing DAC components...")
                        
                        # DACのto()メソッド有無を確認
                        if hasattr(model.autoencoder.dac, 'to'):
                            logger.debug("Moving DAC to CPU...")
                            model.autoencoder.dac = model.autoencoder.dac.to('cpu')
                        
                        # 4. Quantizer部分の移行
                        if hasattr(model.autoencoder.dac, 'quantizer'):
                            logger.debug("Processing quantizer...")
                            if hasattr(model.autoencoder.dac.quantizer, 'to'):
                                logger.debug("Moving quantizer to CPU...")
                                model.autoencoder.dac.quantizer = model.autoencoder.dac.quantizer.to('cpu')
                            
                            # 個別のquantizer部品を移行
                            if hasattr(model.autoencoder.dac.quantizer, 'quantizers'):
                                logger.debug("Moving individual quantizers...")
                                for i, quantizer in enumerate(model.autoencoder.dac.quantizer.quantizers):
                                    if hasattr(quantizer, 'to'):
                                        model.autoencoder.dac.quantizer.quantizers[i] = quantizer.to('cpu')
                        
                        # 5. Encoder/Decoder部分の移行
                        if hasattr(model.autoencoder.dac, 'encoder') and hasattr(model.autoencoder.dac.encoder, 'to'):
                            logger.debug("Moving DAC encoder to CPU...")
                            model.autoencoder.dac.encoder = model.autoencoder.dac.encoder.to('cpu')
                        
                        if hasattr(model.autoencoder.dac, 'decoder') and hasattr(model.autoencoder.dac.decoder, 'to'):
                            logger.debug("Moving DAC decoder to CPU...")
                            model.autoencoder.dac.decoder = model.autoencoder.dac.decoder.to('cpu')
                
                # 6. CPU最適化を適用
                model = self._optimize_model_for_cpu(model)
                
                # 7. MPS関連のキャッシュクリア
                if hasattr(torch.mps, 'empty_cache'):
                    torch.mps.empty_cache()
                
                # 8. CPU専用設定を適用
                if hasattr(model, 'eval'):
                    model.eval()
                
                # 9. パラメータの確認とデバイス移行
                logger.debug("Verifying all parameters are on CPU...")
                try:
                    for name, param in model.named_parameters():
                        if param.device.type != 'cpu':
                            logger.debug(f"Moving parameter {name} to CPU...")
                            param.data = param.data.cpu()
                except Exception as param_error:
                    logger.warning(f"Parameter verification failed: {param_error}")
                
                logger.info("✅ Complete CPU fallback successful")
                
            else:
                logger.warning("No model provided for CPU fallback")
                
            return model
                
        except Exception as fallback_error:
            logger.error(f"❌ Complete CPU fallback failed: {fallback_error}")
            logger.error(f"Fallback error details: {type(fallback_error).__name__}: {str(fallback_error)}")
            
            # 最後の手段: モデル再初期化を推奨
            logger.info("💡 Recommendation: Reinitialize model directly on CPU")
            raise ServiceUnavailableError(f"Device fallback failed - model reinitialiation required: {fallback_error}")
    
    def ensure_tensor_device_consistency(self, tensor: torch.Tensor, model: Any = None) -> torch.Tensor:
        """テンソルのデバイス一貫性を確保
        
        Args:
            tensor: 処理するテンソル
            model: 参照モデル（オプション）
            
        Returns:
            torch.Tensor: デバイス一貫性が確保されたテンソル
        """
        try:
            # モデルのデバイスを取得
            if model is not None:
                model_device = next(model.parameters()).device
            else:
                model_device = torch.device(self.device)
            
            # デバイスが異なる場合は移動
            if tensor.device != model_device:
                logger.debug(f"Moving tensor from {tensor.device} to {model_device}")
                
                if model_device.type == 'mps':
                    try:
                        tensor = tensor.to(model_device)
                        # MPSメモリクリーンアップ
                        if hasattr(torch.mps, 'empty_cache'):
                            torch.mps.empty_cache()
                    except Exception as mps_error:
                        logger.warning(f"MPS tensor move failed: {mps_error}, using CPU")
                        tensor = tensor.to('cpu')
                        self.device = 'cpu'
                else:
                    tensor = tensor.to(model_device)
            
            return tensor
            
        except Exception as e:
            logger.warning(f"Tensor device consistency failed: {e}")
            return tensor
    
    def cleanup_device_memory(self) -> None:
        """デバイスメモリのクリーンアップ"""
        try:
            if self.device == 'cuda' and torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
                logger.debug("CUDA memory cleaned")
            
            elif self.device == 'mps' and hasattr(torch.mps, 'empty_cache'):
                torch.mps.empty_cache()
                logger.debug("MPS memory cleaned")
                
        except Exception as e:
            logger.warning(f"Device memory cleanup failed: {e}")
    
    def get_device_info(self) -> Dict[str, Any]:
        """デバイス情報を取得
        
        Returns:
            Dict[str, Any]: デバイス情報
        """
        device_info = {
            'current_device': self.device,
            'original_device': self.original_device,
            'cuda_available': torch.cuda.is_available(),
            'mps_available': hasattr(torch.backends, 'mps') and torch.backends.mps.is_available(),
            'mps_enabled_in_config': self.tts_config.enable_mps,
            'mps_memory_fraction': self.tts_config.mps_memory_fraction,
            'mps_half_precision': self.tts_config.mps_half_precision
        }
        
        # MPS固有情報
        if self.device == 'mps':
            device_info.update({
                'mps_optimizations_active': True,
                'mps_fallback_enabled': os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK') == '1',
                'mps_cache_depth': os.environ.get('MPS_GRAPH_CACHE_DEPTH', 'not_set')
            })
        
        # CUDA固有情報
        if self.device == 'cuda' and torch.cuda.is_available():
            device_info.update({
                'cuda_device_count': torch.cuda.device_count(),
                'cuda_current_device': torch.cuda.current_device(),
                'cuda_memory_allocated': torch.cuda.memory_allocated() / (1024**3),
                'cuda_memory_reserved': torch.cuda.memory_reserved() / (1024**3)
            })
        
        return device_info 
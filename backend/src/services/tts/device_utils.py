"""
Device Utilities - デバイス選択ユーティリティ

PyTorchデバイスの選択と検証を行うシンプルなユーティリティ関数群
"""

import os
import torch
from typing import Dict, Any, Union

def get_optimal_device(enable_mps: bool = True) -> str:
    """利用可能な最適なデバイスを取得
    
    Args:
        enable_mps: MPSを有効にするかどうか
        
    Returns:
        str: 使用デバイス ('cuda', 'mps', 'cpu')
    """
    if torch.cuda.is_available():
        return 'cuda'
    
    # Apple Silicon MPSのサポート検出
    if hasattr(torch, 'mps') and hasattr(torch.mps, 'is_available') and torch.mps.is_available():
        # MPSが有効かつ混合精度の問題がある場合は特別な処理
        if enable_mps:
            return 'mps'
        else:
            return 'cpu'
    
    return 'cpu'

def configure_device_env(device: str) -> None:
    """デバイス固有の環境変数を設定
    
    Args:
        device: デバイス名
    """
    if device == 'mps':
        # MPS環境変数設定
        os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
        os.environ['MPS_GRAPH_CACHE_DEPTH'] = '5'
        os.environ['PYTORCH_MPS_HIGH_WATERMARK_RATIO'] = '0.75'
        os.environ['PYTORCH_MPS_LOW_WATERMARK_RATIO'] = '0.70'
        os.environ['PYTORCH_MPS_PREFER_CPU_FALLBACK'] = '1'
        os.environ['PYTORCH_ENABLE_MPS_CPU_FALLBACK'] = '1'
        
        # MPSのBF16/F16混合型問題に対処
        # この設定はMPSが自動的にCPUにフォールバックする際の挙動を制御
        os.environ['PYTORCH_MPS_DEBUG_ABI_CHECK'] = '0'
    
    elif device == 'cuda':
        # CUDA関連の設定
        torch.backends.cudnn.benchmark = True
        torch.backends.cudnn.deterministic = False

def cleanup_device_memory(device: str) -> None:
    """デバイスメモリのクリーンアップ
    
    Args:
        device: デバイス名
    """
    if device == 'cuda' and torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
    
    elif device == 'mps' and hasattr(torch.mps, 'empty_cache'):
        torch.mps.empty_cache()

def get_device_info(device: str, enable_mps: bool = True, mps_memory_fraction: float = 0.7) -> Dict[str, Any]:
    """デバイス情報を取得
    
    Args:
        device: 現在のデバイス
        enable_mps: MPSが設定で有効化されているか
        mps_memory_fraction: MPS用のメモリ割り当て率
        
    Returns:
        Dict[str, Any]: デバイス情報
    """
    device_info = {
        'current_device': device,
        'cuda_available': torch.cuda.is_available(),
        'mps_available': hasattr(torch.backends, 'mps') and torch.backends.mps.is_available(),
        'mps_enabled_in_config': enable_mps
    }
    
    # MPS固有情報
    if device == 'mps':
        device_info.update({
            'mps_memory_fraction': mps_memory_fraction,
            'mps_fallback_enabled': os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK') == '1',
            'mps_cache_depth': os.environ.get('MPS_GRAPH_CACHE_DEPTH', 'not_set'),
            'mps_abi_check': os.environ.get('PYTORCH_MPS_DEBUG_ABI_CHECK', 'not_set')
        })
    
    # CUDA固有情報
    if device == 'cuda' and torch.cuda.is_available():
        device_info.update({
            'cuda_device_count': torch.cuda.device_count(),
            'cuda_current_device': torch.cuda.current_device(),
            'cuda_memory_allocated': torch.cuda.memory_allocated() / (1024**3),
            'cuda_memory_reserved': torch.cuda.memory_reserved() / (1024**3)
        })
    
    return device_info

def ensure_tensor_device(tensor: torch.Tensor, target_device: str) -> torch.Tensor:
    """テンソルを指定デバイスに移動（簡素化版）
    
    Args:
        tensor: 対象テンソル
        target_device: 移動先デバイス
        
    Returns:
        torch.Tensor: 移動後のテンソル
    """
    try:
        # MPSデバイスの場合は型を明示的に変換
        if target_device == 'mps':
            # MPSではbf16とf16の混在を避けるためf16に統一
            return tensor.to(target_device, dtype=torch.float16)
        return tensor.to(target_device)
    except Exception:
        # エラー時はCPUにフォールバック
        return tensor.to('cpu') 
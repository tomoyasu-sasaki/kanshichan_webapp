"""
Audio Processor - 音声処理とキャッシュ管理

音声ファイル処理、品質向上、キャッシュシステム、パフォーマンス最適化を管理
"""

import os
import hashlib
import json
import threading
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import torch
import torchaudio
import librosa
import soundfile as sf
import numpy as np

from .tts_config import TTSConfig
from utils.logger import setup_logger
from utils.exceptions import AudioError, wrap_exception

logger = setup_logger(__name__)


class AudioProcessor:
    """音声処理とキャッシュ管理クラス
    
    音声品質向上、キャッシュシステム、パフォーマンス最適化機能
    """
    
    def __init__(self, tts_config: 'TTSConfig'):
        """音声処理初期化
        
        Args:
            tts_config: TTS設定インスタンス
        """
        self.tts_config = tts_config
        
        # キャッシュシステム
        self._audio_cache = {}
        self._cache_lock = threading.Lock()
        
        # パフォーマンス最適化
        self._thread_pool = ThreadPoolExecutor(max_workers=tts_config.max_worker_threads)
        self._generation_queue = asyncio.Queue() if tts_config.enable_async_generation else None
        
        # パフォーマンス指標
        self._metrics = {
            'total_generations': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'avg_generation_time': 0,
            'total_generation_time': 0
        }
        
        logger.info(f"AudioProcessor initialized - Cache: {tts_config.enable_audio_cache}")
    
    def generate_output_path(self) -> str:
        """出力ファイルパスを自動生成
        
        Returns:
            str: 生成されたファイルパス（絶対パス）
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"tts_output_{timestamp}.wav"
        output_path = self.tts_config.audio_cache_dir / filename
        
        # 絶対パスに変換
        absolute_path = str(output_path.resolve())
        logger.debug(f"Generated output path: {absolute_path}")
        return absolute_path
    
    def validate_reference_audio(self, audio_path: str) -> None:
        """参照音声ファイルの検証
        
        Args:
            audio_path: 音声ファイルパス
            
        Raises:
            AudioError: 音声ファイルが不正な場合
        """
        if not os.path.exists(audio_path):
            raise AudioError(f"Reference audio file not found: {audio_path}")
        
        try:
            wav, sampling_rate = torchaudio.load(audio_path)
            duration = wav.shape[1] / sampling_rate
            
            # 推奨時間チェック（5-30秒）
            if duration < 3.0:
                logger.warning(f"Reference audio is very short ({duration:.1f}s). Recommended: 5-30s")
            elif duration > 60.0:
                logger.warning(f"Reference audio is very long ({duration:.1f}s). Recommended: 5-30s")
            
            logger.info(f"Reference audio validated: {duration:.1f}s, {sampling_rate}Hz")
            
        except Exception as e:
            raise AudioError(f"Invalid reference audio file: {str(e)}")
    
    def preprocess_reference_audio(self, audio_path: str) -> str:
        """参照音声ファイルの前処理
        
        Args:
            audio_path: 元音声ファイルパス
            
        Returns:
            str: 前処理済み音声ファイルパス（絶対パス）
        """
        try:
            wav, sampling_rate = torchaudio.load(audio_path)
            
            # 音声品質向上処理
            processed_wav = self.enhance_audio_quality(wav, sampling_rate)
            
            # 一時ファイルに保存
            temp_filename = f"preprocessed_{os.path.basename(audio_path)}"
            temp_path = self.tts_config.audio_cache_dir / temp_filename
            torchaudio.save(str(temp_path), processed_wav, sampling_rate)
            
            # 絶対パスに変換
            absolute_temp_path = str(temp_path.resolve())
            logger.info(f"Reference audio preprocessed: {audio_path} -> {absolute_temp_path}")
            return absolute_temp_path
            
        except Exception as e:
            logger.warning(f"Audio preprocessing failed: {e}, using original file")
            return audio_path
    
    def enhance_audio_quality(self, wav: torch.Tensor, sampling_rate: int) -> torch.Tensor:
        """音声品質向上処理
        
        Args:
            wav: 音声波形テンソル
            sampling_rate: サンプリングレート
            
        Returns:
            torch.Tensor: 品質向上済み音声波形
        """
        try:
            with torch.no_grad():
                # 1. 正規化（音量正規化）
                wav = self._normalize_audio_level(wav)
                
                # 2. ノイズ軽減（簡易版）
                wav = self._apply_noise_reduction(wav)
                
                # 3. 音声の開始・終了の無音削除
                wav = self._trim_silence(wav, sampling_rate)
                
                # 4. 適切な長さに調整（5-30秒の範囲内）
                wav = self._adjust_audio_length(wav, sampling_rate)
                
                logger.debug(f"Audio enhancement completed. Final shape: {wav.shape}")
                return wav
                
        except Exception as e:
            logger.warning(f"Audio enhancement failed: {e}, using original audio")
            return wav
    
    def _normalize_audio_level(self, wav: torch.Tensor) -> torch.Tensor:
        """音声レベル正規化"""
        try:
            # RMS正規化
            rms = torch.sqrt(torch.mean(wav ** 2))
            if rms > 0:
                target_rms = 0.1  # 目標RMSレベル
                wav = wav * (target_rms / rms)
            
            # ピーククリッピング防止
            wav = torch.clamp(wav, -0.95, 0.95)
            return wav
        except Exception as e:
            logger.warning(f"Audio normalization failed: {e}")
            return wav
    
    def _apply_noise_reduction(self, wav: torch.Tensor) -> torch.Tensor:
        """簡易ノイズ軽減"""
        try:
            # 高周波ノイズの軽減（簡易ローパスフィルタ）
            if wav.dim() > 1 and wav.shape[1] > 1000:
                # 単純な移動平均フィルタ
                kernel_size = 3
                padding = kernel_size // 2
                wav_filtered = torch.nn.functional.avg_pool1d(
                    wav.unsqueeze(0), kernel_size, stride=1, padding=padding
                ).squeeze(0)
                return wav_filtered
            
            return wav
        except Exception as e:
            logger.warning(f"Noise reduction failed: {e}")
            return wav
    
    def _trim_silence(self, wav: torch.Tensor, sampling_rate: int) -> torch.Tensor:
        """無音部分の削除"""
        try:
            # 音声検出の閾値
            threshold = 0.01
            
            # ステレオをモノラルに変換
            if wav.dim() > 1 and wav.shape[0] > 1:
                wav_mono = torch.mean(wav, dim=0, keepdim=True)
            else:
                wav_mono = wav
            
            # 音声の開始と終了を検出
            audio_magnitude = torch.abs(wav_mono.squeeze())
            above_threshold = audio_magnitude > threshold
            
            if above_threshold.any():
                start_idx = torch.where(above_threshold)[0][0].item()
                end_idx = torch.where(above_threshold)[0][-1].item()
                
                # 前後に少しマージンを追加
                margin = int(0.1 * sampling_rate)  # 0.1秒のマージン
                start_idx = max(0, start_idx - margin)
                end_idx = min(wav.shape[-1], end_idx + margin)
                
                wav_trimmed = wav[..., start_idx:end_idx]
                logger.debug(f"Silence trimmed: {wav.shape[-1]} -> {wav_trimmed.shape[-1]} samples")
                return wav_trimmed
            
            return wav
        except Exception as e:
            logger.warning(f"Silence trimming failed: {e}")
            return wav
    
    def _adjust_audio_length(self, wav: torch.Tensor, sampling_rate: int) -> torch.Tensor:
        """音声長さの調整"""
        try:
            duration = wav.shape[-1] / sampling_rate
            min_duration = 3.0  # 最小3秒
            max_duration = 30.0  # 最大30秒
            
            if duration < min_duration:
                # 短すぎる場合は繰り返し
                repeat_count = int(min_duration / duration) + 1
                wav = wav.repeat(1, repeat_count) if wav.dim() > 1 else wav.repeat(repeat_count)
                
                # 必要な長さに切り詰め
                target_samples = int(min_duration * sampling_rate)
                wav = wav[..., :target_samples]
                logger.debug(f"Audio repeated and trimmed to {min_duration}s")
                
            elif duration > max_duration:
                # 長すぎる場合は切り詰め
                target_samples = int(max_duration * sampling_rate)
                wav = wav[..., :target_samples]
                logger.debug(f"Audio trimmed to {max_duration}s")
            
            return wav
        except Exception as e:
            logger.warning(f"Audio length adjustment failed: {e}")
            return wav
    
    # キャッシュシステム
    def generate_cache_key(self, text: str, emotion: str, language: str, 
                          voice_sample: Optional[str] = None) -> str:
        """音声キャッシュキーを生成
        
        Args:
            text: 生成テキスト
            emotion: 感情設定
            language: 言語設定
            voice_sample: 音声サンプルパス（オプション）
            
        Returns:
            str: キャッシュキー
        """
        cache_data = {
            'text': text.strip().lower(),
            'emotion': emotion,
            'language': language,
            'model': self.tts_config.model_name
        }
        
        if voice_sample:
            # 音声サンプルのハッシュを含める
            try:
                with open(voice_sample, 'rb') as f:
                    sample_hash = hashlib.md5(f.read()).hexdigest()[:8]
                cache_data['voice_sample_hash'] = sample_hash
            except Exception as e:
                logger.warning(f"Failed to hash voice sample: {e}")
                cache_data['voice_sample'] = str(voice_sample)
        
        content = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def get_from_cache(self, cache_key: str) -> Optional[str]:
        """音声キャッシュから取得
        
        Args:
            cache_key: キャッシュキー
            
        Returns:
            Optional[str]: キャッシュされた音声ファイルパスまたはNone
        """
        if not self.tts_config.enable_audio_cache:
            return None
        
        with self._cache_lock:
            cache_entry = self._audio_cache.get(cache_key)
            
            if cache_entry:
                # TTLチェック
                cached_time = datetime.fromisoformat(cache_entry['created_at'])
                if datetime.now() - cached_time < timedelta(hours=self.tts_config.cache_ttl_hours):
                    # ファイル存在チェック
                    if Path(cache_entry['file_path']).exists():
                        self._metrics['cache_hits'] += 1
                        logger.debug(f"Audio cache hit: {cache_key[:8]}...")
                        return cache_entry['file_path']
                    else:
                        # ファイルが削除されている場合はキャッシュエントリも削除
                        del self._audio_cache[cache_key]
                else:
                    # 期限切れのエントリを削除
                    del self._audio_cache[cache_key]
        
        self._metrics['cache_misses'] += 1
        return None
    
    def save_to_cache(self, cache_key: str, file_path: str) -> None:
        """音声キャッシュに保存
        
        Args:
            cache_key: キャッシュキー
            file_path: 音声ファイルパス
        """
        if not self.tts_config.enable_audio_cache:
            return
        
        with self._cache_lock:
            # キャッシュサイズ制限チェック
            current_size = self._calculate_cache_size_mb()
            
            if current_size > self.tts_config.max_cache_size_mb:
                self._cleanup_cache_by_size()
            
            self._audio_cache[cache_key] = {
                'file_path': file_path,
                'created_at': datetime.now().isoformat(),
                'file_size_mb': Path(file_path).stat().st_size / (1024 * 1024)
            }
    
    def _calculate_cache_size_mb(self) -> float:
        """現在のキャッシュサイズを計算（MB）"""
        total_size = 0
        for entry in self._audio_cache.values():
            total_size += entry.get('file_size_mb', 0)
        return total_size
    
    def _cleanup_cache_by_size(self) -> None:
        """サイズ制限に基づいてキャッシュをクリーンアップ"""
        # 古いエントリから削除（LRU風）
        sorted_entries = sorted(
            self._audio_cache.items(),
            key=lambda x: x[1]['created_at']
        )
        
        current_size = self._calculate_cache_size_mb()
        target_size = self.tts_config.max_cache_size_mb * 0.8  # 80%まで削減
        
        deleted_count = 0
        for cache_key, entry in sorted_entries:
            if current_size <= target_size:
                break
            
            # ファイル削除
            try:
                Path(entry['file_path']).unlink(missing_ok=True)
                current_size -= entry.get('file_size_mb', 0)
                del self._audio_cache[cache_key]
                deleted_count += 1
            except Exception as e:
                logger.warning(f"Failed to delete cache file: {e}")
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} audio cache entries for size limit")
    
    def clear_cache(self) -> int:
        """音声キャッシュをクリア
        
        Returns:
            int: クリアしたエントリ数
        """
        with self._cache_lock:
            deleted_count = 0
            
            # ファイル削除
            for entry in self._audio_cache.values():
                try:
                    Path(entry['file_path']).unlink(missing_ok=True)
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"Failed to delete cache file: {e}")
            
            # キャッシュクリア
            self._audio_cache.clear()
            
            logger.info(f"Cleared {deleted_count} audio cache entries")
            return deleted_count
    
    def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        """古いキャッシュファイルを削除
        
        Args:
            max_age_hours: 保持時間（時間）
            
        Returns:
            int: 削除されたファイル数
        """
        try:
            deleted_count = 0
            current_time = datetime.now()
            
            for file_path in self.tts_config.audio_cache_dir.glob("*.wav"):
                file_age = current_time - datetime.fromtimestamp(file_path.stat().st_mtime)
                
                if file_age.total_seconds() > max_age_hours * 3600:
                    file_path.unlink()
                    deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old audio cache files")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old audio files: {e}")
            return 0
    
    # 非同期処理
    async def generate_audio_async(self, generation_func, *args, **kwargs) -> str:
        """非同期音声生成
        
        Args:
            generation_func: 音声生成関数
            *args, **kwargs: 生成関数の引数
            
        Returns:
            str: 生成された音声ファイルパス
        """
        if not self.tts_config.enable_async_generation:
            return generation_func(*args, **kwargs)
        
        # スレッドプールで実行
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._thread_pool,
            generation_func,
            *args,
            **kwargs
        )
    
    def update_metrics(self, generation_time: float) -> None:
        """パフォーマンス指標を更新
        
        Args:
            generation_time: 生成時間（秒）
        """
        self._metrics['total_generations'] += 1
        self._metrics['total_generation_time'] += generation_time
        self._metrics['avg_generation_time'] = (
            self._metrics['total_generation_time'] / self._metrics['total_generations']
        )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """パフォーマンス指標を取得
        
        Returns:
            Dict[str, Any]: パフォーマンス指標
        """
        cache_stats = {
            'enabled': self.tts_config.enable_audio_cache,
            'size_mb': self._calculate_cache_size_mb(),
            'entries': len(self._audio_cache),
            'max_size_mb': self.tts_config.max_cache_size_mb,
            'ttl_hours': self.tts_config.cache_ttl_hours
        }
        
        return {
            'generation_metrics': self._metrics.copy(),
            'cache_stats': cache_stats,
            'optimization_settings': {
                'async_generation': self.tts_config.enable_async_generation,
                'max_worker_threads': self.tts_config.max_worker_threads
            }
        } 
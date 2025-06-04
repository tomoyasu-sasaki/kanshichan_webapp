"""
Voice Manager Service

音声ファイルの保存・管理・キャッシュ機能を提供するサービス
"""

import os
import hashlib
import json
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import uuid
import logging
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, asdict
import torchaudio  # 音声ファイル情報取得のために追加

from utils.logger import setup_logger
from utils.exceptions import AudioError, FileNotFoundError, wrap_exception

logger = setup_logger(__name__)


@dataclass
class AudioFileMetadata:
    """音声ファイルメタデータ"""
    file_path: str
    original_filename: str
    file_size: int
    duration_seconds: float
    sample_rate: int
    channels: int
    created_at: str
    audio_format: str
    compressed: bool = False
    voice_sample_for: Optional[str] = None  # 音声クローン用サンプルの場合、対象ユーザーID
    text_content: Optional[str] = None      # 合成音声の場合、元テキスト
    emotion: Optional[str] = None           # 使用された感情設定
    language: Optional[str] = None          # 使用された言語
    file_hash: Optional[str] = None         # ファイルハッシュ
    display_name: Optional[str] = None      # ユーザー設定の表示名


class VoiceManager:
    """音声ファイル管理サービス
    
    音声ファイルの効率的な保存・取得・管理機能を提供
    - 音声ファイルの保存・キャッシュ
    - ファイル圧縮・最適化
    - メタデータ管理
    - 自動クリーンアップ
    """
    
    def __init__(self, config: Dict[str, Any]):
        """音声マネージャー初期化
        
        Args:
            config: 設定辞書
        """
        self.config = config
        self.voice_config = config.get('voice_manager', {})
        
        # ディレクトリ設定（backendディレクトリ基準の絶対パス）
        base_dir_config = self.voice_config.get('base_dir', 'voice_data')
        
        # 現在のファイルからbackendディレクトリの絶対パスを取得
        current_file = Path(__file__).resolve()
        backend_dir = current_file.parent.parent.parent  # services/voice_manager.py から backend/ への相対パス
        
        # 設定値が絶対パスでない場合は、backendディレクトリからの相対パスとして処理
        if Path(base_dir_config).is_absolute():
            self.base_dir = Path(base_dir_config)
        else:
            self.base_dir = backend_dir / base_dir_config
        
        self.cache_dir = self.base_dir / 'cache'
        self.samples_dir = self.base_dir / 'samples'
        self.generated_dir = self.base_dir / 'generated'
        self.metadata_dir = self.base_dir / 'metadata'
        
        # 設定値
        self.enable_compression = self.voice_config.get('enable_compression', True)
        self.auto_cleanup_hours = self.voice_config.get('auto_cleanup_hours', 24)
        self.max_cache_size_mb = self.voice_config.get('max_cache_size_mb', 1024)
        self.compression_quality = self.voice_config.get('compression_quality', 0.5)
        
        # ディレクトリ作成
        self._create_directories()
        
        # メタデータファイルパス
        self.metadata_file = self.metadata_dir / 'voice_files.json'
        self.metadata = self._load_metadata()
        
        logger.info(f"VoiceManager initialized - Base dir: {self.base_dir}")
        logger.debug(f"Backend dir resolved to: {backend_dir}")
        logger.debug(f"Final base_dir path: {self.base_dir}")
    
    def _create_directories(self) -> None:
        """必要なディレクトリを作成"""
        for directory in [self.base_dir, self.cache_dir, self.samples_dir, 
                         self.generated_dir, self.metadata_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _load_metadata(self) -> Dict[str, AudioFileMetadata]:
        """メタデータファイルを読み込み
        
        Returns:
            Dict[str, AudioFileMetadata]: ファイルID -> メタデータのマップ
        """
        if not self.metadata_file.exists():
            return {}
        
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                metadata_dict = json.load(f)
            
            # 辞書からAudioFileMetadataオブジェクトに変換
            metadata = {}
            for file_id, data in metadata_dict.items():
                # 互換性のための処理：古いデータにdisplay_nameがない場合
                if 'display_name' not in data:
                    data['display_name'] = None
                metadata[file_id] = AudioFileMetadata(**data)
            
            logger.info(f"Loaded metadata for {len(metadata)} audio files")
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")
            return {}
    
    def _save_metadata(self) -> None:
        """メタデータをファイルに保存"""
        try:
            # AudioFileMetadataオブジェクトを辞書に変換
            metadata_dict = {}
            for file_id, metadata in self.metadata.items():
                metadata_dict[file_id] = asdict(metadata)
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata_dict, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Metadata saved for {len(metadata_dict)} files")
            
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def save_audio_file(self,
                       audio_path: str,
                       file_type: str = 'generated',
                       metadata: Optional[Dict[str, Any]] = None,
                       compress: Optional[bool] = None) -> str:
        """音声ファイルを保存
        
        Args:
            audio_path: 保存する音声ファイルパス
            file_type: ファイルタイプ ('generated', 'sample', 'cache')
            metadata: 追加メタデータ
            compress: 圧縮するかどうか（Noneの場合は設定値を使用）
            
        Returns:
            str: 保存されたファイルのID
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        try:
            # ファイル情報取得
            audio_info = self._get_audio_info(audio_path)
            file_id = self._generate_file_id(audio_path, audio_info)
            
            # 保存先ディレクトリ決定
            if file_type == 'sample':
                target_dir = self.samples_dir
            elif file_type == 'cache':
                target_dir = self.cache_dir
            else:
                target_dir = self.generated_dir
            
            # ファイル名生成
            original_name = Path(audio_path).name
            saved_filename = f"{file_id}_{original_name}"
            saved_path = target_dir / saved_filename
            
            # ファイルコピーまたは圧縮
            should_compress = compress if compress is not None else self.enable_compression
            if should_compress and file_type != 'sample':  # サンプルファイルは圧縮しない
                compressed_path = self._compress_audio_file(audio_path, saved_path)
                saved_path = compressed_path
                compressed = True
            else:
                shutil.copy2(audio_path, saved_path)
                compressed = False
            
            # メタデータ作成
            file_metadata = AudioFileMetadata(
                file_path=str(saved_path),
                original_filename=original_name,
                file_size=os.path.getsize(saved_path),
                duration_seconds=audio_info['duration'],
                sample_rate=audio_info['sample_rate'],
                channels=audio_info['channels'],
                created_at=datetime.now().isoformat(),
                audio_format=audio_info['format'],
                compressed=compressed,
                file_hash=self._calculate_file_hash(audio_path)
            )
            
            # 追加メタデータを設定
            if metadata:
                if 'voice_sample_for' in metadata:
                    file_metadata.voice_sample_for = metadata['voice_sample_for']
                if 'text_content' in metadata:
                    file_metadata.text_content = metadata['text_content']
                if 'emotion' in metadata:
                    file_metadata.emotion = metadata['emotion']
                if 'language' in metadata:
                    file_metadata.language = metadata['language']
                if 'display_name' in metadata:
                    file_metadata.display_name = metadata['display_name']
            
            # メタデータ保存
            self.metadata[file_id] = file_metadata
            self._save_metadata()
            
            logger.info(f"Audio file saved: {file_id} ({file_type})")
            return file_id
            
        except Exception as e:
            error = wrap_exception(
                e, AudioError,
                f"Failed to save audio file: {audio_path}",
                details={
                    'audio_path': audio_path,
                    'file_type': file_type,
                    'target_dir': str(target_dir) if 'target_dir' in locals() else None
                }
            )
            logger.error(f"Audio save error: {error.to_dict()}")
            raise AudioError(f"Failed to save audio file: {str(e)}")
    
    def get_audio_file(self, file_id: str) -> Tuple[str, AudioFileMetadata]:
        """音声ファイルを取得
        
        Args:
            file_id: ファイルID
            
        Returns:
            Tuple[str, AudioFileMetadata]: (ファイルパス, メタデータ)
        """
        if file_id not in self.metadata:
            raise FileNotFoundError(f"Audio file not found: {file_id}")
        
        metadata = self.metadata[file_id]
        file_path = metadata.file_path
        
        if not os.path.exists(file_path):
            logger.warning(f"Audio file missing: {file_path}")
            # メタデータから削除
            del self.metadata[file_id]
            self._save_metadata()
            raise FileNotFoundError(f"Audio file missing: {file_id}")
        
        # 圧縮ファイルの場合は展開
        if metadata.compressed:
            decompressed_path = self._decompress_audio_file(file_path)
            return decompressed_path, metadata
        
        return file_path, metadata
    
    def list_audio_files(self, 
                        file_type: Optional[str] = None,
                        user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """音声ファイル一覧を取得
        
        Args:
            file_type: フィルタするファイルタイプ
            user_id: フィルタするユーザーID
            
        Returns:
            List[Dict[str, Any]]: ファイル情報リスト
        """
        results = []
        
        for file_id, metadata in self.metadata.items():
            # ファイルタイプフィルタ
            if file_type:
                if file_type == 'sample' and 'samples' not in metadata.file_path:
                    continue
                elif file_type == 'generated' and 'generated' not in metadata.file_path:
                    continue
                elif file_type == 'cache' and 'cache' not in metadata.file_path:
                    continue
            
            # ユーザーIDフィルタ
            if user_id and metadata.voice_sample_for != user_id:
                continue
            
            file_info = asdict(metadata)
            file_info['file_id'] = file_id
            file_info['exists'] = os.path.exists(metadata.file_path)
            # 表示名の設定：display_nameがあればそれを、なければoriginal_filenameを使用
            file_info['filename'] = metadata.display_name if metadata.display_name else metadata.original_filename
            results.append(file_info)
        
        return results
    
    def delete_audio_file(self, file_id: str) -> bool:
        """音声ファイルを削除
        
        Args:
            file_id: ファイルID
            
        Returns:
            bool: 削除成功フラグ
        """
        if file_id not in self.metadata:
            logger.warning(f"Audio file ID not found: {file_id}")
            return False
        
        try:
            metadata = self.metadata[file_id]
            file_path = metadata.file_path
            
            # ファイル削除
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # メタデータから削除
            del self.metadata[file_id]
            self._save_metadata()
            
            logger.info(f"Audio file deleted: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete audio file {file_id}: {e}")
            return False
    
    def _get_audio_info(self, audio_path: str) -> Dict[str, Any]:
        """音声ファイル情報を取得
        
        Args:
            audio_path: 音声ファイルパス
            
        Returns:
            Dict[str, Any]: 音声ファイル情報
        """
        try:
            # ファイルの存在確認
            if not os.path.exists(audio_path):
                raise AudioError(f"Audio file not found: {audio_path}")
            
            # torchaudioで音声ファイルを読み込み
            wav, sample_rate = torchaudio.load(audio_path)
            duration = wav.shape[1] / sample_rate
            channels = wav.shape[0]
            file_format = Path(audio_path).suffix.lower().lstrip('.')
            
            # 基本的な検証
            if duration <= 0:
                raise AudioError(f"Invalid audio duration: {duration}")
            if sample_rate <= 0:
                raise AudioError(f"Invalid sample rate: {sample_rate}")
            if channels <= 0:
                raise AudioError(f"Invalid channel count: {channels}")
            
            logger.debug(f"Audio info extracted: duration={duration:.2f}s, rate={sample_rate}Hz, channels={channels}")
            
            return {
                'duration': duration,
                'sample_rate': sample_rate,
                'channels': channels,
                'format': file_format
            }
            
        except Exception as e:
            # より詳細なエラー情報を提供
            error_details = {
                'audio_path': audio_path,
                'file_exists': os.path.exists(audio_path) if audio_path else False,
                'file_size': os.path.getsize(audio_path) if os.path.exists(audio_path) else 0,
                'torchaudio_available': 'torchaudio' in globals()
            }
            
            logger.error(f"Failed to get audio info: {str(e)}, details: {error_details}")
            raise AudioError(f"Failed to get audio info: {str(e)}", details=error_details)
    
    def _generate_file_id(self, audio_path: str, audio_info: Dict[str, Any]) -> str:
        """ファイルIDを生成
        
        Args:
            audio_path: 音声ファイルパス
            audio_info: 音声ファイル情報
            
        Returns:
            str: 生成されたファイルID
        """
        # ファイル内容とメタデータからハッシュ生成
        content_hash = self._calculate_file_hash(audio_path)
        info_str = f"{audio_info['duration']:.2f}_{audio_info['sample_rate']}_{audio_info['channels']}"
        combined = f"{content_hash}_{info_str}"
        
        file_id = hashlib.md5(combined.encode()).hexdigest()[:16]
        return file_id
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """ファイルハッシュを計算
        
        Args:
            file_path: ファイルパス
            
        Returns:
            str: ファイルハッシュ
        """
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _compress_audio_file(self, source_path: str, target_path: Path) -> Path:
        """音声ファイルを圧縮
        
        Args:
            source_path: 元ファイルパス
            target_path: 保存先パス
            
        Returns:
            Path: 圧縮ファイルパス
        """
        compressed_path = target_path.with_suffix(target_path.suffix + '.gz')
        
        try:
            with open(source_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            logger.debug(f"Audio file compressed: {source_path} -> {compressed_path}")
            return compressed_path
            
        except Exception as e:
            logger.error(f"Failed to compress audio file: {e}")
            # 圧縮に失敗した場合は通常コピー
            shutil.copy2(source_path, target_path)
            return target_path
    
    def _decompress_audio_file(self, compressed_path: str) -> str:
        """圧縮音声ファイルを展開
        
        Args:
            compressed_path: 圧縮ファイルパス
            
        Returns:
            str: 展開されたファイルパス
        """
        decompressed_path = compressed_path.replace('.gz', '')
        temp_path = f"/tmp/{Path(decompressed_path).name}"
        
        try:
            with gzip.open(compressed_path, 'rb') as f_in:
                with open(temp_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            logger.debug(f"Audio file decompressed: {compressed_path} -> {temp_path}")
            return temp_path
            
        except Exception as e:
            raise AudioError(f"Failed to decompress audio file: {str(e)}")
    
    def cleanup_old_files(self, max_age_hours: Optional[int] = None) -> int:
        """古いファイルをクリーンアップ
        
        Args:
            max_age_hours: 保持時間（時間）
            
        Returns:
            int: 削除されたファイル数
        """
        max_age = max_age_hours or self.auto_cleanup_hours
        cutoff_time = datetime.now() - timedelta(hours=max_age)
        deleted_count = 0
        
        files_to_delete = []
        
        for file_id, metadata in self.metadata.items():
            created_at = datetime.fromisoformat(metadata.created_at)
            
            # キャッシュファイルのみ自動削除対象
            if 'cache' in metadata.file_path and created_at < cutoff_time:
                files_to_delete.append(file_id)
        
        # ファイル削除実行
        for file_id in files_to_delete:
            if self.delete_audio_file(file_id):
                deleted_count += 1
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old audio files")
        
        return deleted_count
    
    def get_cache_size(self) -> Dict[str, Any]:
        """キャッシュサイズ情報を取得
        
        Returns:
            Dict[str, Any]: キャッシュサイズ情報
        """
        total_size = 0
        file_count = 0
        
        for file_id, metadata in self.metadata.items():
            if 'cache' in metadata.file_path:
                total_size += metadata.file_size
                file_count += 1
        
        total_size_mb = total_size / (1024 * 1024)
        
        return {
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size_mb, 2),
            'file_count': file_count,
            'max_size_mb': self.max_cache_size_mb,
            'usage_percentage': round((total_size_mb / self.max_cache_size_mb) * 100, 1)
        }
    
    def get_service_status(self) -> Dict[str, Any]:
        """サービス状態を取得
        
        Returns:
            Dict[str, Any]: サービス状態情報
        """
        cache_info = self.get_cache_size()
        
        return {
            'base_directory': str(self.base_dir),
            'total_files': len(self.metadata),
            'cache_info': cache_info,
            'compression_enabled': self.enable_compression,
            'auto_cleanup_hours': self.auto_cleanup_hours,
            'directories': {
                'cache': str(self.cache_dir),
                'samples': str(self.samples_dir),
                'generated': str(self.generated_dir),
                'metadata': str(self.metadata_dir)
            }
        } 
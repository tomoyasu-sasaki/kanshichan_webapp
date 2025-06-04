"""
Storage Service

効率的なデータ保存・管理サービス
"""

import os
import gzip
import json
import shutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

from models.behavior_log import BehaviorLog
from models.analysis_result import AnalysisResult
from models import db
from utils.logger import setup_logger

logger = setup_logger(__name__)


class StorageService:
    """データ保存サービス
    
    効率的なデータ保存、圧縮、アーカイブ、削除機能を提供
    """
    
    def __init__(self, 
                 backup_dir: str = "./data/backups",
                 archive_dir: str = "./data/archives",
                 retention_days: int = 90):
        """初期化
        
        Args:
            backup_dir: バックアップディレクトリ
            archive_dir: アーカイブディレクトリ
            retention_days: データ保持期間（日）
        """
        self.backup_dir = Path(backup_dir)
        self.archive_dir = Path(archive_dir)
        self.retention_days = retention_days
        
        # ディレクトリ作成
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"StorageService initialized - retention: {retention_days} days")
    
    def save_behavior_logs_batch(self, logs_data: List[Dict[str, Any]]) -> bool:
        """行動ログをバッチ保存
        
        Args:
            logs_data: 行動ログデータのリスト
            
        Returns:
            bool: 保存成功フラグ
        """
        if not logs_data:
            return True
        
        try:
            db.session.begin()
            
            logs_to_save = []
            for log_data in logs_data:
                behavior_log = BehaviorLog.create_log(**log_data)
                logs_to_save.append(behavior_log)
            
            # バッチ保存
            db.session.add_all(logs_to_save)
            db.session.commit()
            
            logger.debug(f"Batch saved {len(logs_to_save)} behavior logs")
            return True
            
        except Exception as e:
            logger.error(f"Error in batch save behavior logs: {e}")
            db.session.rollback()
            return False
    
    def save_analysis_result(self, analysis_data: Dict[str, Any]) -> bool:
        """分析結果を保存
        
        Args:
            analysis_data: 分析結果データ
            
        Returns:
            bool: 保存成功フラグ
        """
        try:
            analysis_result = AnalysisResult.create_analysis(**analysis_data)
            analysis_result.save()
            
            logger.debug(f"Saved analysis result: {analysis_result.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving analysis result: {e}")
            return False
    
    def compress_old_data(self, days_threshold: int = 30) -> bool:
        """古いデータを圧縮してアーカイブ
        
        Args:
            days_threshold: 圧縮対象の日数閾値
            
        Returns:
            bool: 圧縮成功フラグ
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)
            
            # 古い行動ログを取得
            old_logs = BehaviorLog.query.filter(
                BehaviorLog.created_at < cutoff_date
            ).all()
            
            if not old_logs:
                logger.info("No old logs to compress")
                return True
            
            # 日付別にグループ化
            logs_by_date = {}
            for log in old_logs:
                date_key = log.created_at.date().isoformat()
                if date_key not in logs_by_date:
                    logs_by_date[date_key] = []
                logs_by_date[date_key].append(log.to_dict())
            
            # 日付別に圧縮保存
            compressed_count = 0
            for date_key, logs in logs_by_date.items():
                if self._compress_logs_for_date(date_key, logs):
                    compressed_count += len(logs)
            
            logger.info(f"Compressed {compressed_count} old logs")
            return True
            
        except Exception as e:
            logger.error(f"Error compressing old data: {e}")
            return False
    
    def _compress_logs_for_date(self, date_key: str, logs: List[Dict[str, Any]]) -> bool:
        """指定日のログを圧縮
        
        Args:
            date_key: 日付キー (YYYY-MM-DD)
            logs: ログデータのリスト
            
        Returns:
            bool: 圧縮成功フラグ
        """
        try:
            archive_file = self.archive_dir / f"behavior_logs_{date_key}.json.gz"
            
            # JSON形式でシリアライズ
            json_data = json.dumps(logs, ensure_ascii=False, indent=2)
            
            # gzip圧縮して保存
            with gzip.open(archive_file, 'wt', encoding='utf-8') as f:
                f.write(json_data)
            
            logger.debug(f"Compressed {len(logs)} logs for {date_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error compressing logs for {date_key}: {e}")
            return False
    
    def delete_old_data(self, force: bool = False) -> Dict[str, int]:
        """古いデータを削除
        
        Args:
            force: 強制削除フラグ
            
        Returns:
            dict: 削除統計
        """
        stats = {
            'deleted_logs': 0,
            'deleted_analyses': 0,
            'deleted_archives': 0
        }
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
            
            # 古い行動ログを削除
            old_logs = BehaviorLog.query.filter(
                BehaviorLog.created_at < cutoff_date
            )
            stats['deleted_logs'] = old_logs.count()
            
            if stats['deleted_logs'] > 0 and (force or self._confirm_deletion()):
                old_logs.delete(synchronize_session=False)
                db.session.commit()
                logger.info(f"Deleted {stats['deleted_logs']} old behavior logs")
            
            # 古い分析結果を削除
            old_analyses = AnalysisResult.query.filter(
                AnalysisResult.created_at < cutoff_date
            )
            stats['deleted_analyses'] = old_analyses.count()
            
            if stats['deleted_analyses'] > 0 and (force or self._confirm_deletion()):
                old_analyses.delete(synchronize_session=False)
                db.session.commit()
                logger.info(f"Deleted {stats['deleted_analyses']} old analysis results")
            
            # 古いアーカイブファイルを削除
            stats['deleted_archives'] = self._delete_old_archives()
            
            return stats
            
        except Exception as e:
            logger.error(f"Error deleting old data: {e}")
            db.session.rollback()
            return stats
    
    def _delete_old_archives(self) -> int:
        """古いアーカイブファイルを削除
        
        Returns:
            int: 削除したファイル数
        """
        deleted_count = 0
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days * 2)  # アーカイブは2倍長く保持
            
            for archive_file in self.archive_dir.glob("*.gz"):
                file_stat = archive_file.stat()
                file_date = datetime.fromtimestamp(file_stat.st_mtime)
                
                if file_date < cutoff_date:
                    archive_file.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted old archive: {archive_file.name}")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error deleting old archives: {e}")
            return deleted_count
    
    def _confirm_deletion(self) -> bool:
        """削除確認（本番環境では慎重に）
        
        Returns:
            bool: 削除実行フラグ
        """
        # 開発環境では自動実行、本番環境では手動確認
        env = os.getenv('FLASK_ENV', 'development')
        if env == 'production':
            # 本番環境では管理者による手動削除を推奨
            return False
        return True
    
    def backup_database(self) -> bool:
        """データベースをバックアップ
        
        Returns:
            bool: バックアップ成功フラグ
        """
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"kanshichan_backup_{timestamp}.json.gz"
            
            # 全データを取得
            all_logs = BehaviorLog.query.all()
            all_analyses = AnalysisResult.query.all()
            
            backup_data = {
                'timestamp': timestamp,
                'behavior_logs': [log.to_dict() for log in all_logs],
                'analysis_results': [analysis.to_dict() for analysis in all_analyses]
            }
            
            # 圧縮してバックアップ
            json_data = json.dumps(backup_data, ensure_ascii=False, default=str)
            
            with gzip.open(backup_file, 'wt', encoding='utf-8') as f:
                f.write(json_data)
            
            logger.info(f"Database backup created: {backup_file.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating database backup: {e}")
            return False
    
    def restore_from_backup(self, backup_file_path: str) -> bool:
        """バックアップからデータを復元
        
        Args:
            backup_file_path: バックアップファイルパス
            
        Returns:
            bool: 復元成功フラグ
        """
        try:
            backup_file = Path(backup_file_path)
            if not backup_file.exists():
                logger.error(f"Backup file not found: {backup_file_path}")
                return False
            
            # バックアップファイルを読み込み
            with gzip.open(backup_file, 'rt', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # データベーストランザクション開始
            db.session.begin()
            
            # 行動ログの復元
            behavior_logs_data = backup_data.get('behavior_logs', [])
            for log_data in behavior_logs_data:
                # 既存データとの重複チェック
                existing_log = BehaviorLog.query.filter_by(
                    timestamp=datetime.fromisoformat(log_data['timestamp'])
                ).first()
                
                if not existing_log:
                    # 新しいログとして追加
                    log_data.pop('id', None)  # IDを除去して新規作成
                    behavior_log = BehaviorLog(**log_data)
                    db.session.add(behavior_log)
            
            # 分析結果の復元
            analysis_results_data = backup_data.get('analysis_results', [])
            for analysis_data in analysis_results_data:
                # 既存データとの重複チェック
                existing_analysis = AnalysisResult.query.filter_by(
                    analysis_start_time=datetime.fromisoformat(analysis_data['analysis_start_time']),
                    analysis_type=analysis_data['analysis_type']
                ).first()
                
                if not existing_analysis:
                    # 新しい分析結果として追加
                    analysis_data.pop('id', None)  # IDを除去して新規作成
                    analysis_result = AnalysisResult(**analysis_data)
                    db.session.add(analysis_result)
            
            db.session.commit()
            logger.info(f"Database restored from backup: {backup_file.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring from backup: {e}")
            db.session.rollback()
            return False
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """ストレージ統計を取得
        
        Returns:
            dict: ストレージ統計情報
        """
        try:
            # データベース統計
            total_logs = BehaviorLog.query.count()
            total_analyses = AnalysisResult.query.count()
            
            # 最新・最古のデータ日時
            latest_log = BehaviorLog.query.order_by(BehaviorLog.created_at.desc()).first()
            oldest_log = BehaviorLog.query.order_by(BehaviorLog.created_at.asc()).first()
            
            # ディスク使用量（概算）
            backup_size = sum(f.stat().st_size for f in self.backup_dir.glob("*.gz")) / 1024 / 1024  # MB
            archive_size = sum(f.stat().st_size for f in self.archive_dir.glob("*.gz")) / 1024 / 1024  # MB
            
            stats = {
                'database': {
                    'total_behavior_logs': total_logs,
                    'total_analysis_results': total_analyses,
                    'latest_data': latest_log.created_at.isoformat() if latest_log else None,
                    'oldest_data': oldest_log.created_at.isoformat() if oldest_log else None
                },
                'storage': {
                    'backup_size_mb': round(backup_size, 2),
                    'archive_size_mb': round(archive_size, 2),
                    'total_size_mb': round(backup_size + archive_size, 2)
                },
                'files': {
                    'backup_files': len(list(self.backup_dir.glob("*.gz"))),
                    'archive_files': len(list(self.archive_dir.glob("*.gz")))
                },
                'retention': {
                    'retention_days': self.retention_days,
                    'archive_retention_days': self.retention_days * 2
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {}
    
    def optimize_database(self) -> bool:
        """データベースを最適化
        
        Returns:
            bool: 最適化成功フラグ
        """
        try:
            # SQLiteの場合はVACUUM実行
            db.session.execute("VACUUM")
            db.session.commit()
            
            # インデックスの再構築（必要に応じて）
            db.session.execute("REINDEX")
            db.session.commit()
            
            logger.info("Database optimization completed")
            return True
            
        except Exception as e:
            logger.error(f"Error optimizing database: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """ストレージシステムのヘルスチェック
        
        Returns:
            dict: ヘルスチェック結果
        """
        health = {
            'status': 'healthy',
            'issues': [],
            'recommendations': []
        }
        
        try:
            # データベース接続確認
            db.session.execute("SELECT 1")
            
            # ディスク容量確認
            stats = self.get_storage_stats()
            total_size_mb = stats.get('storage', {}).get('total_size_mb', 0)
            
            if total_size_mb > 1000:  # 1GB以上
                health['issues'].append("Large storage usage detected")
                health['recommendations'].append("Consider archiving old data")
            
            # 古いデータの確認
            cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
            old_logs_count = BehaviorLog.query.filter(
                BehaviorLog.created_at < cutoff_date
            ).count()
            
            if old_logs_count > 1000:
                health['issues'].append(f"Found {old_logs_count} old logs")
                health['recommendations'].append("Run data cleanup process")
            
            # ディレクトリの書き込み権限確認
            if not os.access(self.backup_dir, os.W_OK):
                health['issues'].append("Backup directory not writable")
                health['status'] = 'warning'
            
            if not os.access(self.archive_dir, os.W_OK):
                health['issues'].append("Archive directory not writable")
                health['status'] = 'warning'
            
            if health['issues']:
                health['status'] = 'warning' if health['status'] == 'healthy' else health['status']
            
        except Exception as e:
            health['status'] = 'error'
            health['issues'].append(f"Database connection error: {str(e)}")
        
        return health 
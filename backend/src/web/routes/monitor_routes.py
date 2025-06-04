"""
Monitor API Routes - システム監視API

システム全体の監視・状態管理機能のAPIエンドポイント
"""

import logging
from typing import Dict, Any, Optional
from flask import Blueprint, jsonify, request
from datetime import datetime

# Monitor の簡素化ラッパークラス
class SimpleMonitor:
    """Monitor API用の簡素化されたMonitorラッパークラス"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_active = True
        self.initialized_at = datetime.utcnow()
        
    def start(self):
        """監視開始（シミュレーション）"""
        self.is_active = True
        
    def stop(self):
        """監視停止（シミュレーション）"""
        self.is_active = False
        
    def get_camera_status(self):
        """カメラ状態取得（シミュレーション）"""
        return 'active' if self.is_active else 'inactive'
        
    def get_device_status(self):
        """デバイス状態取得（シミュレーション）"""
        return 'active' if self.is_active else 'inactive'

from models.behavior_log import BehaviorLog
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Blueprint定義
monitor_bp = Blueprint('monitor', __name__, url_prefix='/api/monitor')

# Monitorインスタンス（アプリケーション初期化時に設定）
monitor_instance: Optional[SimpleMonitor] = None


def init_monitor_service(config: Dict[str, Any]) -> None:
    """Monitorサービスを初期化
    
    Args:
        config: アプリケーション設定
    """
    global monitor_instance
    
    try:
        monitor_instance = SimpleMonitor(config)
        logger.info("Monitor service initialized successfully (simplified)")
    except Exception as e:
        logger.error(f"Failed to initialize Monitor service: {e}")
        raise


@monitor_bp.route('/status', methods=['GET'])
def get_monitor_status():
    """監視システムの状態取得API
    
    監視システム全体の健康状態とデータ収集状況を返す
    
    Returns:
        JSON: 監視システムの状態情報
    """
    try:
        # Monitor サービスの状態
        monitor_status = 'active' if monitor_instance and monitor_instance.is_active else 'inactive'
        
        # データ収集状況の確認
        try:
            # 最近1時間のログ取得でデータ収集確認
            recent_logs = BehaviorLog.get_recent_logs(hours=1)
            # 最初の10件だけ使用
            data_collection_status = 'active' if recent_logs else 'inactive'
            logs_count = len(recent_logs) if recent_logs else 0
        except Exception:
            data_collection_status = 'error'
            logs_count = 0
        
        # カメラ・デバイス状態（Monitor実装に依存）
        camera_status = 'unknown'
        device_status = 'unknown'
        
        if monitor_instance:
            try:
                camera_status = monitor_instance.get_camera_status()
                device_status = monitor_instance.get_device_status()
            except Exception as e:
                logger.warning(f"Error getting monitor device status: {e}")
        
        # 全体健康度計算
        active_services = sum([
            1 for status in [monitor_status, data_collection_status]
            if status == 'active'
        ])
        health_score = active_services / 2.0
        
        return jsonify({
            'status': 'success',
            'data': {
                'overall_status': 'healthy' if health_score >= 0.75 else 'degraded' if health_score >= 0.5 else 'critical',
                'health_score': health_score,
                'services': {
                    'monitor_service': monitor_status,
                    'data_collection': data_collection_status,
                    'camera': camera_status,
                    'device': device_status
                },
                'metrics': {
                    'recent_logs_count': logs_count,
                    'last_log_time': recent_logs[0].timestamp.isoformat() if recent_logs else None
                },
                'last_check': datetime.utcnow().isoformat()
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error checking monitor status: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': 'Failed to check monitor system status',
            'code': 'STATUS_CHECK_ERROR',
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@monitor_bp.route('/toggle', methods=['POST'])
def toggle_monitoring():
    """監視の開始/停止制御API
    
    Request Body:
        {
            "enabled": true/false
        }
    
    Returns:
        JSON: 操作結果
    """
    try:
        data = request.get_json()
        enabled = data.get('enabled', False)
        
        if not monitor_instance:
            return jsonify({
                'status': 'error',
                'error': 'Monitor service not available',
                'code': 'SERVICE_UNAVAILABLE',
                'timestamp': datetime.utcnow().isoformat()
            }), 503
        
        # Monitor の開始/停止メソッドが存在する場合の処理
        if hasattr(monitor_instance, 'start') and hasattr(monitor_instance, 'stop'):
            if enabled:
                monitor_instance.start()
                action = 'started'
            else:
                monitor_instance.stop()
                action = 'stopped'
        else:
            # メソッドが存在しない場合はシミュレーション
            action = 'started' if enabled else 'stopped'
            logger.info(f"Monitor service {action} (simulated)")
        
        return jsonify({
            'status': 'success',
            'data': {
                'monitoring_enabled': enabled,
                'action': action,
                'timestamp': datetime.utcnow().isoformat()
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error toggling monitoring: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': 'Failed to toggle monitoring',
            'code': 'TOGGLE_ERROR',
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@monitor_bp.route('/metrics', methods=['GET'])
def get_monitoring_metrics():
    """監視メトリクス取得API
    
    Query Parameters:
        timeframe (str): 取得期間 (hour/day/week) - デフォルト: hour
    
    Returns:
        JSON: 監視メトリクス
    """
    try:
        timeframe = request.args.get('timeframe', 'hour')
        
        if timeframe not in ['hour', 'day', 'week']:
            return jsonify({
                'status': 'error',
                'error': 'Invalid timeframe. Must be one of: hour, day, week',
                'code': 'VALIDATION_ERROR',
                'timestamp': datetime.utcnow().isoformat()
            }), 400
        
        # 期間に応じたデータ取得
        hours_map = {'hour': 1, 'day': 24, 'week': 168}
        hours = hours_map[timeframe]
        
        logs = BehaviorLog.get_recent_logs(hours=hours)
        
        # メトリクス計算
        metrics = {
            'total_logs': len(logs) if logs else 0,
            'timeframe': timeframe,
            'period_hours': hours,
            'collection_rate': len(logs) / hours if logs else 0,  # ログ/時間
            'last_activity': logs[0].timestamp.isoformat() if logs else None,
            'data_coverage': {
                'has_data': len(logs) > 0 if logs else False,
                'continuous_collection': True  # 実際の実装では継続性チェック
            }
        }
        
        return jsonify({
            'status': 'success',
            'data': metrics,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting monitoring metrics: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': 'Failed to get monitoring metrics',
            'code': 'METRICS_ERROR',
            'timestamp': datetime.utcnow().isoformat()
        }), 500 
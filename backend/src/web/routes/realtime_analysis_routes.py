"""
Realtime Analysis API Routes - リアルタイム分析API

リアルタイム分析機能のAPIエンドポイント群
リアルタイムデータストリーミング、ストリーミング状態監視、アラート管理、パフォーマンスレポートを提供
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, current_app

from utils.logger import setup_logger
from services.monitoring.alert_system import AlertSystem
from services.monitoring.performance_monitor import PerformanceMonitor
from .analysis_helpers import (
    generate_comprehensive_insights,
    calculate_behavior_score,
    detect_behavioral_patterns,
    generate_contextual_recommendations,
    calculate_data_quality_metrics
)

logger = setup_logger(__name__)

# Blueprint定義
realtime_analysis_bp = Blueprint('realtime_analysis', __name__, url_prefix='/api/analysis/realtime')


@realtime_analysis_bp.route('/realtime-stream', methods=['POST'])
def submit_realtime_data():
    """リアルタイムデータ投入API
    
    リアルタイム分析用のデータストリームに新しいデータポイントを追加
    
    Request JSON:
        {
            "user_id": "string",
            "data": {
                "eye_movement": {...},
                "pose_data": {...},
                "environment": {...}
            },
            "timestamp": "ISO datetime string (optional)"
        }
        
    Returns:
        JSON: データ投入結果
    """
    try:
        # リクエストデータ取得
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'error': 'No JSON data provided',
                'code': 'VALIDATION_ERROR',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 400
        
        # 必須フィールドチェック
        user_id = data.get('user_id')
        analysis_data = data.get('data')
        
        if not user_id:
            return jsonify({
                'status': 'error',
                'error': 'user_id is required',
                'code': 'VALIDATION_ERROR',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 400
        
        if not analysis_data:
            return jsonify({
                'status': 'error',
                'error': 'data is required',
                'code': 'VALIDATION_ERROR',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 400
        
        # リアルタイム分析器取得
        real_time_analyzer = _get_real_time_analyzer()
        if not real_time_analyzer:
            return jsonify({
                'status': 'error',
                'error': 'Real-time analyzer not available',
                'code': 'SERVICE_UNAVAILABLE',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 500
        
        # タイムスタンプ処理
        timestamp_str = data.get('timestamp')
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                analysis_data['timestamp'] = timestamp
            except ValueError:
                return jsonify({
                    'status': 'error',
                    'error': 'Invalid timestamp format',
                    'code': 'VALIDATION_ERROR',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }), 400
        
        analysis_data['user_id'] = user_id
        
        # データポイント追加
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(
                real_time_analyzer.add_data_point(analysis_data, user_id)
            )
        finally:
            loop.close()
        
        # 特徴量抽出
        features = real_time_analyzer.extract_realtime_features(analysis_data)
        
        return jsonify({
            'status': 'success',
            'data': {
                'user_id': user_id,
                'processed_at': datetime.now(timezone.utc).isoformat(),
                'extracted_features': features,
                'data_quality': features.get('data_quality', 0.0)
            },
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error processing realtime data: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': 'Failed to process realtime data',
            'code': 'PROCESSING_ERROR',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500


@realtime_analysis_bp.route('/streaming-status', methods=['GET'])
def get_streaming_status():
    """ストリーミング処理状態取得API
    
    リアルタイムストリーミングプロセッサーの現在の状態を取得
    
    Query Parameters:
        details (bool): 詳細情報含める - デフォルト: false
        
    Returns:
        JSON: ストリーミング処理状態
    """
    try:
        include_details = request.args.get('details', 'false').lower() == 'true'
        
        # ストリーミングプロセッサー取得
        streaming_processor = _get_streaming_processor()
        if not streaming_processor:
            return jsonify({
                'status': 'error',
                'error': 'Streaming processor not available',
                'code': 'SERVICE_UNAVAILABLE',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 500
        
        # リアルタイム分析器取得
        real_time_analyzer = _get_real_time_analyzer()
        
        # 状態取得
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # ストリーミング状態
            stream_status = loop.run_until_complete(
                streaming_processor.get_stream_status()
            )
            
            # リアルタイムメトリクス
            realtime_metrics = None
            if real_time_analyzer:
                realtime_metrics = real_time_analyzer.get_realtime_metrics()
        finally:
            loop.close()
        
        # レスポンス構築
        response_data = {
            'streaming_status': stream_status,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        if realtime_metrics:
            response_data['realtime_metrics'] = {
                'processing_latency_ms': realtime_metrics.processing_latency_ms,
                'throughput_fps': realtime_metrics.throughput_fps,
                'queue_depth': realtime_metrics.queue_depth,
                'error_rate': realtime_metrics.error_rate,
                'active_streams': realtime_metrics.active_streams
            }
        
        if include_details:
            # パフォーマンス監視
            performance_monitor = _get_performance_monitor()
            if performance_monitor:
                comprehensive_status = performance_monitor.get_comprehensive_status()
                response_data['performance_details'] = comprehensive_status
        
        return jsonify({
            'status': 'success',
            'data': response_data,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting streaming status: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': 'Failed to get streaming status',
            'code': 'STATUS_ERROR',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500


@realtime_analysis_bp.route('/alerts', methods=['GET'])
def get_active_alerts():
    """アクティブアラート取得API
    
    現在アクティブなアラートと統計情報を取得
    
    Query Parameters:
        level (str): フィルタするアラートレベル (info/warning/alert/critical)
        limit (int): 取得件数制限 - デフォルト: 50
        
    Returns:
        JSON: アクティブアラート一覧
    """
    try:
        # パラメータ取得
        level_filter = request.args.get('level')
        limit = int(request.args.get('limit', 50))
        
        # バリデーション
        if level_filter and level_filter not in ['high', 'medium', 'low']:
            return jsonify({
                'status': 'error',
                'error': 'Invalid alert level. Must be one of: high, medium, low',
                'code': 'VALIDATION_ERROR',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 400
        
        # アラートシステム取得
        alert_system = _get_alert_system()
        if not alert_system:
            return jsonify({
                'status': 'error',
                'error': 'Alert system not available',
                'code': 'SERVICE_UNAVAILABLE',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 500
        
        # アラート統計取得
        alert_stats = alert_system.get_alert_statistics()
        
        # アクティブアラート取得（実装に依存）
        active_alerts = []
        for alert_id, alert in alert_system.active_alerts.items():
            # レベルフィルタ
            if level_filter and alert.level.value != level_filter:
                continue
            
            alert_data = {
                'alert_id': alert.alert_id,
                'rule_id': alert.rule_id,
                'level': alert.level.value,
                'title': alert.title,
                'message': alert.message,
                'timestamp': alert.timestamp.isoformat(),
                'urgency_score': alert.urgency_score,
                'channels': [ch.value for ch in alert.channels],
                'status': alert.status.value
            }
            active_alerts.append(alert_data)
            
            if len(active_alerts) >= limit:
                break
        
        return jsonify({
            'status': 'success',
            'data': {
                'active_alerts': active_alerts,
                'statistics': alert_stats,
                'filter_applied': {
                    'level': level_filter,
                    'limit': limit
                }
            },
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting active alerts: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': 'Failed to get active alerts',
            'code': 'ALERTS_ERROR',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500


@realtime_analysis_bp.route('/performance-report', methods=['GET'])
def get_performance_report():
    """パフォーマンスレポート取得API
    
    システムパフォーマンスの詳細レポートを生成・取得
    
    Query Parameters:
        hours (int): レポート対象期間（時間） - デフォルト: 24
        format (str): レポート形式 (summary/detailed) - デフォルト: summary
        
    Returns:
        JSON: パフォーマンスレポート
    """
    try:
        # パラメータ取得
        hours = int(request.args.get('hours', 24))
        report_format = request.args.get('format', 'summary')
        
        # バリデーション
        if hours < 1 or hours > 24:
            return jsonify({
                'status': 'error',
                'error': 'Hours must be between 1 and 24',
                'code': 'VALIDATION_ERROR',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 400
        
        if report_format not in ['summary', 'detailed']:
            return jsonify({
                'status': 'error',
                'error': 'Format must be summary or detailed',
                'code': 'VALIDATION_ERROR',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 400
        
        # パフォーマンス監視取得
        performance_monitor = _get_performance_monitor()
        if not performance_monitor:
            return jsonify({
                'status': 'error',
                'error': 'Performance monitor not available',
                'code': 'SERVICE_UNAVAILABLE',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 500
        
        # レポート生成
        performance_report = performance_monitor.generate_performance_report(hours)
        
        # 現在の包括的状態も追加
        current_status = performance_monitor.get_comprehensive_status()
        
        # レスポンス構築
        response_data = {
            'performance_report': performance_report,
            'current_status': current_status,
            'report_parameters': {
                'period_hours': hours,
                'format': report_format,
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
        }
        
        # 詳細形式の場合は追加情報
        if report_format == 'detailed':
            # リアルタイム分析器メトリクス
            real_time_analyzer = _get_real_time_analyzer()
            if real_time_analyzer:
                response_data['realtime_analyzer_metrics'] = real_time_analyzer.get_realtime_metrics()
            
            # ストリーミングプロセッサー状態
            streaming_processor = _get_streaming_processor()
            if streaming_processor:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    stream_status = loop.run_until_complete(
                        streaming_processor.get_stream_status()
                    )
                    response_data['streaming_processor_status'] = stream_status
                finally:
                    loop.close()
            
            # アラートシステム統計
            alert_system = _get_alert_system()
            if alert_system:
                response_data['alert_system_statistics'] = alert_system.get_alert_statistics()
        
        return jsonify({
            'status': 'success',
            'data': response_data,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error generating performance report: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': 'Failed to generate performance report',
            'code': 'REPORT_ERROR',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500


# ========== ヘルパー関数 ==========

def _get_real_time_analyzer() -> Optional[Any]:
    """リアルタイム分析器インスタンス取得
    
    RealTimeAnalyzerのインスタンスを作成し、設定を適用します。
    ストリーミングデータのリアルタイム解析に使用されます。
    
    Returns:
        Optional[Any]: RealTimeAnalyzerインスタンス、またはエラー時はNone
        
    Note:
        設定はFlaskのcurrent_app.configから取得されます。
        初期化に失敗した場合はログに記録し、Noneを返します。
    """
    try:
        from services.streaming.real_time_analyzer import RealTimeAnalyzer
        config = current_app.config.get('config_manager').get_all()
        return RealTimeAnalyzer(config)
    except Exception as e:
        logger.error(f"Error creating RealTimeAnalyzer: {e}")
    return None


def _get_streaming_processor() -> Optional[Any]:
    """ストリーミングプロセッサーインスタンス取得
    
    StreamingProcessorのインスタンスを作成し、設定を適用します。
    リアルタイムデータストリーミング処理に使用されます。
    
    Returns:
        Optional[Any]: StreamingProcessorインスタンス、またはエラー時はNone
        
    Note:
        設定はFlaskのcurrent_app.configから取得されます。
        初期化に失敗した場合はログに記録し、Noneを返します。
    """
    try:
        from services.streaming.streaming_processor import StreamingProcessor
        config = current_app.config.get('config_manager').get_all()
        return StreamingProcessor(config)
    except Exception as e:
        logger.error(f"Error creating StreamingProcessor: {e}")
    return None


def _get_alert_system() -> Optional[AlertSystem]:
    """AlertSystemインスタンス取得"""
    try:
        config = current_app.config.get('ALERT_SYSTEM', {})
        return AlertSystem(config)
    except Exception as e:
        logger.error(f"Error creating AlertSystem: {e}")
        return None


def _get_performance_monitor() -> Optional[PerformanceMonitor]:
    """PerformanceMonitorインスタンス取得"""
    try:
        config = current_app.config.get('PERFORMANCE_MONITOR', {})
        return PerformanceMonitor(config)
    except Exception as e:
        logger.error(f"Error creating PerformanceMonitor: {e}")
        return None 
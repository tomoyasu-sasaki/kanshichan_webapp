"""
Realtime Analysis API Routes - リアルタイム分析API

リアルタイム分析機能のAPIエンドポイント群
リアルタイムデータストリーミング、ストリーミング状態監視、アラート管理、パフォーマンスレポートを提供
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from flask import Blueprint, request, current_app

from utils.logger import setup_logger
from services.monitoring.alert_system import AlertSystem
from services.monitoring.performance_monitor import PerformanceMonitor
from .helpers import (
    generate_comprehensive_insights,
    calculate_behavior_score,
    detect_behavioral_patterns,
    generate_contextual_recommendations,
    calculate_data_quality_metrics
)
from web.response_utils import success_response, error_response

logger = setup_logger(__name__)

# Blueprint定義（相対パス化。上位で /api および /api/v1 を付与）
realtime_analysis_bp = Blueprint('realtime_analysis', __name__, url_prefix='/analysis')


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
            return error_response('No JSON data provided', code='VALIDATION_ERROR', status_code=400)
        
        # 必須フィールドチェック
        user_id = data.get('user_id')
        analysis_data = data.get('data')
        
        if not user_id:
            return error_response('user_id is required', code='VALIDATION_ERROR', status_code=400)
        
        if not analysis_data:
            return error_response('data is required', code='VALIDATION_ERROR', status_code=400)
        
        # リアルタイム分析器取得
        real_time_analyzer = _get_real_time_analyzer()
        if not real_time_analyzer:
            return error_response('Real-time analyzer not available', code='SERVICE_UNAVAILABLE', status_code=500)
        
        # タイムスタンプ処理
        timestamp_str = data.get('timestamp')
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                analysis_data['timestamp'] = timestamp
            except ValueError:
                return error_response('Invalid timestamp format', code='VALIDATION_ERROR', status_code=400)
        
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
        
        return success_response({
            'user_id': user_id,
            'processed_at': datetime.now(timezone.utc).isoformat(),
            'extracted_features': features,
            'data_quality': features.get('data_quality', 0.0)
        })
        
    except Exception as e:
        logger.error(f"Error submitting realtime data: {e}", exc_info=True)
        return error_response('Failed to submit realtime data', code='STREAM_ERROR', status_code=500)


@realtime_analysis_bp.route('/stream-status', methods=['GET'])
def get_stream_status():
    """ストリーミング状態取得API
    
    リアルタイムデータストリームの現在の状態を取得
    
    Query Parameters:
        user_id (str): ユーザーID (オプション)
        
    Returns:
        JSON: ストリーミング状態情報
    """
    try:
        user_id = request.args.get('user_id')
        
        # リアルタイム分析器取得
        real_time_analyzer = _get_real_time_analyzer()
        if not real_time_analyzer:
            return error_response('Real-time analyzer not available', code='SERVICE_UNAVAILABLE', status_code=500)
        
        # ストリーム状態取得
        stream_status = real_time_analyzer.get_stream_status(user_id)
        
        return success_response({
            'stream_active': stream_status.get('active', False),
            'data_points_count': stream_status.get('data_points', 0),
            'last_update': stream_status.get('last_update'),
            'processing_latency_ms': stream_status.get('latency', 0),
            'user_id': user_id
        })
        
    except Exception as e:
        logger.error(f"Error getting stream status: {e}", exc_info=True)
        return error_response('Failed to get stream status', code='STATUS_ERROR', status_code=500)


@realtime_analysis_bp.route('/realtime-insights', methods=['GET'])
def get_realtime_insights():
    """リアルタイムインサイト取得API
    
    現在のストリーミングデータからリアルタイムインサイトを生成
    
    Query Parameters:
        user_id (str): ユーザーID (オプション)
        window_size (int): 分析ウィンドウサイズ（秒、デフォルト: 300）
        
    Returns:
        JSON: リアルタイムインサイト
    """
    try:
        user_id = request.args.get('user_id')
        window_size = int(request.args.get('window_size', 300))
        
        if window_size < 60 or window_size > 3600:
            return error_response('Window size must be between 60 and 3600 seconds', code='VALIDATION_ERROR', status_code=400)
        
        # リアルタイム分析器取得
        real_time_analyzer = _get_real_time_analyzer()
        if not real_time_analyzer:
            return error_response('Real-time analyzer not available', code='SERVICE_UNAVAILABLE', status_code=500)
        
        # リアルタイムインサイト生成
        insights = real_time_analyzer.generate_realtime_insights(user_id, window_size)
        
        return success_response({
            'user_id': user_id,
            'window_size_seconds': window_size,
            'insights': insights,
            'generated_at': datetime.now(timezone.utc).isoformat()
        })
        
    except ValueError as e:
        return error_response(f'Invalid parameter: {str(e)}', code='VALIDATION_ERROR', status_code=400)
    except Exception as e:
        logger.error(f"Error getting realtime insights: {e}", exc_info=True)
        return error_response('Failed to generate realtime insights', code='ANALYSIS_ERROR', status_code=500)


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
            return error_response('Invalid alert level. Must be one of: high, medium, low', code='VALIDATION_ERROR', status_code=400)
        
        # アラートシステム取得
        alert_system = _get_alert_system()
        if not alert_system:
            return error_response('Alert system not available', code='SERVICE_UNAVAILABLE', status_code=500)
        
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
        
        return success_response({
            'active_alerts': active_alerts,
            'statistics': alert_stats,
            'filter_applied': {
                'level': level_filter,
                'limit': limit
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting active alerts: {e}", exc_info=True)
        return error_response('Failed to get active alerts', code='ALERTS_ERROR', status_code=500)


@realtime_analysis_bp.route('/performance', methods=['GET'])
def get_streaming_performance():
    """ストリーミングパフォーマンス取得API
    
    リアルタイム分析システムのパフォーマンスメトリクスを取得
    
    Query Parameters:
        user_id (str): ユーザーID (オプション)
        
    Returns:
        JSON: パフォーマンスメトリクス
    """
    try:
        user_id = request.args.get('user_id')
        
        # パフォーマンスモニター取得
        performance_monitor = _get_performance_monitor()
        if not performance_monitor:
            return error_response('Performance monitor not available', code='SERVICE_UNAVAILABLE', status_code=500)
        
        # パフォーマンスメトリクス取得
        metrics = performance_monitor.get_realtime_metrics(user_id)
        
        return success_response({
            'user_id': user_id,
            'metrics': metrics,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting streaming performance: {e}", exc_info=True)
        return error_response('Failed to get performance metrics', code='PERFORMANCE_ERROR', status_code=500)


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
            return error_response('Streaming processor not available', code='SERVICE_UNAVAILABLE', status_code=500)
        
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
        
        return success_response(response_data)
        
    except Exception as e:
        logger.error(f"Error getting streaming status: {e}", exc_info=True)
        return error_response('Failed to get streaming status', code='STATUS_ERROR', status_code=500)


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
        
        # バリデーション（最大1週間）
        if hours < 1 or hours > 168:
            return error_response('Hours must be between 1 and 168', code='VALIDATION_ERROR', status_code=400)
        
        if report_format not in ['summary', 'detailed']:
            return error_response('Format must be summary or detailed', code='VALIDATION_ERROR', status_code=400)
        
        # パフォーマンス監視取得
        performance_monitor = _get_performance_monitor()
        if not performance_monitor:
            return error_response('Performance monitor not available', code='SERVICE_UNAVAILABLE', status_code=500)
        
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
        
        return success_response(response_data)
        
    except Exception as e:
        logger.error(f"Error generating performance report: {e}", exc_info=True)
        return error_response('Failed to generate performance report', code='REPORT_ERROR', status_code=500)


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

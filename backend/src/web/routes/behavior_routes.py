"""
行動データ操作API

行動ログデータの取得、サマリー情報、ページング・フィルタリング機能を提供
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from flask import Blueprint, request, current_app
import logging

from models.behavior_log import BehaviorLog
from models.analysis_result import AnalysisResult
from utils.logger import setup_logger
from web.response_utils import success_response, error_response

logger = setup_logger(__name__)

# Blueprint定義（相対パス化。上位で /api および /api/v1 を付与）
behavior_bp = Blueprint('behavior', __name__, url_prefix='/behavior')


@behavior_bp.route('/logs', methods=['GET'])
def get_behavior_logs():
    """行動ログデータ取得API
    
    指定条件に基づいて行動ログを取得（ページング、フィルタリング対応）
    
    Query Parameters:
        page (int): ページ番号 (1から開始、デフォルト: 1)
        per_page (int): 1ページあたりの件数 (1-100、デフォルト: 20)
        start_date (str): 開始日時 (ISO 8601形式)
        end_date (str): 終了日時 (ISO 8601形式)
        user_id (str): ユーザーID (オプション)
        focus_min (float): 最低集中度 (0.0-1.0)
        focus_max (float): 最高集中度 (0.0-1.0)
        smartphone_detected (bool): スマートフォン検出フィルタ
        presence_status (str): 在席状態フィルタ (present/absent/unknown)
        order_by (str): ソート順 (timestamp_asc/timestamp_desc、デフォルト: timestamp_desc)
        
    Returns:
        JSON: ページングされた行動ログデータ
    """
    try:
        # パラメータ取得・バリデーション
        params = _validate_logs_params(request.args)
        if 'error' in params:
            return error_response(params.get('error', 'Invalid parameters'), code=params.get('code', 'VALIDATION_ERROR'), status_code=400)
        
        # フィルタ条件の構築
        filters = _build_log_filters(params)
        
        # データ取得（ページング適用）
        logs, total_count = BehaviorLog.get_logs_with_pagination(
            page=params['page'],
            per_page=params['per_page'],
            filters=filters,
            order_by=params['order_by']
        )
        
        # ページング情報の計算
        pagination_info = _calculate_pagination(
            total_count, params['page'], params['per_page']
        )
        
        # レスポンスデータの構築
        logs_data = []
        for log in logs:
            logs_data.append({
                'id': log.id,
                'timestamp': log.timestamp.isoformat(),
                'focus_level': log.focus_level,
                'smartphone_detected': log.smartphone_detected,
                'presence_status': log.presence_status,
                'detected_objects': log.detected_objects,
                'posture_data': log.posture_data,
                'screen_activity': log.screen_activity,
                'created_at': log.created_at.isoformat() if log.created_at else None
            })
        
        return success_response({
            'logs': logs_data,
            'pagination': pagination_info,
            'filters_applied': {k: v for k, v in filters.items() if v is not None},
            'total_count': total_count
        })
        
    except Exception as e:
        logger.error(f"Error getting behavior logs: {e}", exc_info=True)
        return error_response('Failed to retrieve behavior logs', code='DATA_RETRIEVAL_ERROR', status_code=500)


@behavior_bp.route('/summary/dashboard', methods=['GET'])
def get_dashboard_summary():
    """ダッシュボード専用サマリーAPI
    
    今日・昨日のデータをtoday/yesterday構造で返す
    フロントエンド期待値に完全対応
    """
    try:
        logger.info("Dashboard summary API called")
        user_id = request.args.get('user_id')
        
        # 今日・昨日のデータ取得
        today_data = _get_daily_dashboard_data('today', user_id)
        yesterday_data = _get_daily_dashboard_data('yesterday', user_id)
        
        response_data = {
            'today': today_data,
            'yesterday': yesterday_data
        }
        logger.info(f"Dashboard summary generated: today={today_data.get('total_time', 0)}s, yesterday={yesterday_data.get('total_time', 0)}s")
        return success_response(response_data)
        
    except Exception as e:
        logger.error(f"Dashboard summary error: {e}", exc_info=True)
        return error_response('Failed to get dashboard summary', code='SUMMARY_ERROR', status_code=500)


@behavior_bp.route('/summary', methods=['GET'])
def get_behavior_summary():
    """行動データサマリー情報取得API
    
    指定期間の行動データの統計サマリーを取得
    
    Query Parameters:
        timeframe (str): 期間 (today/yesterday/week/month、デフォルト: today)
        user_id (str): ユーザーID (オプション)
        start_date (str): カスタム開始日時 (ISO 8601形式)
        end_date (str): カスタム終了日時 (ISO 8601形式)
        include_details (bool): 詳細統計を含むか (デフォルト: false)
        
    Returns:
        JSON: 行動データサマリー
    """
    try:
        # パラメータ取得・バリデーション
        timeframe = request.args.get('timeframe', 'today')
        user_id = request.args.get('user_id')
        include_details = request.args.get('include_details', 'false').lower() == 'true'
        
        # 時間範囲の決定
        start_time, end_time = _get_timeframe_range(
            timeframe,
            request.args.get('start_date'),
            request.args.get('end_date')
        )
        
        if isinstance(start_time, dict) and 'error' in start_time:
            return error_response(start_time.get('error', 'Invalid timeframe'), code=start_time.get('code', 'VALIDATION_ERROR'), status_code=400)
        
        # データ取得
        logs = BehaviorLog.get_logs_by_timerange(
            start_time=start_time,
            end_time=end_time,
            user_id=user_id
        )
        
        # 基本統計の計算
        summary = _calculate_basic_summary(logs, timeframe)
        
        # 詳細統計（オプション）
        if include_details:
            summary['detailed_stats'] = _calculate_detailed_stats(logs)
            summary['hourly_breakdown'] = _calculate_hourly_breakdown(logs)
            summary['focus_distribution'] = _calculate_focus_distribution(logs)
        
        return success_response(summary)
        
    except Exception as e:
        logger.error(f"Error getting behavior summary: {e}", exc_info=True)
        return error_response('Failed to generate behavior summary', code='SUMMARY_GENERATION_ERROR', status_code=500)


@behavior_bp.route('/stats', methods=['GET'])
def get_behavior_stats():
    """行動統計情報取得API
    
    期間別の詳細な統計情報を取得
    
    Query Parameters:
        period (str): 統計期間 (hour/day/week/month、デフォルト: day)
        limit (int): 取得期間数 (1-365、デフォルト: 7)
        user_id (str): ユーザーID (オプション)
        metrics (str): 取得指標 (csv形式: focus,smartphone,presence)
        
    Returns:
        JSON: 期間別統計データ
    """
    try:
        # パラメータ取得・バリデーション
        period = request.args.get('period', 'day')
        limit = int(request.args.get('limit', 7))
        user_id = request.args.get('user_id')
        metrics_str = request.args.get('metrics', 'focus,smartphone,presence')
        
        if period not in ['hour', 'day', 'week', 'month']:
            return error_response('Invalid period. Must be one of: hour, day, week, month', code='VALIDATION_ERROR', status_code=400)
        
        if limit < 1 or limit > 365:
            return error_response('Limit must be between 1 and 365', code='VALIDATION_ERROR', status_code=400)
        
        # 指標の解析
        requested_metrics = [m.strip() for m in metrics_str.split(',')]
        valid_metrics = ['focus', 'smartphone', 'presence', 'activity']
        metrics = [m for m in requested_metrics if m in valid_metrics]
        
        # 統計データ取得
        stats_data = _get_period_statistics(period, limit, user_id, metrics)
        
        return success_response({
            'period': period,
            'limit': limit,
            'metrics': metrics,
            'statistics': stats_data,
            'generated_at': datetime.utcnow().isoformat()
        })
        
    except ValueError as e:
        return error_response(f'Invalid parameter: {str(e)}', code='VALIDATION_ERROR', status_code=400)
    except Exception as e:
        logger.error(f"Error getting behavior stats: {e}", exc_info=True)
        return error_response('Failed to calculate behavior statistics', code='STATISTICS_ERROR', status_code=500)


@behavior_bp.route('/export', methods=['GET'])
def export_behavior_data():
    """行動データエクスポートAPI
    
    指定条件の行動データをCSV形式でエクスポート
    
    Query Parameters:
        format (str): エクスポート形式 (csv/json、デフォルト: csv)
        start_date (str): 開始日時 (ISO 8601形式、必須)
        end_date (str): 終了日時 (ISO 8601形式、必須)
        user_id (str): ユーザーID (オプション)
        fields (str): 出力フィールド (csv形式)
        
    Returns:
        CSV/JSON: エクスポートされた行動データ
    """
    try:
        # パラメータ取得・バリデーション
        export_format = request.args.get('format', 'csv')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        user_id = request.args.get('user_id')
        fields_str = request.args.get('fields', 'timestamp,focus_level,smartphone_detected,presence_status')
        
        if not start_date_str or not end_date_str:
            return error_response('start_date and end_date are required', code='VALIDATION_ERROR', status_code=400)
        
        if export_format not in ['csv', 'json']:
            return error_response('Invalid format. Must be csv or json', code='VALIDATION_ERROR', status_code=400)
        
        # 日時パースと検証
        try:
            start_time = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        except ValueError:
            return error_response('Invalid date format. Use ISO 8601 format', code='VALIDATION_ERROR', status_code=400)
        
        # データ期間制限（最大90日）
        if (end_time - start_time).days > 90:
            return error_response('Export period cannot exceed 90 days', code='VALIDATION_ERROR', status_code=400)
        
        # データ取得
        logs = BehaviorLog.get_logs_by_timerange(
            start_time=start_time,
            end_time=end_time,
            user_id=user_id
        )
        
        if not logs:
            return success_response({
                'message': 'No data found for the specified period',
                'count': 0
            })
        
        # フィールド定義
        available_fields = {
            'timestamp': lambda log: log.timestamp.isoformat(),
            'focus_level': lambda log: log.focus_level,
            'smartphone_detected': lambda log: log.smartphone_detected,
            'presence_status': lambda log: log.presence_status,
            'detected_objects': lambda log: log.detected_objects,
            'posture_data': lambda log: log.posture_data,
            'screen_activity': lambda log: log.screen_activity
        }
        
        fields = [f.strip() for f in fields_str.split(',') if f.strip() in available_fields]
        
        # データエクスポート
        if export_format == 'csv':
            csv_data = _generate_csv_export(logs, fields, available_fields)
            return csv_data
        else:
            json_data = _generate_json_export(logs, fields, available_fields)
            return success_response({
                'records': json_data,
                'count': len(json_data),
                'fields': fields,
                'export_info': {
                    'start_date': start_date_str,
                    'end_date': end_date_str,
                    'generated_at': datetime.utcnow().isoformat()
                }
            })
        
    except Exception as e:
        logger.error(f"Error exporting behavior data: {e}", exc_info=True)
        return error_response('Failed to export behavior data', code='EXPORT_ERROR', status_code=500)


def _validate_logs_params(args) -> Dict[str, Any]:
    """ログ取得パラメータのバリデーション"""
    try:
        params = {
            'page': int(args.get('page', 1)),
            'per_page': int(args.get('per_page', 20)),
            'start_date': args.get('start_date'),
            'end_date': args.get('end_date'),
            'user_id': args.get('user_id'),
            'focus_min': float(args.get('focus_min')) if args.get('focus_min') else None,
            'focus_max': float(args.get('focus_max')) if args.get('focus_max') else None,
            'smartphone_detected': _parse_bool(args.get('smartphone_detected')),
            'presence_status': args.get('presence_status'),
            'order_by': args.get('order_by', 'timestamp_desc')
        }
        
        # バリデーション
        if params['page'] < 1:
            return {'error': 'Page must be >= 1', 'code': 'VALIDATION_ERROR'}
        
        if params['per_page'] < 1 or params['per_page'] > 100:
            return {'error': 'per_page must be between 1 and 100', 'code': 'VALIDATION_ERROR'}
        
        if params['focus_min'] is not None and (params['focus_min'] < 0 or params['focus_min'] > 1):
            return {'error': 'focus_min must be between 0.0 and 1.0', 'code': 'VALIDATION_ERROR'}
        
        if params['focus_max'] is not None and (params['focus_max'] < 0 or params['focus_max'] > 1):
            return {'error': 'focus_max must be between 0.0 and 1.0', 'code': 'VALIDATION_ERROR'}
        
        if params['presence_status'] and params['presence_status'] not in ['present', 'absent', 'unknown']:
            return {'error': 'Invalid presence_status', 'code': 'VALIDATION_ERROR'}
        
        if params['order_by'] not in ['timestamp_asc', 'timestamp_desc']:
            return {'error': 'Invalid order_by', 'code': 'VALIDATION_ERROR'}
        
        return params
        
    except ValueError as e:
        return {'error': f'Invalid parameter type: {str(e)}', 'code': 'VALIDATION_ERROR'}


def _build_log_filters(params: Dict[str, Any]) -> Dict[str, Any]:
    """ログフィルタ条件の構築"""
    filters = {}
    
    if params['start_date']:
        try:
            filters['start_time'] = datetime.fromisoformat(params['start_date'].replace('Z', '+00:00'))
        except ValueError:
            pass
    
    if params['end_date']:
        try:
            filters['end_time'] = datetime.fromisoformat(params['end_date'].replace('Z', '+00:00'))
        except ValueError:
            pass
    
    filters['user_id'] = params['user_id']
    filters['focus_min'] = params['focus_min']
    filters['focus_max'] = params['focus_max']
    filters['smartphone_detected'] = params['smartphone_detected']
    filters['presence_status'] = params['presence_status']
    
    return filters


def _calculate_pagination(total_count: int, page: int, per_page: int) -> Dict[str, Any]:
    """ページング情報の計算"""
    total_pages = (total_count + per_page - 1) // per_page
    
    return {
        'current_page': page,
        'per_page': per_page,
        'total_pages': total_pages,
        'total_count': total_count,
        'has_next': page < total_pages,
        'has_prev': page > 1,
        'next_page': page + 1 if page < total_pages else None,
        'prev_page': page - 1 if page > 1 else None
    }


def _get_timeframe_range(timeframe: str, start_date: str = None, end_date: str = None) -> Tuple[datetime, datetime]:
    """時間枠に基づく期間の取得"""
    now = datetime.now()
    
    if timeframe == 'today':
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(days=1)
    elif timeframe == 'yesterday':
        start_time = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(days=1)
    elif timeframe == 'week':
        start_time = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = now
    elif timeframe == 'month':
        start_time = (now - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = now
    elif timeframe == 'custom':
        if not start_date or not end_date:
            return {'error': 'start_date and end_date required for custom timeframe', 'code': 'VALIDATION_ERROR'}, None
        try:
            start_time = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError:
            return {'error': 'Invalid date format', 'code': 'VALIDATION_ERROR'}, None
    else:
        return {'error': 'Invalid timeframe', 'code': 'VALIDATION_ERROR'}, None
    
    return start_time, end_time


def _calculate_posture_alerts(logs: List[BehaviorLog]) -> int:
    """姿勢アラート回数を計算
    
    Args:
        logs: 行動ログリスト
        
    Returns:
        int: 姿勢アラート回数
    """
    try:
        alert_count = 0
        for log in logs:
            if hasattr(log, 'posture_data') and log.posture_data:
                posture_score = log.posture_data.get('score', 1.0)
                # 姿勢スコアが閾値60%以下の場合をアラートとする
                if posture_score < 0.6:
                    alert_count += 1
        return alert_count
    except Exception as e:
        logger.error(f"Error calculating posture alerts: {e}")
        return 0


def _calculate_productivity_score(logs: List[BehaviorLog]) -> float:
    """生産性スコアを算出
    
    Args:
        logs: 行動ログリスト
        
    Returns:
        float: 生産性スコア (0.0-1.0の範囲)
    """
    try:
        if not logs:
            return 0.0
        
        # 重み付け設定
        focus_weight = 0.6
        presence_weight = 0.3
        smartphone_penalty = 0.1
        
        # 各指標の計算
        focus_scores = [log.focus_level for log in logs if log.focus_level is not None]
        avg_focus = sum(focus_scores) / len(focus_scores) if focus_scores else 0.0
        
        presence_rate = sum(1 for log in logs if log.presence_status == 'present') / len(logs)
        
        smartphone_penalty_rate = sum(1 for log in logs if log.smartphone_detected) / len(logs)
        
        # 生産性スコア算出
        score = (avg_focus * focus_weight + 
                presence_rate * presence_weight - 
                smartphone_penalty_rate * smartphone_penalty)
        
        # 0.0-1.0の範囲に正規化
        return max(0.0, min(1.0, score))
        
    except Exception as e:
        logger.error(f"Error calculating productivity score: {e}")
        return 0.0


def _calculate_basic_summary(logs: List[BehaviorLog], timeframe: str) -> Dict[str, Any]:
    """基本統計サマリーの計算"""
    if not logs:
        return {
            'timeframe': timeframe,
            'total_entries': 0,
            'message': 'No data available for the specified period'
        }
    
    total_logs = len(logs)
    focus_scores = [log.focus_level for log in logs if log.focus_level is not None]
    smartphone_count = sum(1 for log in logs if log.smartphone_detected)
    present_count = sum(1 for log in logs if log.presence_status == 'present')
    
    posture_alerts = _calculate_posture_alerts(logs)
    productivity_score = _calculate_productivity_score(logs)
    
    return {
        'timeframe': timeframe,
        'period_start': logs[-1].timestamp.isoformat(),
        'period_end': logs[0].timestamp.isoformat(),
        'total_entries': total_logs,
        'average_focus': sum(focus_scores) / len(focus_scores) if focus_scores else 0,
        'smartphone_usage_rate': smartphone_count / total_logs,
        'presence_rate': present_count / total_logs,
        'active_time_minutes': total_logs * 0.5,  # 30秒間隔と仮定
        'data_completeness': len(focus_scores) / total_logs if total_logs > 0 else 0,
        'posture_alerts': posture_alerts,
        'productivity_score': productivity_score
    }


def _calculate_detailed_stats(logs: List[BehaviorLog]) -> Dict[str, Any]:
    """詳細統計の計算"""
    if not logs:
        return {}
    
    focus_scores = [log.focus_level for log in logs if log.focus_level is not None]
    
    if not focus_scores:
        return {'message': 'No focus data available'}
    
    import numpy as np
    
    return {
        'focus_statistics': {
            'mean': float(np.mean(focus_scores)),
            'median': float(np.median(focus_scores)),
            'std': float(np.std(focus_scores)),
            'min': float(np.min(focus_scores)),
            'max': float(np.max(focus_scores)),
            'q25': float(np.percentile(focus_scores, 25)),
            'q75': float(np.percentile(focus_scores, 75))
        },
        'activity_patterns': {
            'peak_focus_time': _find_peak_focus_time(logs),
            'low_focus_periods': _find_low_focus_periods(logs),
            'longest_session': _find_longest_session(logs)
        }
    }


def _calculate_hourly_breakdown(logs: List[BehaviorLog]) -> Dict[str, Any]:
    """時間別内訳の計算"""
    hourly_data = {}
    
    for log in logs:
        hour = log.timestamp.hour
        if hour not in hourly_data:
            hourly_data[hour] = {'count': 0, 'focus_sum': 0, 'smartphone_count': 0}
        
        hourly_data[hour]['count'] += 1
        if log.focus_level is not None:
            hourly_data[hour]['focus_sum'] += log.focus_level
        if log.smartphone_detected:
            hourly_data[hour]['smartphone_count'] += 1
    
    # 平均値の計算
    hourly_stats = {}
    for hour, data in hourly_data.items():
        hourly_stats[str(hour)] = {
            'entry_count': data['count'],
            'average_focus': data['focus_sum'] / data['count'] if data['count'] > 0 else 0,
            'smartphone_rate': data['smartphone_count'] / data['count'] if data['count'] > 0 else 0
        }
    
    return hourly_stats


def _calculate_focus_distribution(logs: List[BehaviorLog]) -> Dict[str, Any]:
    """集中度分布の計算"""
    focus_scores = [log.focus_level for log in logs if log.focus_level is not None]
    
    if not focus_scores:
        return {}
    
    ranges = {
        'very_low': [0.0, 0.2],
        'low': [0.2, 0.4],
        'medium': [0.4, 0.6],
        'high': [0.6, 0.8],
        'very_high': [0.8, 1.0]
    }
    
    distribution = {}
    total = len(focus_scores)
    
    for range_name, (min_val, max_val) in ranges.items():
        count = sum(1 for score in focus_scores if min_val <= score < max_val or (range_name == 'very_high' and score == 1.0))
        distribution[range_name] = {
            'count': count,
            'percentage': (count / total) * 100 if total > 0 else 0
        }
    
    return distribution


def _get_period_statistics(period: str, limit: int, user_id: str, metrics: List[str]) -> List[Dict[str, Any]]:
    """期間別統計データの取得"""
    # 実装簡易版 - 実際にはより複雑なクエリが必要
    stats = []
    now = datetime.now()
    
    for i in range(limit):
        if period == 'hour':
            period_start = now - timedelta(hours=i+1)
            period_end = now - timedelta(hours=i)
        elif period == 'day':
            period_start = (now - timedelta(days=i+1)).replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(days=1)
        elif period == 'week':
            period_start = now - timedelta(weeks=i+1)
            period_end = now - timedelta(weeks=i)
        else:  # month
            period_start = now - timedelta(days=(i+1)*30)
            period_end = now - timedelta(days=i*30)
        
        # 期間のデータ取得
        logs = BehaviorLog.get_logs_by_timerange(
            start_time=period_start,
            end_time=period_end,
            user_id=user_id
        )
        
        period_stats = {
            'period_start': period_start.isoformat(),
            'period_end': period_end.isoformat(),
            'data_count': len(logs)
        }
        
        # 指定されたメトリクスを計算
        if 'focus' in metrics:
            focus_scores = [log.focus_level for log in logs if log.focus_level is not None]
            period_stats['average_focus'] = sum(focus_scores) / len(focus_scores) if focus_scores else 0
        
        if 'smartphone' in metrics:
            period_stats['smartphone_usage_rate'] = sum(1 for log in logs if log.smartphone_detected) / len(logs) if logs else 0
        
        if 'presence' in metrics:
            period_stats['presence_rate'] = sum(1 for log in logs if log.presence_status == 'present') / len(logs) if logs else 0
        
        if 'activity' in metrics:
            period_stats['activity_time_minutes'] = len(logs) * 0.5
        
        stats.append(period_stats)
    
    return stats


def _parse_bool(value: str) -> Optional[bool]:
    """文字列をbooleanに変換"""
    if value is None:
        return None
    if value.lower() in ['true', '1', 'yes']:
        return True
    elif value.lower() in ['false', '0', 'no']:
        return False
    return None


def _find_peak_focus_time(logs: List[BehaviorLog]) -> str:
    """最も集中度が高い時間帯を特定"""
    hourly_focus = {}
    
    for log in logs:
        if log.focus_level is not None:
            hour = log.timestamp.hour
            if hour not in hourly_focus:
                hourly_focus[hour] = []
            hourly_focus[hour].append(log.focus_level)
    
    if not hourly_focus:
        return "データなし"
    
    avg_focus_by_hour = {hour: sum(scores)/len(scores) for hour, scores in hourly_focus.items()}
    peak_hour = max(avg_focus_by_hour, key=avg_focus_by_hour.get)
    
    return f"{peak_hour:02d}:00"


def _find_low_focus_periods(logs: List[BehaviorLog]) -> List[str]:
    """集中度が低い期間を特定"""
    low_periods = []
    current_low_start = None
    
    for log in logs:
        if log.focus_level is not None and log.focus_level < 0.3:
            if current_low_start is None:
                current_low_start = log.timestamp
        else:
            if current_low_start is not None:
                low_periods.append(f"{current_low_start.strftime('%H:%M')}-{log.timestamp.strftime('%H:%M')}")
                current_low_start = None
    
    return low_periods[:5]  # 最大5つまで


def _find_longest_session(logs: List[BehaviorLog]) -> str:
    """最も長いセッションを特定"""
    if not logs:
        return "データなし"
    
    # セッション検出の簡易版
    session_start = logs[-1].timestamp
    session_end = logs[0].timestamp
    duration = (session_end - session_start).total_seconds() / 60
    
    return f"{duration:.1f}分"


def _generate_csv_export(logs: List[BehaviorLog], fields: List[str], field_map: Dict) -> str:
    """CSV形式でのデータエクスポート"""
    from flask import Response
    import io
    
    output = io.StringIO()
    
    # ヘッダー行
    output.write(','.join(fields) + '\n')
    
    # データ行
    for log in logs:
        row_data = []
        for field in fields:
            value = field_map[field](log)
            if isinstance(value, (dict, list)):
                value = str(value).replace(',', ';')  # CSV対応
            row_data.append(str(value) if value is not None else '')
        output.write(','.join(row_data) + '\n')
    
    csv_content = output.getvalue()
    output.close()
    
    return Response(
        csv_content,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=behavior_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
    )


def _generate_json_export(logs: List[BehaviorLog], fields: List[str], field_map: Dict) -> List[Dict]:
    """JSON形式でのデータエクスポート"""
    export_data = []
    
    for log in logs:
        record = {}
        for field in fields:
            record[field] = field_map[field](log)
        export_data.append(record)
    
    return export_data


def _get_daily_dashboard_data(timeframe: str, user_id: str = None) -> Dict[str, Any]:
    """日次ダッシュボードデータ取得
    
    Args:
        timeframe: 'today' または 'yesterday'
        user_id: ユーザーID（オプション）
        
    Returns:
        dict: ダッシュボード用データ（秒単位）
    """
    try:
        # 時間範囲の取得
        start_time, end_time = _get_timeframe_range(timeframe)
        if isinstance(start_time, dict):  # エラーの場合
            logger.warning(f"Invalid timeframe: {timeframe}")
            return _empty_dashboard_data()
        
        # ログデータ取得
        logs = BehaviorLog.get_logs_by_timerange(start_time, end_time, user_id)
        
        if not logs:
            logger.info(f"No logs found for {timeframe}")
            return _empty_dashboard_data()
        
        # 基本統計計算
        total_seconds = len(logs) * 2  # 5秒間隔と仮定
        
        # 集中度関連計算
        focus_scores = [log.focus_level for log in logs if log.focus_level is not None]
        avg_focus = sum(focus_scores) / len(focus_scores) if focus_scores else 0
        
        # 在席率計算
        presence_rate = sum(1 for log in logs if log.presence_status == 'present') / len(logs)
        
        # スマートフォン使用率計算
        smartphone_rate = sum(1 for log in logs if log.smartphone_detected) / len(logs)
        
        # 姿勢アラート計算
        posture_alerts = _calculate_posture_alerts(logs)
        
        dashboard_data = {
            'total_time': total_seconds,
            'focus_time': int(total_seconds * avg_focus),
            'break_time': int(total_seconds * (1 - avg_focus) * presence_rate),
            'absence_time': int(total_seconds * (1 - presence_rate)),
            'smartphone_usage_time': int(total_seconds * smartphone_rate),
            'posture_alerts': posture_alerts
        }
        
        logger.info(f"Dashboard data for {timeframe}: {dashboard_data}")
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Error getting daily dashboard data for {timeframe}: {e}", exc_info=True)
        return _empty_dashboard_data()


def _empty_dashboard_data() -> Dict[str, Any]:
    """空のダッシュボードデータを返す"""
    return {
        'total_time': 0,
        'focus_time': 0,
        'break_time': 0,
        'absence_time': 0,
        'smartphone_usage_time': 0,
        'posture_alerts': 0
    } 
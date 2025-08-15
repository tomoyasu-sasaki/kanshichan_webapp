"""
Advanced Analysis API Routes - 高度分析API

より高度な行動分析機能のAPIエンドポイント群
パターン認識、詳細分析、健康評価などを提供
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from flask import Blueprint, request, current_app

from models.behavior_log import BehaviorLog
from utils.logger import setup_logger
from .helpers import (
    generate_comprehensive_insights,
    calculate_behavior_score,
    detect_behavioral_patterns,
    generate_contextual_recommendations,
    calculate_data_quality_metrics
)
from services.analysis.service_loader import (
    get_advanced_behavior_analyzer,
    get_pattern_recognizer
)
from web.response_utils import success_response, error_response

logger = setup_logger(__name__)

# Blueprint定義（相対パス化。上位で /api および /api/v1 を付与）
advanced_analysis_bp = Blueprint('advanced_analysis', __name__, url_prefix='/analysis')


@advanced_analysis_bp.route('/advanced-patterns', methods=['GET'])
def get_advanced_patterns():
    """高度パターン分析API
    
    高度な行動パターン分析と機械学習ベースの洞察を提供
    
    Query Parameters:
        timeframe (str): 分析期間 (hourly/daily/weekly/monthly) - デフォルト: daily
        user_id (str): ユーザーID (オプション)
        pattern_type (str): パターンタイプ (cyclical/trending/seasonal/all) - デフォルト: all
        
    Returns:
        JSON: 高度パターン分析結果
    """
    try:
        # パラメータ取得
        timeframe = request.args.get('timeframe', 'daily')
        user_id = request.args.get('user_id')
        pattern_type = request.args.get('pattern_type', 'all')
        
        # バリデーション
        if timeframe not in ['hourly', 'daily', 'weekly', 'monthly']:
            return error_response(
                'Invalid timeframe. Must be one of: hourly, daily, weekly, monthly',
                code='VALIDATION_ERROR', status_code=400
            )
        
        if pattern_type not in ['cyclical', 'trending', 'seasonal', 'all']:
            return error_response(
                'Invalid pattern_type. Must be one of: cyclical, trending, seasonal, all',
                code='VALIDATION_ERROR', status_code=400
            )
        
        # 高度分析エンジン取得
        advanced_analyzer = _get_advanced_behavior_analyzer()
        pattern_recognizer = _get_pattern_recognizer()
        
        if not advanced_analyzer or not pattern_recognizer:
            return error_response('Advanced analysis services not available', code='SERVICE_UNAVAILABLE', status_code=500)
        
        # 期間に応じたデータ取得
        hours_map = {'hourly': 1, 'daily': 24, 'weekly': 168, 'monthly': 720}
        hours = hours_map[timeframe]
        logs = BehaviorLog.get_recent_logs(hours=hours, user_id=user_id)
        
        if not logs:
            return success_response({
                'message': f'{timeframe}のデータが見つかりません',
                'timeframe': timeframe,
                'pattern_type': pattern_type,
                'logs_count': 0
            })
        
        # 時系列パターン分析
        timeseries_analysis = advanced_analyzer.analyze_time_series_patterns(logs, timeframe)
        
        # パターン認識分析
        pattern_analysis = pattern_recognizer.recognize_temporal_patterns(logs)
        
        # クラスタリング分析
        clustering_analysis = pattern_recognizer.perform_clustering_analysis(logs)
        
        # パターンタイプ別フィルタリング
        if pattern_type != 'all':
            pattern_analysis = _filter_patterns_by_type(pattern_analysis, pattern_type)
        
        result_data = {
            'timeframe': timeframe,
            'pattern_type': pattern_type,
            'period_start': logs[-1].timestamp.isoformat() if logs else None,
            'period_end': logs[0].timestamp.isoformat() if logs else None,
            'total_logs': len(logs),
            'timeseries_analysis': timeseries_analysis,
            'pattern_recognition': pattern_analysis,
            'clustering_analysis': clustering_analysis,
            'insights': _generate_advanced_pattern_insights(
                timeseries_analysis, pattern_analysis, clustering_analysis
            )
        }
        
        return success_response(result_data)
        
    except Exception as e:
        logger.error(f"Error getting advanced patterns: {e}", exc_info=True)
        return error_response('Failed to analyze advanced patterns', code='ANALYSIS_ERROR', status_code=500)


@advanced_analysis_bp.route('/detailed-analysis', methods=['GET'])
def get_detailed_analysis():
    """詳細分析API
    
    行動データの詳細な分析と洞察を提供
    
    Query Parameters:
        timeframe (str): 分析期間 (hourly/daily/weekly) - デフォルト: daily
        user_id (str): ユーザーID (オプション)
        analysis_type (str): 分析タイプ (comprehensive/behavioral/health/all) - デフォルト: all
        
    Returns:
        JSON: 詳細分析結果
    """
    try:
        # パラメータ取得
        timeframe = request.args.get('timeframe', 'daily')
        user_id = request.args.get('user_id')
        analysis_type = request.args.get('analysis_type', 'all')
        
        # バリデーション
        if timeframe not in ['hourly', 'daily', 'weekly']:
            return error_response(
                'Invalid timeframe. Must be one of: hourly, daily, weekly',
                code='VALIDATION_ERROR', status_code=400
            )
        
        if analysis_type not in ['comprehensive', 'behavioral', 'health', 'all']:
            return error_response(
                'Invalid analysis_type. Must be one of: comprehensive, behavioral, health, all',
                code='VALIDATION_ERROR', status_code=400
            )
        
        # 高度分析エンジン取得
        advanced_analyzer = _get_advanced_behavior_analyzer()
        if not advanced_analyzer:
            return error_response('Advanced analyzer not available', code='SERVICE_UNAVAILABLE', status_code=500)
        
        # 期間に応じたデータ取得
        hours_map = {'hourly': 1, 'daily': 24, 'weekly': 168}
        hours = hours_map[timeframe]
        logs = BehaviorLog.get_recent_logs(hours=hours, user_id=user_id)
        
        if not logs:
            return success_response({
                'message': f'{timeframe}のデータが見つかりません',
                'timeframe': timeframe,
                'analysis_type': analysis_type,
                'logs_count': 0
            })
        
        # 包括的分析
        comprehensive_analysis = {}
        if analysis_type in ['comprehensive', 'all']:
            comprehensive_analysis = advanced_analyzer.perform_comprehensive_analysis(logs)
        
        # 行動分析
        behavioral_analysis = {}
        if analysis_type in ['behavioral', 'all']:
            behavioral_analysis = advanced_analyzer.analyze_behavioral_patterns(logs)
        
        # 健康評価
        health_analysis = {}
        if analysis_type in ['health', 'all']:
            health_analysis = advanced_analyzer.evaluate_health_metrics(logs)
        
        result_data = {
            'timeframe': timeframe,
            'analysis_type': analysis_type,
            'logs_analyzed': len(logs),
            'comprehensive_analysis': comprehensive_analysis,
            'behavioral_analysis': behavioral_analysis,
            'health_analysis': health_analysis,
            'analysis_timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        return success_response(result_data)
        
    except Exception as e:
        logger.error(f"Error getting detailed analysis: {e}", exc_info=True)
        return error_response('Failed to perform detailed analysis', code='ANALYSIS_ERROR', status_code=500)


@advanced_analysis_bp.route('/health-evaluation', methods=['GET'])
def get_health_evaluation():
    """健康評価API
    
    行動データに基づく健康状態の評価を提供
    
    Query Parameters:
        timeframe (str): 分析期間 (daily/weekly/monthly) - デフォルト: daily
        user_id (str): ユーザーID (オプション)
        evaluation_type (str): 評価タイプ (posture/eye_health/overall/all) - デフォルト: all
        
    Returns:
        JSON: 健康評価結果
    """
    try:
        # パラメータ取得
        timeframe = request.args.get('timeframe', 'daily')
        user_id = request.args.get('user_id')
        evaluation_type = request.args.get('evaluation_type', 'all')
        
        # バリデーション
        if timeframe not in ['daily', 'weekly', 'monthly']:
            return error_response(
                'Invalid timeframe. Must be one of: daily, weekly, monthly',
                code='VALIDATION_ERROR', status_code=400
            )
        
        if evaluation_type not in ['posture', 'eye_health', 'overall', 'all']:
            return error_response(
                'Invalid evaluation_type. Must be one of: posture, eye_health, overall, all',
                code='VALIDATION_ERROR', status_code=400
            )
        
        # 高度分析エンジン取得
        advanced_analyzer = _get_advanced_behavior_analyzer()
        if not advanced_analyzer:
            return error_response('Advanced analyzer not available', code='SERVICE_UNAVAILABLE', status_code=500)
        
        # 期間に応じたデータ取得
        hours_map = {'daily': 24, 'weekly': 168, 'monthly': 720}
        hours = hours_map[timeframe]
        logs = BehaviorLog.get_recent_logs(hours=hours, user_id=user_id)
        
        if not logs:
            return success_response({
                'message': f'{timeframe}のデータが見つかりません',
                'timeframe': timeframe,
                'evaluation_type': evaluation_type,
                'logs_count': 0
            })
        
        # 健康評価実行
        health_evaluation = advanced_analyzer.evaluate_health_metrics(logs, evaluation_type)
        
        result_data = {
            'timeframe': timeframe,
            'evaluation_type': evaluation_type,
            'logs_analyzed': len(logs),
            'health_evaluation': health_evaluation,
            'evaluation_timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        return success_response(result_data)
        
    except Exception as e:
        logger.error(f"Error getting health evaluation: {e}", exc_info=True)
        return error_response('Failed to evaluate health metrics', code='ANALYSIS_ERROR', status_code=500)


@advanced_analysis_bp.route('/correlation-analysis', methods=['GET'])
def get_correlation_analysis():
    """相関分析API
    
    行動データの相関関係を分析して提供
    
    Query Parameters:
        timeframe (str): 分析期間 (daily/weekly/monthly) - デフォルト: daily
        user_id (str): ユーザーID (オプション)
        variables (str): 分析対象変数 (focus_presence/focus_posture/all) - デフォルト: all
        
    Returns:
        JSON: 相関分析結果
    """
    try:
        # パラメータ取得
        timeframe = request.args.get('timeframe', 'daily')
        user_id = request.args.get('user_id')
        variables = request.args.get('variables', 'all')
        
        # バリデーション
        if timeframe not in ['daily', 'weekly', 'monthly']:
            return error_response(
                'Invalid timeframe. Must be one of: daily, weekly, monthly',
                code='VALIDATION_ERROR', status_code=400
            )
        
        if variables not in ['focus_presence', 'focus_posture', 'all']:
            return error_response(
                'Invalid variables. Must be one of: focus_presence, focus_posture, all',
                code='VALIDATION_ERROR', status_code=400
            )
        
        # 高度分析エンジン取得
        advanced_analyzer = _get_advanced_behavior_analyzer()
        if not advanced_analyzer:
            return error_response('Advanced analyzer not available', code='SERVICE_UNAVAILABLE', status_code=500)
        
        # 期間に応じたデータ取得
        hours_map = {'daily': 24, 'weekly': 168, 'monthly': 720}
        hours = hours_map[timeframe]
        logs = BehaviorLog.get_recent_logs(hours=hours, user_id=user_id)
        
        if not logs:
            return success_response({
                'message': f'{timeframe}のデータが見つかりません',
                'timeframe': timeframe,
                'variables': variables,
                'logs_count': 0
            })
        
        # 相関分析実行
        correlation_analysis = advanced_analyzer.analyze_correlations(logs, variables)
        
        result_data = {
            'timeframe': timeframe,
            'variables': variables,
            'logs_analyzed': len(logs),
            'correlation_analysis': correlation_analysis,
            'analysis_timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        return success_response(result_data)
        
    except Exception as e:
        logger.error(f"Error getting correlation analysis: {e}", exc_info=True)
        return error_response('Failed to analyze correlations', code='ANALYSIS_ERROR', status_code=500)


@advanced_analysis_bp.route('/focus-deep-dive', methods=['GET'])
def get_focus_deep_dive():
    """集中度詳細分析API
    
    集中度に関する詳細な分析と品質評価を提供
    
    Query Parameters:
        user_id (str): ユーザーID (オプション)
        hours (int): 分析対象時間 (デフォルト: 24)
        include_sessions (bool): セッション詳細を含めるか (デフォルト: true)
        
    Returns:
        JSON: 集中度詳細分析結果
    """
    try:
        # パラメータ取得
        user_id = request.args.get('user_id')
        hours = int(request.args.get('hours', 24))
        include_sessions = request.args.get('include_sessions', 'true').lower() == 'true'
        
        # バリデーション
        if hours < 1 or hours > 720:  # 最大30日
            return error_response('Hours must be between 1 and 720', code='VALIDATION_ERROR', status_code=400)
        
        # 高度分析エンジン取得
        advanced_analyzer = _get_advanced_behavior_analyzer()
        if not advanced_analyzer:
            return error_response('Advanced behavior analyzer not available', code='SERVICE_UNAVAILABLE', status_code=500)
        
        # データ取得
        logs = BehaviorLog.get_recent_logs(hours=hours, user_id=user_id)
        
        if not logs:
            return success_response({
                'message': f'過去{hours}時間のデータが見つかりません',
                'hours': hours,
                'logs_count': 0
            })
        
        # 集中度詳細分析実行
        focus_analysis = advanced_analyzer.analyze_focus_detailed(logs)
        
        # セッション詳細を含めない場合は除外
        if not include_sessions:
            focus_analysis.pop('focus_sessions', None)
        
        result_data = {
            'analysis_period_hours': hours,
            'period_start': logs[-1].timestamp.isoformat() if logs else None,
            'period_end': logs[0].timestamp.isoformat() if logs else None,
            'total_logs': len(logs),
            'focus_analysis': focus_analysis,
            'summary': _generate_focus_summary(focus_analysis)
        }
        
        return success_response(result_data)
        
    except ValueError as e:
        return error_response('Invalid parameter format', code='VALIDATION_ERROR', status_code=400)
    except Exception as e:
        logger.error(f"Error getting focus deep dive: {e}", exc_info=True)
        return error_response('Failed to analyze focus details', code='ANALYSIS_ERROR', status_code=500)


@advanced_analysis_bp.route('/health-assessment', methods=['GET'])
def get_health_assessment():
    """健康評価API
    
    姿勢、健康状態、リスクアセスメントを提供
    
    Query Parameters:
        user_id (str): ユーザーID (オプション)
        hours (int): 分析対象時間 (デフォルト: 24)
        include_timeline (bool): リスクタイムラインを含めるか (デフォルト: false)
        
    Returns:
        JSON: 健康評価結果
    """
    try:
        # パラメータ取得
        user_id = request.args.get('user_id')
        hours = int(request.args.get('hours', 24))
        include_timeline = request.args.get('include_timeline', 'false').lower() == 'true'
        
        # バリデーション
        if hours < 1 or hours > 720:
            return error_response('Hours must be between 1 and 720', code='VALIDATION_ERROR', status_code=400)
        
        # 高度分析エンジン取得
        advanced_analyzer = _get_advanced_behavior_analyzer()
        if not advanced_analyzer:
            return error_response('Advanced behavior analyzer not available', code='SERVICE_UNAVAILABLE', status_code=500)
        
        # データ取得
        logs = BehaviorLog.get_recent_logs(hours=hours, user_id=user_id)
        
        if not logs:
            return success_response({
                'message': f'過去{hours}時間のデータが見つかりません',
                'hours': hours,
                'logs_count': 0
            })
        
        # 健康評価分析実行
        health_analysis = advanced_analyzer.analyze_health_assessment(logs)
        
        # タイムラインを含めない場合は除外
        if not include_timeline:
            health_analysis.pop('risk_timeline', None)
        
        result_data = {
            'analysis_period_hours': hours,
            'period_start': logs[-1].timestamp.isoformat() if logs else None,
            'period_end': logs[0].timestamp.isoformat() if logs else None,
            'total_logs': len(logs),
            'health_analysis': health_analysis,
            'risk_summary': _generate_health_risk_summary(health_analysis)
        }
        
        return success_response(result_data)
        
    except ValueError as e:
        return error_response('Invalid parameter format', code='VALIDATION_ERROR', status_code=400)
    except Exception as e:
        logger.error(f"Error getting health assessment: {e}", exc_info=True)
        return error_response('Failed to perform health assessment', code='ANALYSIS_ERROR', status_code=500)


@advanced_analysis_bp.route('/productivity-score', methods=['GET'])
def get_productivity_score():
    """生産性スコアAPI
    
    作業効率、生産性指標、活動パターン分析を提供
    
    Query Parameters:
        user_id (str): ユーザーID (オプション)
        hours (int): 分析対象時間 (デフォルト: 24)
        include_timeline (bool): 活動タイムラインを含めるか (デフォルト: false)
        
    Returns:
        JSON: 生産性スコア結果
    """
    try:
        # パラメータ取得
        user_id = request.args.get('user_id')
        hours = int(request.args.get('hours', 24))
        include_timeline = request.args.get('include_timeline', 'false').lower() == 'true'
        
        # バリデーション
        if hours < 1 or hours > 720:
            return error_response('Hours must be between 1 and 720', code='VALIDATION_ERROR', status_code=400)
        
        # 高度分析エンジン取得
        advanced_analyzer = _get_advanced_behavior_analyzer()
        if not advanced_analyzer:
            return error_response('Advanced behavior analyzer not available', code='SERVICE_UNAVAILABLE', status_code=500)
        
        # データ取得
        logs = BehaviorLog.get_recent_logs(hours=hours, user_id=user_id)
        
        if not logs:
            return success_response({
                'message': f'過去{hours}時間のデータが見つかりません',
                'hours': hours,
                'logs_count': 0
            })
        
        # 活動パターン分析実行
        activity_analysis = advanced_analyzer.analyze_activity_patterns(logs)
        
        # タイムラインを含めない場合は除外
        if not include_timeline:
            activity_analysis.pop('activity_timeline', None)
        
        result_data = {
            'analysis_period_hours': hours,
            'period_start': logs[-1].timestamp.isoformat() if logs else None,
            'period_end': logs[0].timestamp.isoformat() if logs else None,
            'total_logs': len(logs),
            'activity_analysis': activity_analysis,
            'productivity_summary': _generate_productivity_summary(activity_analysis)
        }
        
        return success_response(result_data)
        
    except ValueError as e:
        return error_response('Invalid parameter format', code='VALIDATION_ERROR', status_code=400)
    except Exception as e:
        logger.error(f"Error getting productivity score: {e}", exc_info=True)
        return error_response('Failed to calculate productivity score', code='ANALYSIS_ERROR', status_code=500)


# ========== ヘルパー関数 ==========

def _get_advanced_behavior_analyzer():
    """高度行動分析器インスタンスを取得"""
    return get_advanced_behavior_analyzer()


def _get_pattern_recognizer():
    """パターン認識器インスタンスを取得"""
    return get_pattern_recognizer()


def _filter_patterns_by_type(pattern_analysis: Dict[str, Any], pattern_type: str) -> Dict[str, Any]:
    """パターンタイプ別にフィルタリング"""
    try:
        filtered_analysis = pattern_analysis.copy()
        
        if pattern_type == 'cyclical':
            filtered_analysis = {
                'cyclical_patterns': pattern_analysis.get('cyclical_patterns', []),
                'pattern_strength': pattern_analysis.get('pattern_strength', {}),
                'summary': f"Cyclical patterns: {len(pattern_analysis.get('cyclical_patterns', []))} found"
            }
        elif pattern_type == 'trending':
            filtered_analysis = {
                'trend_patterns': pattern_analysis.get('trend_patterns', []),
                'pattern_strength': pattern_analysis.get('pattern_strength', {}),
                'summary': f"Trend patterns: {len(pattern_analysis.get('trend_patterns', []))} found"
            }
        elif pattern_type == 'seasonal':
            filtered_analysis = {
                'seasonal_patterns': pattern_analysis.get('seasonal_patterns', []),
                'pattern_strength': pattern_analysis.get('pattern_strength', {}),
                'summary': f"Seasonal patterns: {len(pattern_analysis.get('seasonal_patterns', []))} found"
            }
        
        return filtered_analysis
        
    except Exception as e:
        logger.error(f"Error filtering patterns: {e}")
        return pattern_analysis


def _generate_advanced_pattern_insights(timeseries_analysis: Dict, pattern_analysis: Dict, 
                                      clustering_analysis: Dict) -> List[str]:
    """高度パターンインサイト生成"""
    try:
        insights = []
        
        # 時系列分析からのインサイト
        if 'trends' in timeseries_analysis:
            trends = timeseries_analysis['trends']
            for metric, trend_info in trends.items():
                if trend_info.get('direction') == 'ascending':
                    insights.append(f"{metric}に上昇傾向が見られます")
                elif trend_info.get('direction') == 'descending':
                    insights.append(f"{metric}に下降傾向が見られます")
        
        # パターン認識からのインサイト
        if 'cyclical_patterns' in pattern_analysis:
            cyclical_count = len(pattern_analysis['cyclical_patterns'])
            if cyclical_count > 0:
                insights.append(f"{cyclical_count}個の周期的パターンが検出されました")
        
        # クラスタリングからのインサイト
        if 'cluster_analysis' in clustering_analysis:
            cluster_count = len(clustering_analysis['cluster_analysis'])
            insights.append(f"行動は{cluster_count}つの主要パターンに分類されます")
        
        return insights if insights else ["詳細な分析パターンが検出されませんでした"]
        
    except Exception as e:
        logger.error(f"Error generating advanced pattern insights: {e}")
        return ["パターンインサイトの生成中にエラーが発生しました"]


def _generate_focus_summary(focus_analysis: Dict) -> Dict[str, Any]:
    """集中度サマリー生成"""
    try:
        summary = {
            'total_sessions': 0,
            'average_quality': 0.0,
            'primary_distractions': [],
            'optimal_periods': []
        }
        
        if 'focus_sessions' in focus_analysis:
            sessions = focus_analysis['focus_sessions']
            summary['total_sessions'] = len(sessions)
            
            if sessions:
                qualities = [s.get('quality_score', 0) for s in sessions]
                summary['average_quality'] = sum(qualities) / len(qualities)
        
        if 'distraction_analysis' in focus_analysis:
            summary['primary_distractions'] = focus_analysis['distraction_analysis'].get('top_distractions', [])
        
        if 'optimal_periods' in focus_analysis:
            summary['optimal_periods'] = focus_analysis['optimal_periods']
        
        return summary
        
    except Exception as e:
        logger.error(f"Error generating focus summary: {e}")
        return {'error': 'サマリー生成エラー'}


def _generate_health_risk_summary(health_analysis: Dict) -> Dict[str, Any]:
    """健康リスクサマリー生成"""
    try:
        summary = {
            'overall_risk': 'moderate',
            'primary_concerns': [],
            'recommended_actions': []
        }
        
        if 'health_assessment' in health_analysis:
            assessment = health_analysis['health_assessment']
            summary['overall_risk'] = assessment.get('overall_risk', 'moderate')
            summary['recommended_actions'] = assessment.get('recommendations', [])
        
        return summary
        
    except Exception as e:
        logger.error(f"Error generating health risk summary: {e}")
        return {'error': 'リスクサマリー生成エラー'}


def _generate_productivity_summary(activity_analysis: Dict) -> Dict[str, Any]:
    """生産性サマリー生成"""
    try:
        summary = {
            'efficiency_score': 0.5,
            'focus_consistency': 0.5,
            'key_insights': []
        }
        
        if 'productivity_metrics' in activity_analysis:
            metrics = activity_analysis['productivity_metrics']
            summary['efficiency_score'] = metrics.get('efficiency_score', 0.5)
            summary['focus_consistency'] = metrics.get('focus_consistency', 0.5)
        
        if 'insights' in activity_analysis:
            summary['key_insights'] = activity_analysis['insights']
        
        return summary
        
    except Exception as e:
        logger.error(f"Error generating productivity summary: {e}")
        return {'error': '生産性サマリー生成エラー'}

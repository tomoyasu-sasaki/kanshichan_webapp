"""
Advanced Analysis API Routes - 高度行動分析API

高度な行動分析機能のAPIエンドポイント群
パターン認識、集中度詳細分析、健康評価、生産性スコアを提供
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app

from models.behavior_log import BehaviorLog
from utils.logger import setup_logger
from .analysis_helpers import (
    generate_comprehensive_insights,
    calculate_behavior_score,
    detect_behavioral_patterns,
    generate_contextual_recommendations,
    calculate_data_quality_metrics
)

logger = setup_logger(__name__)

# Blueprint定義
advanced_analysis_bp = Blueprint('advanced_analysis', __name__, url_prefix='/api/analysis')


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
        valid_timeframes = ['hourly', 'daily', 'weekly', 'monthly']
        valid_pattern_types = ['cyclical', 'trending', 'seasonal', 'all']
        
        if timeframe not in valid_timeframes:
            return jsonify({
                'status': 'error',
                'error': f'Invalid timeframe. Must be one of: {", ".join(valid_timeframes)}',
                'code': 'VALIDATION_ERROR',
                'timestamp': datetime.utcnow().isoformat()
            }), 400
        
        if pattern_type not in valid_pattern_types:
            return jsonify({
                'status': 'error',
                'error': f'Invalid pattern_type. Must be one of: {", ".join(valid_pattern_types)}',
                'code': 'VALIDATION_ERROR',
                'timestamp': datetime.utcnow().isoformat()
            }), 400
        
        # 高度分析エンジン取得
        advanced_analyzer = _get_advanced_behavior_analyzer()
        pattern_recognizer = _get_pattern_recognizer()
        
        if not advanced_analyzer or not pattern_recognizer:
            return jsonify({
                'status': 'error',
                'error': 'Advanced analysis services not available',
                'code': 'SERVICE_UNAVAILABLE',
                'timestamp': datetime.utcnow().isoformat()
            }), 500
        
        # 期間に応じたデータ取得
        hours_map = {'hourly': 1, 'daily': 24, 'weekly': 168, 'monthly': 720}
        hours = hours_map[timeframe]
        logs = BehaviorLog.get_recent_logs(hours=hours, user_id=user_id)
        
        if not logs:
            return jsonify({
                'status': 'success',
                'data': {
                    'message': f'{timeframe}のデータが見つかりません',
                    'timeframe': timeframe,
                    'pattern_type': pattern_type,
                    'logs_count': 0
                },
                'timestamp': datetime.utcnow().isoformat()
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
        
        return jsonify({
            'status': 'success',
            'data': result_data,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting advanced patterns: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': 'Failed to analyze advanced patterns',
            'code': 'ANALYSIS_ERROR',
            'timestamp': datetime.utcnow().isoformat()
        }), 500


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
            return jsonify({
                'status': 'error',
                'error': 'Hours must be between 1 and 720',
                'code': 'VALIDATION_ERROR',
                'timestamp': datetime.utcnow().isoformat()
            }), 400
        
        # 高度分析エンジン取得
        advanced_analyzer = _get_advanced_behavior_analyzer()
        if not advanced_analyzer:
            return jsonify({
                'status': 'error',
                'error': 'Advanced behavior analyzer not available',
                'code': 'SERVICE_UNAVAILABLE',
                'timestamp': datetime.utcnow().isoformat()
            }), 500
        
        # データ取得
        logs = BehaviorLog.get_recent_logs(hours=hours, user_id=user_id)
        
        if not logs:
            return jsonify({
                'status': 'success',
                'data': {
                    'message': f'過去{hours}時間のデータが見つかりません',
                    'hours': hours,
                    'logs_count': 0
                },
                'timestamp': datetime.utcnow().isoformat()
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
        
        return jsonify({
            'status': 'success',
            'data': result_data,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'error': 'Invalid parameter format',
            'code': 'VALIDATION_ERROR',
            'timestamp': datetime.utcnow().isoformat()
        }), 400
    except Exception as e:
        logger.error(f"Error getting focus deep dive: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': 'Failed to analyze focus details',
            'code': 'ANALYSIS_ERROR',
            'timestamp': datetime.utcnow().isoformat()
        }), 500


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
            return jsonify({
                'status': 'error',
                'error': 'Hours must be between 1 and 720',
                'code': 'VALIDATION_ERROR',
                'timestamp': datetime.utcnow().isoformat()
            }), 400
        
        # 高度分析エンジン取得
        advanced_analyzer = _get_advanced_behavior_analyzer()
        if not advanced_analyzer:
            return jsonify({
                'status': 'error',
                'error': 'Advanced behavior analyzer not available',
                'code': 'SERVICE_UNAVAILABLE',
                'timestamp': datetime.utcnow().isoformat()
            }), 500
        
        # データ取得
        logs = BehaviorLog.get_recent_logs(hours=hours, user_id=user_id)
        
        if not logs:
            return jsonify({
                'status': 'success',
                'data': {
                    'message': f'過去{hours}時間のデータが見つかりません',
                    'hours': hours,
                    'logs_count': 0
                },
                'timestamp': datetime.utcnow().isoformat()
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
        
        return jsonify({
            'status': 'success',
            'data': result_data,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'error': 'Invalid parameter format',
            'code': 'VALIDATION_ERROR',
            'timestamp': datetime.utcnow().isoformat()
        }), 400
    except Exception as e:
        logger.error(f"Error getting health assessment: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': 'Failed to perform health assessment',
            'code': 'ANALYSIS_ERROR',
            'timestamp': datetime.utcnow().isoformat()
        }), 500


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
            return jsonify({
                'status': 'error',
                'error': 'Hours must be between 1 and 720',
                'code': 'VALIDATION_ERROR',
                'timestamp': datetime.utcnow().isoformat()
            }), 400
        
        # 高度分析エンジン取得
        advanced_analyzer = _get_advanced_behavior_analyzer()
        if not advanced_analyzer:
            return jsonify({
                'status': 'error',
                'error': 'Advanced behavior analyzer not available',
                'code': 'SERVICE_UNAVAILABLE',
                'timestamp': datetime.utcnow().isoformat()
            }), 500
        
        # データ取得
        logs = BehaviorLog.get_recent_logs(hours=hours, user_id=user_id)
        
        if not logs:
            return jsonify({
                'status': 'success',
                'data': {
                    'message': f'過去{hours}時間のデータが見つかりません',
                    'hours': hours,
                    'logs_count': 0
                },
                'timestamp': datetime.utcnow().isoformat()
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
        
        return jsonify({
            'status': 'success',
            'data': result_data,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'error': 'Invalid parameter format',
            'code': 'VALIDATION_ERROR',
            'timestamp': datetime.utcnow().isoformat()
        }), 400
    except Exception as e:
        logger.error(f"Error getting productivity score: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': 'Failed to calculate productivity score',
            'code': 'ANALYSIS_ERROR',
            'timestamp': datetime.utcnow().isoformat()
        }), 500


# ========== ヘルパー関数 ==========

def _get_advanced_behavior_analyzer() -> Optional[Any]:
    """高度行動分析器インスタンス取得（シングルトンパターン）
    
    AdvancedBehaviorAnalyzerのインスタンスを作成し、設定を適用します。
    複雑な行動パターンの詳細分析に使用されます。
    
    Returns:
        Optional[Any]: AdvancedBehaviorAnalyzerインスタンス、またはエラー時はNone
        
    Note:
        設定はFlaskのcurrent_app.configから取得されます。
        初期化に失敗した場合はログに記録し、Noneを返します。
        インスタンスはFlaskアプリケーションコンテキストにキャッシュされます。
    """
    # インスタンスがすでにFlaskアプリケーションコンテキストに存在するか確認
    if 'advanced_behavior_analyzer' in current_app.config:
        return current_app.config['advanced_behavior_analyzer']
    
    try:
        from services.ai_ml.advanced_behavior_analyzer import AdvancedBehaviorAnalyzer
        config = current_app.config.get('config_manager').get_all()
        analyzer = AdvancedBehaviorAnalyzer(config)
        # キャッシュに保存
        current_app.config['advanced_behavior_analyzer'] = analyzer
        return analyzer
    except Exception as e:
        logger.error(f"Error creating AdvancedBehaviorAnalyzer: {e}")
    return None


def _get_pattern_recognizer() -> Optional[Any]:
    """パターン認識エンジンインスタンス取得（シングルトンパターン）
    
    PatternRecognizerのインスタンスを作成し、設定を適用します。
    行動データからの複雑なパターン認識に使用されます。
    
    Returns:
        Optional[Any]: PatternRecognizerインスタンス、またはエラー時はNone
        
    Note:
        設定はFlaskのcurrent_app.configから取得されます。
        初期化に失敗した場合はログに記録し、Noneを返します。
        インスタンスはFlaskアプリケーションコンテキストにキャッシュされます。
    """
    # インスタンスがすでにFlaskアプリケーションコンテキストに存在するか確認
    if 'pattern_recognizer' in current_app.config:
        return current_app.config['pattern_recognizer']
    
    try:
        from services.ai_ml.pattern_recognition import PatternRecognizer
        config = current_app.config.get('config_manager').get_all()
        recognizer = PatternRecognizer(config)
        # キャッシュに保存
        current_app.config['pattern_recognizer'] = recognizer
        return recognizer
    except Exception as e:
        logger.error(f"Error creating PatternRecognizer: {e}")
    return None


def _filter_patterns_by_type(pattern_analysis: Dict[str, Any], pattern_type: str) -> Dict[str, Any]:
    """パターンタイプ別フィルタリング"""
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
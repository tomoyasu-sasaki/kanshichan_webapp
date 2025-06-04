"""
Basic Analysis API Routes - 基本行動分析API

基本的な行動分析機能のAPIエンドポイント群
システム状態、トレンド分析、日次インサイト、推奨事項を提供
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app

from models.behavior_log import BehaviorLog
from models.user_profile import UserProfile
from utils.logger import setup_logger
from services.ai_ml.llm_service import LLMService
from services.ai_ml.advice_generator import AdviceGenerator
from services.analysis.behavior_analyzer import BehaviorAnalyzer
from .analysis_helpers import (
    generate_comprehensive_insights,
    calculate_behavior_score,
    detect_behavioral_patterns,
    generate_contextual_recommendations,
    calculate_data_quality_metrics
)

logger = setup_logger(__name__)

# Blueprint定義
basic_analysis_bp = Blueprint('basic_analysis', __name__, url_prefix='/api/analysis')


@basic_analysis_bp.route('/status', methods=['GET'])
def get_analysis_status():
    """分析システムの状態取得API
    
    分析システム全体の健康状態とサービス状況を返す
    
    Returns:
        JSON: 分析システムの状態情報
    """
    try:
        # 各サービスの状態チェック
        analyzer_status = 'active' if _get_behavior_analyzer() else 'inactive'
        llm_status = 'active' if _get_llm_service() else 'inactive'
        advanced_analyzer_status = 'active' if _get_advanced_behavior_analyzer() else 'inactive'
        
        # データベース接続確認
        try:
            recent_logs = BehaviorLog.get_recent_logs(hours=1)
            db_status = 'active'
        except Exception:
            db_status = 'error'
        
        # 全体健康度計算
        active_services = sum([
            1 for status in [analyzer_status, llm_status, advanced_analyzer_status, db_status]
            if status == 'active'
        ])
        health_score = active_services / 4.0
        
        return jsonify({
            'status': 'success',
            'data': {
                'overall_status': 'healthy' if health_score >= 0.75 else 'degraded' if health_score >= 0.5 else 'critical',
                'health_score': health_score,
                'services': {
                    'behavior_analyzer': analyzer_status,
                    'llm_service': llm_status,
                    'advanced_analyzer': advanced_analyzer_status,
                    'database': db_status
                },
                'last_check': datetime.utcnow().isoformat()
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error checking analysis status: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': 'Failed to check analysis system status',
            'code': 'STATUS_CHECK_ERROR',
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@basic_analysis_bp.route('/trends', methods=['GET'])
def get_behavior_trends():
    """行動トレンド取得API
    
    指定期間の行動トレンドを分析して返す
    
    Query Parameters:
        timeframe (str): 分析期間 (hourly/daily/weekly) - デフォルト: daily
        user_id (str): ユーザーID (オプション)
        
    Returns:
        JSON: 行動トレンド分析結果
    """
    try:
        # パラメータ取得
        timeframe = request.args.get('timeframe', 'daily')
        user_id = request.args.get('user_id')
        
        if timeframe not in ['hourly', 'daily', 'weekly']:
            return jsonify({
                'status': 'error',
                'error': 'Invalid timeframe. Must be one of: hourly, daily, weekly',
                'code': 'VALIDATION_ERROR',
                'timestamp': datetime.utcnow().isoformat()
            }), 400
        
        # BehaviorAnalyzerインスタンス取得
        analyzer = _get_behavior_analyzer()
        if not analyzer:
            return jsonify({
                'status': 'error',
                'error': 'BehaviorAnalyzer not available',
                'code': 'SERVICE_UNAVAILABLE',
                'timestamp': datetime.utcnow().isoformat()
            }), 500
        
        # 期間に応じたデータ取得
        hours_map = {'hourly': 1, 'daily': 24, 'weekly': 168}
        hours = hours_map[timeframe]
        
        # 行動ログ取得
        logs = BehaviorLog.get_recent_logs(hours=hours, user_id=user_id)
        
        # Phase 3.2: フォールバック処理追加
        if not logs or len(logs) == 0:
            return jsonify({
                'status': 'success',
                'data': {
                    'message': 'データ収集中です。しばらくお待ちください。',
                    'data_collection_status': 'active',
                    'estimated_wait_time': '2-5分',
                    'timeframe': timeframe,
                    'period_hours': hours,
                    'logs_count': 0
                },
                'timestamp': datetime.utcnow().isoformat()
            })
        
        # 最小データ要件チェック
        if len(logs) < 5:
            return jsonify({
                'status': 'success',
                'data': {
                    'message': f'データ収集中です（{len(logs)}件収集済み）。より詳細な分析には5件以上のデータが必要です。',
                    'data_collection_status': 'active',
                    'estimated_wait_time': '2-3分',
                    'timeframe': timeframe,
                    'period_hours': hours,
                    'logs_count': len(logs)
                },
                'timestamp': datetime.utcnow().isoformat()
            })
        
        if not logs:
            return jsonify({
                'status': 'success',
                'data': {
                    'message': f'{timeframe}のデータが見つかりません',
                    'timeframe': timeframe,
                    'period_hours': hours,
                    'logs_count': 0
                },
                'timestamp': datetime.utcnow().isoformat()
            })
        
        # 集中度パターン分析
        focus_analysis = analyzer.analyze_focus_pattern(logs)
        
        # 🆕 フロントエンド用の追加メトリクス計算
        total_logs = len(logs)
        present_count = sum(1 for log in logs if log.presence_status == 'present')
        smartphone_count = sum(1 for log in logs if log.smartphone_detected)
        
        # focus_analysisにフロントエンド互換データを追加
        if focus_analysis and 'error' not in focus_analysis:
            # 既存のbasic_statisticsに追加データを含める
            if 'basic_statistics' not in focus_analysis:
                focus_analysis['basic_statistics'] = {}
            
            # 在席率の計算
            presence_rate = present_count / total_logs if total_logs > 0 else 0
            focus_analysis['presence_rate'] = presence_rate
            
            # スマートフォン使用率の計算
            smartphone_usage_rate = smartphone_count / total_logs if total_logs > 0 else 0
            focus_analysis['smartphone_usage_rate'] = smartphone_usage_rate
            
            # セッション数（時間別統計の数）
            hourly_sessions = len(focus_analysis.get('hourly_patterns', {}).get('hourly_statistics', {}))
            focus_analysis['total_sessions'] = hourly_sessions
            
            # 平均集中度（フロントエンド互換用）
            avg_focus = focus_analysis.get('basic_statistics', {}).get('mean', 0)
            focus_analysis['average_focus'] = avg_focus
            
            # 良い姿勢の割合（高集中度の割合を代用）
            good_posture_percentage = focus_analysis.get('basic_statistics', {}).get('high_focus_ratio', 0)
            focus_analysis['good_posture_percentage'] = good_posture_percentage
            
            # トレンド方向（フロントエンド互換用）
            trend_analysis = focus_analysis.get('trend_analysis', {})
            trend_direction_map = {
                'improving': 'up',
                'declining': 'down',
                'stable': 'stable'
            }
            focus_analysis['trend_direction'] = trend_direction_map.get(
                trend_analysis.get('trend', 'stable'), 'stable'
            )
            focus_analysis['trend_percentage'] = trend_analysis.get('trend_strength', 0)
        
        # 異常検知
        anomalies = analyzer.detect_anomalies(logs)
        
        # トレンドデータ構築
        trend_data = {
            'timeframe': timeframe,
            'period_start': logs[-1].timestamp.isoformat() if logs else None,
            'period_end': logs[0].timestamp.isoformat() if logs else None,
            'total_logs': len(logs),
            'focus_analysis': focus_analysis,
            'anomalies': anomalies,
            'trend_summary': _generate_trend_summary(focus_analysis, timeframe)
        }
        
        return jsonify({
            'status': 'success',
            'data': trend_data,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting behavior trends: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': 'Failed to analyze behavior trends',
            'code': 'ANALYSIS_ERROR',
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@basic_analysis_bp.route('/insights', methods=['GET'])
def get_daily_insights():
    """今日の洞察取得API
    
    今日の行動データから生成したインサイトを返す
    
    Query Parameters:
        user_id (str): ユーザーID (オプション)
        date (str): 対象日付 (YYYY-MM-DD形式、デフォルト: 今日)
        
    Returns:
        JSON: 今日の行動インサイト
    """
    try:
        # パラメータ取得
        user_id = request.args.get('user_id')
        date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        # 日付バリデーション
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({
                'status': 'error',
                'error': 'Invalid date format. Use YYYY-MM-DD',
                'code': 'VALIDATION_ERROR',
                'timestamp': datetime.utcnow().isoformat()
            }), 400
        
        # BehaviorAnalyzerインスタンス取得
        analyzer = _get_behavior_analyzer()
        if not analyzer:
            return jsonify({
                'status': 'error',
                'error': 'BehaviorAnalyzer not available',
                'code': 'SERVICE_UNAVAILABLE',
                'timestamp': datetime.utcnow().isoformat()
            }), 500
        
        # 対象日の行動ログ取得
        start_time = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(days=1)
        
        logs = BehaviorLog.get_logs_by_timerange(
            start_time=start_time,
            end_time=end_time,
            user_id=user_id
        )
        
        # Phase 3.2: フォールバック処理追加
        if not logs or len(logs) == 0:
            return jsonify({
                'status': 'success',
                'data': {
                    'message': 'データ収集中です。しばらくお待ちください。',
                    'data_collection_status': 'active',
                    'estimated_wait_time': '2-5分',
                    'target_date': date_str,
                    'insights': [],
                    'recommendations': []
                },
                'timestamp': datetime.utcnow().isoformat()
            })
        
        # 最小データ要件チェック
        if len(logs) < 5:
            return jsonify({
                'status': 'success',
                'data': {
                    'message': f'データ収集中です（{len(logs)}件収集済み）。より詳細な分析には5件以上のデータが必要です。',
                    'data_collection_status': 'active',
                    'estimated_wait_time': '2-3分',
                    'target_date': date_str,
                    'insights': [],
                    'recommendations': []
                },
                'timestamp': datetime.utcnow().isoformat()
            })
        
        if not logs:
            return jsonify({
                'status': 'success',
                'data': {
                    'message': f'{date_str}のデータが見つかりません',
                    'target_date': date_str,
                    'insights': [],
                    'recommendations': []
                },
                'timestamp': datetime.utcnow().isoformat()
            })
        
        # インサイト生成
        insights_data = analyzer.generate_insights(timeframe='daily')
        
        # LLMサービスでより詳細なインサイト生成
        llm_service = _get_llm_service()
        if llm_service:
            behavior_summary = _create_behavior_summary(logs)
            llm_insights = llm_service.generate_behavior_analysis(
                behavior_summary,
                {'date': date_str, 'user_id': user_id}
            )
            insights_data['llm_analysis'] = llm_insights
        
        return jsonify({
            'status': 'success',
            'data': {
                'target_date': date_str,
                'logs_analyzed': len(logs),
                'insights': insights_data,
                'summary': _generate_daily_summary(insights_data, logs)
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting daily insights: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': 'Failed to generate daily insights',
            'code': 'ANALYSIS_ERROR',
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@basic_analysis_bp.route('/recommendations', methods=['GET'])
def get_recommendations():
    """推奨事項取得API
    
    現在の行動状況に基づく推奨事項を生成して返す
    
    Query Parameters:
        user_id (str): ユーザーID (オプション)
        priority (str): 優先度フィルタ (high/medium/low)
        limit (int): 最大返却数 (デフォルト: 5)
        
    Returns:
        JSON: 推奨事項リスト
    """
    try:
        # パラメータ取得
        user_id = request.args.get('user_id')
        priority_filter = request.args.get('priority')
        limit = int(request.args.get('limit', 5))
        
        if priority_filter and priority_filter not in ['high', 'medium', 'low']:
            return jsonify({
                'status': 'error',
                'error': 'Invalid priority. Must be one of: high, medium, low',
                'code': 'VALIDATION_ERROR',
                'timestamp': datetime.utcnow().isoformat()
            }), 400
        
        if limit < 1 or limit > 20:
            return jsonify({
                'status': 'error',
                'error': 'Limit must be between 1 and 20',
                'code': 'VALIDATION_ERROR',
                'timestamp': datetime.utcnow().isoformat()
            }), 400
        
        # 最近の行動データ取得（過去1時間）
        recent_logs = BehaviorLog.get_recent_logs(hours=1, user_id=user_id)
        
        # AdviceGeneratorインスタンス取得
        advice_generator = _get_advice_generator()
        if not advice_generator:
            return jsonify({
                'status': 'error',
                'error': 'AdviceGenerator not available',
                'code': 'SERVICE_UNAVAILABLE',
                'timestamp': datetime.utcnow().isoformat()
            }), 500
        
        # 現在の行動状況を分析
        current_behavior = _analyze_current_behavior(recent_logs)
        
        # ユーザープロファイル取得
        user_profile = None
        if user_id:
            user_profile = UserProfile.get_by_user_id(user_id)
        
        # アドバイス生成
        advice_result = advice_generator.generate_contextual_advice(
            current_behavior, user_id
        )
        
        # 既存の分析結果から追加推奨事項取得
        analyzer = _get_behavior_analyzer()
        if analyzer:
            insights = analyzer.generate_insights(timeframe='daily')
            additional_recommendations = insights.get('recommendations', [])
        else:
            additional_recommendations = []
        
        # 推奨事項をまとめて優先度フィルタリング
        all_recommendations = []
        
        # メインアドバイス
        if advice_result.get('advice_text'):
            all_recommendations.append({
                'type': 'contextual_advice',
                'priority': advice_result.get('priority', 'medium'),
                'message': advice_result['advice_text'],
                'emotion': advice_result.get('emotion', 'encouraging'),
                'source': 'llm_advice',
                'timestamp': advice_result.get('generation_timestamp')
            })
        
        # 分析ベースの推奨事項
        for rec in additional_recommendations:
            all_recommendations.append({
                'type': rec.get('type', 'behavioral'),
                'priority': rec.get('priority', 'medium'),
                'message': rec.get('message', ''),
                'action': rec.get('action', ''),
                'source': 'behavior_analysis',
                'timestamp': datetime.utcnow().isoformat()
            })
        
        # 優先度フィルタ適用
        if priority_filter:
            all_recommendations = [
                rec for rec in all_recommendations 
                if rec['priority'] == priority_filter
            ]
        
        # 優先度順にソートしてリミット適用
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        all_recommendations.sort(
            key=lambda x: priority_order.get(x['priority'], 3)
        )
        
        recommendations = all_recommendations[:limit]
        
        return jsonify({
            'status': 'success',
            'data': {
                'recommendations': recommendations,
                'total_available': len(all_recommendations),
                'filtered_by_priority': priority_filter,
                'current_behavior_summary': current_behavior,
                'user_personalized': user_profile is not None
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'error': f'Invalid parameter: {str(e)}',
            'code': 'VALIDATION_ERROR',
            'timestamp': datetime.utcnow().isoformat()
        }), 400
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': 'Failed to generate recommendations',
            'code': 'ANALYSIS_ERROR',
            'timestamp': datetime.utcnow().isoformat()
        }), 500


# ========== ヘルパー関数 ==========

def _get_behavior_analyzer() -> Optional[BehaviorAnalyzer]:
    """BehaviorAnalyzerインスタンスを取得"""
    # Phase 3.2: main.pyで設定したBehaviorAnalyzerインスタンスを取得
    return current_app.config.get('behavior_analyzer')


def _get_llm_service() -> Optional[LLMService]:
    """LLMServiceインスタンスを取得"""
    config_manager = current_app.config.get('config_manager')
    if not config_manager:
        return None
    
    try:
        config = config_manager.get_all() if hasattr(config_manager, 'get_all') else {}
        return LLMService(config)
    except Exception as e:
        logger.warning(f"Failed to initialize LLMService: {e}")
        return None


def _get_advice_generator() -> Optional[AdviceGenerator]:
    """AdviceGeneratorインスタンスを取得"""
    config_manager = current_app.config.get('config_manager')
    if not config_manager:
        return None
    
    try:
        config = config_manager.get_all() if hasattr(config_manager, 'get_all') else {}
        llm_service = _get_llm_service()
        analyzer = _get_behavior_analyzer()
        
        if not llm_service or not analyzer:
            return None
            
        return AdviceGenerator(llm_service, analyzer, config)
    except Exception as e:
        logger.warning(f"Failed to initialize AdviceGenerator: {e}")
        return None


def _get_advanced_behavior_analyzer() -> Optional[Any]:
    """AdvancedBehaviorAnalyzerインスタンス取得 - Phase 5.2で復旧"""
    try:
        # Phase 5.2: 実際にAdvancedBehaviorAnalyzerをインポートして使用
        from services.ai_ml.advanced_behavior_analyzer import AdvancedBehaviorAnalyzer
        
        config_manager = current_app.config.get('config_manager')
        if not config_manager:
            logger.warning("ConfigManager not available for AdvancedBehaviorAnalyzer")
            return None
        
        # 設定取得
        config = config_manager.get_all() if hasattr(config_manager, 'get_all') else {}
        logger.debug("Creating AdvancedBehaviorAnalyzer instance...")
        
        # AdvancedBehaviorAnalyzerのインスタンス作成
        advanced_analyzer = AdvancedBehaviorAnalyzer(config)
        logger.info("AdvancedBehaviorAnalyzer initialized successfully")
        return advanced_analyzer
        
    except ImportError as e:
        logger.error(f"Failed to import AdvancedBehaviorAnalyzer: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize AdvancedBehaviorAnalyzer: {e}", exc_info=True)
        return None


def _generate_trend_summary(focus_analysis: Dict[str, Any], timeframe: str) -> Dict[str, Any]:
    """トレンドサマリーを生成"""
    basic_stats = focus_analysis.get('basic_statistics', {})
    trend_analysis = focus_analysis.get('trend_analysis', {})
    
    avg_focus = basic_stats.get('mean', 0)
    trend_direction = trend_analysis.get('trend', 'stable')
    
    return {
        'average_focus_level': round(avg_focus, 2),
        'trend_direction': trend_direction,
        'focus_stability': trend_analysis.get('stability', 'medium'),
        'timeframe': timeframe,
        'summary_text': f"{timeframe}の平均集中度: {avg_focus:.1f}, 傾向: {trend_direction}"
    }


def _create_behavior_summary(logs: list) -> Dict[str, Any]:
    """行動ログから行動サマリーを作成"""
    if not logs:
        return {}
    
    total_logs = len(logs)
    focus_scores = [log.focus_level for log in logs if log.focus_level is not None]
    smartphone_count = sum(1 for log in logs if log.smartphone_detected)
    present_count = sum(1 for log in logs if log.presence_status == 'present')
    
    return {
        'total_entries': total_logs,
        'average_focus': sum(focus_scores) / len(focus_scores) if focus_scores else 0,
        'smartphone_usage_rate': smartphone_count / total_logs if total_logs > 0 else 0,
        'presence_rate': present_count / total_logs if total_logs > 0 else 0,
        'session_duration_minutes': total_logs * 0.5,  # 30秒間隔と仮定
        'period_start': logs[-1].timestamp.isoformat() if logs else None,
        'period_end': logs[0].timestamp.isoformat() if logs else None
    }


def _generate_daily_summary(insights_data: Dict[str, Any], logs: list) -> Dict[str, Any]:
    """日次サマリーを生成"""
    productivity_analysis = insights_data.get('productivity_analysis', {})
    focus_analysis = insights_data.get('focus_analysis', {})
    
    # フロントエンド期待値に対応したfocus_scoreとproductivity_scoreを追加
    avg_focus = focus_analysis.get('basic_statistics', {}).get('mean', 0)
    productivity_score = productivity_analysis.get('productivity_score', 0)
    
    # バックエンド計算による生産性スコア（フォールバック）
    if productivity_score == 0 and logs:
        # 一時的に behavior_routes の関数をインポート
        try:
            from . import behavior_routes
            productivity_score = behavior_routes._calculate_productivity_score(logs)
        except Exception:
            productivity_score = 0
    
    return {
        'total_active_time': f"{len(logs) * 0.5:.1f} minutes",
        'productivity_score': productivity_score,
        'average_focus': avg_focus,
        'key_insights_count': len(insights_data.get('key_insights', [])),
        'recommendations_count': len(insights_data.get('recommendations', [])),
        'overall_assessment': _assess_daily_performance(insights_data),
        # フロントエンド期待値対応
        'insights': {
            'focus_score': avg_focus,
            'productivity_score': productivity_score,
            'key_findings': insights_data.get('key_insights', []),
            'improvement_areas': insights_data.get('recommendations', [])
        }
    }


def _analyze_current_behavior(logs: list) -> Dict[str, Any]:
    """現在の行動状況を分析"""
    if not logs:
        return {
            'status': 'no_data',
            'focus_level': 0,
            'session_duration_minutes': 0,
            'smartphone_detected': False,
            'presence_status': 'unknown'
        }
    
    recent_log = logs[0]  # 最新のログ
    
    return {
        'status': 'active',
        'focus_level': recent_log.focus_level or 0,
        'session_duration_minutes': len(logs) * 0.5,
        'smartphone_detected': recent_log.smartphone_detected,
        'presence_status': recent_log.presence_status,
        'last_update': recent_log.timestamp.isoformat()
    }


def _assess_daily_performance(insights_data: Dict[str, Any]) -> str:
    """日次パフォーマンスを評価"""
    productivity_score = insights_data.get('productivity_analysis', {}).get('productivity_score', 0)
    
    if productivity_score >= 0.7:
        return 'excellent'
    elif productivity_score >= 0.5:
        return 'good'
    elif productivity_score >= 0.3:
        return 'average'
    else:
        return 'needs_improvement' 
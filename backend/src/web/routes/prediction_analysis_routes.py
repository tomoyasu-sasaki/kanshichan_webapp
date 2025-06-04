"""
Prediction Analysis API Routes - 予測・パーソナライゼーション分析API

機械学習ベースの予測分析とパーソナライゼーション機能のAPIエンドポイント群
行動予測、パーソナライズド推奨、ユーザープロファイル、適応学習を提供
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
    calculate_data_quality_metrics,

)

logger = setup_logger(__name__)

# Blueprint定義
prediction_analysis_bp = Blueprint('prediction_analysis', __name__, url_prefix='/api/analysis')


@prediction_analysis_bp.route('/predictions', methods=['GET'])
def get_predictions():
    """予測結果API
    
    機械学習ベースの行動予測と将来のパターン予測を提供
    
    Query Parameters:
        user_id (str): ユーザーID (オプション)
        metrics (str): 予測対象指標 (カンマ区切り) - デフォルト: focus_score,posture_score
        horizon (int): 予測時間（分） (デフォルト: 60)
        
    Returns:
        JSON: 予測結果
    """
    try:
        # パラメータ取得
        user_id = request.args.get('user_id')
        metrics_str = request.args.get('metrics', 'focus_score,posture_score')
        horizon = int(request.args.get('horizon', 60))
        
        # メトリクス解析
        target_metrics = [m.strip() for m in metrics_str.split(',') if m.strip()]
        
        # バリデーション
        valid_metrics = ['focus_score', 'posture_score', 'activity_level', 'distraction_level']
        invalid_metrics = [m for m in target_metrics if m not in valid_metrics]
        
        if invalid_metrics:
            return jsonify({
                'status': 'error',
                'error': f'Invalid metrics: {", ".join(invalid_metrics)}. Valid metrics: {", ".join(valid_metrics)}',
                'code': 'VALIDATION_ERROR',
                'timestamp': datetime.utcnow().isoformat()
            }), 400
        
        if horizon < 5 or horizon > 1440:  # 5分〜24時間
            return jsonify({
                'status': 'error',
                'error': 'Horizon must be between 5 and 1440 minutes',
                'code': 'VALIDATION_ERROR',
                'timestamp': datetime.utcnow().isoformat()
            }), 400
        
        # パターン認識エンジン取得
        pattern_recognizer = _get_pattern_recognizer()
        if not pattern_recognizer:
            return jsonify({
                'status': 'error',
                'error': 'Pattern recognizer not available',
                'code': 'SERVICE_UNAVAILABLE',
                'timestamp': datetime.utcnow().isoformat()
            }), 500
        
        # 予測に必要な十分なデータを取得
        hours = max(24, horizon // 60 * 4)  # 最低24時間、予測期間の4倍
        logs = BehaviorLog.get_recent_logs(hours=hours, user_id=user_id)
        
        if len(logs) < 30:  # 最低30データポイント必要
            return jsonify({
                'status': 'success',
                'data': {
                    'message': '予測に十分なデータがありません（最低30データポイント必要）',
                    'available_logs': len(logs),
                    'required_logs': 30
                },
                'timestamp': datetime.utcnow().isoformat()
            })
        
        # 予測実行
        predictions = pattern_recognizer.generate_predictions(logs, target_metrics)
        
        result_data = {
            'target_metrics': target_metrics,
            'prediction_horizon_minutes': horizon,
            'data_period_hours': hours,
            'period_start': logs[-1].timestamp.isoformat() if logs else None,
            'period_end': logs[0].timestamp.isoformat() if logs else None,
            'total_logs': len(logs),
            'predictions': predictions,
            'prediction_summary': _generate_prediction_summary(predictions, target_metrics)
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
        logger.error(f"Error getting predictions: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': 'Failed to generate predictions',
            'code': 'ANALYSIS_ERROR',
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@prediction_analysis_bp.route('/personalized-recommendations', methods=['GET'])
def get_personalized_recommendations():
    """パーソナライズド推奨API
    
    ユーザーの個人特性とコンテキストに基づいて最適化された推奨事項を提供
    
    Query Parameters:
        user_id (str): ユーザーID (必須)
        context_type (str): コンテキストタイプ (time_based/behavior_based/environment_based) - デフォルト: behavior_based
        max_recommendations (int): 最大推奨数 (デフォルト: 5)
        
    Returns:
        JSON: パーソナライズド推奨結果
    """
    try:
        # パラメータ取得
        user_id = request.args.get('user_id')
        context_type = request.args.get('context_type', 'behavior_based')
        max_recommendations = int(request.args.get('max_recommendations', 5))
        
        # バリデーション
        if not user_id:
            return jsonify({
                'status': 'error',
                'error': 'user_id is required',
                'code': 'VALIDATION_ERROR',
                'timestamp': datetime.utcnow().isoformat()
            }), 400
        
        valid_context_types = ['time_based', 'behavior_based', 'environment_based']
        if context_type not in valid_context_types:
            return jsonify({
                'status': 'error',
                'error': f'Invalid context_type. Must be one of: {", ".join(valid_context_types)}',
                'code': 'VALIDATION_ERROR',
                'timestamp': datetime.utcnow().isoformat()
            }), 400
        
        if max_recommendations < 1 or max_recommendations > 10:
            return jsonify({
                'status': 'error',
                'error': 'max_recommendations must be between 1 and 10',
                'code': 'VALIDATION_ERROR',
                'timestamp': datetime.utcnow().isoformat()
            }), 400
        
        # パーソナライゼーションエンジン取得
        personalization_engine = _get_personalization_engine()
        if not personalization_engine:
            return jsonify({
                'status': 'error',
                'error': 'Personalization engine not available',
                'code': 'SERVICE_UNAVAILABLE',
                'timestamp': datetime.utcnow().isoformat()
            }), 500
        
        # 行動ログ取得
        logs = BehaviorLog.get_recent_logs(hours=24, user_id=user_id)
        
        # コンテキスト構築
        current_context = {
            'type': context_type,
            'timestamp': datetime.utcnow().isoformat(),
            'environment': request.args.to_dict()
        }
        
        # パーソナライズド推奨生成
        recommendations = personalization_engine.get_personalized_recommendations(
            user_id, logs, current_context
        )
        
        # 推奨数制限
        limited_recommendations = recommendations[:max_recommendations]
        
        result_data = {
            'user_id': user_id,
            'context_type': context_type,
            'recommendations_count': len(limited_recommendations),
            'total_available': len(recommendations),
            'recommendations': [_personalized_recommendation_to_dict(r) for r in limited_recommendations],
            'context_analysis': {
                'context_type': context_type,
                'data_points': len(logs),
                'generation_timestamp': datetime.utcnow().isoformat()
            }
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
        logger.error(f"Error getting personalized recommendations: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': 'Failed to generate personalized recommendations',
            'code': 'ANALYSIS_ERROR',
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@prediction_analysis_bp.route('/user-profile', methods=['GET'])
def get_user_profile():
    """ユーザープロファイル取得API
    
    ユーザーの包括的プロファイル情報を取得
    
    Query Parameters:
        user_id (str): ユーザーID (必須)
        include_insights (bool): インサイト情報を含めるか (デフォルト: true)
        
    Returns:
        JSON: ユーザープロファイル情報
    """
    try:
        # パラメータ取得
        user_id = request.args.get('user_id')
        include_insights = request.args.get('include_insights', 'true').lower() == 'true'
        
        if not user_id:
            return jsonify({
                'status': 'error',
                'error': 'user_id is required',
                'code': 'VALIDATION_ERROR',
                'timestamp': datetime.utcnow().isoformat()
            }), 400
        
        # ユーザープロファイルビルダー取得
        profile_builder = _get_user_profile_builder()
        if not profile_builder:
            return jsonify({
                'status': 'error',
                'error': 'User profile builder not available',
                'code': 'SERVICE_UNAVAILABLE',
                'timestamp': datetime.utcnow().isoformat()
            }), 500
        
        # 行動ログ取得
        logs = BehaviorLog.get_recent_logs(hours=720, user_id=user_id)  # 30日分
        
        # 包括的プロファイル構築
        comprehensive_profile = profile_builder.build_comprehensive_profile(user_id, logs)
        
        # インサイト取得
        profile_insights = None
        if include_insights:
            profile_insights = profile_builder.get_profile_insights(user_id)
        
        result_data = {
            'user_id': user_id,
            'profile': comprehensive_profile,
            'insights': profile_insights,
            'data_summary': {
                'observation_period_days': comprehensive_profile.get('profile_metadata', {}).get('observation_period_days', 0),
                'data_points': len(logs),
                'profile_confidence': comprehensive_profile.get('confidence_score', 0.0)
            }
        }
        
        return jsonify({
            'status': 'success',
            'data': result_data,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting user profile: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': 'Failed to get user profile',
            'code': 'ANALYSIS_ERROR',
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@prediction_analysis_bp.route('/recommendation-feedback', methods=['POST'])
def submit_recommendation_feedback():
    """推奨事項フィードバック送信API
    
    ユーザーからの推奨事項フィードバックを受信・処理
    
    Request Body:
        {
            "user_id": "user123",
            "recommendation_id": "rec_456",
            "feedback": {
                "rating": 4.5,
                "text_feedback": "とても役に立ちました",
                "outcome": "implemented"
            }
        }
        
    Returns:
        JSON: フィードバック処理結果
    """
    try:
        # リクエストデータ取得
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'error': 'Request body is required',
                'code': 'VALIDATION_ERROR',
                'timestamp': datetime.utcnow().isoformat()
            }), 400
        
        # 必須フィールド検証
        required_fields = ['user_id', 'recommendation_id', 'feedback']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'error': f'Required field missing: {field}',
                    'code': 'VALIDATION_ERROR',
                    'timestamp': datetime.utcnow().isoformat()
                }), 400
        
        # パーソナライゼーションエンジン取得
        personalization_engine = _get_personalization_engine()
        if not personalization_engine:
            return jsonify({
                'status': 'error',
                'error': 'Personalization engine not available',
                'code': 'SERVICE_UNAVAILABLE',
                'timestamp': datetime.utcnow().isoformat()
            }), 500
        
        # フィードバック更新
        success = personalization_engine.update_recommendation_feedback(
            data['user_id'],
            data['recommendation_id'],
            data['feedback']
        )
        
        if success:
            return jsonify({
                'status': 'success',
                'data': {
                    'message': 'Feedback processed successfully',
                    'user_id': data['user_id'],
                    'recommendation_id': data['recommendation_id']
                },
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({
                'status': 'error',
                'error': 'Failed to process feedback',
                'code': 'PROCESSING_ERROR',
                'timestamp': datetime.utcnow().isoformat()
            }), 500
        
    except Exception as e:
        logger.error(f"Error submitting recommendation feedback: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': 'Failed to submit feedback',
            'code': 'ANALYSIS_ERROR',
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@prediction_analysis_bp.route('/adaptive-learning-status', methods=['GET'])
def get_adaptive_learning_status():
    """適応学習ステータス取得API
    
    ユーザーの学習効果と適応状況を取得
    
    Query Parameters:
        user_id (str): ユーザーID (必須)
        time_window_days (int): 分析期間（日数） (デフォルト: 30)
        
    Returns:
        JSON: 適応学習ステータス
    """
    try:
        # パラメータ取得
        user_id = request.args.get('user_id')
        time_window_days = int(request.args.get('time_window_days', 30))
        
        if not user_id:
            return jsonify({
                'status': 'error',
                'error': 'user_id is required',
                'code': 'VALIDATION_ERROR',
                'timestamp': datetime.utcnow().isoformat()
            }), 400
        
        if time_window_days < 1 or time_window_days > 365:
            return jsonify({
                'status': 'error',
                'error': 'time_window_days must be between 1 and 365',
                'code': 'VALIDATION_ERROR',
                'timestamp': datetime.utcnow().isoformat()
            }), 400
        
        # 適応学習システム取得
        adaptive_learning = _get_adaptive_learning_system()
        if not adaptive_learning:
            return jsonify({
                'status': 'error',
                'error': 'Adaptive learning system not available',
                'code': 'SERVICE_UNAVAILABLE',
                'timestamp': datetime.utcnow().isoformat()
            }), 500
        
        # 学習効果測定
        learning_metrics = adaptive_learning.measure_learning_effectiveness(user_id, time_window_days)
        
        # 行動変化適応状況取得
        logs = BehaviorLog.get_recent_logs(hours=time_window_days * 24, user_id=user_id)
        personalization_engine = _get_personalization_engine()
        
        adaptation_status = {}
        if personalization_engine:
            adaptation_status = personalization_engine.adapt_to_behavioral_changes(user_id, logs)
        
        result_data = {
            'user_id': user_id,
            'time_window_days': time_window_days,
            'learning_metrics': {
                'accuracy_score': learning_metrics.accuracy_score,
                'precision': learning_metrics.precision,
                'recall': learning_metrics.recall,
                'f1_score': learning_metrics.f1_score,
                'improvement_rate': learning_metrics.improvement_rate,
                'confidence_level': learning_metrics.confidence_level,
                'stability_score': learning_metrics.stability_score
            },
            'adaptation_status': adaptation_status,
            'performance_summary': _generate_learning_performance_summary(learning_metrics)
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
        logger.error(f"Error getting adaptive learning status: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': 'Failed to get adaptive learning status',
            'code': 'ANALYSIS_ERROR',
            'timestamp': datetime.utcnow().isoformat()
        }), 500


# ========== ヘルパー関数 ==========

def _get_pattern_recognizer() -> Optional[Any]:
    """パターン認識エンジンインスタンス取得（予測分析用）
    
    PatternRecognizerのインスタンスを作成し、設定を適用します。
    予測モデルのベースとなるパターン認識に使用されます。
    
    Returns:
        Optional[Any]: PatternRecognizerインスタンス、またはエラー時はNone
        
    Note:
        設定はFlaskのcurrent_app.configから取得されます。
        初期化に失敗した場合はログに記録し、Noneを返します。
    """
    try:
        from services.ai_ml.pattern_recognition import PatternRecognizer
        config = current_app.config.get('config_manager').get_all()
        return PatternRecognizer(config)
    except Exception as e:
        logger.error(f"Error creating PatternRecognizer: {e}")
    return None


def _get_personalization_engine() -> Optional[Any]:
    """個人化エンジンインスタンス取得
    
    PersonalizationEngineのインスタンスを作成し、設定を適用します。
    ユーザー固有の行動パターンに基づく個人化推奨に使用されます。
    
    Returns:
        Optional[Any]: PersonalizationEngineインスタンス、またはエラー時はNone
        
    Note:
        設定はFlaskのcurrent_app.configから取得されます。
        初期化に失敗した場合はログに記録し、Noneを返します。
    """
    try:
        from services.personalization.personalization_engine import PersonalizationEngine
        config = current_app.config.get('config_manager').get_all()
        return PersonalizationEngine(config)
    except Exception as e:
        logger.error(f"Error creating PersonalizationEngine: {e}")
    return None


def _get_user_profile_builder() -> Optional[Any]:
    """ユーザープロファイル構築器インスタンス取得
    
    UserProfileBuilderのインスタンスを作成し、設定を適用します。
    ユーザーの行動履歴からプロファイル構築に使用されます。
    
    Returns:
        Optional[Any]: UserProfileBuilderインスタンス、またはエラー時はNone
        
    Note:
        設定はFlaskのcurrent_app.configから取得されます。
        初期化に失敗した場合はログに記録し、Noneを返します。
    """
    try:
        from services.personalization.user_profile_builder import UserProfileBuilder
        config = current_app.config.get('config_manager').get_all()
        return UserProfileBuilder(config)
    except Exception as e:
        logger.error(f"Error creating UserProfileBuilder: {e}")
    return None


def _get_adaptive_learning_system() -> Optional[Any]:
    """適応学習システムインスタンス取得
    
    AdaptiveLearningSystemのインスタンスを作成し、設定を適用します。
    ユーザー行動に適応する学習システムに使用されます。
    
    Returns:
        Optional[Any]: AdaptiveLearningSystemインスタンス、またはエラー時はNone
        
    Note:
        設定はFlaskのcurrent_app.configから取得されます。
        初期化に失敗した場合はログに記録し、Noneを返します。
    """
    try:
        from services.personalization.adaptive_learning import AdaptiveLearningSystem
        config = current_app.config.get('config_manager').get_all()
        return AdaptiveLearningSystem(config)
    except Exception as e:
        logger.error(f"Error creating AdaptiveLearningSystem: {e}")
    return None


def _generate_prediction_summary(predictions: Dict, target_metrics: List[str]) -> Dict[str, Any]:
    """予測サマリー生成"""
    try:
        summary = {
            'target_metrics': target_metrics,
            'overall_confidence': 0.0,
            'key_predictions': []
        }
        
        if 'overall_confidence' in predictions:
            summary['overall_confidence'] = predictions['overall_confidence']
        
        if 'predictions' in predictions:
            for metric, pred_data in predictions['predictions'].items():
                summary['key_predictions'].append({
                    'metric': metric,
                    'predicted_value': pred_data.get('predicted_value', 0.0),
                    'confidence': pred_data.get('accuracy_score', 0.0)
                })
        
        return summary
        
    except Exception as e:
        logger.error(f"Error generating prediction summary: {e}")
        return {'error': '予測サマリー生成エラー'}


def _personalized_recommendation_to_dict(recommendation) -> Dict[str, Any]:
    """PersonalizedRecommendationを辞書に変換"""
    try:
        if hasattr(recommendation, '__dict__'):
            return {
                'recommendation_id': recommendation.recommendation_id,
                'type': recommendation.type,
                'priority': recommendation.priority,
                'message': recommendation.message,
                'personalization_score': recommendation.personalization_score,
                'context_factors': recommendation.context_factors,
                'expected_impact': recommendation.expected_impact,
                'timing': recommendation.timing,
                'action_required': recommendation.action_required
            }
        else:
            return recommendation
    except Exception as e:
        logger.error(f"Error converting recommendation to dict: {e}")
        return {'error': 'Conversion failed'}


def _generate_learning_performance_summary(learning_metrics) -> Dict[str, Any]:
    """学習パフォーマンスサマリー生成"""
    try:
        # 総合スコア計算
        overall_score = (
            learning_metrics.accuracy_score * 0.3 +
            learning_metrics.f1_score * 0.3 +
            learning_metrics.confidence_level * 0.2 +
            learning_metrics.stability_score * 0.2
        )
        
        # パフォーマンスレベル判定
        if overall_score >= 0.8:
            performance_level = 'excellent'
        elif overall_score >= 0.6:
            performance_level = 'good'
        elif overall_score >= 0.4:
            performance_level = 'fair'
        else:
            performance_level = 'needs_improvement'
        
        return {
            'overall_score': overall_score,
            'performance_level': performance_level,
            'key_strengths': _identify_performance_strengths(learning_metrics),
            'improvement_areas': _identify_improvement_areas(learning_metrics)
        }
        
    except Exception as e:
        logger.error(f"Error generating learning performance summary: {e}")
        return {'overall_score': 0.5, 'performance_level': 'unknown'}


def _identify_performance_strengths(learning_metrics) -> List[str]:
    """パフォーマンス強みの特定"""
    strengths = []
    
    if learning_metrics.accuracy_score >= 0.7:
        strengths.append('High prediction accuracy')
    if learning_metrics.stability_score >= 0.7:
        strengths.append('Stable learning performance')
    if learning_metrics.improvement_rate > 0.05:
        strengths.append('Consistent improvement trend')
    if learning_metrics.confidence_level >= 0.8:
        strengths.append('High confidence in recommendations')
    
    return strengths if strengths else ['Basic functionality working']


def _identify_improvement_areas(learning_metrics) -> List[str]:
    """改善エリアの特定"""
    areas = []
    
    if learning_metrics.get('accuracy_trend', 0) < 0.05:
        areas.append("予測精度の向上")
    
    if learning_metrics.get('adaptation_speed', 0.5) < 0.3:
        areas.append("学習適応速度の改善")
    
    if learning_metrics.get('user_satisfaction', 0.5) < 0.6:
        areas.append("ユーザー満足度の向上")
    
    return areas 
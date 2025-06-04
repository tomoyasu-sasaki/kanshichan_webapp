"""
Pattern Recognition Service

パターン認識アルゴリズム - Phase 4.1実装
行動パターンのクラスタリング、時系列パターン認識、予測モデル
"""

from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from collections import defaultdict, Counter
from dataclasses import dataclass
from enum import Enum
import logging
import json

from models.behavior_log import BehaviorLog
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PatternType(Enum):
    """パターンタイプ分類"""
    CYCLICAL = "cyclical"
    TRENDING = "trending"
    RANDOM = "random"
    SEASONAL = "seasonal"
    BREAK_POINT = "break_point"


class ClusterType(Enum):
    """クラスタータイプ"""
    HIGH_FOCUS = "high_focus"
    MEDIUM_FOCUS = "medium_focus"
    LOW_FOCUS = "low_focus"
    DISTRACTED = "distracted"
    BREAK_TIME = "break_time"


@dataclass
class BehaviorCluster:
    """行動クラスターデータクラス"""
    cluster_id: int
    cluster_type: ClusterType
    center: List[float]
    size: int
    variance: float
    typical_behaviors: List[str]
    time_periods: List[Tuple[datetime, datetime]]


@dataclass
class PatternMatch:
    """パターンマッチング結果"""
    pattern_id: str
    pattern_type: PatternType
    confidence: float
    start_time: datetime
    end_time: datetime
    features: Dict[str, float]
    description: str


@dataclass
class PredictionResult:
    """予測結果データクラス"""
    target_metric: str
    predicted_value: float
    confidence_interval: Tuple[float, float]
    prediction_horizon: int  # 分
    accuracy_score: float
    factors: List[str]


class PatternRecognizer:
    """パターン認識エンジン
    
    機械学習アルゴリズムを使用した行動パターンの自動認識と分類
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初期化
        
        Args:
            config: 設定辞書
        """
        self.config = config.get('pattern_recognition', {})
        
        # クラスタリングパラメータ
        self.clustering_params = {
            'n_clusters': self.config.get('n_clusters', 5),
            'max_iter': self.config.get('max_iter', 100),
            'tolerance': self.config.get('tolerance', 1e-4)
        }
        
        # パターンマッチングパラメータ
        self.pattern_params = {
            'min_pattern_length': self.config.get('min_pattern_length', 10),
            'confidence_threshold': self.config.get('confidence_threshold', 0.7),
            'similarity_threshold': self.config.get('similarity_threshold', 0.8)
        }
        
        # 予測パラメータ
        self.prediction_params = {
            'window_size': self.config.get('window_size', 30),
            'horizon': self.config.get('prediction_horizon', 60),  # 分
            'validation_split': self.config.get('validation_split', 0.2)
        }
        
        # 学習済みパターン
        self.learned_patterns = {}
        self.cluster_centers = {}
        
        logger.info("PatternRecognizer initialized with ML capabilities")
    
    def perform_clustering_analysis(self, logs: List[BehaviorLog]) -> Dict[str, Any]:
        """行動パターンのクラスタリング分析
        
        Args:
            logs: 行動ログリスト
            
        Returns:
            dict: クラスタリング分析結果
        """
        try:
            if len(logs) < self.clustering_params['n_clusters']:
                return {'error': 'Insufficient data for clustering analysis'}
            
            # 特徴量抽出
            features = self._extract_clustering_features(logs)
            
            # K-means クラスタリング実行
            clusters = self._perform_kmeans_clustering(features)
            
            # クラスター特性分析
            cluster_analysis = self._analyze_cluster_characteristics(logs, clusters, features)
            
            # クラスター分布分析
            distribution_analysis = self._analyze_cluster_distribution(clusters, logs)
            
            # 異常クラスター検出
            anomaly_clusters = self._detect_anomaly_clusters(cluster_analysis)
            
            return {
                'n_clusters': len(cluster_analysis),
                'cluster_analysis': [self._cluster_to_dict(c) for c in cluster_analysis],
                'distribution': distribution_analysis,
                'anomalies': anomaly_clusters,
                'silhouette_score': self._calculate_silhouette_score(features, clusters),
                'cluster_quality': self._assess_cluster_quality(cluster_analysis)
            }
            
        except Exception as e:
            logger.error(f"Error in clustering analysis: {e}", exc_info=True)
            return {'error': str(e)}
    
    def recognize_temporal_patterns(self, logs: List[BehaviorLog]) -> Dict[str, Any]:
        """時系列パターン認識
        
        Args:
            logs: 行動ログリスト
            
        Returns:
            dict: 認識されたパターン情報
        """
        try:
            if len(logs) < self.pattern_params['min_pattern_length']:
                return {'error': 'Insufficient data for pattern recognition'}
            
            # 時系列データ準備
            time_series = self._prepare_time_series(logs)
            
            # 周期性パターン検出
            cyclical_patterns = self._detect_cyclical_patterns(time_series)
            
            # トレンドパターン検出
            trend_patterns = self._detect_trend_patterns(time_series)
            
            # 季節性パターン検出
            seasonal_patterns = self._detect_seasonal_patterns(time_series)
            
            # 変化点検出
            change_points = self._detect_change_points(time_series)
            
            # パターンマッチング
            pattern_matches = self._match_known_patterns(time_series)
            
            # パターン強度評価
            pattern_strength = self._evaluate_pattern_strength(
                cyclical_patterns, trend_patterns, seasonal_patterns
            )
            
            return {
                'cyclical_patterns': cyclical_patterns,
                'trend_patterns': trend_patterns,
                'seasonal_patterns': seasonal_patterns,
                'change_points': change_points,
                'pattern_matches': [self._pattern_match_to_dict(p) for p in pattern_matches],
                'pattern_strength': pattern_strength,
                'summary': self._generate_pattern_summary(
                    cyclical_patterns, trend_patterns, seasonal_patterns, change_points
                )
            }
            
        except Exception as e:
            logger.error(f"Error in temporal pattern recognition: {e}", exc_info=True)
            return {'error': str(e)}
    
    def generate_predictions(self, logs: List[BehaviorLog], target_metrics: List[str]) -> Dict[str, Any]:
        """予測モデル生成と実行
        
        Args:
            logs: 行動ログリスト
            target_metrics: 予測対象指標リスト
            
        Returns:
            dict: 予測結果
        """
        try:
            if len(logs) < self.prediction_params['window_size']:
                return {'error': 'Insufficient data for prediction'}
            
            predictions = {}
            
            for metric in target_metrics:
                # メトリック別予測実行
                prediction_result = self._predict_metric(logs, metric)
                predictions[metric] = prediction_result
            
            # 統合予測評価
            overall_confidence = self._calculate_overall_prediction_confidence(predictions)
            
            # 予測精度評価
            accuracy_assessment = self._assess_prediction_accuracy(predictions)
            
            return {
                'predictions': {k: self._prediction_to_dict(v) for k, v in predictions.items()},
                'overall_confidence': overall_confidence,
                'accuracy_assessment': accuracy_assessment,
                'prediction_horizon_minutes': self.prediction_params['horizon'],
                'model_performance': self._evaluate_model_performance(predictions)
            }
            
        except Exception as e:
            logger.error(f"Error in prediction generation: {e}", exc_info=True)
            return {'error': str(e)}
    
    def learn_user_patterns(self, logs: List[BehaviorLog], user_id: Optional[str] = None) -> Dict[str, Any]:
        """ユーザー固有パターンの学習
        
        Args:
            logs: 行動ログリスト
            user_id: ユーザーID（オプション）
            
        Returns:
            dict: 学習結果
        """
        try:
            # ユーザー固有の特徴量抽出
            user_features = self._extract_user_specific_features(logs, user_id)
            
            # 個人パターンの識別
            personal_patterns = self._identify_personal_patterns(user_features)
            
            # 習慣パターンの検出
            habit_patterns = self._detect_habit_patterns(logs)
            
            # 異常行動パターンの学習
            anomaly_patterns = self._learn_anomaly_patterns(logs)
            
            # パターン辞書の更新
            pattern_dictionary = self._update_pattern_dictionary(
                personal_patterns, habit_patterns, anomaly_patterns, user_id
            )
            
            # 学習効果の評価
            learning_effectiveness = self._evaluate_learning_effectiveness(pattern_dictionary)
            
            return {
                'user_id': user_id,
                'personal_patterns': personal_patterns,
                'habit_patterns': habit_patterns,
                'anomaly_patterns': anomaly_patterns,
                'pattern_dictionary_size': len(pattern_dictionary),
                'learning_effectiveness': learning_effectiveness,
                'recommendations': self._generate_learning_recommendations(learning_effectiveness)
            }
            
        except Exception as e:
            logger.error(f"Error in user pattern learning: {e}", exc_info=True)
            return {'error': str(e)}
    
    # ========== Private Methods ==========
    
    def _extract_clustering_features(self, logs: List[BehaviorLog]) -> np.ndarray:
        """クラスタリング用特徴量抽出"""
        try:
            features = []
            
            for log in logs:
                feature_vector = [
                    log.focus_score or 0.0,
                    log.posture_score or 0.0,
                    log.screen_time or 0.0,
                    1.0 if log.is_present else 0.0,
                    1.0 if log.smartphone_detected else 0.0,
                    log.timestamp.hour / 24.0,  # 時間正規化
                    log.timestamp.weekday() / 7.0,  # 曜日正規化
                ]
                features.append(feature_vector)
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error extracting clustering features: {e}")
            return np.array([])
    
    def _perform_kmeans_clustering(self, features: np.ndarray) -> np.ndarray:
        """K-meansクラスタリング実行"""
        try:
            # 簡易K-meansアルゴリズム実装
            n_clusters = min(self.clustering_params['n_clusters'], len(features))
            n_features = features.shape[1]
            
            # クラスターセンター初期化
            centers = np.random.rand(n_clusters, n_features)
            
            # 正規化
            features_normalized = (features - np.mean(features, axis=0)) / np.std(features, axis=0)
            
            for iteration in range(self.clustering_params['max_iter']):
                # 距離計算とクラスター割り当て
                distances = np.sqrt(((features_normalized - centers[:, np.newaxis])**2).sum(axis=2))
                cluster_assignments = np.argmin(distances, axis=0)
                
                # センター更新
                new_centers = np.array([
                    features_normalized[cluster_assignments == k].mean(axis=0) 
                    if np.sum(cluster_assignments == k) > 0 
                    else centers[k]
                    for k in range(n_clusters)
                ])
                
                # 収束判定
                if np.linalg.norm(new_centers - centers) < self.clustering_params['tolerance']:
                    break
                
                centers = new_centers
            
            self.cluster_centers = centers
            return cluster_assignments
            
        except Exception as e:
            logger.error(f"Error in K-means clustering: {e}")
            return np.array([])
    
    def _analyze_cluster_characteristics(self, logs: List[BehaviorLog], 
                                       clusters: np.ndarray, features: np.ndarray) -> List[BehaviorCluster]:
        """クラスター特性分析"""
        try:
            cluster_results = []
            unique_clusters = np.unique(clusters)
            
            for cluster_id in unique_clusters:
                cluster_mask = clusters == cluster_id
                cluster_logs = [logs[i] for i in range(len(logs)) if cluster_mask[i]]
                cluster_features = features[cluster_mask]
                
                if len(cluster_features) == 0:
                    continue
                
                # クラスター中心計算
                center = np.mean(cluster_features, axis=0).tolist()
                
                # 分散計算
                variance = float(np.var(cluster_features))
                
                # クラスタータイプ判定
                cluster_type = self._determine_cluster_type(center, cluster_logs)
                
                # 典型的な行動パターン抽出
                typical_behaviors = self._extract_typical_behaviors(cluster_logs)
                
                # 時間帯分析
                time_periods = self._extract_time_periods(cluster_logs)
                
                cluster_results.append(BehaviorCluster(
                    cluster_id=int(cluster_id),
                    cluster_type=cluster_type,
                    center=center,
                    size=len(cluster_logs),
                    variance=variance,
                    typical_behaviors=typical_behaviors,
                    time_periods=time_periods
                ))
            
            return cluster_results
            
        except Exception as e:
            logger.error(f"Error analyzing cluster characteristics: {e}")
            return []
    
    def _determine_cluster_type(self, center: List[float], logs: List[BehaviorLog]) -> ClusterType:
        """クラスタータイプ判定"""
        try:
            focus_score = center[0] if len(center) > 0 else 0.5
            
            if focus_score >= 0.8:
                return ClusterType.HIGH_FOCUS
            elif focus_score >= 0.6:
                return ClusterType.MEDIUM_FOCUS
            elif focus_score >= 0.3:
                return ClusterType.LOW_FOCUS
            else:
                # スマホ使用率で細分類
                smartphone_rate = sum(1 for log in logs if log.smartphone_detected) / len(logs)
                if smartphone_rate > 0.3:
                    return ClusterType.DISTRACTED
                else:
                    return ClusterType.BREAK_TIME
                    
        except Exception:
            return ClusterType.MEDIUM_FOCUS
    
    def _prepare_time_series(self, logs: List[BehaviorLog]) -> pd.DataFrame:
        """時系列データ準備"""
        try:
            data = []
            for log in logs:
                data.append({
                    'timestamp': log.timestamp,
                    'focus_score': log.focus_score or 0.0,
                    'posture_score': log.posture_score or 0.0,
                    'activity_level': 1.0 if log.is_present else 0.0,
                    'distraction_level': 1.0 if log.smartphone_detected else 0.0
                })
            
            df = pd.DataFrame(data)
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            
            # 欠損値補間
            df = df.interpolate(method='time')
            
            return df
            
        except Exception as e:
            logger.error(f"Error preparing time series: {e}")
            return pd.DataFrame()
    
    def _detect_cyclical_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """周期性パターン検出"""
        try:
            patterns = []
            
            for column in df.columns:
                values = df[column].values
                
                if len(values) < 20:
                    continue
                
                # 自己相関による周期検出
                autocorr = self._calculate_autocorrelation(values)
                
                # ピーク検出
                peaks = self._find_peaks(autocorr)
                
                for peak_idx in peaks:
                    if peak_idx > 0 and autocorr[peak_idx] > 0.3:  # 閾値
                        patterns.append({
                            'metric': column,
                            'period': peak_idx,
                            'strength': float(autocorr[peak_idx]),
                            'type': 'cyclical',
                            'confidence': min(float(autocorr[peak_idx]) * 1.2, 1.0)
                        })
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting cyclical patterns: {e}")
            return []
    
    def _calculate_autocorrelation(self, values: np.ndarray, max_lag: Optional[int] = None) -> np.ndarray:
        """自己相関計算"""
        try:
            if max_lag is None:
                max_lag = min(len(values) // 4, 50)
            
            autocorr = np.correlate(values, values, mode='full')
            mid = len(autocorr) // 2
            autocorr = autocorr[mid:mid+max_lag+1]
            
            # 正規化
            autocorr = autocorr / autocorr[0] if autocorr[0] != 0 else autocorr
            
            return autocorr
            
        except Exception:
            return np.array([])
    
    def _find_peaks(self, values: np.ndarray, min_distance: int = 5) -> List[int]:
        """ピーク検出"""
        try:
            peaks = []
            
            for i in range(1, len(values) - 1):
                if (values[i] > values[i-1] and values[i] > values[i+1] and 
                    all(i - p > min_distance for p in peaks)):
                    peaks.append(i)
            
            return peaks
            
        except Exception:
            return []
    
    # ========== Utility Methods ==========
    
    def _cluster_to_dict(self, cluster: BehaviorCluster) -> Dict[str, Any]:
        """BehaviorClusterを辞書に変換"""
        return {
            'cluster_id': cluster.cluster_id,
            'cluster_type': cluster.cluster_type.value,
            'center': cluster.center,
            'size': cluster.size,
            'variance': cluster.variance,
            'typical_behaviors': cluster.typical_behaviors,
            'time_periods': [(tp[0].isoformat(), tp[1].isoformat()) for tp in cluster.time_periods]
        }
    
    def _pattern_match_to_dict(self, match: PatternMatch) -> Dict[str, Any]:
        """PatternMatchを辞書に変換"""
        return {
            'pattern_id': match.pattern_id,
            'pattern_type': match.pattern_type.value,
            'confidence': match.confidence,
            'start_time': match.start_time.isoformat(),
            'end_time': match.end_time.isoformat(),
            'features': match.features,
            'description': match.description
        }
    
    def _prediction_to_dict(self, prediction: PredictionResult) -> Dict[str, Any]:
        """PredictionResultを辞書に変換"""
        return {
            'target_metric': prediction.target_metric,
            'predicted_value': prediction.predicted_value,
            'confidence_interval': prediction.confidence_interval,
            'prediction_horizon': prediction.prediction_horizon,
            'accuracy_score': prediction.accuracy_score,
            'factors': prediction.factors
        }
    
    # 以下のメソッドは段階的実装が必要
    def _analyze_cluster_distribution(self, clusters, logs):
        """クラスター分布分析 - 実装予定"""
        return {}
    
    def _detect_anomaly_clusters(self, cluster_analysis):
        """異常クラスター検出 - 実装予定"""
        return []
    
    def _calculate_silhouette_score(self, features, clusters):
        """シルエットスコア計算 - 実装予定"""
        return 0.5
    
    def _assess_cluster_quality(self, cluster_analysis):
        """クラスター品質評価 - 実装予定"""
        return {"quality_score": 0.7}
    
    def _detect_trend_patterns(self, df):
        """トレンドパターン検出 - 実装予定"""
        return []
    
    def _detect_seasonal_patterns(self, df):
        """季節性パターン検出 - 実装予定"""
        return []
    
    def _detect_change_points(self, df):
        """変化点検出 - 実装予定"""
        return []
    
    def _match_known_patterns(self, time_series):
        """既知パターンマッチング - 実装予定"""
        return []
    
    def _evaluate_pattern_strength(self, cyclical, trend, seasonal):
        """パターン強度評価 - 実装予定"""
        return {"overall_strength": 0.5}
    
    def _generate_pattern_summary(self, cyclical, trend, seasonal, change_points):
        """パターンサマリー生成 - 実装予定"""
        return "パターン分析完了"
    
    def _predict_metric(self, logs, metric):
        """メトリック予測 - 実装予定"""
        return PredictionResult(
            target_metric=metric,
            predicted_value=0.5,
            confidence_interval=(0.4, 0.6),
            prediction_horizon=self.prediction_params['horizon'],
            accuracy_score=0.7,
            factors=["時間帯", "曜日"]
        )
    
    def _calculate_overall_prediction_confidence(self, predictions):
        """全体予測信頼度計算 - 実装予定"""
        return 0.7
    
    def _assess_prediction_accuracy(self, predictions):
        """予測精度評価 - 実装予定"""
        return {"mean_accuracy": 0.7}
    
    def _evaluate_model_performance(self, predictions):
        """モデル性能評価 - 実装予定"""
        return {"performance_score": 0.7}
    
    def _extract_user_specific_features(self, logs, user_id):
        """ユーザー固有特徴量抽出 - 実装予定"""
        return {}
    
    def _identify_personal_patterns(self, user_features):
        """個人パターン識別 - 実装予定"""
        return []
    
    def _detect_habit_patterns(self, logs):
        """習慣パターン検出 - 実装予定"""
        return []
    
    def _learn_anomaly_patterns(self, logs):
        """異常パターン学習 - 実装予定"""
        return []
    
    def _update_pattern_dictionary(self, personal, habit, anomaly, user_id):
        """パターン辞書更新 - 実装予定"""
        return {}
    
    def _evaluate_learning_effectiveness(self, pattern_dictionary):
        """学習効果評価 - 実装予定"""
        return {"effectiveness_score": 0.7}
    
    def _generate_learning_recommendations(self, effectiveness):
        """学習推奨事項生成 - 実装予定"""
        return ["より多くのデータが必要です"]
    
    def _extract_typical_behaviors(self, logs):
        """典型的行動抽出 - 実装予定"""
        return ["集中状態", "休憩状態"]
    
    def _extract_time_periods(self, logs):
        """時間帯抽出 - 実装予定"""
        if not logs:
            return []
        return [(logs[0].timestamp, logs[-1].timestamp)] 
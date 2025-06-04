"""
Quality Evaluator - 音声品質評価

音声サンプルの品質評価、推奨事項生成、スコア計算を管理
"""

import torch
import torchaudio
from typing import Dict, Any, List
from datetime import datetime
from utils.logger import setup_logger
from utils.exceptions import AudioError, wrap_exception

logger = setup_logger(__name__)


class QualityEvaluator:
    """音声品質評価クラス
    
    音声サンプルの品質評価と改善推奨事項の生成
    """
    
    def __init__(self):
        """品質評価器初期化"""
        logger.info("QualityEvaluator initialized")
    
    def evaluate_voice_sample_quality(self, audio_path: str) -> Dict[str, Any]:
        """音声サンプル品質評価
        
        Args:
            audio_path: 音声ファイルパス
            
        Returns:
            Dict[str, Any]: 品質評価結果
        """
        try:
            wav, sampling_rate = torchaudio.load(audio_path)
            
            # 基本統計
            duration = wav.shape[-1] / sampling_rate
            rms = torch.sqrt(torch.mean(wav ** 2)).item()
            
            # 品質スコア計算
            quality_score = self._calculate_quality_score(wav, sampling_rate, duration)
            
            # 推奨事項生成
            recommendations = self._generate_quality_recommendations(wav, sampling_rate, duration, rms)
            
            evaluation = {
                'overall_score': quality_score,
                'duration_seconds': duration,
                'sampling_rate': sampling_rate,
                'channels': wav.shape[0] if wav.dim() > 1 else 1,
                'rms_level': rms,
                'suitable_for_cloning': quality_score >= 0.7,
                'recommendations': recommendations,
                'evaluation_timestamp': datetime.now().isoformat(),
                'detailed_scores': self._get_detailed_scores(wav, sampling_rate, duration, rms)
            }
            
            logger.info(f"Voice sample evaluation completed: score={quality_score:.2f}")
            return evaluation
            
        except Exception as e:
            error = wrap_exception(
                e, AudioError,
                f"Failed to evaluate voice sample quality: {audio_path}",
                details={'audio_path': audio_path}
            )
            logger.error(f"Quality evaluation error: {error.to_dict()}")
            raise AudioError(f"Quality evaluation failed: {str(e)}")
    
    def _calculate_quality_score(self, wav: torch.Tensor, sampling_rate: int, duration: float) -> float:
        """品質スコア計算
        
        Args:
            wav: 音声波形テンソル
            sampling_rate: サンプリングレート
            duration: 音声長さ（秒）
            
        Returns:
            float: 品質スコア (0.0-1.0)
        """
        try:
            score = 0.0
            
            # 1. 長さスコア (25%)
            length_score = self._calculate_length_score(duration)
            score += length_score * 0.25
            
            # 2. サンプリングレートスコア (20%)
            sr_score = self._calculate_sampling_rate_score(sampling_rate)
            score += sr_score * 0.20
            
            # 3. 音声レベルスコア (25%)
            level_score = self._calculate_level_score(wav)
            score += level_score * 0.25
            
            # 4. 無音割合スコア (15%)
            silence_score = self._calculate_silence_score(wav)
            score += silence_score * 0.15
            
            # 5. ダイナミックレンジスコア (15%)
            dynamic_score = self._calculate_dynamic_range_score(wav)
            score += dynamic_score * 0.15
            
            return min(1.0, max(0.0, score))
            
        except Exception as e:
            logger.warning(f"Quality score calculation failed: {e}")
            return 0.5  # デフォルトスコア
    
    def _calculate_length_score(self, duration: float) -> float:
        """長さスコア計算"""
        if 5 <= duration <= 30:
            return 1.0
        elif 3 <= duration < 5 or 30 < duration <= 60:
            return 0.7
        else:
            return 0.3
    
    def _calculate_sampling_rate_score(self, sampling_rate: int) -> float:
        """サンプリングレートスコア計算"""
        if sampling_rate >= 44100:
            return 1.0
        elif sampling_rate >= 22050:
            return 0.8
        else:
            return 0.5
    
    def _calculate_level_score(self, wav: torch.Tensor) -> float:
        """音声レベルスコア計算"""
        try:
            rms = torch.sqrt(torch.mean(wav ** 2)).item()
            if 0.05 <= rms <= 0.3:
                return 1.0
            elif 0.01 <= rms < 0.05 or 0.3 < rms <= 0.5:
                return 0.7
            else:
                return 0.3
        except Exception as e:
            logger.warning(f"Level score calculation failed: {e}")
            return 0.5
    
    def _calculate_silence_score(self, wav: torch.Tensor) -> float:
        """無音割合スコア計算"""
        try:
            silence_ratio = self._calculate_silence_ratio(wav)
            if silence_ratio < 0.2:
                return 1.0
            elif silence_ratio < 0.4:
                return 0.7
            else:
                return 0.3
        except Exception as e:
            logger.warning(f"Silence score calculation failed: {e}")
            return 0.5
    
    def _calculate_dynamic_range_score(self, wav: torch.Tensor) -> float:
        """ダイナミックレンジスコア計算"""
        try:
            dynamic_range = self._calculate_dynamic_range(wav)
            if dynamic_range > 0.3:
                return 1.0
            elif dynamic_range > 0.1:
                return 0.7
            else:
                return 0.3
        except Exception as e:
            logger.warning(f"Dynamic range score calculation failed: {e}")
            return 0.5
    
    def _calculate_silence_ratio(self, wav: torch.Tensor) -> float:
        """無音割合の計算
        
        Args:
            wav: 音声波形テンソル
            
        Returns:
            float: 無音割合 (0.0-1.0)
        """
        try:
            threshold = 0.01
            audio_magnitude = torch.abs(wav)
            silent_samples = (audio_magnitude < threshold).float().mean().item()
            return silent_samples
        except Exception as e:
            logger.warning(f"Silence ratio calculation failed: {e}")
            return 0.5
    
    def _calculate_dynamic_range(self, wav: torch.Tensor) -> float:
        """ダイナミックレンジの計算
        
        Args:
            wav: 音声波形テンソル
            
        Returns:
            float: ダイナミックレンジ
        """
        try:
            audio_magnitude = torch.abs(wav)
            max_amplitude = torch.max(audio_magnitude).item()
            percentile_10 = torch.quantile(audio_magnitude, 0.1).item()
            dynamic_range = max_amplitude - percentile_10
            return dynamic_range
        except Exception as e:
            logger.warning(f"Dynamic range calculation failed: {e}")
            return 0.3
    
    def _get_detailed_scores(self, wav: torch.Tensor, sampling_rate: int, 
                            duration: float, rms: float) -> Dict[str, Any]:
        """詳細スコアの取得
        
        Args:
            wav: 音声波形テンソル
            sampling_rate: サンプリングレート
            duration: 音声長さ
            rms: RMSレベル
            
        Returns:
            Dict[str, Any]: 詳細スコア辞書
        """
        try:
            return {
                'length_score': self._calculate_length_score(duration),
                'sampling_rate_score': self._calculate_sampling_rate_score(sampling_rate),
                'level_score': self._calculate_level_score(wav),
                'silence_score': self._calculate_silence_score(wav),
                'dynamic_range_score': self._calculate_dynamic_range_score(wav),
                'silence_ratio': self._calculate_silence_ratio(wav),
                'dynamic_range': self._calculate_dynamic_range(wav),
                'peak_amplitude': torch.max(torch.abs(wav)).item(),
                'zero_crossing_rate': self._calculate_zero_crossing_rate(wav)
            }
        except Exception as e:
            logger.warning(f"Detailed scores calculation failed: {e}")
            return {}
    
    def _calculate_zero_crossing_rate(self, wav: torch.Tensor) -> float:
        """ゼロクロス率の計算
        
        Args:
            wav: 音声波形テンソル
            
        Returns:
            float: ゼロクロス率
        """
        try:
            # ゼロクロスの検出
            if wav.dim() > 1:
                wav = torch.mean(wav, dim=0)
            
            zero_crossings = torch.where(torch.diff(torch.sign(wav)) != 0)[0]
            zcr = len(zero_crossings) / len(wav)
            return zcr
        except Exception as e:
            logger.warning(f"Zero crossing rate calculation failed: {e}")
            return 0.0
    
    def _generate_quality_recommendations(self, wav: torch.Tensor, sampling_rate: int, 
                                        duration: float, rms: float) -> List[str]:
        """品質改善推奨事項の生成
        
        Args:
            wav: 音声波形テンソル
            sampling_rate: サンプリングレート
            duration: 音声長さ
            rms: RMSレベル
            
        Returns:
            List[str]: 推奨事項リスト
        """
        recommendations = []
        
        try:
            # 長さの推奨事項
            if duration < 5:
                recommendations.append("音声が短すぎます。5-30秒の音声を推奨します。")
            elif duration > 30:
                recommendations.append("音声が長すぎます。5-30秒の範囲に短縮することを推奨します。")
            
            # サンプリングレートの推奨事項
            if sampling_rate < 22050:
                recommendations.append("サンプリングレートが低いです。44100Hz以上を推奨します。")
            
            # 音声レベルの推奨事項
            if rms < 0.01:
                recommendations.append("音声レベルが低すぎます。もう少し大きな声で録音してください。")
            elif rms > 0.5:
                recommendations.append("音声レベルが高すぎます。音割れしないレベルで録音してください。")
            
            # 無音割合の推奨事項
            silence_ratio = self._calculate_silence_ratio(wav)
            if silence_ratio > 0.4:
                recommendations.append("無音部分が多すぎます。連続して話すように録音してください。")
            
            # ダイナミックレンジの推奨事項
            dynamic_range = self._calculate_dynamic_range(wav)
            if dynamic_range < 0.1:
                recommendations.append("音声の変化が少ないです。感情を込めて自然に話してください。")
            
            # 総合的な推奨事項
            if not recommendations:
                recommendations.append("音声品質は良好です。音声クローンに適しています。")
            
            # 追加の技術的推奨事項
            peak_amplitude = torch.max(torch.abs(wav)).item()
            if peak_amplitude > 0.95:
                recommendations.append("音声にクリッピング（音割れ）が発生している可能性があります。")
            
            zcr = self._calculate_zero_crossing_rate(wav)
            if zcr < 0.01:
                recommendations.append("音声の高周波成分が不足している可能性があります。")
            elif zcr > 0.1:
                recommendations.append("音声にノイズが多く含まれている可能性があります。")
            
            return recommendations
            
        except Exception as e:
            logger.warning(f"Recommendations generation failed: {e}")
            return ["品質評価中にエラーが発生しました。"]
    
    def get_quality_thresholds(self) -> Dict[str, Any]:
        """品質評価の閾値設定を取得
        
        Returns:
            Dict[str, Any]: 閾値設定辞書
        """
        return {
            'duration': {
                'optimal_min': 5.0,
                'optimal_max': 30.0,
                'acceptable_min': 3.0,
                'acceptable_max': 60.0
            },
            'sampling_rate': {
                'optimal_min': 44100,
                'acceptable_min': 22050
            },
            'rms_level': {
                'optimal_min': 0.05,
                'optimal_max': 0.3,
                'acceptable_min': 0.01,
                'acceptable_max': 0.5
            },
            'silence_ratio': {
                'optimal_max': 0.2,
                'acceptable_max': 0.4
            },
            'dynamic_range': {
                'optimal_min': 0.3,
                'acceptable_min': 0.1
            },
            'overall_score': {
                'excellent': 0.9,
                'good': 0.7,
                'acceptable': 0.5,
                'poor': 0.3
            }
        }
    
    def get_score_interpretation(self, score: float) -> Dict[str, Any]:
        """スコアの解釈を取得
        
        Args:
            score: 品質スコア
            
        Returns:
            Dict[str, Any]: スコア解釈辞書
        """
        if score >= 0.9:
            return {
                'grade': 'excellent',
                'description': '優秀',
                'message': '音声品質は非常に良好です。音声クローンに最適です。',
                'color': 'green'
            }
        elif score >= 0.7:
            return {
                'grade': 'good',
                'description': '良好',
                'message': '音声品質は良好です。音声クローンに適しています。',
                'color': 'blue'
            }
        elif score >= 0.5:
            return {
                'grade': 'acceptable',
                'description': '許容可能',
                'message': '音声品質は許容範囲内です。改善の余地があります。',
                'color': 'yellow'
            }
        elif score >= 0.3:
            return {
                'grade': 'poor',
                'description': '不良',
                'message': '音声品質が低いです。録音し直しを推奨します。',
                'color': 'orange'
            }
        else:
            return {
                'grade': 'very_poor',
                'description': '非常に不良',
                'message': '音声品質が非常に低いです。録音環境を改善してください。',
                'color': 'red'
            } 
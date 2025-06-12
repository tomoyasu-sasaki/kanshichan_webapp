"""
Emotion Manager - 感情制御とベクトル管理

Zonos TTS用の感情ベクトル管理、カスタム感情作成、感情ミキシング機能
"""

from typing import Dict, Any, List, Union
from utils.logger import setup_logger

logger = setup_logger(__name__)


class EmotionManager:
    """感情制御管理クラス
    
    Zonos TTS用の感情ベクトル管理と制御機能
    """
    
    def __init__(self):
        """感情管理初期化"""
        self.emotion_presets = self._initialize_emotion_presets()
        logger.info("EmotionManager initialized with presets")
    
    def _initialize_emotion_presets(self) -> Dict[str, List[float]]:
        """感情プリセットの初期化
        
        Returns:
            Dict[str, List[float]]: 感情名とベクトルのマッピング
        """
        return {
            # 基本感情
            'neutral': [0.3077, 0.0256, 0.0256, 0.0256, 0.0256, 0.0256, 0.2564, 0.3077],
            'happy': [0.7000, 0.0100, 0.0100, 0.0100, 0.0200, 0.0100, 0.1500, 0.1000],
            'happiness': [0.7000, 0.0100, 0.0100, 0.0100, 0.0200, 0.0100, 0.1500, 0.1000],
            'joy': [0.8000, 0.0100, 0.0100, 0.0100, 0.0500, 0.0100, 0.1000, 0.0200],
            'cheerful': [0.6500, 0.0100, 0.0100, 0.0100, 0.0300, 0.0100, 0.2000, 0.1800],
            
            # 悲しみ系
            'sad': [0.0100, 0.7000, 0.0200, 0.0300, 0.0100, 0.0100, 0.1500, 0.0800],
            'sadness': [0.0100, 0.7000, 0.0200, 0.0300, 0.0100, 0.0100, 0.1500, 0.0800],
            'melancholy': [0.0200, 0.6000, 0.0200, 0.0200, 0.0100, 0.0100, 0.2200, 0.1000],
            
            # 怒り系
            'angry': [0.0100, 0.0200, 0.1000, 0.0200, 0.0100, 0.7000, 0.1500, 0.0500],
            'anger': [0.0100, 0.0200, 0.1000, 0.0200, 0.0100, 0.7000, 0.1500, 0.0500],
            'annoyed': [0.0200, 0.0300, 0.2000, 0.0100, 0.0100, 0.5500, 0.1500, 0.0300],
            
            # 驚き系
            'surprised': [0.0300, 0.0100, 0.0100, 0.0200, 0.7000, 0.0100, 0.1500, 0.0800],
            'surprise': [0.0300, 0.0100, 0.0100, 0.0200, 0.7000, 0.0100, 0.1500, 0.0800],
            'excited': [0.4000, 0.0100, 0.0100, 0.0100, 0.4500, 0.0100, 0.1000, 0.0200],
            
            # 冷静系
            'calm': [0.1000, 0.0100, 0.0100, 0.0100, 0.0100, 0.0100, 0.2000, 0.6500],
            'peaceful': [0.0800, 0.0100, 0.0100, 0.0100, 0.0100, 0.0100, 0.1500, 0.7200],
            
            # 恐怖系
            'fearful': [0.0100, 0.0300, 0.0200, 0.7000, 0.1000, 0.0200, 0.1000, 0.0200],
            'fear': [0.0100, 0.0300, 0.0200, 0.7000, 0.1000, 0.0200, 0.1000, 0.0200],
            'worried': [0.0100, 0.2000, 0.0200, 0.5000, 0.0300, 0.0100, 0.1500, 0.0800],
            
            # 自信系
            'confident': [0.3000, 0.0100, 0.0100, 0.0100, 0.0200, 0.0100, 0.1500, 0.5000],
            'assertive': [0.2000, 0.0100, 0.0100, 0.0100, 0.0200, 0.1500, 0.2000, 0.4100],
            
            # その他
            'disgust': [0.0100, 0.0200, 0.7000, 0.0200, 0.0100, 0.0300, 0.1500, 0.0600],
        }
    
    def get_emotion_vector(self, emotion: Union[str, List[float]]) -> List[float]:
        """感情ベクトルを取得
        
        Args:
            emotion: 感情名または直接的な感情ベクトル
            
        Returns:
            List[float]: 感情ベクトル [happiness, sadness, disgust, fear, surprise, anger, other, neutral]
        """
        try:
            # リスト形式の場合（カスタム感情ベクトル）
            if isinstance(emotion, list):
                if len(emotion) == 8:
                    logger.debug(f"Using custom emotion vector: {emotion}")
                    return emotion
                else:
                    logger.warning(f"Invalid emotion vector length: {len(emotion)}, using neutral")
                    return self.emotion_presets['neutral']
            
            # 文字列感情名の場合
            emotion_normalized = str(emotion).lower().strip()
            
            if emotion_normalized in self.emotion_presets:
                vector = self.emotion_presets[emotion_normalized]
                logger.debug(f"Emotion '{emotion}' -> vector: {vector}")
                return vector
            
            # 未知の感情名の場合
            logger.warning(f"Unknown emotion '{emotion}', using neutral")
            return self.emotion_presets['neutral']
            
        except Exception as e:
            logger.error(f"Error getting emotion vector for '{emotion}': {e}")
            return self.emotion_presets['neutral']
    
    def create_custom_emotion(self, 
                             happiness: float = 0.3077,
                             sadness: float = 0.0256,
                             disgust: float = 0.0256,
                             fear: float = 0.0256,
                             surprise: float = 0.0256,
                             anger: float = 0.0256,
                             other: float = 0.2564,
                             neutral: float = 0.3077) -> List[float]:
        """カスタム感情ベクトルを作成
        
        Args:
            happiness: 幸福度 (0.0-1.0)
            sadness: 悲しみ度 (0.0-1.0)
            disgust: 嫌悪度 (0.0-1.0)
            fear: 恐怖度 (0.0-1.0)
            surprise: 驚き度 (0.0-1.0)
            anger: 怒り度 (0.0-1.0)
            other: その他 (0.0-1.0)
            neutral: 中性度 (0.0-1.0)
            
        Returns:
            List[float]: 正規化された感情ベクトル
        """
        try:
            # 入力値のクランプ（0.0-1.0範囲）
            values = [
                max(0.0, min(1.0, happiness)),
                max(0.0, min(1.0, sadness)),
                max(0.0, min(1.0, disgust)),
                max(0.0, min(1.0, fear)),
                max(0.0, min(1.0, surprise)),
                max(0.0, min(1.0, anger)),
                max(0.0, min(1.0, other)),
                max(0.0, min(1.0, neutral))
            ]
            
            # 正規化（合計を1.0に）
            total = sum(values)
            if total > 0:
                normalized_values = [v / total for v in values]
            else:
                # すべて0の場合はneutralを使用
                normalized_values = self.emotion_presets['neutral']
            
            logger.info(f"Created custom emotion vector: {normalized_values}")
            return normalized_values
            
        except Exception as e:
            logger.error(f"Error creating custom emotion vector: {e}")
            return self.emotion_presets['neutral']
    
    def mix_emotions(self, primary_emotion: str, secondary_emotion: str, 
                    primary_weight: float = 0.7) -> List[float]:
        """感情をミキシング
        
        Args:
            primary_emotion: 主要感情名
            secondary_emotion: 副感情名
            primary_weight: 主要感情の重み (0.0-1.0)
            
        Returns:
            List[float]: ミキシングされた感情ベクトル
        """
        try:
            # 重みの正規化
            primary_weight = max(0.0, min(1.0, primary_weight))
            secondary_weight = 1.0 - primary_weight
            
            # 感情ベクトル取得
            primary_vector = self.get_emotion_vector(primary_emotion)
            secondary_vector = self.get_emotion_vector(secondary_emotion)
            
            # ミキシング計算
            mixed_vector = [
                primary_vector[i] * primary_weight + secondary_vector[i] * secondary_weight
                for i in range(len(primary_vector))
            ]
            
            logger.info(f"Mixed emotions: {primary_emotion}({primary_weight:.1f}) + {secondary_emotion}({secondary_weight:.1f}) = {mixed_vector}")
            return mixed_vector
            
        except Exception as e:
            logger.error(f"Error mixing emotions '{primary_emotion}' and '{secondary_emotion}': {e}")
            return self.emotion_presets['neutral']
    
    def prepare_emotion_parameters(self, emotion: Union[str, List[float]], 
                                 speed: float = 1.0, pitch: float = 1.0) -> Dict[str, Any]:
        """感情パラメータを準備・正規化
        
        Args:
            emotion: 感情設定（文字列 or 感情ベクトル）
            speed: 話速調整（現在未対応）
            pitch: 音程調整（現在未対応）
            
        Returns:
            Dict[str, Any]: 正規化された感情パラメータ
        """
        params = {}
        
        try:
            # 感情ベクトル取得
            emotion_vector = self.get_emotion_vector(emotion)
            params['emotion'] = emotion_vector
            
            # 速度・音程調整（将来のZonosアップデート用）
            if speed != 1.0:
                speed_clamped = max(0.5, min(2.0, speed))
                if speed != speed_clamped:
                    logger.warning(f"Speed clamped from {speed} to {speed_clamped}")
                logger.debug(f"Speed parameter: {speed_clamped} (currently not applied to Zonos)")
            
            if pitch != 1.0:
                pitch_clamped = max(0.5, min(2.0, pitch))
                if pitch != pitch_clamped:
                    logger.warning(f"Pitch clamped from {pitch} to {pitch_clamped}")
                logger.debug(f"Pitch parameter: {pitch_clamped} (currently not applied to Zonos)")
            
            logger.debug(f"Prepared emotion parameters: {params}")
            return params
            
        except Exception as e:
            logger.warning(f"Failed to prepare emotion parameters: {e}, using neutral defaults")
            return {'emotion': self.emotion_presets['neutral']}
    
    def get_available_emotions(self) -> List[str]:
        """利用可能な感情名のリストを取得
        
        Returns:
            List[str]: 利用可能な感情名のリスト
        """
        return sorted(self.emotion_presets.keys())
    
    def get_emotion_categories(self) -> Dict[str, List[str]]:
        """感情をカテゴリ別に分類して取得
        
        Returns:
            Dict[str, List[str]]: カテゴリ別感情リスト
        """
        categories = {
            'basic': ['neutral'],
            'positive': ['happy', 'happiness', 'joy', 'cheerful', 'excited'],
            'negative': ['sad', 'sadness', 'melancholy', 'angry', 'anger', 'annoyed'],
            'surprise': ['surprised', 'surprise'],
            'calm': ['calm', 'peaceful', 'confident'],
            'fear': ['fearful', 'fear', 'worried'],
            'other': ['assertive', 'disgust']
        }
        
        return categories
    
    def validate_emotion_vector(self, vector: List[float]) -> bool:
        """感情ベクトルの妥当性を検証
        
        Args:
            vector: 検証する感情ベクトル
            
        Returns:
            bool: 妥当性フラグ
        """
        try:
            # 長さチェック
            if len(vector) != 8:
                logger.warning(f"Invalid vector length: {len(vector)}, expected 8")
                return False
            
            # 範囲チェック
            for i, value in enumerate(vector):
                if not isinstance(value, (int, float)):
                    logger.warning(f"Invalid value type at index {i}: {type(value)}")
                    return False
                if value < 0.0 or value > 1.0:
                    logger.warning(f"Invalid value range at index {i}: {value}")
                    return False
            
            # 合計チェック（正規化済みベクトルの場合）
            total = sum(vector)
            if abs(total - 1.0) > 0.01:  # 小数点誤差を考慮
                logger.debug(f"Vector sum is {total}, not normalized")
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating emotion vector: {e}")
            return False
    
    def get_emotion_info(self) -> Dict[str, Any]:
        """感情管理システムの情報を取得
        
        Returns:
            Dict[str, Any]: 感情システム情報
        """
        return {
            'total_emotions': len(self.emotion_presets),
            'available_emotions': self.get_available_emotions(),
            'emotion_categories': self.get_emotion_categories(),
            'vector_dimension': 8,
            'vector_labels': [
                'happiness', 'sadness', 'disgust', 'fear', 
                'surprise', 'anger', 'other', 'neutral'
            ]
        } 
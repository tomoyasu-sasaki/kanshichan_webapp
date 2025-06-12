"""
Recommendation Schema Module

推奨事項に関するデータモデルと変換ユーティリティ
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json


@dataclass
class RecommendationSchema:
    """
    推奨事項の標準化スキーマ
    フロントエンドとバックエンド間で一貫したデータ構造を維持する
    """
    
    # 必須フィールド
    type: str  # 推奨タイプ (focus_improvement, distraction_management, など)
    message: str  # 推奨メッセージ本文
    priority: str  # 優先度 (high, medium, low)
    
    # オプションフィールド
    action: Optional[str] = None  # 推奨されるアクション (focus_training, device_management, など)
    emotion: Optional[str] = None  # 感情トーン (encouraging, alert, celebration など)
    source: Optional[str] = None  # 推奨の発生源 (behavior_analysis, llm_advice など)
    timestamp: Optional[str] = None  # 推奨生成時刻 (ISO8601形式)
    
    # 音声アドバイス関連フィールド
    audio_url: Optional[str] = None  # 音声ファイルのURL (あれば)
    voice_text: Optional[str] = None  # TTS用に最適化されたテキスト
    tts_requested: bool = False  # TTSリクエストフラグ
    
    # 将来の拡張用
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """初期化後の処理"""
        # timestampが未指定の場合は現在時刻を設定
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
            
        # metadataの初期化
        if self.metadata is None:
            self.metadata = {}
            
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    def to_json(self) -> str:
        """JSON文字列に変換"""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RecommendationSchema':
        """辞書からインスタンスを生成"""
        # 不要なキーを除外
        valid_keys = {field.name for field in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered_data)
    
    @classmethod
    def from_analyzer_format(cls, analyzer_rec: Dict[str, Any]) -> 'RecommendationSchema':
        """BehaviorAnalyzerフォーマットから変換"""
        data = {
            'type': analyzer_rec.get('type', 'unknown'),
            'message': analyzer_rec.get('message', ''),
            'priority': analyzer_rec.get('priority', 'medium'),
            'action': analyzer_rec.get('action'),
            'source': analyzer_rec.get('source', 'behavior_analysis'),
            'timestamp': analyzer_rec.get('timestamp', datetime.now(timezone.utc).isoformat())
        }
        return cls(**data)
    
    @classmethod
    def from_advice_generator_format(cls, advice_result: Dict[str, Any]) -> 'RecommendationSchema':
        """AdviceGeneratorフォーマットから変換"""
        data = {
            'type': 'contextual_advice',
            'message': advice_result.get('advice_text', ''),
            'priority': advice_result.get('priority', 'medium'),
            'emotion': advice_result.get('emotion', 'encouraging'),
            'source': 'llm_advice',
            'timestamp': advice_result.get('generation_timestamp', datetime.now(timezone.utc).isoformat())
        }
        return cls(**data)


def standardize_recommendations(recommendations: List[Dict[str, Any]]) -> List[RecommendationSchema]:
    """推奨事項リストを標準化"""
    standardized = []
    
    for rec in recommendations:
        if isinstance(rec, RecommendationSchema):
            standardized.append(rec)
        elif isinstance(rec, dict):
            source = rec.get('source', '')
            if source == 'llm_advice':
                standardized.append(RecommendationSchema.from_advice_generator_format(rec))
            else:
                standardized.append(RecommendationSchema.from_analyzer_format(rec))
    
    return standardized 
"""
Alert Channel Enums - アラート通知チャンネル列挙型

アラート通知の送信先チャネルを管理する列挙型
"""

from enum import Enum, auto


class AlertChannel(Enum):
    """
    アラート通知チャンネルの種類を定義する列挙型
    
    Attributes:
        SOUND: 音声アラート（デフォルト）
        EMAIL: Eメール通知
        DESKTOP: デスクトップ通知
        MOBILE: モバイル通知（将来拡張用）
    """
    SOUND = auto()  # 音声アラート（デフォルト）
    EMAIL = auto()  # Eメール通知
    DESKTOP = auto()  # デスクトップ通知
    MOBILE = auto()  # モバイル通知（将来拡張用） 
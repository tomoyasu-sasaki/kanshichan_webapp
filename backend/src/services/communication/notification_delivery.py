"""
Notification Delivery Service - 通知配信サービス

アラート通知の配信管理を行うサービス
複数の通知チャネルに対する配信ロジックを提供
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from utils.logger import setup_logger
from utils.config_manager import ConfigManager
from utils.exceptions import (
    AlertError, AlertDeliveryError, NetworkError,
    wrap_exception
)
from .enums import AlertChannel

logger = setup_logger(__name__)


class NotificationDeliveryService:
    """
    通知配信サービス
    
    複数チャネル（音声、メール等）への通知配信を管理
    """
    
    def __init__(self, config_manager: ConfigManager):
        """
        NotificationDeliveryServiceを初期化
        
        Args:
            config_manager: 設定管理オブジェクト
        """
        self.config_manager = config_manager
        self._email_config = self._load_email_config()
        logger.info("NotificationDeliveryService initialized")
        
    def _load_email_config(self) -> Dict[str, Any]:
        """
        メール配信の設定を読み込む
        
        Returns:
            メール設定を含む辞書
        """
        try:
            email_config = self.config_manager.get_email_config()
            return email_config or {
                "enabled": False,
                "smtp_server": "",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "from_address": "",
                "to_addresses": []
            }
        except Exception as e:
            logger.warning(f"Failed to load email config: {str(e)}")
            return {
                "enabled": False,
                "smtp_server": "",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "from_address": "",
                "to_addresses": []
            }
    
    def deliver_notification(
        self, 
        message: str, 
        channels: List[AlertChannel],
        subject: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Dict[AlertChannel, bool]:
        """
        指定されたチャンネルに通知を配信
        
        Args:
            message: 通知メッセージ
            channels: 配信先チャンネルのリスト
            subject: メール件名（Emailチャンネル用）
            additional_data: 追加データ（チャンネル固有の情報）
            
        Returns:
            チャンネルごとの配信結果を示す辞書
        """
        results = {}
        
        for channel in channels:
            try:
                if channel == AlertChannel.EMAIL:
                    success = self._send_email(
                        message, 
                        subject or f"KanshiChan通知 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        additional_data
                    )
                    results[channel] = success
                elif channel == AlertChannel.DESKTOP:
                    # デスクトップ通知の実装（将来対応）
                    logger.debug("Desktop notification not implemented yet")
                    results[channel] = False
                elif channel == AlertChannel.MOBILE:
                    # モバイル通知の実装（将来対応）
                    logger.debug("Mobile notification not implemented yet")
                    results[channel] = False
                    
            except Exception as e:
                delivery_error = wrap_exception(
                    e, AlertDeliveryError,
                    f"Failed to deliver notification via {channel.name}",
                    details={
                        'channel': channel.name,
                        'message': message[:100] if message else None
                    }
                )
                logger.error(f"Notification delivery error: {delivery_error.to_dict()}")
                results[channel] = False
                
        return results
    
    def _send_email(
        self, 
        message: str, 
        subject: str, 
        additional_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Eメールでの通知送信
        
        Args:
            message: メールの本文
            subject: メールの件名
            additional_data: 追加データ（HTMLコンテンツなど）
            
        Returns:
            送信成功時True、失敗時False
        """
        if not self._email_config.get("enabled", False):
            logger.info("Email notifications are disabled in configuration")
            return False
            
        try:
            # SMTPクライアント設定
            smtp_server = self._email_config.get("smtp_server")
            smtp_port = self._email_config.get("smtp_port", 587)
            username = self._email_config.get("username")
            password = self._email_config.get("password")
            from_address = self._email_config.get("from_address")
            to_addresses = self._email_config.get("to_addresses", [])
            
            if not (smtp_server and username and password and from_address and to_addresses):
                logger.warning("Incomplete email configuration, skipping email notification")
                return False
                
            # メール作成
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = from_address
            msg["To"] = ", ".join(to_addresses)
            
            # プレーンテキストとHTMLの両方を添付
            plain_text = message
            html_content = additional_data.get("html_content", f"<html><body><p>{message}</p></body></html>") if additional_data else f"<html><body><p>{message}</p></body></html>"
            
            msg.attach(MIMEText(plain_text, "plain"))
            msg.attach(MIMEText(html_content, "html"))
            
            # メール送信
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                server.sendmail(from_address, to_addresses, msg.as_string())
                
            logger.info(f"Email notification sent successfully to {len(to_addresses)} recipient(s)")
            return True
            
        except Exception as e:
            network_error = wrap_exception(
                e, NetworkError,
                "Failed to send email notification",
                details={
                    'smtp_server': self._email_config.get("smtp_server"),
                    'smtp_port': self._email_config.get("smtp_port")
                }
            )
            logger.error(f"Email sending error: {network_error.to_dict()}")
            return False 
import time
from typing import Optional
from utils.logger import setup_logger
from core.state import StateManager
from utils.config_manager import ConfigManager
from utils.exceptions import (
    ConfigError, ValidationError, StateError,
    wrap_exception
)

logger = setup_logger(__name__)


class ThresholdManager:
    """
    閾値管理専門クラス
    - absence_threshold の延長管理
    - 延長時間の表示制御
    - 設定の永続化
    """
    
    def __init__(self,
                 state_manager: StateManager,
                 config_manager: ConfigManager):
        """
        初期化
        
        Args:
            state_manager: 状態管理インスタンス
            config_manager: 設定管理インスタンス
        """
        self.state = state_manager
        self.config_manager = config_manager
        
        # 延長時間を管理する変数
        self.extension_display_time = 0
        self.extension_applied_at: Optional[float] = None
        
        logger.info("ThresholdManager initialized.")

    def extend_absence_threshold(self, extension_time: int) -> bool:
        """
        absence_thresholdを延長するメソッド
        
        Args:
            extension_time: 延長時間（秒）
            
        Returns:
            bool: 延長処理が成功したかどうか
        """
        try:
            # パラメータの型と値のチェック
            logger.info(f"入力された延長時間: {extension_time}, 型: {type(extension_time)}")
            
            # extension_timeがintであることを確認
            extension_time = int(extension_time)
            logger.info(f"型変換後の延長時間: {extension_time}")
            
            # 異常値のチェック
            if extension_time <= 0:
                validation_error = ValidationError(
                    f"無効な延長時間です: {extension_time} (正の値が必要)",
                    details={'extension_time': extension_time, 'expected': '> 0'}
                )
                logger.warning(f"Extension time validation error: {validation_error.to_dict()}")
                return False
                
            # 現在の閾値を取得してログに記録
            current_threshold = self.state.absence_threshold
            logger.info(f"現在の離席閾値: {current_threshold} (型: {type(current_threshold)})")
            
            # 新しい閾値を設定
            new_threshold = current_threshold + extension_time
            self.state.absence_threshold = new_threshold
            
            # 表示用の変数を設定
            self.extension_display_time = extension_time
            self.extension_applied_at = time.time()
            
            # 閾値が変更されたらアラート状態をリセット
            old_alert_status = self.state.alert_triggered_absence
            self.state.alert_triggered_absence = False
            
            logger.info(f"離席閾値を更新しました: {current_threshold} → {new_threshold}")
            logger.info(f"アラート状態: {old_alert_status} → {self.state.alert_triggered_absence}")
            logger.info(f"表示用延長時間: {self.extension_display_time}")
            
            # ConfigManagerにも保存して永続化する
            try:
                self.config_manager.set('conditions.absence.threshold_seconds', float(new_threshold))
                # 設定ファイルにも保存して永続化する
                save_result = self.config_manager.save()
                if save_result:
                    logger.info(f"設定ファイルの離席閾値を更新して永続化しました: {new_threshold}")
                else:
                    logger.error("設定ファイルの保存に失敗しました")
            except Exception as config_e:
                config_error = wrap_exception(
                    config_e, ConfigError,
                    "設定ファイルの更新中にエラーが発生",
                    details={
                        'new_threshold': new_threshold,
                        'config_manager_available': self.config_manager is not None
                    }
                )
                logger.error(f"Config file update error: {config_error.to_dict()}")
            
            return True
            
        except ValueError as ve:
            value_error = wrap_exception(
                ve, ValidationError,
                "延長時間の型変換でエラーが発生",
                details={'extension_time': extension_time, 'expected_type': 'int'}
            )
            logger.error(f"Extension time conversion error: {value_error.to_dict()}")
            return False
        except Exception as e:
            threshold_error = wrap_exception(
                e, StateError,
                "離席閾値の延長中にエラーが発生",
                details={
                    'extension_time': extension_time,
                    'current_threshold': getattr(self.state, 'absence_threshold', None)
                }
            )
            logger.error(f"Threshold extension error: {threshold_error.to_dict()}")
            return False

    def get_extension_display_info(self) -> dict:
        """
        延長時間の表示情報を取得
        
        Returns:
            dict: 延長時間の表示情報
        """
        current_time = time.time()
        display_duration = 5  # 5秒間表示
        
        if (self.extension_applied_at is not None and 
            current_time - self.extension_applied_at < display_duration):
            return {
                'should_display': True,
                'extension_time': self.extension_display_time,
                'remaining_display_time': display_duration - (current_time - self.extension_applied_at)
            }
        else:
            # 表示期間が終了したらリセット
            if self.extension_applied_at is not None:
                logger.info("延長時間の表示期間が終了")
                self.extension_display_time = 0
                self.extension_applied_at = None
            
            return {
                'should_display': False,
                'extension_time': 0,
                'remaining_display_time': 0
            }

    def reset_thresholds(self) -> bool:
        """
        閾値を初期値にリセット
        
        Returns:
            bool: リセット処理が成功したかどうか
        """
        try:
            # 設定ファイルから初期値を取得
            original_threshold = self.config_manager.get('conditions.absence.threshold_seconds', 1800.0)
            
            # StateManagerの閾値を更新
            self.state.absence_threshold = original_threshold
            
            # 延長表示情報をクリア
            self.extension_display_time = 0
            self.extension_applied_at = None
            
            # アラート状態もリセット
            self.state.alert_triggered_absence = False
            
            logger.info(f"閾値を初期値にリセットしました: {original_threshold}")
            return True
            
        except Exception as e:
            logger.error(f"閾値リセット中にエラーが発生: {e}", exc_info=True)
            return False

    def validate_threshold_values(self) -> dict:
        """
        現在の閾値設定の妥当性を検証
        
        Returns:
            dict: 検証結果
        """
        result = {
            'is_valid': True,
            'warnings': [],
            'errors': []
        }
        
        try:
            current_threshold = self.state.absence_threshold
            
            # 閾値の範囲チェック
            if current_threshold <= 0:
                result['is_valid'] = False
                result['errors'].append(f"閾値が無効です: {current_threshold} (正の値が必要)")
            elif current_threshold < 60:
                result['warnings'].append(f"閾値が短すぎる可能性があります: {current_threshold}秒")
            elif current_threshold > 7200:  # 2時間
                result['warnings'].append(f"閾値が長すぎる可能性があります: {current_threshold}秒")
            
            # 型チェック
            if not isinstance(current_threshold, (int, float)):
                result['is_valid'] = False
                result['errors'].append(f"閾値の型が無効です: {type(current_threshold)}")
            
        except Exception as e:
            result['is_valid'] = False
            result['errors'].append(f"閾値検証中にエラーが発生: {str(e)}")
        
        return result

    def get_status(self) -> dict:
        """
        ThresholdManagerの状態情報を取得
        
        Returns:
            dict: 状態情報
        """
        display_info = self.get_extension_display_info()
        validation_result = self.validate_threshold_values()
        
        return {
            'current_threshold': self.state.absence_threshold,
            'extension_display_time': self.extension_display_time,
            'extension_applied_at': self.extension_applied_at,
            'display_info': display_info,
            'validation': validation_result
        } 
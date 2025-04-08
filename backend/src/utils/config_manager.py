# backend/src/utils/config_manager.py

import os
from typing import Any, Dict, Optional
# utils.config から yaml_utils を使う想定（前回確認済み）
from .yaml_utils import load_yaml, save_yaml
from .logger import setup_logger
from copy import deepcopy

logger = setup_logger(__name__)

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
# 設定のデフォルト値を定義 (例)
DEFAULT_CONFIG = {
    'server': {'port': 5001},
    'display': {'show_opencv_window': True},
    'conditions': {
        'absence': {'threshold_seconds': 5},
        'smartphone_usage': {'threshold_seconds': 3}
    },
    'line': {
        'enabled': False,
        'token': 'YOUR_LINE_NOTIFY_TOKEN',
        'channel_secret': 'YOUR_CHANNEL_SECRET', # (現在は未使用かも)
        'user_id': 'YOUR_LINE_USER_ID' # (現在は未使用かも)
    },
    'llm': {
        'enabled': False,
        'model_name': 'TinyLlama/TinyLlama-1.1B-Chat-v1.0',
        'temperature': 0.7,
        'analysis_interval_seconds': 300
    }
    # 必要に応じて他のデフォルト設定を追加
}

class ConfigManager:
    """
    設定ファイル (config.yaml) の読み込み、アクセス、保存を管理するクラス。
    """
    def __init__(self, config_path: Optional[str] = None):
        """
        ConfigManager を初期化します。

        Args:
            config_path (Optional[str]): 設定ファイルのパス。None の場合はデフォルトパスを使用。
        """
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self._config: Dict[str, Any] = {}
        logger.info(f"ConfigManager initialized with path: {self.config_path}")

    def load(self) -> bool:
        """
        設定ファイルを読み込みます。ファイルが存在しない、または読み込みに失敗した場合は
        デフォルト設定を使用します。

        Returns:
            bool: 読み込みに成功した場合は True、失敗またはファイルが存在しない場合は False。
        """
        loaded_successfully = False
        try:
            if os.path.exists(self.config_path):
                loaded_config = load_yaml(self.config_path)
                if loaded_config:
                    self._config = self._merge_configs(DEFAULT_CONFIG, loaded_config)
                    logger.info(f"設定ファイルを読み込みました: {self.config_path}")
                    loaded_successfully = True
                else:
                    logger.warning(f"設定ファイルが空または無効です: {self.config_path}. デフォルト設定を使用します。")
                    self._config = deepcopy(DEFAULT_CONFIG)
            else:
                logger.warning(f"設定ファイルが見つかりません: {self.config_path}. デフォルト設定を使用します。")
                self._config = deepcopy(DEFAULT_CONFIG)
                # デフォルト設定でファイルを作成する？ (今回はしない)
                # self.save()
        except Exception as e:
            logger.error(f"設定ファイルの読み込み中にエラーが発生しました ({self.config_path}): {e}", exc_info=True)
            logger.warning("エラーのためデフォルト設定を使用します。")
            self._config = deepcopy(DEFAULT_CONFIG)

        # デバッグ用に読み込まれた設定を出力 (必要に応じて)
        # logger.debug(f"Loaded config data: {self._config}")
        return loaded_successfully

    def _merge_configs(self, default: Dict, loaded: Dict) -> Dict:
        """デフォルト設定と読み込んだ設定を再帰的にマージする"""
        merged = deepcopy(default)
        for key, value in loaded.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        return merged

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        指定されたキーパスで設定値を取得します。キーはドット区切りで指定します (例: 'line.token')。

        Args:
            key_path (str): ドット区切りのキーパス。
            default (Any, optional): キーが見つからない場合に返すデフォルト値。Defaults to None.

        Returns:
            Any: 設定値。見つからない場合は default 値。
        """
        if not self._config:
            logger.warning("設定が読み込まれていません。get() を呼び出す前に load() を実行してください。")
            # load を試みるか、エラーにするか、デフォルトを返すか
            # self.load() # load を試みる場合
            return default

        keys = key_path.split('.')
        value = self._config
        try:
            for key in keys:
                if isinstance(value, dict):
                    value = value[key]
                else:
                    # パスの途中で辞書でなくなった場合
                    logger.warning(f"設定キーパス '{key_path}' の途中で非辞書要素に到達しました。'{key}'")
                    return default
            return value
        except KeyError:
            logger.debug(f"設定キーが見つかりません: '{key_path}'. デフォルト値 '{default}' を返します。")
            return default
        except Exception as e:
            logger.error(f"設定値の取得中に予期せぬエラーが発生しました (キー: '{key_path}'): {e}", exc_info=True)
            return default

    def get_all(self) -> Dict[str, Any]:
        """
        現在の全ての設定データを返します。

        Returns:
            Dict[str, Any]: 設定データの辞書。
        """
        return deepcopy(self._config) # 外部で変更されないようにコピーを返す

    def get_landmark_settings(self) -> Dict[str, Any]:
        """
        ランドマーク表示の設定を取得します。
        以前は display_settings.py に定義されていた設定です。

        Returns:
            Dict[str, Any]: ランドマーク設定の辞書。
        """
        settings = self.get('landmark_settings', {})
        # ここでキーが存在しない場合などのデフォルト値を設定できます
        return settings
    
    def get_detection_objects(self) -> Dict[str, Any]:
        """
        検出対象物体の設定を取得します。
        以前は display_settings.py に定義されていた設定です。

        Returns:
            Dict[str, Any]: 検出対象の設定辞書。
        """
        objects = self.get('detection_objects', {})
        # ここでキーが存在しない場合などのデフォルト値を設定できます
        return objects
    
    def get_message_sound_mapping(self) -> Dict[str, Any]:
        """
        メッセージと音声のマッピング設定を取得します。
        以前は message_settings.py に定義されていた設定です。

        Returns:
            Dict[str, Any]: メッセージと音声のマッピング辞書。
        """
        mapping = self.get('message_sound_mapping', {})
        # ここでキーが存在しない場合などのデフォルト値を設定できます
        return mapping
    
    def get_alert_sounds(self) -> Dict[str, Any]:
        """
        アラート種別ごとの音声設定を取得します。
        以前は message_settings.py に定義されていた設定です。

        Returns:
            Dict[str, Any]: アラート音声設定の辞書。
        """
        sounds = self.get('alert_sounds', {})
        # ここでキーが存在しない場合などのデフォルト値を設定できます
        return sounds

    def set(self, key_path: str, value: Any):
        """
        指定されたキーパスで設定値を設定します (メモリ上のみ)。
        永続化するには save() を呼び出す必要があります。

        Args:
            key_path (str): ドット区切りのキーパス。
            value (Any): 設定する値。
        """
        if not self._config:
             logger.warning("設定が読み込まれていません。set() を呼び出す前に load() を実行してください。")
             # load を試みるか、エラーにするか
             # self.load()
             # return # 設定しない
             # ここでは、設定がなければ新しい辞書を作ることにする
             self._config = {}

        keys = key_path.split('.')
        current_level = self._config
        for i, key in enumerate(keys):
            if i == len(keys) - 1:
                current_level[key] = value
            else:
                if key not in current_level or not isinstance(current_level[key], dict):
                    current_level[key] = {}
                current_level = current_level[key]
        logger.info(f"設定値を更新しました (メモリ): {key_path} = {value}")

    def save(self) -> bool:
        """
        現在の設定をファイルに保存します。

        Returns:
            bool: 保存に成功した場合は True、失敗した場合は False。
        """
        try:
            # 保存先ディレクトリが存在しない場合は作成
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            save_yaml(self._config, self.config_path)
            logger.info(f"設定をファイルに保存しました: {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"設定ファイルの保存中にエラーが発生しました ({self.config_path}): {e}", exc_info=True)
            return False 
# backend/src/utils/config_manager.py

import os
import json
from typing import Any, Dict, Optional, Union, List
# utils.config から yaml_utils を使う想定（前回確認済み）
from .yaml_utils import load_yaml, save_yaml
from .logger import setup_logger
from .exceptions import ConfigError, ValidationError, wrap_exception
from copy import deepcopy

logger = setup_logger(__name__)

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
# 設定のデフォルト値を定義 (例)
DEFAULT_CONFIG = {
    'server': {'port': 8000},
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
    },
    'models': {
        'yolo': {
            'model_name': 'yolov8n.pt',
            'models_dir': 'models'  # プロジェクトルートからの相対パス
        }
    }
    # 必要に応じて他のデフォルト設定を追加
}

class ConfigManager:
    """
    設定ファイル (config.yaml) の読み込み、アクセス、保存を管理するクラス。
    
    Phase 2-2 強化機能:
    - 環境変数による設定上書き
    - 設定値バリデーション
    - 動的設定更新
    - 複数形式対応（YAML/JSON）
    """
    def __init__(self, config_path: Optional[str] = None, enable_env_override: bool = True):
        """
        ConfigManager を初期化します。

        Args:
            config_path (Optional[str]): 設定ファイルのパス。None の場合はデフォルトパスを使用。
            enable_env_override (bool): 環境変数による設定上書きを有効にするか
        """
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self.enable_env_override = enable_env_override
        self._config: Dict[str, Any] = {}
        self._env_prefix = "KANSHICHAN_"  # 環境変数のプレフィックス
        self._validation_rules: Dict[str, Dict] = {}  # バリデーションルール
        
        # デフォルトバリデーションルールの設定
        self._setup_default_validation_rules()
        
        logger.info(f"ConfigManager initialized with path: {self.config_path}, env_override: {enable_env_override}")

    def _setup_default_validation_rules(self) -> None:
        """
        デフォルトのバリデーションルールを設定
        """
        # サーバー設定
        self.add_validation_rule('server.port', {
            'type': 'int',
            'min': 1,
            'max': 65535,
            'required': True
        })
        
        # 検出設定
        self.add_validation_rule('detector.use_mediapipe', {
            'type': 'bool',
            'required': True
        })
        
        self.add_validation_rule('detector.use_yolo', {
            'type': 'bool',
            'required': True
        })
        
        # 閾値設定
        self.add_validation_rule('conditions.absence.threshold_seconds', {
            'type': 'float',
            'min': 1.0,
            'max': 7200.0,  # 2時間
            'required': True
        })
        
        self.add_validation_rule('conditions.smartphone_usage.threshold_seconds', {
            'type': 'float',
            'min': 1.0,
            'max': 3600.0,  # 1時間
            'required': True
        })
        
        # LINE設定
        self.add_validation_rule('line.enabled', {
            'type': 'bool',
            'required': True
        })
        
        # LLM設定
        self.add_validation_rule('llm.enabled', {
            'type': 'bool',
            'required': True
        })
        
        self.add_validation_rule('llm.temperature', {
            'type': 'float',
            'min': 0.0,
            'max': 2.0
        })
        
        logger.debug("Default validation rules set up")

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

        # 環境変数による設定の上書きを適用
        self._apply_env_overrides()
        
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

    def _apply_env_overrides(self) -> None:
        """
        環境変数による設定の上書きを適用
        
        環境変数名の形式: KANSHICHAN_<KEY_PATH>
        例: KANSHICHAN_SERVER_PORT=5002
        """
        if not self.enable_env_override:
            return
            
        try:
            env_overrides = {}
            for env_key, env_value in os.environ.items():
                if env_key.startswith(self._env_prefix):
                    # プレフィックスを除去してキーパスに変換
                    config_key = env_key[len(self._env_prefix):].lower().replace('_', '.')
                    
                    # 環境変数の値を適切な型に変換
                    converted_value = self._convert_env_value(env_value)
                    env_overrides[config_key] = converted_value
                    
                    logger.info(f"Environment override: {config_key} = {converted_value} (from {env_key}={env_value})")
            
            # 環境変数の値を設定に適用
            for key_path, value in env_overrides.items():
                self._set_nested_value(self._config, key_path, value)
                
        except Exception as e:
            env_error = wrap_exception(
                e, ConfigError,
                "Error applying environment variable overrides",
                details={
                    'prefix': self._env_prefix,
                    'override_count': len(env_overrides) if 'env_overrides' in locals() else 0
                }
            )
            logger.error(f"Environment override error: {env_error.to_dict()}")

    def _convert_env_value(self, value: str) -> Any:
        """
        環境変数の文字列値を適切な型に変換
        
        Args:
            value: 環境変数の値
            
        Returns:
            変換された値
        """
        # 真偽値の変換
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # 数値の変換（整数）
        try:
            if '.' not in value:
                return int(value)
        except ValueError:
            pass
        
        # 数値の変換（浮動小数点）
        try:
            return float(value)
        except ValueError:
            pass
        
        # JSON形式の配列・オブジェクトの変換
        if value.startswith(('[', '{')):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        
        # 文字列として返す
        return value

    def _set_nested_value(self, config: Dict, key_path: str, value: Any) -> None:
        """
        ネストした設定値を設定
        
        Args:
            config: 設定辞書
            key_path: ドット区切りのキーパス
            value: 設定する値
        """
        keys = key_path.split('.')
        current_level = config
        
        for i, key in enumerate(keys):
            if i == len(keys) - 1:
                current_level[key] = value
            else:
                if key not in current_level or not isinstance(current_level[key], dict):
                    current_level[key] = {}
                current_level = current_level[key]

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

    def add_validation_rule(self, key_path: str, rule: Dict[str, Any]) -> None:
        """
        設定値のバリデーションルールを追加
        
        Args:
            key_path: ドット区切りのキーパス
            rule: バリデーションルール
                {
                    'type': 'int' | 'float' | 'str' | 'bool' | 'list' | 'dict',
                    'min': 最小値（数値の場合）,
                    'max': 最大値（数値の場合）,
                    'choices': 選択肢のリスト,
                    'required': True | False
                }
        """
        self._validation_rules[key_path] = rule
        logger.debug(f"Validation rule added for {key_path}: {rule}")

    def validate_config(self) -> List[str]:
        """
        現在の設定をバリデーションし、エラーがあればリストで返す
        
        Returns:
            エラーメッセージのリスト（空なら全て正常）
        """
        errors = []
        
        for key_path, rule in self._validation_rules.items():
            try:
                value = self.get(key_path)
                error = self._validate_value(key_path, value, rule)
                if error:
                    errors.append(error)
            except Exception as e:
                errors.append(f"Validation error for {key_path}: {str(e)}")
        
        return errors

    def _validate_value(self, key_path: str, value: Any, rule: Dict[str, Any]) -> Optional[str]:
        """
        単一の値をバリデーション
        
        Args:
            key_path: キーパス
            value: 検証する値
            rule: バリデーションルール
            
        Returns:
            エラーメッセージ（問題なければNone）
        """
        # 必須チェック
        if rule.get('required', False) and value is None:
            return f"{key_path} is required but not set"
        
        if value is None:
            return None  # 非必須でNoneなら問題なし
        
        # 型チェック
        expected_type = rule.get('type')
        if expected_type:
            type_map = {
                'int': int,
                'float': (int, float),
                'str': str,
                'bool': bool,
                'list': list,
                'dict': dict
            }
            
            expected_python_type = type_map.get(expected_type)
            if expected_python_type and not isinstance(value, expected_python_type):
                return f"{key_path} must be {expected_type}, got {type(value).__name__}"
        
        # 数値範囲チェック
        if isinstance(value, (int, float)):
            min_val = rule.get('min')
            max_val = rule.get('max')
            
            if min_val is not None and value < min_val:
                return f"{key_path} must be >= {min_val}, got {value}"
            
            if max_val is not None and value > max_val:
                return f"{key_path} must be <= {max_val}, got {value}"
        
        # 選択肢チェック
        choices = rule.get('choices')
        if choices and value not in choices:
            return f"{key_path} must be one of {choices}, got {value}"
        
        return None

    def set_with_validation(self, key_path: str, value: Any) -> bool:
        """
        バリデーション付きで設定値を設定
        
        Args:
            key_path: ドット区切りのキーパス
            value: 設定する値
            
        Returns:
            設定に成功したかどうか
        """
        try:
            # バリデーションルールがある場合はチェック
            if key_path in self._validation_rules:
                error = self._validate_value(key_path, value, self._validation_rules[key_path])
                if error:
                    logger.error(f"Validation failed: {error}")
                    return False
            
            # 設定を更新
            self.set(key_path, value)
            return True
            
        except Exception as e:
            set_error = wrap_exception(
                e, ValidationError,
                f"Error setting validated config value for {key_path}",
                details={'key_path': key_path, 'value': value}
            )
            logger.error(f"Set with validation error: {set_error.to_dict()}")
            return False

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

    def reload(self) -> bool:
        """
        設定ファイルを再読み込み（ホットリロード）
        
        Returns:
            再読み込みに成功したかどうか
        """
        logger.info("Reloading configuration...")
        return self.load()

    def get_env_prefix(self) -> str:
        """
        環境変数のプレフィックスを取得
        
        Returns:
            環境変数のプレフィックス
        """
        return self._env_prefix

    def set_env_prefix(self, prefix: str) -> None:
        """
        環境変数のプレフィックスを設定
        
        Args:
            prefix: 新しいプレフィックス
        """
        old_prefix = self._env_prefix
        self._env_prefix = prefix
        logger.info(f"Environment prefix changed: {old_prefix} -> {prefix}")

    def export_to_json(self, file_path: str) -> bool:
        """
        現在の設定をJSONファイルにエクスポート
        
        Args:
            file_path: エクスポート先のJSONファイルパス
            
        Returns:
            エクスポートに成功したかどうか
        """
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            logger.info(f"Configuration exported to JSON: {file_path}")
            return True
        except Exception as e:
            export_error = wrap_exception(
                e, ConfigError,
                f"Error exporting configuration to JSON file",
                details={'file_path': file_path}
            )
            logger.error(f"JSON export error: {export_error.to_dict()}")
            return False

    def import_from_json(self, file_path: str) -> bool:
        """
        JSONファイルから設定をインポート
        
        Args:
            file_path: インポート元のJSONファイルパス
            
        Returns:
            インポートに成功したかどうか
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"JSON file not found: {file_path}")
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # デフォルト設定とマージ
            self._config = self._merge_configs(DEFAULT_CONFIG, imported_config)
            
            # 環境変数の上書きを再適用
            self._apply_env_overrides()
            
            logger.info(f"Configuration imported from JSON: {file_path}")
            return True
        except Exception as e:
            import_error = wrap_exception(
                e, ConfigError,
                f"Error importing configuration from JSON file",
                details={'file_path': file_path}
            )
            logger.error(f"JSON import error: {import_error.to_dict()}")
            return False

    def get_config_summary(self) -> Dict[str, Any]:
        """
        設定の概要情報を取得
        
        Returns:
            設定概要の辞書
        """
        return {
            'config_path': self.config_path,
            'env_override_enabled': self.enable_env_override,
            'env_prefix': self._env_prefix,
            'validation_rules_count': len(self._validation_rules),
            'config_keys': list(self._config.keys()) if self._config else [],
            'validation_errors': self.validate_config()
        } 
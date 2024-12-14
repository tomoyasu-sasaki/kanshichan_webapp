import os
from src.kanshichan.utils.yaml_utils import load_yaml, save_yaml

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')

def load_config(config_path=None):
    """設定ファイルを読み込む"""
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH
    return load_yaml(config_path)

def save_config(config, config_path=None):
    """設定をYAMLファイルに保存する"""
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH
    save_yaml(config, config_path)
import yaml
import os

def load_yaml(file_path):
    """YAMLファイルを読み込む"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise Exception(f"Error loading YAML file: {e}")

def save_yaml(data, file_path):
    """データをYAMLファイルに保存する"""
    try:
        # ディレクトリが存在しない場合は作成
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(data, f, allow_unicode=True, default_flow_style=False)
    except Exception as e:
        raise Exception(f"Error saving YAML file: {e}") 
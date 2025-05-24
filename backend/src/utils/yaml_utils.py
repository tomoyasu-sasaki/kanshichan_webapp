import yaml
import os
from utils.exceptions import YamlError, YAMLParsingError, FileNotFoundError, FileReadError, FileWriteError

def load_yaml(file_path):
    """YAMLファイルを読み込む"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                return yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise YAMLParsingError(
                    message=f"YAML parsing failed for file: {file_path}",
                    details={'file_path': file_path, 'yaml_error': str(e)},
                    original_exception=e
                )
    except FileNotFoundError as e:
        raise FileNotFoundError(
            message=f"YAML file not found: {file_path}",
            details={'file_path': file_path},
            original_exception=e
        )
    except PermissionError as e:
        raise FileReadError(
            message=f"Permission denied reading YAML file: {file_path}",
            details={'file_path': file_path},
            original_exception=e
        )
    except Exception as e:
        raise YamlError(
            message=f"Unexpected error loading YAML file: {file_path}",
            details={'file_path': file_path},
            original_exception=e
        )

def save_yaml(data, file_path):
    """データをYAMLファイルに保存する"""
    try:
        # ディレクトリが存在しない場合は作成
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            try:
                yaml.safe_dump(data, f, allow_unicode=True, default_flow_style=False)
            except yaml.YAMLError as e:
                raise YAMLParsingError(
                    message=f"YAML serialization failed for file: {file_path}",
                    details={'file_path': file_path, 'yaml_error': str(e)},
                    original_exception=e
                )
    except PermissionError as e:
        raise FileWriteError(
            message=f"Permission denied writing YAML file: {file_path}",
            details={'file_path': file_path},
            original_exception=e
        )
    except OSError as e:
        raise FileWriteError(
            message=f"OS error writing YAML file: {file_path}",
            details={'file_path': file_path, 'os_error': str(e)},
            original_exception=e
        )
    except Exception as e:
        raise YamlError(
            message=f"Unexpected error saving YAML file: {file_path}",
            details={'file_path': file_path},
            original_exception=e
        ) 
import os
import sys
import pytest
from unittest.mock import patch, MagicMock
import tempfile
import yaml

# プロジェクトのルートディレクトリをsys.pathに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from utils.config_manager import ConfigManager
from utils.exceptions import ConfigError

class TestConfigManager:
    """ConfigManagerのテスト"""

    def test_load_existing_config(self):
        """存在する設定ファイルの読み込みテスト"""
        # 一時ファイルを作成
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp_file:
            yaml.dump({'server': {'port': 9999}}, tmp_file)
            tmp_path = tmp_file.name

        try:
            # 一時ファイルを設定として読み込む
            config_manager = ConfigManager(config_path=tmp_path)
            assert config_manager.load() == True
            assert config_manager.get('server.port') == 9999
        finally:
            # 一時ファイルを削除
            os.unlink(tmp_path)

    def test_load_nonexistent_config_with_default(self):
        """存在しない設定ファイルの読み込みとデフォルト値の使用"""
        # 存在しないパスを指定
        config_manager = ConfigManager(config_path="/path/to/nonexistent/config.yaml")
        assert config_manager.load() == False
        # デフォルト値が使用されるはず
        assert config_manager.get('server.port') == 8000

    def test_load_nonexistent_config_with_fail_on_missing(self):
        """存在しない設定ファイルの読み込みでfail_on_missingが有効な場合"""
        # 存在しないパスを指定し、fail_on_missingを有効に
        config_manager = ConfigManager(
            config_path="/path/to/nonexistent/config.yaml", 
            fail_on_missing=True
        )
        
        # 例外が発生するはず
        with pytest.raises(ConfigError):
            config_manager.load()

    def test_environment_detection(self):
        """環境検出機能のテスト"""
        # 環境変数を設定
        with patch.dict(os.environ, {"KANSHICHAN_ENV": "dev"}):
            config_manager = ConfigManager()
            assert config_manager.environment == "dev"

        # 環境変数が未設定の場合
        with patch.dict(os.environ, {}, clear=True):
            config_manager = ConfigManager()
            assert config_manager.environment == "prod"  # デフォルト

    def test_config_path_for_environment(self):
        """環境ごとの設定ファイルパスの選択テスト"""
        # dev環境
        with patch.dict(os.environ, {"KANSHICHAN_ENV": "dev"}):
            config_manager = ConfigManager()
            assert "config.dev.yaml" in config_manager.config_path

        # ci環境
        with patch.dict(os.environ, {"KANSHICHAN_ENV": "ci"}):
            config_manager = ConfigManager()
            assert "config.ci.yaml" in config_manager.config_path

        # prod環境
        with patch.dict(os.environ, {"KANSHICHAN_ENV": "prod"}):
            config_manager = ConfigManager()
            assert "config.yaml" in config_manager.config_path and "config.dev.yaml" not in config_manager.config_path

    @pytest.mark.parametrize("env_value", ["ci", "dev", "prod"])
    def test_loaded_flag(self, env_value):
        """is_loaded()フラグのテスト"""
        # 環境変数を設定
        with patch.dict(os.environ, {"KANSHICHAN_ENV": env_value}):
            # モックで.load()を成功させる
            config_manager = ConfigManager()
            with patch.object(ConfigManager, 'load', return_value=True):
                config_manager.load()
                # _loaded属性を直接設定
                config_manager._loaded = True
                assert config_manager.is_loaded() == True

            # モックで.load()を失敗させる
            config_manager = ConfigManager()
            with patch.object(ConfigManager, 'load', return_value=False):
                config_manager.load()
                # _loaded属性を直接設定
                config_manager._loaded = False
                assert config_manager.is_loaded() == False

    def test_ci_mode_with_missing_config(self):
        """CI環境で設定がない場合の動作テスト"""
        # CI環境を設定
        with patch.dict(os.environ, {"KANSHICHAN_ENV": "ci"}):
            # 存在しない設定ファイルパスを使用
            config_manager = ConfigManager(
                config_path="/nonexistent/path.yaml",
                fail_on_missing=True
            )
            
            # CI環境では設定ファイルがないとエラーになる
            with pytest.raises(ConfigError):
                config_manager.load()


if __name__ == "__main__":
    # スクリプトとして実行された場合は、pytestを実行
    sys.exit(pytest.main(["-v", __file__])) 
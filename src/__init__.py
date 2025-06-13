import sys
import types
from pathlib import Path

# ルートから backend/src を解決
_backend_src = Path(__file__).resolve().parent.parent / 'backend' / 'src'

# backend/src が存在する場合のみパスに追加
if _backend_src.exists():
    sys.path.insert(0, str(_backend_src))

    # `src` 配下のモジュールを実際には backend/src から解決できるように、
    # importlib を介さず NamespacePackage を手動生成
    _module = types.ModuleType(__name__)
    _module.__path__ = [str(_backend_src)]  # type: ignore
    sys.modules[__name__] = _module

# クリーンアップ不要: モジュールは import 時にキャッシュされる 
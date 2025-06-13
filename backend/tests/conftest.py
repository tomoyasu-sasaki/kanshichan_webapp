import sys
import os
from pathlib import Path

# プロジェクトルートをsys.pathに含める (pytest 実行場所がどこであっても安定させる)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent  # .../KanshiChan
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# backend/src も直接パスに追加 (src. プレフィックスのインポート互換性確保)
BACKEND_SRC = ROOT_DIR / 'backend' / 'src'
if BACKEND_SRC.exists() and str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC)) 
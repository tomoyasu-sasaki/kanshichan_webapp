"""
Zonos TTS Library - Embedded Version

このコードはApache-2.0ライセンスの下で配布されているZonos TTSライブラリを
埋め込み用に改変したものです。

オリジナルのリポジトリ: https://github.com/Zyphra/Zonos
"""

from .model import Zonos
from .conditioning import make_cond_dict

__version__ = "0.1.0"
__author__ = "Zyphra (Original) / KanshiChan (Embedded)"
__license__ = "Apache-2.0" 
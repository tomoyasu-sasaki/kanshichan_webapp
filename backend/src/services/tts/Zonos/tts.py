import torch
import torchaudio
import os
import argparse
from pathlib import Path
from typing import Optional, Union

from zonos.model import Zonos
from zonos.conditioning import make_cond_dict, supported_language_codes

# 対応言語を日本語と英語のみに制限
SUPPORTED_LANGUAGES = ["ja", "en-us"]

class MacOSTTSApp:
    """macOS対応のTTSアプリケーション（CLI版）"""
    
    def __init__(self):
        # macOS用のデバイス設定（MPSを優先）
        # MPSは現在不安定なため、一時的にCPUを使用
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
            print("✅ MPSデバイスを使用します")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
            print("✅ CUDAデバイスを使用します")
        else:
            self.device = torch.device("cpu")
            print("⚠️  CPUデバイスを使用します（Zonosのコードでは現在MPSが不安定なため）")
        
        self.model = None
        self.current_model_type = None
        self.speaker_embedding = None
        self.speaker_audio_path = None
        
        # 出力ディレクトリを作成
        self.output_dir = Path("generated_audio")
        self.output_dir.mkdir(exist_ok=True)
    
    def load_model(self, model_choice: str = "Zyphra/Zonos-v0.1-hybrid"):
        """モデルを読み込む"""
        if self.current_model_type != model_choice:
            if self.model is not None:
                del self.model
                if torch.backends.mps.is_available():
                    torch.mps.empty_cache()
                elif torch.cuda.is_available():
                    torch.cuda.empty_cache()
            
            print(f"🔄 {model_choice} モデルを読み込み中...")
            try:
                self.model = Zonos.from_pretrained(model_choice, device=self.device)
                self.model.requires_grad_(False).eval()
                self.current_model_type = model_choice
                print(f"✅ {model_choice} モデルの読み込みが完了しました！")
            except Exception as e:
                print(f"❌ モデルの読み込みに失敗しました: {e}")
                # フォールバックとしてtransformerモデルを試す
                if "hybrid" in model_choice:
                    print("🔄 Hybridモデルには'mamba-ssm'パッケージが必要です。transformerモデルを使用します...")
                    fallback_model = "Zyphra/Zonos-v0.1-transformer"
                    self.model = Zonos.from_pretrained(fallback_model, device=self.device)
                    self.model.requires_grad_(False).eval()
                    self.current_model_type = fallback_model
                    print(f"✅ {fallback_model} モデルの読み込みが完了しました！")
                else:
                    raise e
        
        return self.model
    
    def generate_basic_tts(
        self,
        text: str,
        language: str = "en-us",
        model_choice: str = "Zyphra/Zonos-v0.1-transformer",
        seed: int = 42,
        # 音声パラメータ
        fmax: float = 22050.0,
        pitch_std: float = 20.0,
        speaking_rate: float = 15.0,
        # 感情パラメータ
        happiness: float = 0.3077,
        sadness: float = 0.0256,
        anger: float = 0.0256,
        # 生成パラメータ
        cfg_scale: float = 2.0,
        max_new_tokens: int = 2580,
        # サンプリングパラメータ
        top_p: float = 0.9,
        min_p: float = 0.1,
        output_filename: str = None,
    ):
        """基本的なTTS生成（パラメータ拡張版）"""
        if not text.strip():
            print("❌ テキストを入力してください")
            return None
        
        try:
            model = self.load_model(model_choice)
            
            torch.manual_seed(seed)
            
            print("🔊 音声生成中...")
            
            # 感情ベクトルを構築（正規化される）
            # Happiness, Sadness, Disgust, Fear, Surprise, Anger, Other, Neutral
            emotion = [happiness, sadness, 0.0256, 0.0256, 0.0256, anger, 0.2564, 1.0 - happiness - sadness - anger]
            
            cond_dict = make_cond_dict(
                text=text,
                language=language,
                emotion=emotion,
                fmax=fmax,
                pitch_std=pitch_std,
                speaking_rate=speaking_rate,
                device=self.device
            )
            conditioning = model.prepare_conditioning(cond_dict)
            
            print("🔄 音声コード生成中...")
            codes = model.generate(
                conditioning,
                max_new_tokens=max_new_tokens,
                cfg_scale=cfg_scale,
                sampling_params={"top_p": top_p, "min_p": min_p}
            )
            
            print("🔄 音声デコード中...")
            wavs = model.autoencoder.decode(codes).cpu()
            
            # 音声ファイルを保存
            if output_filename:
                output_path = Path(output_filename)
            else:
                output_path = self.output_dir / f"basic_tts_{seed}.wav"
            
            torchaudio.save(str(output_path), wavs[0], model.autoencoder.sampling_rate)
            
            # パラメータ情報を表示
            print(f"""✅ 音声生成が完了しました！
📂 保存先: {output_path}
📊 使用パラメータ:
• 言語: {language}
• 最大周波数: {fmax}Hz
• ピッチ変動: {pitch_std}
• 話速: {speaking_rate}
• 感情 - 幸福: {happiness:.2f}, 悲しみ: {sadness:.2f}, 怒り: {anger:.2f}
• CFGスケール: {cfg_scale}
• シード: {seed}""")
            
            return str(output_path)
            
        except Exception as e:
            print(f"❌ 音声生成に失敗しました: {str(e)}")
            return None
    
    def generate_voice_clone(
        self,
        text: str,
        reference_audio,
        language: str = "en-us",
        model_choice: str = "Zyphra/Zonos-v0.1-transformer",
        seed: int = 42,
        # 音声パラメータ
        fmax: float = 22050.0,
        pitch_std: float = 20.0,
        speaking_rate: float = 15.0,
        # 感情パラメータ
        happiness: float = 0.3077,
        sadness: float = 0.0256,
        anger: float = 0.0256,
        # 生成パラメータ
        cfg_scale: float = 2.0,
        max_new_tokens: int = 2580,
        # サンプリングパラメータ
        top_p: float = 0.9,
        min_p: float = 0.1,
        output_filename: str = None,
    ):
        """ボイスクローン機能付きTTS生成（パラメータ拡張版）"""
        if not text.strip():
            print("❌ テキストを入力してください")
            return None
        
        if not os.path.exists(reference_audio):
            print(f"❌ 参照音声ファイル '{reference_audio}' が見つかりません")
            return None
        
        try:
            model = self.load_model(model_choice)
            
            torch.manual_seed(seed)
            
            print("🔊 参照音声を処理中...")
            
            # 参照音声から話者埋め込みを生成
            if reference_audio != self.speaker_audio_path:
                wav, sr = torchaudio.load(reference_audio)
                self.speaker_embedding = model.make_speaker_embedding(wav, sr)
                self.speaker_embedding = self.speaker_embedding.to(self.device)
                self.speaker_audio_path = reference_audio
                print("✅ 新しい話者埋め込みを生成しました")
            
            print("🔄 条件付けを準備中...")
            
            # 感情ベクトルを構築
            emotion = [happiness, sadness, 0.0256, 0.0256, 0.0256, anger, 0.2564, 1.0 - happiness - sadness - anger]
            
            cond_dict = make_cond_dict(
                text=text,
                language=language,
                speaker=self.speaker_embedding,
                emotion=emotion,
                fmax=fmax,
                pitch_std=pitch_std,
                speaking_rate=speaking_rate,
                device=self.device
            )
            conditioning = model.prepare_conditioning(cond_dict)
            
            print("🔄 音声コード生成中...")
            codes = model.generate(
                conditioning,
                max_new_tokens=max_new_tokens,
                cfg_scale=cfg_scale,
                sampling_params={"top_p": top_p, "min_p": min_p}
            )
            
            print("🔄 音声デコード中...")
            wavs = model.autoencoder.decode(codes).cpu()
            
            # 音声ファイルを保存
            if output_filename:
                output_path = Path(output_filename)
            else:
                output_path = self.output_dir / f"voice_clone_{seed}.wav"
            
            torchaudio.save(str(output_path), wavs[0], model.autoencoder.sampling_rate)
            
            # パラメータ情報を表示
            print(f"""✅ ボイスクローン生成が完了しました！
📂 保存先: {output_path}
📊 使用パラメータ:
• 言語: {language}
• 最大周波数: {fmax}Hz
• ピッチ変動: {pitch_std}
• 話速: {speaking_rate}
• 感情 - 幸福: {happiness:.2f}, 悲しみ: {sadness:.2f}, 怒り: {anger:.2f}
• CFGスケール: {cfg_scale}
• シード: {seed}""")
            
            return str(output_path)
            
        except Exception as e:
            print(f"❌ ボイスクローン生成に失敗しました: {str(e)}")
            return None

def main():
    """メイン関数 - コマンドラインインターフェース"""
    parser = argparse.ArgumentParser(description="Zonos TTS - CLI版")
    
    # サブコマンドの設定
    subparsers = parser.add_subparsers(dest="command", help="使用するコマンド")
    
    # 基本TTSコマンド
    basic_parser = subparsers.add_parser("basic", help="基本的なTTS生成")
    basic_parser.add_argument("--text", "-t", required=True, help="生成するテキスト")
    basic_parser.add_argument("--lang", "-l", choices=SUPPORTED_LANGUAGES, default="en-us", help="言語 (ja/en-us)")
    basic_parser.add_argument("--model", "-m", choices=["Zyphra/Zonos-v0.1-transformer", "Zyphra/Zonos-v0.1-hybrid"], 
                              default="Zyphra/Zonos-v0.1-transformer", help="使用するモデル")
    basic_parser.add_argument("--seed", "-s", type=int, default=42, help="乱数シード")
    basic_parser.add_argument("--output", "-o", help="出力ファイルパス")
    
    # 音声パラメータ
    basic_parser.add_argument("--fmax", type=float, default=22050.0, help="最大周波数 (Hz)")
    basic_parser.add_argument("--pitch-std", type=float, default=20.0, help="ピッチ変動")
    basic_parser.add_argument("--speaking-rate", type=float, default=15.0, help="話速")
    
    # 感情パラメータ
    basic_parser.add_argument("--happiness", type=float, default=0.3077, help="幸福感 (0.0-1.0)")
    basic_parser.add_argument("--sadness", type=float, default=0.0256, help="悲しみ (0.0-1.0)")
    basic_parser.add_argument("--anger", type=float, default=0.0256, help="怒り (0.0-1.0)")
    
    # 生成パラメータ
    basic_parser.add_argument("--cfg-scale", type=float, default=2.0, help="CFGスケール")
    basic_parser.add_argument("--max-tokens", type=int, default=2580, help="最大トークン数")
    
    # サンプリングパラメータ
    basic_parser.add_argument("--top-p", type=float, default=0.9, help="Top-p")
    basic_parser.add_argument("--min-p", type=float, default=0.1, help="Min-p")
    
    # ボイスクローンコマンド
    clone_parser = subparsers.add_parser("clone", help="ボイスクローン生成")
    clone_parser.add_argument("--text", "-t", required=True, help="生成するテキスト")
    clone_parser.add_argument("--reference", "-r", required=True, help="参照音声ファイルのパス")
    clone_parser.add_argument("--lang", "-l", choices=SUPPORTED_LANGUAGES, default="en-us", help="言語 (ja/en-us)")
    clone_parser.add_argument("--model", "-m", choices=["Zyphra/Zonos-v0.1-transformer", "Zyphra/Zonos-v0.1-hybrid"], 
                              default="Zyphra/Zonos-v0.1-transformer", help="使用するモデル")
    clone_parser.add_argument("--seed", "-s", type=int, default=42, help="乱数シード")
    clone_parser.add_argument("--output", "-o", help="出力ファイルパス")
    
    # 音声パラメータ
    clone_parser.add_argument("--fmax", type=float, default=22050.0, help="最大周波数 (Hz)")
    clone_parser.add_argument("--pitch-std", type=float, default=20.0, help="ピッチ変動")
    clone_parser.add_argument("--speaking-rate", type=float, default=15.0, help="話速")
    
    # 感情パラメータ
    clone_parser.add_argument("--happiness", type=float, default=0.3077, help="幸福感 (0.0-1.0)")
    clone_parser.add_argument("--sadness", type=float, default=0.0256, help="悲しみ (0.0-1.0)")
    clone_parser.add_argument("--anger", type=float, default=0.0256, help="怒り (0.0-1.0)")
    
    # 生成パラメータ
    clone_parser.add_argument("--cfg-scale", type=float, default=2.0, help="CFGスケール")
    clone_parser.add_argument("--max-tokens", type=int, default=2580, help="最大トークン数")
    
    # サンプリングパラメータ
    clone_parser.add_argument("--top-p", type=float, default=0.9, help="Top-p")
    clone_parser.add_argument("--min-p", type=float, default=0.1, help="Min-p")
    
    # ヘルプコマンド
    help_parser = subparsers.add_parser("help", help="使用方法を表示")
    
    args = parser.parse_args()
    
    # ヘルプまたはコマンドなしの場合
    if args.command is None or args.command == "help":
        print("""
🎙️ Zonos TTS - CLI版
=====================

基本的な使い方:
--------------
1. 基本的なTTS生成:
   python tts_app_macos.py basic --text "こんにちは、世界" --lang ja

2. ボイスクローン生成:
   python tts_app_macos.py clone --text "こんにちは、世界" --reference voice.wav --lang ja

詳細なヘルプ:
-----------
- 基本TTS: python tts_app_macos.py basic --help
- ボイスクローン: python tts_app_macos.py clone --help

対応言語:
--------
- 日本語: ja
- 英語: en-us
        """)
        return
    
    # アプリケーションの初期化
    app = MacOSTTSApp()
    
    # コマンドに応じた処理
    if args.command == "basic":
        app.generate_basic_tts(
            text=args.text,
            language=args.lang,
            model_choice=args.model,
            seed=args.seed,
            # 音声パラメータ
            fmax=args.fmax,
            pitch_std=args.pitch_std,
            speaking_rate=args.speaking_rate,
            # 感情パラメータ
            happiness=args.happiness,
            sadness=args.sadness,
            anger=args.anger,
            # 生成パラメータ
            cfg_scale=args.cfg_scale,
            max_new_tokens=args.max_tokens,
            # サンプリングパラメータ
            top_p=args.top_p,
            min_p=args.min_p,
            # 出力ファイル
            output_filename=args.output
        )
    
    elif args.command == "clone":
        app.generate_voice_clone(
            text=args.text,
            reference_audio=args.reference,
            language=args.lang,
            model_choice=args.model,
            seed=args.seed,
            # 音声パラメータ
            fmax=args.fmax,
            pitch_std=args.pitch_std,
            speaking_rate=args.speaking_rate,
            # 感情パラメータ
            happiness=args.happiness,
            sadness=args.sadness,
            anger=args.anger,
            # 生成パラメータ
            cfg_scale=args.cfg_scale,
            max_new_tokens=args.max_tokens,
            # サンプリングパラメータ
            top_p=args.top_p,
            min_p=args.min_p,
            # 出力ファイル
            output_filename=args.output
        )


if __name__ == "__main__":
    main() 
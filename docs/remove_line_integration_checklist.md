# LINE 連携機能 削除プロジェクト進捗チェックリスト

## Overview
本ドキュメントは、KanshiChan から LINE 連携機能を完全に削除するためのタスクを **Phase** と **Section** に分割し、進捗を可視化するチェックリストです。各タスクのチェックボックスを更新しながら作業を進めてください。

---

## Phase 1 : Analysis & Planning
| ✅ | Task |
|-----|------|
| [x] | 目的と範囲を確定（LINE Bot & LINE Notify の完全削除） |
| [x] | 影響モジュール調査 (`backend`, `frontend`, `config`, `tests`, CI/CD) |
| [x] | スケジュール作成 & リソース割当 |
| [x] | リスク／ロールバック戦略策定 |
| [x] | 関係者レビュー & 承認 |

---

## Phase 2 : Backend 修正
### Section 2-1 : 依存ライブラリ削除
- [x] `requirements.txt` から `line-bot-sdk` を削除
- [x] `setup.py` の `install_requires` から除去
- [x] Poetry／Dockerfile 等に記載が無いか確認

### Section 2-2 : サービス・ハンドラ削除
- [x] `backend/src/services/communication/line_service.py` を削除
- [x] `AlertService` から LINE 関連コード削除
- [x] `_send_line_notify()` 削除 & 呼び出し除去

### Section 2-3 : Web レイヤ改修
- [x] `backend/src/web/app.py` の LINE import & 初期化ブロック削除
- [x] `backend/src/web/handlers.py` 削除 & 呼び出し除去
- [x] `/api/settings` から `message_extensions` 処理削除

### Section 2-4 : 例外クラス整理
- [x] `LineAPIError` 定義と参照削除（不要なら残しても可）

---

## Phase 3 : Frontend 修正
### Section 3-1 : UI 削除
- [x] `SettingsPanel.tsx` の LINE 関連 UI（`LINEメッセージ設定` ブロック）削除

### Section 3-2 : API 呼び出し更新
- [x] `/api/settings` 取得・更新ロジックから `message_extensions` を除去

### Section 3-3 : テスト更新
- [x] `SettingsPanel.test.(js|ts)x` の対象テストケース削除／修正

---

## Phase 4 : Config & YAML クリーンアップ
- [x] `backend/src/config/config.yaml` から `line:` セクション削除
- [x] `backend/src/config/config.ci.yaml` 同上
- [x] その他環境ファイル（`config.dev.yaml` 等）確認

---

## Phase 5 : CI/CD & スクリプト更新
- [x] CI ワークフローで `line-bot-sdk` インストール行を削除
- [x] ビルドキャッシュのバージョン固定を更新

---

## Phase 6 : テスト & QA
| ✅ | Task |
|-----|------|
| [x] | 単体テスト全通過 (`pytest`) |
| [x] | フロントエンドテスト全通過 (`npm test`) |
| [x] | 手動動作確認（Alert 音声 / WebSocket などが正常） |
| [x] | 不要 import 残存チェック (`flake8`, `mypy`) |

---

## Phase 7 : ドキュメント更新
- [x] `README.md` から LINE 設定手順などを削除
- [x] 生成物・API ドキュメントの修正

---

## Phase 8 : Final Verification & Merge
| ✅ | Task |
|-----|------|
| [ ] | コードレビュー & 承認取得 |
| [ ] | ステージ環境デプロイ & 回帰テスト |
| [ ] | 本番マージ & デプロイ |
| [ ] | リリースノート作成 |

---

## Progress Summary Template
進捗報告時は下記テンプレートを利用してください。

```markdown
### ⌛️ 本日の進捗
- 完了タスク:
  - Phase X / Section Y : …
- 着手中タスク:
  - Phase … : …

### 🚧 課題 / ブロッカー
- …

### 🔜 次の予定
- …
```

---

> **NOTE** このチェックリストは必要に応じて追加・削除・順序変更してください。 
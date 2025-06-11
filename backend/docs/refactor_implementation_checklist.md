# KanshiChan Backend リファクタリング & 実装進捗チェックリスト

> 最終更新: 2025-06-11

---

## 優先度レベル
1. 🟥 **Critical** – 直ちに対応しないと既存機能が停止/重大バグを誘発
2. 🟧 **High** – 早期対応で保守性・将来拡張性を大幅改善
3. 🟨 **Medium** – 品質向上・技術的負債解消
4. 🟩 **Low** – ドキュメント/スタイル調整など

---

## Phase 0: 事前準備

- [x] (🟥) **規約再確認**: `project_rules/` 全 YAML/MD を再読 & チェックリスト更新
- [x] (🟥) **ブランチ戦略確認**: `develop/refactor-*` 用のトピックブランチ作成 (*Git 操作は要承認*)
- [x] (🟥) **現行 CI パイプライン把握**: lint/type-check/pytest 実行ステップの確認
- [x] (🟧) **自動テストカバレッジ計測**: baseline を取得 (coverage%)

---

## Phase 1: 共通サービスローダー抽出

### 1-A AdvancedBehaviorAnalyzer ファクトリ
- [x] (🟥) 既存 2 箇所 (`basic_analysis_routes`, `advanced_analysis_routes`) のロジック比較
- [x] (🟥) `services/analysis/service_loader.py` 新規作成
- [x] (🟥) try/except ImportError → `ServiceUnavailableError` に置換
- [x] (🟧) Blueprint 依存部の共通化
- [x] (🟨) 型ヒント & ドキュメント追加
- [x] (🟩) コードスタイル調整

### 1-B PatternRecognizer ファクトリ
- [x] (🟥) 既存 2 箇所 (`advanced_analysis_routes`, `prediction_analysis_routes`) のロジック比較
- [x] (🟥) `services/analysis/service_loader.py` に追加
- [x] (🟥) try/except ImportError → `ServiceUnavailableError` に置換
- [x] (🟧) Blueprint 依存部の共通化
- [x] (🟨) 型ヒント & ドキュメント追加
- [x] (🟩) コードスタイル調整

### 1-C LINE Bot SDK v3 インポート修正
- [x] (🟥) `web/app.py` の LINE Bot SDK v3 インポートパス修正
- [x] (🟥) `WebhookHandler` を `linebot.v3.webhook` から正しくインポート
- [x] (🟥) メッセージング関連クラスのインポート整理
- [x] (🟨) インポート順序とインデントの調整

---

## Phase 2: Blueprint 階層化 & URL 整理

### 2-A URL プレフィックス整理
- [x] (🟥) 既存 Blueprint の URL プレフィックス調査
- [x] (🟥) 階層構造の設計 (`/api/analysis/basic` など)
- [x] (🟥) Blueprint の URL プレフィックス更新
- [x] (🟧) ルーティングテスト作成
- [x] (🟨) API ドキュメント更新
- [x] (🟩) OpenAPI 定義更新

### 2-B Blueprint 依存関係整理
- [x] (🟥) 循環参照チェック
- [x] (🟥) 共通ユーティリティの抽出
- [x] (🟧) エラーハンドリングの統一
- [x] (🟨) ミドルウェアの共通化
- [x] (🟩) コメント & ドキュメント更新

---

## Phase 3: Monitor.analyze_behavior 実装

- [ ] (🟥) 仕様定義: 必要な入力/出力 & DB 保存フォーマット
- [ ] (🟥) 既存 _extract_focus_trends 等ロジック再利用設計
- [ ] (🟥) リアルタイム WebSocket 連携パス設計
- [ ] (🟧) テストデータ生成スクリプト作成
- [ ] (🟧) 単体 & 結合テスト追加
- [ ] (🟨) パフォーマンス計測 & 30fps 保持確認

---

## Phase 4: 外部 TTS ライブラリ (Zonos) TODO 解消

- [ ] (🟥) `conditioning.py` の `NotImplementedError` 仕様確認 & 代替実装方針
- [ ] (🟥) `model.py` TODO (pad to multiple of 8, cfg_scale=1) 実装 or ガード追加
- [ ] (🟧) `_torch.py` pure 関数化 TODO の実装
- [ ] (🟨) ライブラリ本家 Issue 参照・fork 方針決定
- [ ] (🟩) ドキュメント化: 制限事項・既知の問題

---

## Phase 5: ConfigManager 初期化フロー強化

- [ ] (🟥) `src/main.py` で `ConfigManager` を必ず生成 & `app.config` 注入
- [ ] (🟥) 起動チェック: 未注入時にアプリ起動失敗させる Fail-fast
- [ ] (🟧) 開発モード用デフォルト設定ファイル追加
- [ ] (🟨) CI テスト: `pytest --env=ci` で config なし → 起動エラー期待

---

## Phase 6: テスト & CI 拡充

- [ ] (🟥) unit / integration テスト追加総数 >80% カバレッジ目標
- [ ] (🟥) GitHub Actions に type-check (`mypy`) ステップ追加
- [ ] (🟧) Lint (flake8/black) 自動フォーマッタ整備
- [ ] (🟨) Route 衝突検知テスト (自動生成された URL 一覧重複チェック)
- [ ] (🟩) カバレッジ閾値 75% を下回ったら CI fail

---

## Phase 7: QA & ドキュメント

- [ ] (🟥) エンドポイント毎の Example リクエスト/レスポンスを docs/api_guide.md に追加
- [ ] (🟥) 重大ロジック変更時のリリースノート (CHANGELOG) 更新
- [ ] (🟧) README: セットアップ手順 & 新 URL 反映
- [ ] (🟨) ADR(Architecture Decision Record) 追記 (Blueprint 階層化決定)

---

## Phase 8: 本番リリース準備

- [ ] (🟥) Staging 環境で smoke test 実施
- [ ] (🟧) 旧 URL Deprecation 通知を管理画面 & Slack に掲示
- [ ] (🟨) モニタリングダッシュボード (Grafana) に新メトリクス追加

---

## Appendix: 進捗記録テンプレート

```markdown
### <日付>
- ✅ [完了したタスク名]
- 🔄 [進行中タスク名] (残り <xx%>)
- ⚠️ [ブロッカー・課題]
``` 
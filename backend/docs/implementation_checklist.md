# KanshiChan 実装ギャップ対応チェックリスト

このチェックリストは `implementation_gap_report.adoc` に基づき、KanshiChanプロジェクトの実装漏れを解消するためのタスクを管理します。

---

## Phase 1: AIコア機能の実装 (5日間)

### Section 1.1: 検出結果の安定化 (Detection Smoother)
- [ ] `core/detection_smoother.py` を新規作成する。
- [ ] 信頼度ヒステリシス制御 (`_should_accept_detection`) を実装する。
- [ ] 検出バウンディングボックスの移動平均フィルタを実装する。
- [ ] 欠損フレーム補間ロジック (`interpolate_missing_detections`) を実装する。
- [ ] `ObjectDetector` に `DetectionSmoother` を統合する。

### Section 1.2: パフォーマンス最適化 (AI Optimizer)
- [ ] `core/ai_optimizer.py` を新規作成する。
- [ ] FPSカウンターを実装し、現在の推論速度を常時監視する。
- [ ] 動的フレームスキップ機構 (`FrameSkipper`) を実装する。
- [ ] `ObjectDetector` のメインループに `AIOptimizer` を統合する。
- [ ] パフォーマンステストを作成し、ベースライン性能をCIで検証する。

---

## Phase 2: バックエンド基盤強化 (3日間)

### Section 2.1: 通知システムのマルチチャネル対応
- [ ] `communication-system.adoc` から旧要件のLINE関連記述を削除する。
- [ ] `services/communication/enums.py` に `AlertChannel` Enum を定義する。
- [ ] `services/communication/notification_delivery.py` を新規作成し、配信管理ロジックを実装する。
- [ ] `services/communication/alert_service.py` にEmail通知用の `_send_email` メソッドを実装する。
- [ ] `AlertManager` が複数の `channels` を扱えるように修正する。

### Section 2.2: REST APIのパス統一
- [ ] `basic_analysis_routes.py` 等のBlueprintの `url_prefix` を `/api/analysis` に統一する。
- [ ] 旧URL (`/api/analysis/basic/*`) から新URLへのリダイレクト処理を追加する (任意)。
- [ ] PostmanやSwagger等のAPIドキュメントを更新する。

### Section 2.3: データベースモデルの追加
- [ ] `models/detection_log.py` を作成し、`DETECTION_LOG` スキーマを定義する。
- [ ] `models/detection_summary.py` を作成し、`DETECTION_SUMMARY` スキーマを定義する。
- [ ] `ObjectDetector` から検出結果を非同期で `DetectionLog` に保存する処理を追加する。

---

## Phase 3: システム監視とセキュリティ強化 (3日間)

### Section 3.1: システムメトリクスAPIの実装
- [x] `requirements.txt` に `psutil` を追加する。
- [x] `monitor_routes.py` に `/api/monitor/system-metrics` エンドポイントを追加する。
- [x] `psutil` を利用してCPU, メモリ, GPU使用率を取得するロジックを実装する。
- [x] WebSocketで `system_metrics` イベントを定期的にブロードキャストする機能を追加する。

### Section 3.2: セキュリティ対策の導入
- [x] `requirements.txt` に `flask-wtf` と `flask-limiter` を追加する。
- [x] Flaskアプリに `flask_wtf.csrf.CSRFProtect` を導入する。
- [x] `flask-limiter` を用いて主要なAPIエンドポイントにレート制限 (例: 100回/分) を適用する。
- [x] `flask-cors` の設定を `cors_allowed_origins="*"` から環境変数で指定されたオリジンのみを許可するように変更する。

---

## Phase 4: 品質保証 (QA) (2日間)

### Section 4.1: 機能テスト
- [ ] AIコア機能 (Smoother, Optimizer) の単体テスト・結合テストを実施する。
- [ ] 通知システム (Email) のE2Eテストを実施する。
- [ ] 全REST APIエンドポイントの疎通確認とスキーマ検証を行う。
- [ ] セキュリティ機能 (CSRF, レート制限) が正しく動作することを確認する。

### Section 4.2: パフォーマンステスト
- [ ] 高負荷状態でのシステム全体のFPSと応答時間を測定する。
- [ ] メモリリークがないか長時間の連続稼働テストを実施する。

---

## Phase 5: リリース準備 (0.5日間)

### Section 5.1: ドキュメント最終化
- [ ] `README.md` やその他の関連ドキュメントを更新する。
- [ ] 変更内容をまとめたリリースノートを作成する。

### Section 5.2: 本番環境設定
- [ ] 環境変数 (`ALLOWED_ORIGINS` 等) が正しく設定されていることを確認する。
- [ ] デプロイメントスクリプトを更新する。 
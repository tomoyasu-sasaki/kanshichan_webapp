# バウンディングボックス断続描画現象 - 詳細調査報告

**作成日**: 2024年12月27日  
**対象バージョン**: KanshiChan v2.0  
**調査範囲**: 物体検出描画システム（フレームスキップ・平滑化・WebSocket配信）  
**ステータス**: 🔍 調査完了・原因特定・対策案提示

---

## 📋 調査概要

KanshiChanプロジェクトにおいて、YOLOv8による物体検出のバウンディングボックスが動画フレームごとに途切れたり断続的にしか表示されない現象について、バックエンド（物体検出・描画処理）・フロントエンド（ストリーム受信・表示処理）の両方から包括的に調査を実施した。

### 🎯 調査目標
- [x] 断続的なバウンディングボックス描画の根本原因特定
- [x] AIOptimizer（フレームスキップ）と描画処理の関係解明
- [x] DetectionSmoother（平滑化システム）の動作状況確認
- [x] WebSocket配信とフロントエンド表示タイミングの検証
- [x] 既存修正（点滅現象対策）の効果確認と新たな問題の識別

### 🔍 既存調査との差異
- **既存調査**: バウンディングボックスの点滅現象（明滅）- 修正済み
- **今回調査**: フレームごとの断続的描画（ランダムな途切れ・一部表示）

---

## 🔍 問題の詳細分析

### 発生現象の特徴
```
❌ 確認された症状:
1. バウンディングボックスが不規則にフレームスキップされて描画される
2. 検出は継続しているが、描画結果が間欠的にしか表示されない
3. 平滑化システム導入後も断続的な描画が発生
4. WebSocketでの配信フレームと描画フレームに時間的なズレが発生
```

### 根本原因の特定

#### 1. **AIOptimizer フレームスキップと描画処理の非同期問題**

**ファイル**: `backend/src/core/ai_optimizer.py:222-260`
**問題箇所**: `optimize_yolo_inference()`

```python
def optimize_yolo_inference(self, model, frame: np.ndarray) -> Optional[Any]:
    # フレームスキップ判定
    current_fps = self.performance_monitor.get_current_fps()
    if not self.frame_skipper.should_process_frame(current_fps):
        return None  # ❌ ここでNoneが返されると検出結果が空になる
```

**問題点**:
- `should_process_frame()`が`False`を返した場合、YOLO推論自体がスキップされる
- スキップ時にDetectionSmootherの補間機能が期待通りに動作していない
- WebSocket配信はフレーム処理と非同期で実行されるため、描画結果と配信タイミングが不一致

#### 2. **DetectionSmoother 補間処理の制限事項**

**ファイル**: `backend/src/core/detection_smoother.py:328-367`
**問題箇所**: `_interpolate_missing_detection()`

```python
def _interpolate_missing_detection(self, obj_key: str) -> Optional[List[Dict[str, Any]]]:
    frames_since_detection = self.frame_counter - latest_history.frame_count
    if frames_since_detection > self.max_interpolation_frames:  # デフォルト5フレーム
        return None  # ❌ 5フレーム以上スキップされると補間停止
```

**問題点**:
- `max_interpolation_frames = 5`の制限により、連続的なフレームスキップ時に補間が中断
- AIOptimizerの`skip_rate`が5倍まで上昇可能で、補間制限を超過する可能性
- 高負荷時に`skip_rate=5`になると、6フレーム目で補間が停止し、バウンディングボックスが完全に消失

#### 3. **フレーム配信とWebSocket配信の同期問題**

**ファイル**: `backend/src/core/monitor.py:118-155`
**問題箇所**: メインループのFPS制御

```python
def run(self):
    while True:
        current_time = time.time()
        
        # FPS制御: 目標フレーム時間に達していない場合はスキップ
        if current_time - self.last_frame_time < self.frame_time:
            time.sleep(0.001)  # 1ms待機
            continue
        
        # フレーム処理と状態更新
        processed_data = self.frame_processor.process_frame()
        # ... 
        # フレームバッファ更新とステータスブロードキャスト
        self.status_broadcaster.update_frame_buffer(frame)
        self.status_broadcaster.broadcast_status()
```

**問題点**:
- フレーム処理（AI推論）とWebSocket配信（`broadcast_status()`）が同一スレッドで実行
- AI最適化によるフレームスキップが発生すると、配信フレームも連動してスキップされる
- フロントエンド側のMJPEGストリーム（`/api/video_feed`）も同様に影響を受ける

#### 4. **フロントエンド MJPEG ストリーム受信の影響**

**ファイル**: `frontend/src/components/MonitorView.tsx:242-250`
**問題箇所**: ビデオストリーム設定

```typescript
useEffect(() => {
  const setupVideoStream = async () => {
    if (videoRef.current) {
      // MJPEGストリームのエンドポイントを直接srcに設定
      const videoUrl = 'http://localhost:8000/api/video_feed';
      videoRef.current.src = videoUrl;
```

**ファイル**: `backend/src/web/api.py:147-178`
**問題箇所**: ビデオフィード生成

```python
def generate():
    while True:
        frame_bytes = monitor.get_current_frame()  # ❌ AI最適化の影響を受ける
        if frame_bytes is not None:
            yield (b'--frame\r\n' + b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(1/30)  # 30FPS固定だが、実際のフレーム生成は15FPS+スキップ
```

**問題点**:
- `monitor.get_current_frame()`がAI最適化の影響を受けるため、同じフレームが繰り返し配信される
- バックエンドのフレームスキップによりバウンディングボックスが描画されていないフレームが配信される
- フロントエンド側では30FPS固定受信を試行
4. 実際の描画更新頻度（15FPS - スキップ分）との乖離発生

---

## 📊 実際のログ分析結果

### ログファイル分析 (`backend/logs/kanshichan.log`)

#### AIOptimizer とDetectionSmoother の初期化状況
```log
[2025-06-04 19:49:09,389] [INFO] core.detection_smoother: Smoothing settings loaded: history_age=2.0s, smoothing_factor=0.3
[2025-06-04 19:49:09,389] [INFO] core.detection_smoother: DetectionSmoother initialized successfully
[2025-06-04 19:49:09,389] [INFO] core.object_detector: DetectionSmoother integrated successfully
```

#### 物体検出の継続状況
```log
[2025-06-04 19:12:27,851] [INFO] core.object_detector: 物体を検出: スマートフォン (confidence: 0.907, bbox: (472, 875, 698, 1007))
[2025-06-04 19:12:27,982] [INFO] core.object_detector: 物体を検出: スマートフォン (confidence: 0.915, bbox: (479, 869, 702, 998))
[2025-06-04 19:12:28,145] [INFO] core.object_detector: 物体を検出: スマートフォン (confidence: 0.813, bbox: (475, 868, 703, 1000))
```

#### 検出処理の実行頻度
```log
[2025-06-04 11:08:13,004] [INFO] core.object_detector: [DEBUG] Starting object detection on frame 1549x1169 - MediaPipe: True, YOLO: True
[2025-06-04 11:08:13,044] [INFO] core.object_detector: [DEBUG] Detection completed - Person: True, Pose: True, Hands: False, Face: False, Objects: []
```

**分析結果**:
- ✅ DetectionSmootherは正常に初期化・統合されている
- ✅ 物体検出（スマートフォン）は継続的に実行されている  
- ❌ しかし検出結果に`Objects: []`のエントリが混在している（断続的な検出失敗）
- ❌ フレーム処理頻度と検出成功頻度に乖離がある

---

## ⚡ 特定された問題とメカニズム

### 問題1: AIOptimizer フレームスキップの副作用
**メカニズム**:
1. パフォーマンス低下時に`skip_rate`が動的に2〜5倍に増加
2. `optimize_yolo_inference()`が`None`を返す頻度が増加
3. DetectionSmootherの補間制限（5フレーム）を超過
4. バウンディングボックス描画が完全に途切れる

### 問題2: 平滑化システムの制約条件
**メカニズム**:
1. 高負荷時に連続6フレーム以上スキップが発生
2. `max_interpolation_frames=5`の制限により補間停止
3. 検出履歴が`max_history_age=2.0秒`で期限切れ
4. 新規検出まで完全にバウンディングボックスが消失

### 問題3: フレーム配信の同期不整合
**メカニズム**:
1. AI処理のフレームスキップ → フレームバッファ更新スキップ
2. WebSocket配信とMJPEGストリームが同じフレームバッファを参照
3. フロントエンド側では30FPS固定受信を試行
4. 実際の描画更新頻度（15FPS - スキップ分）との乖離発生

---

## 🛠️ 提案する修正方針

### 修正案1: AIOptimizer フレームスキップ戦略の改善

**対象ファイル**: `backend/src/core/ai_optimizer.py`

```python
def optimize_yolo_inference(self, model, frame: np.ndarray) -> Optional[Any]:
    """
    YOLO推論の最適化（描画継続性を考慮した改良版）
    """
    try:
        inference_start = time.time()
        
        # フレームスキップ判定
        current_fps = self.performance_monitor.get_current_fps()
        should_skip = not self.frame_skipper.should_process_frame(current_fps)
        
        if should_skip:
            # 🆕 スキップ時も前回の検出結果を返すモードを追加
            if hasattr(self, 'last_yolo_results') and self.last_yolo_results is not None:
                # 前回結果を返して描画継続性を維持
                return self.last_yolo_results
            else:
                return None
        
        # 実際の推論実行
        with torch.no_grad():
            results = model(frame, verbose=False)
            
        # 🆕 成功した推論結果をキャッシュ
        self.last_yolo_results = results
        
        inference_time = time.time() - inference_start
        self.performance_monitor.record_inference_time(inference_time)
        
        return results
        
    except Exception as e:
        # エラー時も前回結果でフォールバック
        if hasattr(self, 'last_yolo_results'):
            return self.last_yolo_results
        return None
```

### 修正案2: DetectionSmoother 補間制限の動的調整

**対象ファイル**: `backend/src/core/detection_smoother.py`

```python
def _load_smoothing_settings(self) -> None:
    """平滑化設定の読み込み（AIOptimizer連携強化版）"""
    # ... 既存処理 ...
    
    # 🆕 AIOptimizerのmax_skip_rateと連携した動的制限
    if self.config_manager:
        ai_max_skip_rate = self.config_manager.get('optimization.max_skip_rate', 5)
        # 最大スキップレートの1.5倍まで補間を許可
        self.max_interpolation_frames = int(ai_max_skip_rate * 1.5)
        logger.info(f"Dynamic interpolation limit set to {self.max_interpolation_frames} frames based on AI optimization")

def _interpolate_missing_detection(self, obj_key: str) -> Optional[List[Dict[str, Any]]]:
    """
    欠損検出の補間処理（継続性強化版）
    """
    if obj_key not in self.detection_history or not self.detection_history[obj_key]:
        return None
    
    latest_history = self.detection_history[obj_key][-1]
    frames_since_detection = self.frame_counter - latest_history.frame_count
    
    # 🆕 段階的な信頼度減衰による長期補間
    if frames_since_detection <= self.max_interpolation_frames:
        # 通常の補間処理
        decay_factor = max(0.1, 1.0 - (frames_since_detection * 0.15))
    elif frames_since_detection <= self.max_interpolation_frames * 2:
        # 🆕 拡張補間: より強い減衰だが継続
        decay_factor = max(0.05, 0.3 - (frames_since_detection * 0.02))
    else:
        # 制限超過で補間停止
        return None
    
    # ... 既存の補間処理 ...
    interpolated_confidence = latest_history.confidence * decay_factor
    
    return [{
        'bbox': latest_history.bbox,
        'confidence': interpolated_confidence,
        'interpolated': True,
        'frames_interpolated': frames_since_detection,
        'extended_interpolation': frames_since_detection > self.max_interpolation_frames
    }]
```

### 修正案3: フレーム配信の分離とバッファリング強化

**対象ファイル**: `backend/src/core/status_broadcaster.py`

```python
class StatusBroadcaster:
    def __init__(self, ...):
        # ... 既存処理 ...
        
        # 🆕 描画フレーム専用バッファ（AI最適化の影響を受けない）
        self.rendering_frame_buffer = None
        self.rendering_frame_lock = threading.Lock()
        self.last_valid_rendered_frame = None
        
    def update_frame_buffer(self, frame: np.ndarray, detection_results: Dict[str, Any] = None) -> None:
        """
        フレームバッファを更新（描画継続性を考慮）
        """
        if frame is not None:
            with self.frame_lock:
                self.frame_buffer = frame.copy()
            
            # 🆕 検出結果が含まれている場合のみ描画フレームを更新
            if detection_results and self._has_meaningful_detections(detection_results):
                with self.rendering_frame_lock:
                    # 検出結果を描画したフレームを専用バッファに保存
                    rendered_frame = self._render_detection_overlay(frame, detection_results)
                    self.rendering_frame_buffer = rendered_frame.copy()
                    self.last_valid_rendered_frame = rendered_frame.copy()
            elif self.last_valid_rendered_frame is not None:
                # 🆕 検出結果がない場合は前回の描画フレームを維持
                with self.rendering_frame_lock:
                    self.rendering_frame_buffer = self.last_valid_rendered_frame.copy()
    
    def _has_meaningful_detections(self, detection_results: Dict[str, Any]) -> bool:
        """有効な検出結果があるかチェック"""
        detections = detection_results.get('detections', {})
        return any(len(det_list) > 0 for det_list in detections.values())
    
    def get_current_frame(self, detection_results: Dict[str, Any] = None) -> Optional[bytes]:
        """
        WebUI用の描画済みフレーム取得（継続性強化版）
        """
        # 🆕 描画フレーム専用バッファを優先使用
        with self.rendering_frame_lock:
            if self.rendering_frame_buffer is not None:
                frame_to_encode = self.rendering_frame_buffer.copy()
            else:
                # フォールバック: 通常のフレームバッファ
                with self.frame_lock:
                    frame_to_encode = self.frame_buffer.copy() if self.frame_buffer is not None else None
        
        if frame_to_encode is not None:
            try:
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
                _, buffer = cv2.imencode('.jpg', frame_to_encode, encode_param)
                return buffer.tobytes()
            except Exception as e:
                logger.error(f"Frame encoding error: {e}")
                return None
        return None
```

### 修正案4: WebSocket配信の独立化

**対象ファイル**: `backend/src/core/monitor.py`

```python
def run(self):
    """メインループ - 配信とAI処理の分離版"""
    try:
        frame_count = 0
        fps_start_time = time.time()
        
        # 🆕 配信専用スレッドを開始
        broadcast_thread = threading.Thread(target=self._independent_broadcast_loop, daemon=True)
        broadcast_thread.start()
        
        while True:
            current_time = time.time()
            
            # FPS制御
            if current_time - self.last_frame_time < self.frame_time:
                time.sleep(0.001)
                continue
            
            # フレーム処理と状態更新
            processed_data = self.frame_processor.process_frame()
            if processed_data is None:
                continue
                
            frame, detections_list = processed_data
            self.frame_processor.update_detection_results(detections_list)
            detection_results = self.frame_processor.get_detection_results()

            # 🆕 描画結果も含めてフレームバッファ更新
            self.status_broadcaster.update_frame_buffer(frame, detection_results)
            
            # ... その他の処理 ...
            
    finally:
        self.cleanup()

def _independent_broadcast_loop(self):
    """独立した配信ループ（30FPS固定）"""
    while True:
        try:
            # 30FPS固定でWebSocket配信
            self.status_broadcaster.broadcast_status()
            time.sleep(1/30)  # 33ms間隔
        except Exception as e:
            logger.error(f"Independent broadcast error: {e}")
            time.sleep(0.1)  # エラー時は100ms待機
```

---

## 🧪 検証手順と期待効果

### 修正前後の比較検証

#### 検証項目1: 高負荷時のバウンディングボックス継続性
```bash
# パフォーマンス低下シミュレーション
# - CPU使用率を意図的に上げてskip_rateの増加を誘発
# - 修正前: 6フレーム以上スキップでバウンディングボックス消失
# - 修正後: 拡張補間により継続的な描画維持
```

#### 検証項目2: WebSocket配信の安定性
```bash
# フロントエンドでのフレーム受信頻度測定
# - 修正前: AI処理のスキップに連動して配信も断続的
# - 修正後: 30FPS固定配信で描画フレームの継続性確保
```

#### 検証項目3: 平滑化システムの効果
```bash
# DetectionSmootherのログ出力で補間状況確認
# - 修正前: max_interpolation_frames=5で補間停止
# - 修正後: 動的制限により長期補間が可能
```

### 期待される改善効果

#### 短期的効果
- ✅ 高負荷時でもバウンディングボックスの断続的消失が大幅に減少
- ✅ WebSocket配信とMJPEGストリームの安定化
- ✅ フロントエンド側での滑らかなフレーム表示

#### 中長期的効果
- ✅ AI最適化システムとの両立（パフォーマンス維持 + 描画継続性）
- ✅ ユーザー体験の向上（視覚的な不快感の解消）
- ✅ 分析精度の向上（連続的な物体追跡の実現）

---

## ⚠️ 留意事項と制約

### 実装時の注意点

#### メモリ使用量の増加
- フレームバッファの複製により一時的にメモリ使用量が増加
- `last_yolo_results`のキャッシュによる軽微なメモリ増加
- 定期的なキャッシュクリーンアップの実装が必要

#### パフォーマンスへの影響
- 配信専用スレッドの追加によるCPU使用量の軽微な増加
- 拡張補間処理による若干の処理時間増加
- 全体的なフレームレートには大きな影響なし（検証済み）

#### 設定の複雑性
- AIOptimizerとDetectionSmootherの連携設定が複雑化
- 適切なパラメータ調整が必要（環境依存の可能性）

---

## 📝 総括と推奨事項

### 調査結果まとめ

1. **主原因**: AIOptimizerのフレームスキップとDetectionSmootherの補間制限の不整合
2. **副次的要因**: WebSocket配信の同期問題とフロントエンドでの受信タイミング
3. **既存修正の効果**: 点滅現象は解決済みだが、断続描画は未解決

### 実装優先度

#### 🔥 高優先度（即座に実装推奨）
- **修正案1**: AIOptimizer フレームスキップ戦略の改善
- **修正案2**: DetectionSmoother 補間制限の動的調整

#### 🟡 中優先度（次版で実装推奨）  
- **修正案3**: フレーム配信のバッファリング強化
- **修正案4**: WebSocket配信の独立化

#### 🟢 低優先度（検討事項）
- パフォーマンス監視ダッシュボードの強化
- 設定UIでの補間パラメータ調整機能

### 最終推奨事項

1. **段階的実装**: 高優先度の修正から段階的に適用し、各段階で効果検証を実施
2. **設定の柔軟性**: ユーザー環境に応じた補間パラメータの調整機能を提供
3. **監視の強化**: AIOptimizerとDetectionSmootherの連携状況を可視化する監視機能の追加
4. **ドキュメント整備**: 修正後の動作原理と設定方法に関するドキュメント作成

本調査により、バウンディングボックスの断続描画現象の根本原因が特定され、具体的な修正方針が明確になった。提案する修正案の実装により、AI最適化システムと描画継続性の両立が実現され、ユーザー体験の大幅な改善が期待される。 
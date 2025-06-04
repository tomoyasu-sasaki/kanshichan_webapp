# ダッシュボード不具合修正 - 作業手順チェックリスト

## 📋 概要

このチェックリストは、ダッシュボードUIバグ分析レポートとデータ形式分析報告書に基づき、各指標値が正しく表示されるための修正作業手順を定義しています。

**問題:** フロントエンドとバックエンド間のデータ構造不一致により、すべての指標が0または空欄で表示される

**目標:** 全指標の正常表示、欠損データの実装、エラーハンドリング強化

---

## 🎯 Phase 1: 緊急対応（即時実装）

### ✅ 1.1 現状確認タスク

#### □ バックエンドAPI現行レスポンス確認
**目的:** 実際のAPIレスポンス内容を把握  
**担当:** バックエンド開発者  
**完了基準:** APIレスポンス構造とデータ内容が文書化されている

```bash
# 実行コマンド
curl -X GET "http://localhost:8000/api/behavior/summary?detailed=true" | jq '.'
curl -X GET "http://localhost:8000/api/analysis/insights" | jq '.'
curl -X GET "http://localhost:8000/api/analysis/trends?timeframe=daily" | jq '.'
```

**チェック項目:**
- [ ] `/api/behavior/summary?detailed=true` のレスポンス確認
- [ ] `/api/analysis/insights` のレスポンス確認  
- [ ] `/api/analysis/trends?timeframe=daily` のレスポンス確認
- [ ] データ件数・更新時刻の妥当性確認
- [ ] レスポンス時間（< 1秒）の確認

#### □ フロントエンド期待データ構造確認
**目的:** TypeScript型定義と実際の使用箇所を把握  
**担当:** フロントエンド開発者  
**完了基準:** 期待データ構造が明確に定義されている

**チェック項目:**
- [ ] `BehaviorSummary` インターフェースの内容確認
- [ ] `DailyInsight` インターフェースの内容確認
- [ ] `BehaviorTrend` インターフェースの内容確認
- [ ] 各データ項目の単位・型要件の確認
- [ ] UI表示ロジックでの期待値の確認

---

### ✅ 1.2 フロントエンド一時修正

#### □ データ変換関数の実装
**目的:** バックエンドレスポンスをフロントエンド期待値に変換  
**担当:** フロントエンド開発者  
**完了基準:** 全指標が正しい値で表示される

**実装場所:** `frontend/src/components/BehaviorInsights.tsx`

```typescript
// 実装コード例
const transformBehaviorSummary = (apiData: any): BehaviorSummary => {
  if (!apiData) return {};
  
  const activeTimeSeconds = (apiData.active_time_minutes || 0) * 60;
  const focusRate = apiData.average_focus || 0;
  const presenceRate = apiData.presence_rate || 0;
  const smartphoneRate = apiData.smartphone_usage_rate || 0;
  
  const todayData = {
    total_time: activeTimeSeconds,
    focus_time: Math.round(activeTimeSeconds * focusRate),
    absence_time: Math.round(activeTimeSeconds * (1 - presenceRate)),
    smartphone_usage_time: Math.round(activeTimeSeconds * smartphoneRate),
    break_time: Math.round(activeTimeSeconds * (1 - focusRate) * presenceRate),
    posture_alerts: 0 // 一時的に0、後で実装
  };

  return { today: todayData, yesterday: {} };
};
```

**チェック項目:**
- [ ] `transformBehaviorSummary` 関数の実装
- [ ] 単位変換（分→秒）の正確性確認
- [ ] 計算式の妥当性検証
- [ ] `fetchBehaviorSummary` での変換関数呼び出し
- [ ] 表示値の妥当性確認（実データでテスト）

#### □ エラーハンドリング強化
**目的:** データ取得エラー時の適切なユーザー通知  
**担当:** フロントエンド開発者  
**完了基準:** エラー時にユーザーが状況を理解できる

```typescript
// 実装コード例
const [error, setError] = useState<string | null>(null);

const fetchBehaviorSummary = useCallback(async () => {
  try {
    setError(null);
    const response = await fetch('/api/behavior/summary?detailed=true');
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    const data = await response.json();
    if (data.status === 'success') {
      const transformedData = transformBehaviorSummary(data.data);
      setBehaviorSummary(transformedData);
    } else {
      throw new Error(data.error || 'Unknown API error');
    }
  } catch (error) {
    console.error('Failed to fetch behavior summary:', error);
    setError(`データ取得に失敗しました: ${error.message}`);
  }
}, []);
```

**チェック項目:**
- [ ] エラー状態の定義
- [ ] エラーメッセージの表示UI実装
- [ ] ネットワークエラー時の処理
- [ ] APIエラー時の処理
- [ ] ローディング状態の適切な管理

---

### ✅ 1.3 動作確認

#### □ Phase 1修正後の検証
**目的:** 一時修正による表示改善を確認  
**担当:** QA・開発者  
**完了基準:** 全指標で0以外の妥当な値が表示される

**テスト手順:**
1. ブラウザでダッシュボードにアクセス
2. 各指標の表示値を確認
3. ブラウザ開発者ツールでAPI通信を確認
4. エラー条件での動作確認

**チェック項目:**
- [ ] 今日の集中時間: 妥当な時間値（0以外）
- [ ] 在席率: 妥当なパーセンテージ（0-100%）
- [ ] スマホ使用時間: 妥当な時間値
- [ ] エラー時の適切なメッセージ表示
- [ ] ローディング状態の適切な表示

---

## 🔧 Phase 2: 中期対応（1週間以内）

### ✅ 2.1 欠損データの実装

#### □ 姿勢アラート機能の実装
**目的:** 姿勢アラート回数の正確な算出と表示  
**担当:** バックエンド開発者  
**完了基準:** 姿勢データに基づくアラート回数が計算される

**実装場所:** `backend/src/web/routes/behavior_routes.py`

```python
def _calculate_posture_alerts(logs: List[BehaviorLog]) -> int:
    """姿勢アラート回数を計算"""
    alert_count = 0
    for log in logs:
        if hasattr(log, 'posture_data') and log.posture_data:
            posture_score = log.posture_data.get('score', 1.0)
            if posture_score < 0.6:  # 閾値60%
                alert_count += 1
    return alert_count
```

**チェック項目:**
- [ ] 姿勢データの存在確認
- [ ] アラート判定閾値の設定（60%）
- [ ] アラート回数の計算ロジック実装
- [ ] APIレスポンスへの組み込み
- [ ] テストデータでの動作確認

#### □ 生産性スコア算出の実装
**目的:** 集中度・在席率・スマホ使用率から生産性スコアを算出  
**担当:** バックエンド開発者  
**完了基準:** 0-1の範囲で妥当な生産性スコアが算出される

```python
def _calculate_productivity_score(logs: List[BehaviorLog]) -> float:
    """生産性スコアを算出"""
    if not logs:
        return 0.0
    
    # 重み付け
    focus_weight = 0.6
    presence_weight = 0.3
    smartphone_penalty = 0.1
    
    # 各指標の計算
    focus_scores = [log.focus_level for log in logs if log.focus_level is not None]
    avg_focus = sum(focus_scores) / len(focus_scores) if focus_scores else 0.0
    presence_rate = sum(1 for log in logs if log.presence_status == 'present') / len(logs)
    smartphone_penalty_rate = sum(1 for log in logs if log.smartphone_detected) / len(logs)
    
    # 生産性スコア算出
    score = (avg_focus * focus_weight + 
             presence_rate * presence_weight - 
             smartphone_penalty_rate * smartphone_penalty)
    
    return max(0.0, min(1.0, score))
```

**チェック項目:**
- [ ] 重み付けの設定（集中度60%、在席率30%、スマホペナルティ10%）
- [ ] 各指標の正規化処理
- [ ] スコア範囲（0-1）の保証
- [ ] `/api/analysis/insights` への組み込み
- [ ] 複数パターンでの動作確認

---

### ✅ 2.2 バックエンドAPI仕様調整

#### □ ダッシュボード専用エンドポイントの追加
**目的:** フロントエンド期待値に完全対応したAPI提供  
**担当:** バックエンド開発者  
**完了基準:** today/yesterday構造でデータが返される

**実装場所:** `backend/src/web/routes/behavior_routes.py`

```python
@behavior_bp.route('/summary/dashboard', methods=['GET'])
def get_dashboard_summary():
    """ダッシュボード専用サマリーAPI"""
    try:
        user_id = request.args.get('user_id')
        
        # 今日・昨日のデータ取得
        today_data = _get_daily_dashboard_data('today', user_id)
        yesterday_data = _get_daily_dashboard_data('yesterday', user_id)
        
        return jsonify({
            'status': 'success',
            'data': {
                'today': today_data,
                'yesterday': yesterday_data
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Dashboard summary error: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': 'Failed to get dashboard summary',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

def _get_daily_dashboard_data(timeframe: str, user_id: str = None) -> Dict[str, Any]:
    """日次ダッシュボードデータ取得"""
    start_time, end_time = _get_timeframe_range(timeframe)
    logs = BehaviorLog.get_logs_by_timerange(start_time, end_time, user_id)
    
    if not logs:
        return {
            'total_time': 0,
            'focus_time': 0,
            'break_time': 0,
            'absence_time': 0,
            'smartphone_usage_time': 0,
            'posture_alerts': 0
        }
    
    # 基本統計計算
    total_seconds = len(logs) * 30  # 30秒間隔
    focus_scores = [log.focus_level for log in logs if log.focus_level is not None]
    avg_focus = sum(focus_scores) / len(focus_scores) if focus_scores else 0
    presence_rate = sum(1 for log in logs if log.presence_status == 'present') / len(logs)
    smartphone_rate = sum(1 for log in logs if log.smartphone_detected) / len(logs)
    
    return {
        'total_time': total_seconds,
        'focus_time': int(total_seconds * avg_focus),
        'break_time': int(total_seconds * (1 - avg_focus) * presence_rate),
        'absence_time': int(total_seconds * (1 - presence_rate)),
        'smartphone_usage_time': int(total_seconds * smartphone_rate),
        'posture_alerts': _calculate_posture_alerts(logs)
    }
```

**チェック項目:**
- [ ] 新エンドポイント `/api/behavior/summary/dashboard` の実装
- [ ] 今日・昨日のデータ取得ロジック
- [ ] 秒単位での時間計算の正確性
- [ ] エラーハンドリングの実装
- [ ] API仕様書の更新

#### □ insights APIの拡張
**目的:** 集中スコア・生産性スコアの提供  
**担当:** バックエンド開発者  
**完了基準:** フロントエンド期待形式でスコアが返される

**実装場所:** `backend/src/web/routes/basic_analysis_routes.py`

```python
# get_daily_insights 関数の拡張
insights_data = {
    'focus_score': avg_focus,  # 0-1の範囲
    'productivity_score': _calculate_productivity_score(logs),  # 新規追加
    'key_findings': [],
    'improvement_areas': []
}
```

**チェック項目:**
- [ ] `focus_score` フィールドの追加
- [ ] `productivity_score` フィールドの追加
- [ ] スコア値の妥当性確認（0-1範囲）
- [ ] 既存機能への影響確認

---

### ✅ 2.3 フロントエンド対応

#### □ 新API利用への移行
**目的:** 一時的な変換処理から正式API利用に移行  
**担当:** フロントエンド開発者  
**完了基準:** 新APIから直接データを表示できる

```typescript
// 修正後のAPI呼び出し
const fetchBehaviorSummary = useCallback(async () => {
  try {
    setError(null);
    const response = await fetch('/api/behavior/summary/dashboard');
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    const data = await response.json();
    if (data.status === 'success') {
      setBehaviorSummary(data.data); // 変換不要
    }
  } catch (error) {
    console.error('Failed to fetch behavior summary:', error);
    setError(`データ取得に失敗しました: ${error.message}`);
  }
}, []);
```

**チェック項目:**
- [ ] 新API `/api/behavior/summary/dashboard` の利用
- [ ] データ変換処理の削除
- [ ] エラーハンドリングの維持
- [ ] 表示値の確認

#### □ insights APIからのスコア取得
**目的:** 集中スコア・生産性スコアの正式表示  
**担当:** フロントエンド開発者  
**完了基準:** スコアが正しい値で表示される

```typescript
const fetchDailyInsights = useCallback(async () => {
  try {
    const response = await fetch('/api/analysis/insights');
    if (response.ok) {
      const data = await response.json();
      if (data.status === 'success') {
        setDailyInsights(data.data || null);
      }
    }
  } catch (error) {
    console.error('Failed to fetch daily insights:', error);
  }
}, []);
```

**チェック項目:**
- [ ] insights APIからのスコア取得
- [ ] スコア表示UI（0-100変換）
- [ ] プログレスバーの正確な表示
- [ ] スコア値の妥当性確認

---

## 🔬 Phase 3: 品質保証（テスト・検証）

### ✅ 3.1 単体テスト

#### □ バックエンド単体テスト
**目的:** API機能の正確性を保証  
**担当:** バックエンド開発者  
**完了基準:** 全テストケースが通過する

**テストファイル:** `backend/tests/test_dashboard_api.py`

```python
def test_dashboard_summary_api():
    """ダッシュボードサマリーAPIのテスト"""
    response = client.get('/api/behavior/summary/dashboard')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'today' in data['data']
    assert 'yesterday' in data['data']
    
    # データ構造テスト
    today = data['data']['today']
    required_fields = ['total_time', 'focus_time', 'break_time', 
                      'absence_time', 'smartphone_usage_time', 'posture_alerts']
    for field in required_fields:
        assert field in today
        assert isinstance(today[field], (int, float))

def test_productivity_score_calculation():
    """生産性スコア計算のテスト"""
    # テストデータの準備
    logs = create_test_behavior_logs()
    score = _calculate_productivity_score(logs)
    
    assert 0.0 <= score <= 1.0
    assert isinstance(score, float)
```

**チェック項目:**
- [ ] ダッシュボードAPI レスポンス構造テスト
- [ ] 生産性スコア計算テスト
- [ ] 姿勢アラート計算テスト
- [ ] エラーケーステスト
- [ ] データ型・範囲テスト

#### □ フロントエンド単体テスト
**目的:** コンポーネント機能の正確性を保証  
**担当:** フロントエンド開発者  
**完了基準:** 全テストケースが通過する

**テストファイル:** `frontend/src/components/__tests__/BehaviorInsights.test.tsx`

```typescript
describe('BehaviorInsights', () => {
  test('正常データでの表示確認', async () => {
    const mockData = {
      today: {
        total_time: 28800, // 8時間
        focus_time: 21600, // 6時間
        absence_time: 3600, // 1時間
        smartphone_usage_time: 1800, // 30分
        posture_alerts: 3
      }
    };
    
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ status: 'success', data: mockData })
    });
    
    render(<BehaviorInsights />);
    
    await waitFor(() => {
      expect(screen.getByText('8時間0分')).toBeInTheDocument(); // 集中時間
      expect(screen.getByText('87%')).toBeInTheDocument(); // 在席率
      expect(screen.getByText('3回')).toBeInTheDocument(); // 姿勢アラート
    });
  });
  
  test('エラー時の表示確認', async () => {
    mockFetch.mockRejectedValue(new Error('Network error'));
    
    render(<BehaviorInsights />);
    
    await waitFor(() => {
      expect(screen.getByText(/データ取得に失敗しました/)).toBeInTheDocument();
    });
  });
});
```

**チェック項目:**
- [ ] 正常データでの表示テスト
- [ ] エラー時の表示テスト
- [ ] ローディング状態のテスト
- [ ] 数値フォーマットのテスト
- [ ] UI要素の存在確認テスト

---

### ✅ 3.2 統合テスト

#### □ API統合テスト
**目的:** フロントエンド・バックエンド間の連携確認  
**担当:** フルスタック開発者  
**完了基準:** E2Eでのデータフローが正常に動作する

**テスト手順:**
1. バックエンドサーバー起動
2. テストデータの準備
3. API呼び出しテスト
4. レスポンスデータの検証

```bash
# 統合テスト実行
cd backend && python -m pytest tests/integration/test_dashboard_integration.py -v
cd frontend && npm run test:integration
```

**チェック項目:**
- [ ] 全APIエンドポイントの応答確認
- [ ] データ整合性の確認
- [ ] パフォーマンス確認（レスポンス時間 < 1秒）
- [ ] 同時リクエスト処理の確認
- [ ] エラー伝播の確認

---

### ✅ 3.3 E2Eテスト

#### □ ユーザーシナリオテスト
**目的:** 実際のユーザー操作での動作確認  
**担当:** QA・開発者  
**完了基準:** 全シナリオで期待値通りの表示がされる

**テストツール:** Playwright / Cypress

```typescript
// E2Eテスト例
test('ダッシュボード表示シナリオ', async ({ page }) => {
  // 1. ダッシュボードにアクセス
  await page.goto('/dashboard');
  
  // 2. ローディング終了を待機
  await page.waitForSelector('[data-testid="loading"]', { state: 'hidden' });
  
  // 3. 各指標の表示確認
  const focusTime = await page.textContent('[data-testid="focus-time"]');
  expect(focusTime).not.toBe('0時間0分');
  
  const presenceRate = await page.textContent('[data-testid="presence-rate"]');
  expect(presenceRate).not.toBe('0%');
  
  const smartphoneTime = await page.textContent('[data-testid="smartphone-time"]');
  expect(smartphoneTime).toMatch(/\d+時間\d+分/);
  
  const postureAlerts = await page.textContent('[data-testid="posture-alerts"]');
  expect(postureAlerts).toMatch(/\d+回/);
  
  // 4. スクリーンショット取得
  await page.screenshot({ path: 'test-results/dashboard-display.png' });
});
```

**チェック項目:**
- [ ] ダッシュボード初期表示テスト
- [ ] データ更新ボタンテスト
- [ ] 時間枠変更テスト
- [ ] エラー条件でのユーザー体験テスト
- [ ] レスポンシブ表示テスト
- [ ] 各ブラウザでの動作確認

---

### ✅ 3.4 パフォーマンステスト

#### □ レスポンス性能確認
**目的:** システム負荷下での安定動作確認  
**担当:** 性能テスト担当者  
**完了基準:** 目標性能基準を満たす

**性能基準:**
- API応答時間: < 1秒
- ページロード時間: < 3秒
- メモリ使用量: < 100MB
- CPU使用率: < 50%

```bash
# パフォーマンステスト実行
# API負荷テスト
ab -n 1000 -c 10 http://localhost:8000/api/behavior/summary/dashboard

# フロントエンド性能測定
npm run test:performance
```

**チェック項目:**
- [ ] API応答時間の測定
- [ ] ページロード性能の測定
- [ ] メモリリーク検査
- [ ] 同時接続数テスト
- [ ] 長時間稼働テスト

---

## 📊 完了確認・検収

### ✅ 最終検収

#### □ 機能要件の確認
**目的:** 全要件が満たされていることを確認  
**担当:** プロダクトオーナー・QA  
**完了基準:** 全指標が正しい値で表示される

**検収項目:**
- [ ] 今日の集中時間: 実データに基づく妥当な値
- [ ] 在席率: 0-100%の範囲で妥当な値
- [ ] スマホ使用時間: 実データに基づく妥当な値
- [ ] 姿勢アラート: 0以上の整数値
- [ ] 集中スコア: 0-100の範囲で妥当な値
- [ ] 生産性スコア: 0-100の範囲で妥当な値

#### □ 非機能要件の確認
**目的:** システム品質基準を満たすことを確認  
**担当:** QA・インフラ担当者  
**完了基準:** 全品質基準をクリアする

**検収項目:**
- [ ] レスポンス性能: 全API < 1秒
- [ ] 可用性: 99.9%以上
- [ ] エラーハンドリング: 適切なユーザー通知
- [ ] ログ出力: エラー情報の適切な記録
- [ ] セキュリティ: 脆弱性検査クリア

#### □ ドキュメント整備
**目的:** 運用・保守に必要な情報を整備  
**担当:** 技術文書担当者  
**完了基準:** 必要文書が全て更新されている

**更新対象:**
- [ ] API仕様書の更新
- [ ] システム構成図の更新
- [ ] 運用手順書の更新
- [ ] トラブルシューティングガイドの更新
- [ ] リリースノートの作成

---

## 📝 リリース準備

### ✅ デプロイ前チェック

#### □ 本番環境準備
**目的:** 本番環境での安全なリリース  
**担当:** インフラ・DevOps担当者  
**完了基準:** 本番環境が正常に動作する

**チェック項目:**
- [ ] ステージング環境での最終確認
- [ ] データベースマイグレーション計画
- [ ] バックアップ取得の確認
- [ ] ロールバック手順の準備
- [ ] 監視アラート設定の確認

#### □ リリース実行
**目的:** 計画的で安全なリリース実行  
**担当:** リリース責任者  
**完了基準:** 新機能が本番で正常動作する

**実行手順:**
1. メンテナンス通知
2. バックエンドのデプロイ
3. フロントエンドのデプロイ
4. 動作確認テスト
5. 監視状況確認
6. リリース完了通知

**チェック項目:**
- [ ] デプロイ成功の確認
- [ ] 全機能の動作確認
- [ ] エラーログの監視
- [ ] ユーザー影響の確認
- [ ] 性能指標の監視

---

## 📋 作業ログ・報告

### 作業完了時の報告フォーマット

```markdown
## 作業完了報告

### 実施内容
- Phase: [1/2/3]
- 作業項目: [具体的な作業内容]
- 実施日時: [YYYY-MM-DD HH:MM]
- 担当者: [担当者名]

### 結果
- 完了状況: [完了/部分完了/未完了]
- 動作確認結果: [正常/異常]
- 問題点: [発生した問題があれば記載]

### 添付資料
- スクリーンショット: [ファイルパス]
- テストログ: [ファイルパス]
- エラーログ: [エラー内容]

### 次の作業
- 後続タスク: [次に実施する作業]
- 依存関係: [他チームとの調整事項]
```

---

**作成日:** 2024-12-27  
**更新者:** KanshiChan AI Assistant  
**次回レビュー:** 各Phase完了時 
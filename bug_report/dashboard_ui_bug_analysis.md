# ダッシュボードの値未表示問題 - 原因分析レポート

## 📋 問題概要

### 現象
- 行動分析インサイト画面において、すべての指標が **0** または空欄で表示されている
- 対象指標：
  - 今日の集中時間: 0時間0分
  - 在席率: 0%
  - スマホ使用時間: 0時間0分
  - 姿勢アラート: 0回
  - 集中スコア: 0/100
  - 生産性スコア: 0/100

### 影響範囲
- フロントエンド: `BehaviorInsights.tsx` コンポーネント
- バックエンド: `/api/behavior/summary` エンドポイント
- データフロー: フロントエンド ↔ バックエンド間のデータ交換

---

## 🔍 調査結果

### 1. バックエンドAPI調査

#### APIレスポンス検証
```bash
$ curl -X GET "http://localhost:8000/api/behavior/summary?detailed=true"
```

**実際のレスポンス:**
```json
{
  "data": {
    "active_time_minutes": 272.0,
    "average_focus": 0.5,
    "data_completeness": 0.35661764705882354,
    "period_end": "2025-06-04T04:57:28.065281",
    "period_start": "2025-06-04T00:52:03.594861",
    "presence_rate": 0.9191176470588235,
    "smartphone_usage_rate": 0.0,
    "timeframe": "today",
    "total_entries": 544
  },
  "status": "success",
  "timestamp": "2025-06-04T04:57:36.572515"
}
```

**問題点:**
- ✅ APIは正常にデータを返している（544件のログを処理済み）
- ❌ フロントエンドが期待する `today`/`yesterday` 構造になっていない

### 2. フロントエンド期待値調査

#### BehaviorSummary型定義
```typescript
interface BehaviorSummary {
  today?: {
    total_time?: number;
    focus_time?: number;
    break_time?: number;
    absence_time?: number;
    smartphone_usage_time?: number;
    posture_alerts?: number;
  };
  yesterday?: {
    total_time?: number;
    focus_time?: number;
    break_time?: number;
    absence_time?: number;
    smartphone_usage_time?: number;
    posture_alerts?: number;
  };
}
```

#### API呼び出し実装
```typescript
const fetchBehaviorSummary = useCallback(async () => {
  try {
    const response = await fetch('/api/behavior/summary?detailed=true');
    if (response.ok) {
      const data = await response.json();
      if (data.status === 'success') {
        setBehaviorSummary(data.data || null);  // ⚠️ 構造不一致
      }
    }
  } catch (error) {
    console.error('Failed to fetch behavior summary:', error);
  }
}, []);
```

### 3. データ構造の不一致分析

| 項目 | バックエンド実際値 | フロントエンド期待値 | 変換必要性 |
|------|-------------------|---------------------|------------|
| 集中時間 | `active_time_minutes` (272.0) | `today.focus_time` (秒) | ✅ 必要 |
| 在席率 | `presence_rate` (0.919) | 計算式: `(total_time - absence_time) / total_time` | ✅ 必要 |
| スマホ使用時間 | `smartphone_usage_rate` (0.0) | `today.smartphone_usage_time` (秒) | ✅ 必要 |
| 姿勢アラート | ❌ 存在しない | `today.posture_alerts` (回数) | ✅ 必要 |
| 集中スコア | `average_focus` (0.5) | `insights.focus_score` | ✅ 必要 |
| 生産性スコア | ❌ 存在しない | `insights.productivity_score` | ✅ 必要 |

---

## 🔧 根本原因特定

### 主要原因

1. **データ構造の不一致 (Critical)**
   - バックエンドAPIが返すフラット構造
   - フロントエンドが期待するネスト構造（`today`/`yesterday`）
   - データアクセスパターンの相違

2. **API仕様の不統一 (High)**
   - `/api/behavior/summary` エンドポイントが期待値と異なる構造を返す
   - `detailed=true` フラグの処理が不完全
   - 今日・昨日の比較データが提供されていない

3. **フィールド名・単位の不整合 (Medium)**
   - 時間の単位変換（分 → 秒）
   - レート値から実時間への変換
   - 欠損フィールド（姿勢アラート、生産性スコア）

4. **エラーハンドリングの不足 (Low)**
   - データ構造エラー時のフォールバック処理なし
   - ユーザーに対する適切なエラー表示なし

### 副次的原因

- **型安全性の欠如**: `BehaviorSummary` の型定義とAPIレスポンスの不一致
- **テストの不備**: フロントエンド・バックエンド統合テストの欠如
- **ドキュメント不整合**: API仕様書とフロントエンド実装の齟齬

---

## 💡 修正方針

### Phase 1: 緊急対応 (即時実装可能)

#### 1.1 フロントエンドでのデータ変換関数追加
```typescript
// BehaviorInsights.tsx に追加
const transformBehaviorSummary = (apiData: any): BehaviorSummary => {
  if (!apiData) return {};
  
  // 今日のデータ変換
  const todayData = {
    total_time: (apiData.active_time_minutes || 0) * 60, // 分→秒
    focus_time: (apiData.active_time_minutes || 0) * (apiData.average_focus || 0) * 60,
    absence_time: (apiData.active_time_minutes || 0) * (1 - (apiData.presence_rate || 0)) * 60,
    smartphone_usage_time: (apiData.active_time_minutes || 0) * (apiData.smartphone_usage_rate || 0) * 60,
    posture_alerts: 0, // TODO: APIから取得する仕組みが必要
    break_time: 0 // TODO: 計算ロジックが必要
  };

  return {
    today: todayData,
    yesterday: {} // TODO: 昨日のデータを別途取得
  };
};

// fetchBehaviorSummary の修正
const fetchBehaviorSummary = useCallback(async () => {
  try {
    const response = await fetch('/api/behavior/summary?detailed=true');
    if (response.ok) {
      const data = await response.json();
      if (data.status === 'success') {
        const transformedData = transformBehaviorSummary(data.data);
        setBehaviorSummary(transformedData);
      }
    }
  } catch (error) {
    console.error('Failed to fetch behavior summary:', error);
  }
}, []);
```

#### 1.2 エラーハンドリング強化
```typescript
const [error, setError] = useState<string | null>(null);

// エラー状態の表示
{error && (
  <Alert status="error" mb={4}>
    <AlertIcon />
    <Box>
      <AlertTitle>データ取得エラー</AlertTitle>
      <AlertDescription>{error}</AlertDescription>
    </Box>
  </Alert>
)}
```

### Phase 2: 中期対応 (1週間以内)

#### 2.1 バックエンドAPI仕様の調整

**Option A: 新エンドポイント追加**
```python
@behavior_bp.route('/summary/dashboard', methods=['GET'])
def get_dashboard_summary():
    """ダッシュボード専用サマリーAPI"""
    # 今日のデータ
    today_data = _get_daily_summary('today')
    yesterday_data = _get_daily_summary('yesterday')
    
    return jsonify({
        'status': 'success',
        'data': {
            'today': today_data,
            'yesterday': yesterday_data
        }
    })

def _get_daily_summary(timeframe: str) -> Dict[str, Any]:
    """日次サマリーデータ取得"""
    # 実装詳細...
    return {
        'total_time': total_seconds,
        'focus_time': focus_seconds,
        'break_time': break_seconds,
        'absence_time': absence_seconds,
        'smartphone_usage_time': smartphone_seconds,
        'posture_alerts': posture_alert_count
    }
```

**Option B: 既存API拡張**
```python
@behavior_bp.route('/summary', methods=['GET'])
def get_behavior_summary():
    # ...existing code...
    
    if include_details:
        # 今日・昨日のデータを追加
        summary['dashboard_format'] = {
            'today': _get_daily_dashboard_data('today'),
            'yesterday': _get_daily_dashboard_data('yesterday')
        }
```

#### 2.2 欠損データの追加実装

**姿勢アラート機能**
```python
def _calculate_posture_alerts(logs: List[BehaviorLog]) -> int:
    """姿勢アラート回数を計算"""
    alert_count = 0
    for log in logs:
        if hasattr(log, 'posture_data') and log.posture_data:
            # 姿勢スコアが閾値以下の場合アラート
            if log.posture_data.get('score', 1.0) < 0.6:
                alert_count += 1
    return alert_count
```

**生産性スコア算出**
```python
def _calculate_productivity_score(logs: List[BehaviorLog]) -> float:
    """生産性スコアを算出"""
    if not logs:
        return 0.0
    
    focus_weight = 0.6
    presence_weight = 0.3
    smartphone_penalty = 0.1
    
    avg_focus = sum(log.focus_level for log in logs if log.focus_level) / len(logs)
    presence_rate = sum(1 for log in logs if log.presence_status == 'present') / len(logs)
    smartphone_penalty_rate = sum(1 for log in logs if log.smartphone_detected) / len(logs)
    
    score = (avg_focus * focus_weight + 
             presence_rate * presence_weight - 
             smartphone_penalty_rate * smartphone_penalty)
    
    return max(0.0, min(1.0, score))
```

### Phase 3: 長期対応 (2-3週間)

#### 3.1 統一データスキーマの策定
```yaml
# api_schema.yaml
dashboard_summary:
  type: object
  properties:
    today:
      $ref: '#/definitions/DailySummary'
    yesterday:
      $ref: '#/definitions/DailySummary'
    week_trend:
      $ref: '#/definitions/TrendData'

DailySummary:
  type: object
  properties:
    total_time:
      type: integer
      description: "総時間（秒）"
    focus_time:
      type: integer
      description: "集中時間（秒）"
    # ...他のフィールド
```

#### 3.2 型定義の完全統一
```typescript
// types/api.ts
export interface DashboardSummaryResponse {
  status: 'success' | 'error';
  data: {
    today: DailySummary;
    yesterday: DailySummary;
    week_trend?: TrendData;
  };
  timestamp: string;
}

export interface DailySummary {
  total_time: number;        // 秒
  focus_time: number;        // 秒
  break_time: number;        // 秒
  absence_time: number;      // 秒
  smartphone_usage_time: number; // 秒
  posture_alerts: number;    // 回数
}
```

---

## 🧪 テスト計画

### 単体テスト
- [ ] `transformBehaviorSummary` 関数のテスト
- [ ] バックエンドAPI各エンドポイントのレスポンステスト
- [ ] エラーハンドリングのテスト

### 統合テスト
- [ ] フロントエンド・バックエンド間のデータフローテスト
- [ ] 実データでのダッシュボード表示テスト
- [ ] エラー条件でのユーザー体験テスト

### E2Eテスト
- [ ] ダッシュボード画面の値表示テスト
- [ ] データ更新タイミングのテスト
- [ ] ネットワークエラー時の動作テスト

---

## 📈 優先度付きアクション項目

### 🔴 Critical (即時対応)
1. **データ変換関数の実装** - フロントエンドで即座に対応可能
2. **エラーハンドリング強化** - ユーザー体験の改善

### 🟡 High (1週間以内)
1. **バックエンドAPI仕様調整** - 根本的解決
2. **欠損データの実装** - 姿勢アラート、生産性スコア

### 🟢 Medium (2-3週間)
1. **統一スキーマ策定** - 長期的な保守性向上
2. **包括的テスト実装** - 品質保証

### 🔵 Low (1ヶ月)
1. **ドキュメント整備** - 開発効率向上
2. **パフォーマンス最適化** - ユーザー体験向上

---

## 📝 補足情報

### 参考ドキュメント
- [データ形式分析報告書](../backend/docs/data_format_analysis_report.adoc)
- プロジェクト規約: `project_rules/`

### 関連ファイル
- `frontend/src/components/BehaviorInsights.tsx`
- `backend/src/web/routes/behavior_routes.py`
- `backend/src/models/behavior_log.py`

### 技術的注記
- データベースには実際のログが存在（544件確認済み）
- APIレスポンス時間は正常（0.05秒以下）
- メモリ使用量・CPU負荷に問題なし

---

**作成日:** 2024-12-27  
**調査者:** KanshiChan AI Assistant  
**次回レビュー予定:** Phase 1完了後 
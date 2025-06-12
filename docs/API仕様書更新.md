# 改善提案 API 仕様書

## 概要

行動分析に基づいて生成される推奨事項（改善提案）を取得するためのAPIエンドポイント

## エンドポイント

```
GET /api/analysis/basic/recommendations
```

## リクエストパラメータ

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|------------|------|----------|--------------|-------------|
| priority | string | いいえ | "all" | 優先度フィルター: "high", "medium", "low", "all" |
| page | integer | いいえ | 1 | ページ番号（1から開始） |
| limit | integer | いいえ | 5 | 1ページあたりの項目数（最大10） |
| tts_enabled | boolean | いいえ | false | 音声合成テキスト生成フラグ |

## レスポンス

### 成功時レスポンス (200 OK)

```json
{
  "status": "success",
  "data": {
    "recommendations": [
      {
        "type": "focus_improvement",
        "priority": "high",
        "message": "集中力を高めるために休憩を規則的に取ることを推奨します",
        "action": "focus_training",
        "emotion": "encouraging",
        "source": "behavior_analysis",
        "timestamp": "2023-06-12T10:30:00Z",
        "audio_url": "/api/tts/rec_12345.mp3",
        "voice_text": "集中力を高めるために休憩を規則的に取ることを推奨します",
        "tts_requested": true,
        "metadata": {
          "trigger": "low_focus_pattern",
          "relevant_period": "morning"
        }
      },
      // ... 他の推奨事項 ...
    ],
    "pagination": {
      "page": 1,
      "limit": 5,
      "total_items": 12,
      "total_pages": 3
    }
  },
  "timestamp": "2023-06-12T10:35:22Z"
}
```

### エラーレスポンス (400 Bad Request)

```json
{
  "status": "error",
  "message": "Invalid parameters",
  "errors": [
    {
      "param": "priority",
      "message": "priority must be one of: high, medium, low, all"
    }
  ],
  "timestamp": "2023-06-12T10:35:22Z"
}
```

## フィールド仕様

### recommendations

| フィールド | 型 | 必須 | 説明 |
|------------|------|----------|-------------|
| type | string | はい | 推奨タイプ: "focus_improvement", "distraction_management", "contextual_advice" など |
| priority | string | はい | 優先度: "high", "medium", "low" |
| message | string | はい | 推奨メッセージ本文 |
| action | string | いいえ | 推奨されるアクション: "focus_training", "device_management" など |
| emotion | string | いいえ | 感情トーン: "encouraging", "alert", "celebration" など |
| source | string | いいえ | 推奨の発生源: "behavior_analysis", "llm_advice" など |
| timestamp | string | はい | 推奨生成時刻 (ISO8601形式) |
| audio_url | string | いいえ | 音声合成済みファイルのURL (tts_enabled=true時のみ) |
| voice_text | string | いいえ | 音声合成用に最適化されたテキスト |
| tts_requested | boolean | いいえ | 音声合成リクエストフラグ |
| metadata | object | いいえ | 任意の追加メタデータ |

### pagination

| フィールド | 型 | 必須 | 説明 |
|------------|------|----------|-------------|
| page | integer | はい | 現在のページ番号 |
| limit | integer | はい | ページあたりの項目数 |
| total_items | integer | はい | 合計項目数 |
| total_pages | integer | はい | 合計ページ数 |

## 使用例

### すべての重要な推奨事項を取得

```
GET /api/analysis/basic/recommendations?priority=high
```

### 2ページ目の推奨事項を取得（3件ずつ）

```
GET /api/analysis/basic/recommendations?page=2&limit=3
```

### 音声合成が有効な中程度の優先度の推奨事項を取得

```
GET /api/analysis/basic/recommendations?priority=medium&tts_enabled=true
```

## 注意事項

- 音声合成は処理負荷が高いため、`tts_enabled=true` は必要な場合のみ使用してください
- 推奨事項は生成された順に優先度ごとにソートされます（高→中→低）
- 通常のユースケースでは `limit=5` が推奨されます 
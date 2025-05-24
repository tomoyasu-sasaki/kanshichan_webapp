# 📋 KanshiChan プロジェクト規約

## 📖 概要
このディレクトリには、KanshiChan（監視ちゃん）プロジェクトの開発において、一貫したアプリケーションを構築するために必要な規約が定義されています。

## 🎯 目的
- **一貫性**: チーム全体での統一された開発スタイル
- **品質**: 高品質なコードと設計の維持
- **保守性**: 長期的な保守性とスケーラビリティの確保
- **効率性**: 開発効率の向上と学習コストの削減

## 📁 規約ファイル一覧

### 🌟 [`main_rules.yaml`](./main_rules.yaml) - メイン規約
**プロジェクト全体に適用される基本規約**
- 技術スタック規約
- プロジェクト構造規約
- 命名規約
- コーディング規約
- API設計規約
- 設定管理規約
- エラーハンドリング規約
- テスト規約
- Git運用規約
- セキュリティ規約
- パフォーマンス規約

### 🐍 [`backend_rules.yaml`](./backend_rules.yaml) - バックエンド規約
**Python/Flask バックエンド開発に特化した規約**
- Python コーディング規約
- プロジェクト構造規約
- クラス設計規約
- エラーハンドリング規約
- 設定管理規約
- API設計規約
- テスト規約
- 依存関係管理
- パフォーマンス規約
- セキュリティ規約

### ⚛️ [`frontend_rules.yaml`](./frontend_rules.yaml) - フロントエンド規約
**React/TypeScript フロントエンド開発に特化した規約**
- TypeScript コーディング規約
- React コンポーネント規約
- プロジェクト構造規約
- State管理規約
- UI/UX デザイン規約
- API通信規約
- テスト規約
- パフォーマンス規約
- アクセシビリティ規約
- 開発環境規約
- 型定義規約

### 🤖 [`ai_ml_rules.yaml`](./ai_ml_rules.yaml) - AI/ML規約
**AI/ML機能（YOLO、MediaPipe等）に特化した規約**
- AI/ML アーキテクチャ規約
- 物体検出（YOLO）規約
- 姿勢検出（MediaPipe）規約
- 画像処理規約
- パフォーマンス最適化規約
- 設定管理規約
- エラーハンドリング規約
- テスト規約
- モデル管理規約
- 品質保証規約

## 🔍 規約の使用方法

### 新機能開発時
1. **`main_rules.yaml`** で全体的な方針を確認
2. 該当する領域の詳細規約（backend/frontend/ai_ml）を参照
3. 命名規約、コーディングスタイルに従って実装
4. テスト規約に従ってテストを作成

### コードレビュー時
- 各規約ファイルの該当セクションを参照してレビュー
- 規約違反がある場合は具体的な規約項目を指摘
- 新しいパターンが必要な場合は規約の更新を検討

### 新メンバー参加時
1. **`main_rules.yaml`** を最初に読んで全体像を把握
2. 担当する領域の詳細規約を熟読
3. 既存コードを規約の観点から分析して理解を深める

## ⚙️ 規約の更新

### 更新プロセス
1. **課題の特定**: 現在の規約で対応できない問題を特定
2. **提案作成**: 規約の追加・修正提案を作成
3. **チーム討議**: 提案について議論し合意形成
4. **規約更新**: 該当するYAMLファイルを更新
5. **周知徹底**: 変更内容をチーム全体に周知

### 更新時の注意点
- 既存コードとの互換性を考慮
- 段階的な移行計画を策定
- 影響範囲を明確にして文書化

## 📊 規約遵守の確認

### 自動チェック
- **Backend**: Black, Flake8, mypy による自動チェック
- **Frontend**: ESLint, Prettier による自動チェック
- **CI/CD**: GitHub Actions での自動検証

### 手動確認
- コードレビューでの規約遵守確認
- 定期的な規約遵守状況の棚卸し
- 新機能リリース前の規約チェック

## 🎨 コーディングスタイル例

### Python (Backend)
```python
# ✅ Good - 規約に準拠
from typing import Dict, Any
import numpy as np

class Detector:
    def __init__(self, config_manager=None):
        """物体検出器の初期化
        
        Args:
            config_manager: 設定管理オブジェクト
        """
        self.config_manager = config_manager
        
    def detect_objects(self, frame: np.ndarray) -> Dict[str, Any]:
        """物体検出を実行"""
        if frame is None or frame.size == 0:
            logger.warning("Invalid frame received")
            return {}
            
        try:
            # 検出処理
            return self._process_detection(frame)
        except Exception as e:
            logger.error(f"Detection failed: {e}", exc_info=True)
            return {}
```

### TypeScript (Frontend)
```typescript
// ✅ Good - 規約に準拠
interface MonitorViewProps {
  isFullscreen?: boolean;
  onToggleFullscreen: () => void;
}

export const MonitorView: React.FC<MonitorViewProps> = ({
  isFullscreen = false,
  onToggleFullscreen
}) => {
  const [status, setStatus] = useState<DetectionStatus>({
    personDetected: false,
    smartphoneDetected: false,
    absenceTime: 0,
    smartphoneUseTime: 0
  });

  const handleFullscreenToggle = useCallback(async () => {
    try {
      if (!document.fullscreenElement) {
        await containerRef.current?.requestFullscreen();
      } else {
        await document.exitFullscreen();
      }
    } catch (error) {
      console.error('Fullscreen toggle failed:', error);
    }
  }, []);

  return (
    <Box position="relative" width="100%" height="100vh" bg="black">
      {/* Component content */}
    </Box>
  );
};
```

## 🔗 関連ドキュメント
- [プロジェクト README](../README.md)
- [技術仕様書](../docs/) ※将来実装
- [API仕様書](../docs/api/) ※将来実装

## 📝 ライセンス
これらの規約は KanshiChan プロジェクトの一部として、プロジェクトと同じライセンス（MIT）の下で提供されます。 
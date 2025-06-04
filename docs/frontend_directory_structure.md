# フロントエンド ディレクトリ構造定義書

## 概要
KanshiChan フロントエンドプロジェクトのディレクトリ構造と各ファイルの役割を定義した文書です。

## プロジェクト構造

```
frontend/
├── public/                    # 静的ファイル
│   ├── index.html            # メインHTMLテンプレート
│   └── vite.svg              # アイコンファイル
├── src/                      # ソースコード
│   ├── components/           # Reactコンポーネント
│   │   ├── __tests__/       # コンポーネントテスト
│   │   │   ├── MonitorView.test.tsx
│   │   │   ├── ScheduleView.test.tsx
│   │   │   └── SettingsPanel.test.tsx
│   │   ├── LanguageSwitcher.tsx    # 言語切り替えコンポーネント
│   │   ├── MonitorView.tsx         # メイン監視画面
│   │   ├── PerformanceStats.tsx    # パフォーマンス統計
│   │   ├── ScheduleView.tsx        # スケジュール管理画面
│   │   └── SettingsPanel.tsx       # 設定パネル
│   ├── utils/                # ユーティリティ関数
│   │   ├── __tests__/       # ユーティリティテスト
│   │   └── websocket.ts     # WebSocket管理
│   ├── i18n/                # 国際化設定
│   │   ├── locales/         # 言語ファイル
│   │   │   ├── en.json      # 英語リソース
│   │   │   └── ja.json      # 日本語リソース
│   │   └── index.ts         # i18n設定
│   ├── assets/              # 静的アセット
│   │   ├── logo.svg         # アプリケーションロゴ
│   │   └── react.svg        # Reactロゴ
│   ├── __tests__/           # グローバルテスト設定
│   ├── App.css              # アプリケーションスタイル
│   ├── App.tsx              # メインアプリケーション
│   ├── index.css            # グローバルスタイル
│   ├── main.tsx             # エントリーポイント
│   ├── setupTests.ts        # テスト環境設定
│   └── theme.ts             # Chakra UIテーマ
├── coverage/                # テストカバレッジレポート
├── dist/                    # ビルド出力
├── node_modules/            # 依存パッケージ
├── .gitignore              # Git除外設定
├── eslint.config.js        # ESLint設定
├── index.html              # 開発用HTMLテンプレート
├── jest.config.js          # Jest設定
├── package.json            # npm設定
├── package-lock.json       # 依存関係ロック
├── README.md               # プロジェクト説明
├── tsconfig.json           # TypeScript基本設定
├── tsconfig.app.json       # アプリケーション用TS設定
├── tsconfig.jest.json      # Jest用TS設定
├── tsconfig.node.json      # Node.js用TS設定
├── tsconfig.tsbuildinfo    # TypeScriptビルド情報
└── vite.config.ts          # Vite設定
```

## ディレクトリ詳細

### `/src/components/`
React コンポーネントファイルを格納するディレクトリ

#### 主要コンポーネント
- **MonitorView.tsx**: リアルタイム監視画面。MJPEGストリーム表示、検出ステータス表示、全画面機能
- **SettingsPanel.tsx**: システム設定画面。検出設定、アラート設定、保存機能
- **ScheduleView.tsx**: スケジュール管理画面。アラート設定、時間管理機能
- **PerformanceStats.tsx**: システムパフォーマンス統計表示
- **LanguageSwitcher.tsx**: 言語切り替えUI

#### テストファイル
- `__tests__/` ディレクトリ内にコンポーネントごとのテストファイル
- 命名規則: `<ComponentName>.test.tsx`

### `/src/utils/`
ユーティリティ関数とヘルパー機能

- **websocket.ts**: WebSocket通信管理、シングルトンパターン実装、型安全なイベント処理

### `/src/i18n/`
国際化（多言語対応）設定

- **index.ts**: i18next設定、言語検出、リソース読み込み
- **locales/**: 言語別リソースファイル
  - `ja.json`: 日本語翻訳
  - `en.json`: 英語翻訳

### `/src/assets/`
静的アセットファイル
- SVGアイコン、画像ファイル等

## 設定ファイル詳細

### 開発環境設定
- **vite.config.ts**: Vite設定、プロキシ設定、ビルド設定
- **tsconfig.json**: TypeScript基本設定
- **eslint.config.js**: コード品質チェック設定
- **jest.config.js**: テスト環境設定

### 依存関係管理
- **package.json**: npm パッケージ設定、スクリプト定義
- **package-lock.json**: 依存関係バージョンロック

## 技術スタック

### コア技術
- **React 19.0.0**: UIライブラリ
- **TypeScript 5.7.2**: 型安全性
- **Vite 6.2.0**: ビルドツール

### UIライブラリ
- **Chakra UI 2.8.2**: デザインシステム
- **Framer Motion 11.0.8**: アニメーション
- **React Icons 5.5.0**: アイコンセット

### 通信・データ管理
- **Socket.IO Client 4.8.1**: WebSocket通信
- **Axios 1.8.2**: HTTP通信

### 国際化
- **i18next 25.2.0**: 国際化フレームワーク
- **react-i18next 15.5.2**: React統合

### 開発・テスト
- **Jest 29.7.0**: テストフレームワーク
- **React Testing Library**: コンポーネントテスト
- **ESLint**: コード品質管理

## 命名規則

### ファイル名
- コンポーネント: PascalCase（例: `MonitorView.tsx`）
- ユーティリティ: camelCase（例: `websocket.ts`）
- テスト: `<ComponentName>.test.tsx`

### ディレクトリ名
- 小文字、必要に応じてハイフン（例: `components`、`__tests__`）

### 変数・関数名
- camelCase（例: `isFullscreen`、`handleToggleFullscreen`）
- React Hook: `use` prefix（例: `useWebSocket`）

## ビルド・デプロイ

### 開発環境
```bash
npm run dev        # 開発サーバー起動
npm run test       # テスト実行
npm run lint       # コード品質チェック
```

### プロダクション
```bash
npm run build      # プロダクションビルド
npm run preview    # プレビューサーバー
```

## パフォーマンス考慮事項

### 最適化技術
- Viteによる高速ビルド・HMR
- React.memoによる不要な再レンダリング防止
- useCallback/useMemoによるメモ化
- コード分割とlazy loading対応

### リソース管理
- 効率的なWebSocket接続管理
- 適切なイベントリスナーのクリーンアップ
- メモリリーク防止

## セキュリティ

### CORS設定
- Viteプロキシによるバックエンド通信
- 開発時のCORS問題回避

### 型安全性
- TypeScript strictモード
- 明示的な型定義
- 型安全なAPI通信

## 今後の拡張予定

### 予定機能
- グローバル状態管理（Context API / Redux Toolkit）
- エラーバウンダリ実装
- PWA対応
- E2Eテスト追加

### ディレクトリ追加予定
```
src/
├── types/           # 型定義ファイル
├── hooks/           # カスタムHook
├── contexts/        # React Context
├── services/        # API サービス層
└── constants/       # 定数定義
``` 
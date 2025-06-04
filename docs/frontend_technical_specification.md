# フロントエンド 技術仕様書

## 概要
KanshiChan フロントエンドアプリケーションの技術スタック、開発環境、ビルド設定、品質管理に関する詳細仕様書です。

## 技術スタック

### コア技術

#### React 19.0.0
- **UIライブラリ**: 最新のReact機能を活用
- **新機能**: Server Components対応準備、Concurrent Features
- **Hooks**: useState, useEffect, useCallback, useMemo, useRef
- **パターン**: 関数コンポーネント + Hooks

#### TypeScript 5.7.2
- **設定**: Strictモード有効
- **型チェック**: 厳格な型検証
- **設定ファイル**: 複数のtsconfig.json（app/node/jest用）
- **型安全性**: 明示的な型定義を推奨

#### Vite 6.2.0
- **ビルドツール**: 高速な開発体験
- **特徴**: Hot Module Replacement (HMR)
- **プラグイン**: React プラグイン統合
- **プロキシ**: 開発時のAPI通信サポート

### UIフレームワーク

#### Chakra UI 2.8.2
- **デザインシステム**: モダンなコンポーネントライブラリ
- **テーマ**: カスタマイズ可能なデザイントークン
- **レスポンシブ**: モバイルファースト設計
- **アクセシビリティ**: WCAG準拠

#### Emotion 11.11.4
- **CSS-in-JS**: styled-components対応
- **パフォーマンス**: 効率的なスタイリング
- **テーマ**: Chakra UIとの統合

#### Framer Motion 11.0.8
- **アニメーション**: 滑らかなUI遷移
- **用途**: モーダル、ページ遷移
- **パフォーマンス**: GPU加速対応

### 通信・状態管理

#### Socket.IO Client 4.8.1
- **WebSocket**: リアルタイム通信
- **特徴**: 自動再接続、フォールバック
- **パターン**: シングルトン管理

#### Axios 1.8.2
- **HTTP通信**: RESTful API対応
- **特徴**: インターセプター、タイムアウト
- **使用予定**: 設定管理API

### 国際化

#### i18next 25.2.0
- **国際化フレームワーク**: 多言語対応
- **機能**: 動的言語切り替え、補間、複数形
- **ブラウザ統合**: 言語検出、ローカルストレージ

#### react-i18next 15.5.2
- **React統合**: Hooks API
- **機能**: useTranslation、Trans コンポーネント

### アイコン・アセット

#### React Icons 5.5.0
- **アイコンライブラリ**: Font Awesome、Material Design等
- **パフォーマンス**: ツリーシェイキング対応
- **一貫性**: 統一されたアイコン体験

---

## 開発環境設定

### Node.js要件
- **バージョン**: Node.js 18.x 以上
- **パッケージマネージャー**: npm

### 開発サーバー設定

#### Vite開発サーバー
```typescript
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5001',
        changeOrigin: true,
      },
      '/socket.io': {
        target: 'http://localhost:5001',
        changeOrigin: true,
        ws: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ui: ['@chakra-ui/react', '@emotion/react'],
        },
      },
    },
  },
});
```

### TypeScript設定

#### メイン設定（tsconfig.json）
```json
{
  "compilerOptions": {
    "esModuleInterop": true,
    "jsx": "react-jsx"
  },
  "include": ["src"],
  "references": [
    { "path": "./tsconfig.app.json" },
    { "path": "./tsconfig.node.json" }
  ]
}
```

#### アプリケーション用設定（tsconfig.app.json）
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true
  }
}
```

---

## コード品質管理

### ESLint設定

#### eslint.config.js
```javascript
import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'

export default tseslint.config(
  { ignores: ['dist'] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      'react-refresh/only-export-components': [
        'warn',
        { allowConstantExport: true },
      ],
    },
  },
)
```

### 主要ルール
- **TypeScript**: strict モード、型安全性
- **React**: Hooks ルール、refresh対応
- **Code Style**: 一貫したコーディングスタイル

---

## テスト環境

### Jest 29.7.0設定

#### jest.config.js
```javascript
export default {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  moduleNameMapping: {
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/main.tsx',
    '!src/vite-env.d.ts',
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },
};
```

### React Testing Library
- **コンポーネントテスト**: ユーザー中心のテスト
- **アクセシビリティ**: スクリーンリーダー対応テスト
- **インタラクション**: ユーザーイベントテスト

### テスト戦略
- **単体テスト**: コンポーネント別テスト
- **統合テスト**: WebSocket通信テスト
- **E2Eテスト**: 将来実装予定

---

## ビルド・デプロイ

### 開発コマンド
```bash
npm run dev        # 開発サーバー起動 (port: 3000)
npm run build      # プロダクションビルド
npm run preview    # ビルド後プレビュー
npm run lint       # ESLintチェック
npm run test       # Jestテスト実行
npm run test:watch # テスト監視モード
```

### ビルド最適化

#### バンドル分割
```typescript
// vite.config.ts
build: {
  rollupOptions: {
    output: {
      manualChunks: {
        vendor: ['react', 'react-dom'],
        ui: ['@chakra-ui/react', '@emotion/react'],
        utils: ['socket.io-client', 'axios', 'i18next'],
      },
    },
  },
},
```

#### パフォーマンス最適化
- **Code Splitting**: 動的インポート対応
- **Tree Shaking**: 不要コード削除
- **Minification**: 圧縮最適化
- **Asset Optimization**: 静的ファイル最適化

---

## アーキテクチャパターン

### ディレクトリ構造パターン
```
src/
├── components/     # 機能別コンポーネント
├── utils/         # ユーティリティ関数
├── i18n/          # 国際化設定
├── assets/        # 静的アセット
└── __tests__/     # グローバルテスト設定
```

### コンポーネント設計原則

#### 単一責任原則
- 1コンポーネント1機能
- 明確な責務分担
- 再利用可能な設計

#### コンポーネント合成
```typescript
// Good: Composition Pattern
<MonitorView>
  <VideoStream />
  <StatusOverlay />
  <FullscreenButton />
</MonitorView>

// Avoid: Monolithic Component
<MonitorViewWithEverything />
```

### カスタムHooksパターン
```typescript
// WebSocket管理Hook
export const useWebSocket = () => {
  const [status, setStatus] = useState<DetectionStatus>();
  const [isConnected, setIsConnected] = useState(false);
  
  useEffect(() => {
    websocketManager.initialize();
    
    const unsubscribe = websocketManager.onStatusUpdate(setStatus);
    const connectUnsubscribe = websocketManager.onConnect(() => 
      setIsConnected(true)
    );
    
    return () => {
      unsubscribe();
      connectUnsubscribe();
    };
  }, []);
  
  return { status, isConnected };
};
```

---

## 状態管理戦略

### ローカル状態
- **useState**: 単純な状態
- **useReducer**: 複雑な状態ロジック
- **useRef**: DOM参照、値の保持

### グローバル状態（将来実装）
```typescript
// Context API パターン
const AppContext = createContext<AppContextType>();

export const AppProvider: React.FC<{ children: ReactNode }> = ({ 
  children 
}) => {
  const [state, dispatch] = useReducer(appReducer, initialState);
  
  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
};
```

### サーバー状態
- **WebSocket**: リアルタイムデータ
- **HTTP**: 設定・操作
- **キャッシュ**: React Query導入検討

---

## パフォーマンス最適化

### レンダリング最適化

#### React.memo
```typescript
const StatusBadge = React.memo<StatusBadgeProps>(({ status }) => {
  return (
    <Badge colorScheme={status ? 'green' : 'red'}>
      {status ? '在席中' : '不在'}
    </Badge>
  );
});
```

#### useCallback/useMemo
```typescript
const MonitorView = () => {
  const [isFullscreen, setIsFullscreen] = useState(false);
  
  const toggleFullscreen = useCallback(async () => {
    try {
      if (!document.fullscreenElement) {
        await containerRef.current?.requestFullscreen();
      } else {
        await document.exitFullscreen();
      }
    } catch (error) {
      console.error('Fullscreen error:', error);
    }
  }, []);
  
  const statusDisplay = useMemo(() => 
    formatStatusDisplay(status), [status]
  );
  
  return (
    <Box>
      <button onClick={toggleFullscreen}>Toggle</button>
      <div>{statusDisplay}</div>
    </Box>
  );
};
```

### バンドルサイズ最適化
- **Dynamic Imports**: コード分割
- **Tree Shaking**: 不要コード削除
- **Bundle Analyzer**: サイズ分析

---

## セキュリティ

### XSS対策
- **React**: デフォルトでエスケープ
- **DOMPurify**: HTML sanitization（必要時）
- **CSP**: Content Security Policy

### CSRF対策
- **SameSite Cookie**: CSRF保護
- **CSRFトークン**: API通信時

### 通信セキュリティ
- **HTTPS**: 本番環境必須
- **WSS**: WebSocket暗号化
- **CORS**: 適切な設定

---

## 監視・ログ

### エラー監視
```typescript
// Error Boundary (将来実装)
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }
  
  static getDerivedStateFromError(error) {
    return { hasError: true };
  }
  
  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    // エラー報告サービスに送信
  }
  
  render() {
    if (this.state.hasError) {
      return <ErrorFallback />;
    }
    
    return this.props.children;
  }
}
```

### パフォーマンス監視
- **Web Vitals**: Core Web Vitals測定
- **React DevTools**: コンポーネント分析
- **Network Monitoring**: API通信監視

---

## 今後の技術拡張

### PWA対応
- **Service Worker**: オフライン対応
- **App Manifest**: アプリ化
- **Push Notifications**: プッシュ通知

### 状態管理拡張
- **Redux Toolkit**: 複雑な状態管理
- **Zustand**: 軽量状態管理
- **React Query**: サーバー状態管理

### UI/UX拡張
- **Dark Mode**: ダークテーマ
- **Responsive**: モバイル対応
- **Accessibility**: WCAG 2.1 AA準拠

### 開発体験向上
- **Storybook**: コンポーネント開発
- **Playwright**: E2Eテスト
- **Chromatic**: ビジュアルテスト 
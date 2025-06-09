import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/socket.io': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        ws: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    chunkSizeWarningLimit: 500,
    rollupOptions: {
      output: {
        manualChunks: {
          // React関連を分離
          'react-vendor': ['react', 'react-dom'],
          // Chakra UI関連を分離  
          'chakra-vendor': ['@chakra-ui/react', '@emotion/react', '@emotion/styled'],
          // 国際化ライブラリを分離
          'i18n-vendor': ['react-i18next', 'i18next'],
          // アイコンライブラリを分離
          'icons-vendor': ['react-icons'],
          // WebSocket・通信関連を分離
          'network-vendor': ['socket.io-client'],
          // ユーティリティライブラリを分離
          'utils-vendor': ['framer-motion']
        },
        // ファイル名の最適化
        chunkFileNames: 'assets/[name]-[hash].js',
        entryFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]'
      }
    },
    // 圧縮設定
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true, // 本番でconsole.logを削除
        drop_debugger: true,
        pure_funcs: ['console.log', 'console.info', 'console.debug']
      },
      mangle: {
        safari10: true
      }
    },
    // ソースマップ無効化（本番では無効）
    sourcemap: false
  },
  // 最適化設定
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      '@chakra-ui/react',
      'react-i18next',
      'socket.io-client'
    ]
  }
})

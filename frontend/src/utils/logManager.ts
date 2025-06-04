/**
 * ログシステム統合管理
 * 
 * 全てのログ関連機能を統一的に管理し、
 * アプリケーション全体のログ機能を提供します。
 * 
 * @example
 * ```typescript
 * import { logManager } from '@/utils/logManager';
 * 
 * // システム初期化
 * await logManager.initialize();
 * 
 * // ログ出力（各種機能が自動適用）
 * await logManager.info('Application started');
 * ```
 */

import { logger } from './logger';
import { logBackup } from './logBackup';
import { logRotation } from './logRotation';
import { performanceMonitor } from './performanceMonitor';
import { LogLevel, LogEntry } from './types';

export interface LogSystemConfig {
  /** ログ機能を有効にするか */
  enabled: boolean;
  /** バックアップ機能を有効にするか */
  enableBackup: boolean;
  /** ローテーション機能を有効にするか */
  enableRotation: boolean;
  /** パフォーマンス監視を有効にするか */
  enablePerformanceMonitoring: boolean;
  /** 環境モード */
  environment: 'development' | 'production' | 'test';
}

export interface LogSystemStatus {
  /** ログシステムの状態 */
  isActive: boolean;
  /** 各サブシステムの状態 */
  subsystems: {
    logger: boolean;
    backup: boolean;
    rotation: boolean;
    performance: boolean;
  };
  /** 最後の初期化時刻 */
  lastInitialized?: string;
  /** エラー情報 */
  errors: string[];
}

class LogManager {
  private config: LogSystemConfig = {
    enabled: true,
    enableBackup: false, // 本番環境でのみ有効化推奨
    enableRotation: true,
    enablePerformanceMonitoring: true,
    environment: process.env.NODE_ENV === 'production' ? 'production' : 'development',
  };

  private isInitialized = false;
  private initializationErrors: string[] = [];

  /**
   * ログシステム全体を初期化
   */
  async initialize(customConfig?: Partial<LogSystemConfig>): Promise<void> {
    try {
      // 設定をマージ
      if (customConfig) {
        this.config = { ...this.config, ...customConfig };
      }

      await logger.info('LogManager: ログシステム初期化開始', 
        { 
          component: 'LogManager', 
          action: 'initialize_start',
          config: this.config 
        }, 
        'LogManager'
      );

      this.initializationErrors = [];

      // 各サブシステムを順次初期化
      if (this.config.enabled) {
        await this.initializeSubsystems();
      }

      this.isInitialized = true;

      await logger.info('LogManager: ログシステム初期化完了', 
        { 
          component: 'LogManager', 
          action: 'initialize_complete',
          hasErrors: this.initializationErrors.length > 0,
          errorCount: this.initializationErrors.length
        }, 
        'LogManager'
      );

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      this.initializationErrors.push(errorMessage);
      
      await logger.error('LogManager: 初期化失敗', 
        { 
          component: 'LogManager', 
          action: 'initialize_error',
          error: errorMessage
        }, 
        'LogManager'
      );
      throw error;
    }
  }

  /**
   * サブシステムを初期化
   */
  private async initializeSubsystems(): Promise<void> {
    // パフォーマンス監視を最初に初期化（他の初期化も監視するため）
    if (this.config.enablePerformanceMonitoring) {
      try {
        await performanceMonitor.initialize();
      } catch (error) {
        const errorMessage = `Performance Monitor: ${error instanceof Error ? error.message : String(error)}`;
        this.initializationErrors.push(errorMessage);
        console.warn('Performance Monitor initialization failed:', error);
      }
    }

    // ログローテーション初期化
    if (this.config.enableRotation) {
      try {
        await logRotation.initialize();
      } catch (error) {
        const errorMessage = `Log Rotation: ${error instanceof Error ? error.message : String(error)}`;
        this.initializationErrors.push(errorMessage);
        console.warn('Log Rotation initialization failed:', error);
      }
    }

    // バックアップシステム初期化（本番環境推奨）
    if (this.config.enableBackup) {
      try {
        await logBackup.initialize();
      } catch (error) {
        const errorMessage = `Log Backup: ${error instanceof Error ? error.message : String(error)}`;
        this.initializationErrors.push(errorMessage);
        console.warn('Log Backup initialization failed:', error);
      }
    }
  }

  /**
   * ログシステムの状態を取得
   */
  async getStatus(): Promise<LogSystemStatus> {
    return {
      isActive: this.isInitialized && this.config.enabled,
      subsystems: {
        logger: true, // 常に利用可能
        backup: this.config.enableBackup,
        rotation: this.config.enableRotation,
        performance: this.config.enablePerformanceMonitoring,
      },
      lastInitialized: this.isInitialized ? new Date().toISOString() : undefined,
      errors: [...this.initializationErrors],
    };
  }

  /**
   * 設定を更新
   */
  updateConfig(newConfig: Partial<LogSystemConfig>): void {
    const oldConfig = { ...this.config };
    this.config = { ...this.config, ...newConfig };

    // 設定変更に基づいてサブシステムを更新
    this.handleConfigChanges(oldConfig, this.config);

    void logger.info('LogManager: 設定更新', 
      { 
        component: 'LogManager', 
        action: 'config_update',
        oldConfig,
        newConfig: this.config
      }, 
      'LogManager'
    );
  }

  /**
   * 設定変更を処理
   */
  private handleConfigChanges(oldConfig: LogSystemConfig, newConfig: LogSystemConfig): void {
    // バックアップ設定変更
    if (oldConfig.enableBackup !== newConfig.enableBackup) {
      if (newConfig.enableBackup) {
        void logBackup.initialize().catch(console.warn);
      } else {
        logBackup.dispose();
      }
    }

    // ローテーション設定変更
    if (oldConfig.enableRotation !== newConfig.enableRotation) {
      if (newConfig.enableRotation) {
        void logRotation.initialize().catch(console.warn);
      } else {
        logRotation.dispose();
      }
    }

    // パフォーマンス監視設定変更
    if (oldConfig.enablePerformanceMonitoring !== newConfig.enablePerformanceMonitoring) {
      if (newConfig.enablePerformanceMonitoring) {
        void performanceMonitor.initialize().catch(console.warn);
      } else {
        performanceMonitor.dispose();
      }
    }
  }

  /**
   * 現在の設定を取得
   */
  getConfig(): LogSystemConfig {
    return { ...this.config };
  }

  /**
   * エラーログ（統合版）
   */
  async error(
    message: string,
    context?: Record<string, unknown>,
    source?: string
  ): Promise<void> {
    await logger.error(message, context, source);
  }

  /**
   * 警告ログ（統合版）
   */
  async warn(
    message: string,
    context?: Record<string, unknown>,
    source?: string
  ): Promise<void> {
    await logger.warn(message, context, source);
  }

  /**
   * 情報ログ（統合版）
   */
  async info(
    message: string,
    context?: Record<string, unknown>,
    source?: string
  ): Promise<void> {
    await logger.info(message, context, source);
  }

  /**
   * デバッグログ（統合版）
   */
  async debug(
    message: string,
    context?: Record<string, unknown>,
    source?: string
  ): Promise<void> {
    await logger.debug(message, context, source);
  }

  /**
   * API呼び出しのパフォーマンス測定（統合版）
   */
  async measureApiCall<T>(
    name: string,
    apiCall: () => Promise<T>,
    context?: Record<string, unknown>
  ): Promise<T> {
    if (this.config.enablePerformanceMonitoring) {
      return await performanceMonitor.measureApiCall(name, apiCall, context);
    } else {
      return await apiCall();
    }
  }

  /**
   * レンダリング時間測定（統合版）
   */
  async measureRender(componentName: string, renderFn: () => void): Promise<void> {
    if (this.config.enablePerformanceMonitoring) {
      await performanceMonitor.measureRender(componentName, renderFn);
    } else {
      renderFn();
    }
  }

  /**
   * 手動ログ同期（統合版）
   */
  async syncLogs(): Promise<void> {
    if (this.config.enableBackup) {
      await logBackup.syncLogs();
    } else {
      await logger.warn('LogManager: バックアップが無効のため同期をスキップ', 
        { component: 'LogManager', action: 'sync_skipped' }, 
        'LogManager'
      );
    }
  }

  /**
   * 手動ログローテーション（統合版）
   */
  async rotateLogs(): Promise<void> {
    if (this.config.enableRotation) {
      await logRotation.rotate(true);
    } else {
      await logger.warn('LogManager: ローテーションが無効のため実行をスキップ', 
        { component: 'LogManager', action: 'rotation_skipped' }, 
        'LogManager'
      );
    }
  }

  /**
   * メモリ使用量チェック（統合版）
   */
  async checkMemoryUsage(): Promise<void> {
    if (this.config.enablePerformanceMonitoring) {
      await performanceMonitor.checkMemoryUsage();
    }
  }

  /**
   * ログ統計情報を取得
   */
  async getLogStatistics(): Promise<{
    totalLogs: number;
    rotationMetrics?: Record<string, unknown>;
    performanceMetrics?: Record<string, unknown>;
    storageStats?: Record<string, unknown>;
  }> {
    const stats: Record<string, unknown> = {};

    try {
      // 基本ストレージ統計
      const logStorage = logger.getLogStorage();
      if (logStorage) {
        stats.storageStats = await logStorage.getStorageStats();
        stats.totalLogs = (stats.storageStats as { totalLogs: number }).totalLogs;
      }

      // ローテーション統計
      if (this.config.enableRotation) {
        stats.rotationMetrics = await logRotation.getMetrics();
      }

      // パフォーマンス統計
      if (this.config.enablePerformanceMonitoring) {
        stats.performanceMetrics = await performanceMonitor.getPerformanceMetrics();
      }

    } catch (error) {
      await logger.error('LogManager: 統計情報取得エラー', 
        { 
          component: 'LogManager', 
          action: 'get_statistics_error',
          error: error instanceof Error ? error.message : String(error)
        }, 
        'LogManager'
      );
    }

    return stats as {
      totalLogs: number;
      rotationMetrics?: Record<string, unknown>;
      performanceMetrics?: Record<string, unknown>;
      storageStats?: Record<string, unknown>;
    };
  }

  /**
   * システム全体を停止
   */
  dispose(): void {
    try {
      if (this.config.enableBackup) {
        logBackup.dispose();
      }
      
      if (this.config.enableRotation) {
        logRotation.dispose();
      }
      
      if (this.config.enablePerformanceMonitoring) {
        performanceMonitor.dispose();
      }

      this.isInitialized = false;

      void logger.info('LogManager: システム停止完了', 
        { component: 'LogManager', action: 'dispose' }, 
        'LogManager'
      );

    } catch (error) {
      console.warn('LogManager disposal error:', error);
    }
  }
}

// グローバルログマネージャーインスタンス
export const logManager = new LogManager();

// 便利な関数エクスポート（従来のAPIとの互換性のため）
export {
  logger,
  logBackup,
  logRotation,
  performanceMonitor,
};

export type { LogLevel, LogEntry }; 
/**
 * ログバックアップ・同期ユーティリティ
 * 
 * フロントエンドログをバックエンドサーバーと同期し、
 * バックアップとリストア機能を提供します。
 * 
 * @example
 * ```typescript
 * import { logBackup } from '@/utils/logBackup';
 * 
 * // ログを同期
 * await logBackup.syncLogs();
 * 
 * // バックアップを作成
 * await logBackup.createBackup();
 * ```
 */

import axios from 'axios';
import { LogEntry, LogQueryFilters } from './types';
import { logger } from './logger';

export interface BackupMetadata {
  id: string;
  createdAt: string;
  size: number;
  entryCount: number;
  source: 'frontend' | 'backend' | 'sync';
  version: string;
}

export interface SyncConfig {
  /** 自動同期を有効にするか */
  enabled: boolean;
  /** 同期間隔（分） */
  intervalMinutes: number;
  /** 最大リトライ回数 */
  maxRetries: number;
  /** バッチサイズ */
  batchSize: number;
  /** 圧縮を有効にするか */
  enableCompression: boolean;
}

class LogBackup {
  private syncConfig: SyncConfig = {
    enabled: true,
    intervalMinutes: 15,
    maxRetries: 3,
    batchSize: 100,
    enableCompression: true,
  };
  
  private syncTimer: NodeJS.Timeout | null = null;
  private lastSyncTimestamp: string | null = null;
  private isActive = false;

  /**
   * バックアップシステムを初期化
   */
  async initialize(): Promise<void> {
    try {
      await logger.info('LogBackup: バックアップシステム初期化開始', 
        { component: 'LogBackup', action: 'initialize' }, 
        'LogBackup'
      );

      // 設定を取得
      await this.loadConfig();
      
      // 最後の同期時刻を取得
      await this.loadLastSyncTimestamp();

      // 自動同期を開始
      if (this.syncConfig.enabled) {
        await this.startAutoSync();
      }

      this.isActive = true;

      await logger.info('LogBackup: バックアップシステム初期化完了', 
        { 
          component: 'LogBackup', 
          action: 'initialize_complete',
          config: this.syncConfig,
          lastSync: this.lastSyncTimestamp
        }, 
        'LogBackup'
      );

    } catch (error) {
      await logger.error('LogBackup: 初期化エラー', 
        { 
          component: 'LogBackup', 
          action: 'initialize_error',
          error: error instanceof Error ? error.message : String(error)
        }, 
        'LogBackup'
      );
      throw error;
    }
  }

  /**
   * ログをバックエンドと同期
   */
  async syncLogs(): Promise<void> {
    if (!this.isActive) {
      await logger.warn('LogBackup: 非アクティブ状態での同期試行', 
        { component: 'LogBackup', action: 'sync_inactive' }, 
        'LogBackup'
      );
      return;
    }

    try {
      await logger.info('LogBackup: ログ同期開始', 
        { component: 'LogBackup', action: 'sync_start' }, 
        'LogBackup'
      );

      const logStorage = logger.getLogStorage();
      if (!logStorage) {
        throw new Error('ログストレージが利用できません');
      }

      // 最後の同期以降のログを取得
      const filters: LogQueryFilters = {};
      if (this.lastSyncTimestamp) {
        filters.startDate = new Date(this.lastSyncTimestamp);
      }

      const logsToSync = await logStorage.getLogs(filters);
      
      if (logsToSync.length === 0) {
        await logger.debug('LogBackup: 同期対象ログなし', 
          { component: 'LogBackup', action: 'sync_no_logs' }, 
          'LogBackup'
        );
        return;
      }

      // バッチごとに処理
      const batches = this.createBatches(logsToSync, this.syncConfig.batchSize);
      let syncedCount = 0;

      for (const batch of batches) {
        await this.syncBatch(batch);
        syncedCount += batch.length;
        
        await logger.debug('LogBackup: バッチ同期完了', 
          { 
            component: 'LogBackup', 
            action: 'sync_batch_complete',
            batchSize: batch.length,
            totalSynced: syncedCount
          }, 
          'LogBackup'
        );
      }

      // 同期時刻を更新
      this.lastSyncTimestamp = new Date().toISOString();
      await this.saveLastSyncTimestamp();

      await logger.info('LogBackup: ログ同期完了', 
        { 
          component: 'LogBackup', 
          action: 'sync_complete',
          syncedCount,
          lastSync: this.lastSyncTimestamp
        }, 
        'LogBackup'
      );

    } catch (error) {
      await logger.error('LogBackup: ログ同期エラー', 
        { 
          component: 'LogBackup', 
          action: 'sync_error',
          error: error instanceof Error ? error.message : String(error)
        }, 
        'LogBackup'
      );
      throw error;
    }
  }

  /**
   * バックアップを作成
   */
  async createBackup(): Promise<BackupMetadata> {
    try {
      await logger.info('LogBackup: バックアップ作成開始', 
        { component: 'LogBackup', action: 'backup_start' }, 
        'LogBackup'
      );

      const logStorage = logger.getLogStorage();
      if (!logStorage) {
        throw new Error('ログストレージが利用できません');
      }

      const allLogs = await logStorage.getLogs();
      const stats = await logStorage.getStorageStats();

      const backupData = {
        metadata: {
          createdAt: new Date().toISOString(),
          source: 'frontend' as const,
          version: '1.0.0',
          entryCount: allLogs.length,
          storageType: stats.storageType,
        },
        logs: allLogs,
      };

      const response = await axios.post('/api/logs/backup', backupData, {
        headers: {
          'Content-Type': 'application/json',
        },
        timeout: 30000, // 30秒タイムアウト
      });

      const backup: BackupMetadata = response.data;

      await logger.info('LogBackup: バックアップ作成完了', 
        { 
          component: 'LogBackup', 
          action: 'backup_complete',
          backupId: backup.id,
          entryCount: backup.entryCount,
          size: backup.size
        }, 
        'LogBackup'
      );

      return backup;

    } catch (error) {
      await logger.error('LogBackup: バックアップ作成エラー', 
        { 
          component: 'LogBackup', 
          action: 'backup_error',
          error: error instanceof Error ? error.message : String(error)
        }, 
        'LogBackup'
      );
      throw error;
    }
  }

  /**
   * バックアップからリストア
   */
  async restoreFromBackup(backupId: string): Promise<void> {
    try {
      await logger.info('LogBackup: リストア開始', 
        { 
          component: 'LogBackup', 
          action: 'restore_start',
          backupId 
        }, 
        'LogBackup'
      );

      const response = await axios.get(`/api/logs/backup/${backupId}`, {
        timeout: 60000, // 60秒タイムアウト
      });

      const backupData = response.data;
      const logs: LogEntry[] = backupData.logs;

      const logStorage = logger.getLogStorage();
      if (!logStorage) {
        throw new Error('ログストレージが利用できません');
      }

      // 既存ログをクリア
      await logStorage.clearLogs();

      // バックアップログを復元
      for (const log of logs) {
        await logStorage.saveLog(log);
      }

      await logger.info('LogBackup: リストア完了', 
        { 
          component: 'LogBackup', 
          action: 'restore_complete',
          backupId,
          restoredCount: logs.length
        }, 
        'LogBackup'
      );

    } catch (error) {
      await logger.error('LogBackup: リストアエラー', 
        { 
          component: 'LogBackup', 
          action: 'restore_error',
          backupId,
          error: error instanceof Error ? error.message : String(error)
        }, 
        'LogBackup'
      );
      throw error;
    }
  }

  /**
   * バックアップ一覧を取得
   */
  async getBackupList(): Promise<BackupMetadata[]> {
    try {
      const response = await axios.get('/api/logs/backups');
      return response.data;
    } catch (error) {
      await logger.error('LogBackup: バックアップ一覧取得エラー', 
        { 
          component: 'LogBackup', 
          action: 'backup_list_error',
          error: error instanceof Error ? error.message : String(error)
        }, 
        'LogBackup'
      );
      throw error;
    }
  }

  /**
   * 自動同期を開始
   */
  private async startAutoSync(): Promise<void> {
    if (this.syncTimer) {
      clearInterval(this.syncTimer);
    }

    const intervalMs = this.syncConfig.intervalMinutes * 60 * 1000;
    
    this.syncTimer = setInterval(async () => {
      try {
        await this.syncLogs();
      } catch (error) {
        await logger.warn('LogBackup: 自動同期エラー（継続）', 
          { 
            component: 'LogBackup', 
            action: 'auto_sync_error',
            error: error instanceof Error ? error.message : String(error)
          }, 
          'LogBackup'
        );
      }
    }, intervalMs);

    await logger.info('LogBackup: 自動同期開始', 
      { 
        component: 'LogBackup', 
        action: 'auto_sync_start',
        intervalMinutes: this.syncConfig.intervalMinutes
      }, 
      'LogBackup'
    );
  }

  /**
   * バッチ同期を実行
   */
  private async syncBatch(logs: LogEntry[]): Promise<void> {
    const maxRetries = this.syncConfig.maxRetries;
    let attempt = 0;

    while (attempt < maxRetries) {
      try {
        await axios.post('/api/logs/sync', {
          logs,
          timestamp: new Date().toISOString(),
          batchId: `batch_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        }, {
          timeout: 15000, // 15秒タイムアウト
        });
        
        return; // 成功したら終了
        
      } catch (error) {
        attempt++;
        
        if (attempt >= maxRetries) {
          throw error;
        }
        
        const delayMs = Math.pow(2, attempt) * 1000; // エクスポネンシャルバックオフ
        await new Promise(resolve => setTimeout(resolve, delayMs));
        
        await logger.warn('LogBackup: バッチ同期リトライ', 
          { 
            component: 'LogBackup', 
            action: 'sync_batch_retry',
            attempt,
            maxRetries,
            delayMs,
            error: error instanceof Error ? error.message : String(error)
          }, 
          'LogBackup'
        );
      }
    }
  }

  /**
   * ログを指定サイズのバッチに分割
   */
  private createBatches<T>(array: T[], batchSize: number): T[][] {
    const batches: T[][] = [];
    for (let i = 0; i < array.length; i += batchSize) {
      batches.push(array.slice(i, i + batchSize));
    }
    return batches;
  }

  /**
   * 設定を読み込み
   */
  private async loadConfig(): Promise<void> {
    try {
      const response = await axios.get('/api/logs/sync-config');
      this.syncConfig = { ...this.syncConfig, ...response.data };
    } catch {
      // 設定取得に失敗した場合はデフォルト設定を使用
      await logger.warn('LogBackup: 設定取得失敗、デフォルト設定を使用', 
        { 
          component: 'LogBackup', 
          action: 'config_load_fallback',
          defaultConfig: this.syncConfig
        }, 
        'LogBackup'
      );
    }
  }

  /**
   * 最後の同期時刻を読み込み
   */
  private async loadLastSyncTimestamp(): Promise<void> {
    try {
      this.lastSyncTimestamp = localStorage.getItem('lastSyncTimestamp');
    } catch {
      await logger.debug('LogBackup: 同期時刻読み込みエラー', 
        { component: 'LogBackup', action: 'load_sync_timestamp_error' }, 
        'LogBackup'
      );
    }
  }

  /**
   * 最後の同期時刻を保存
   */
  private async saveLastSyncTimestamp(): Promise<void> {
    try {
      if (this.lastSyncTimestamp) {
        localStorage.setItem('lastSyncTimestamp', this.lastSyncTimestamp);
      }
    } catch {
      await logger.debug('LogBackup: 同期時刻保存エラー', 
        { component: 'LogBackup', action: 'save_sync_timestamp_error' }, 
        'LogBackup'
      );
    }
  }

  /**
   * 同期設定を更新
   */
  updateConfig(newConfig: Partial<SyncConfig>): void {
    this.syncConfig = { ...this.syncConfig, ...newConfig };
    
    // 自動同期が有効になった場合は開始
    if (newConfig.enabled && !this.syncTimer) {
      void this.startAutoSync();
    }
    
    // 自動同期が無効になった場合は停止
    if (newConfig.enabled === false && this.syncTimer) {
      clearInterval(this.syncTimer);
      this.syncTimer = null;
    }
  }

  /**
   * 現在の設定を取得
   */
  getConfig(): SyncConfig {
    return { ...this.syncConfig };
  }

  /**
   * システムを停止
   */
  dispose(): void {
    if (this.syncTimer) {
      clearInterval(this.syncTimer);
      this.syncTimer = null;
    }
    this.isActive = false;
  }
}

// グローバルバックアップインスタンス
export const logBackup = new LogBackup(); 
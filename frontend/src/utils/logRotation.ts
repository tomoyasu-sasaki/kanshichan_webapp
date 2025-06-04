/**
 * ログローテーション管理システム
 * 
 * ファイルサイズ、エントリ数、日付に基づく自動ローテーション機能を提供します。
 * 古いログファイルのアーカイブと削除も管理します。
 * 
 * @example
 * ```typescript
 * import { logRotation } from '@/utils/logRotation';
 * 
 * // ローテーション設定
 * logRotation.configure({
 *   maxSizeKB: 1024,
 *   maxEntries: 1000,
 *   retentionDays: 30
 * });
 * 
 * // 手動ローテーション実行
 * await logRotation.rotate();
 * ```
 */

import { LogEntry, LogLevel } from './types';
import { logger } from './logger';

export interface RotationConfig {
  /** 自動ローテーションを有効にするか */
  enabled: boolean;
  /** 最大ファイルサイズ（KB） */
  maxSizeKB: number;
  /** 最大エントリ数 */
  maxEntries: number;
  /** ログ保持期間（日） */
  retentionDays: number;
  /** ローテーションチェック間隔（分） */
  checkIntervalMinutes: number;
  /** アーカイブ形式 */
  archiveFormat: 'json' | 'csv';
  /** 圧縮を有効にするか */
  enableCompression: boolean;
}

export interface RotationMetrics {
  /** 現在のログサイズ（KB） */
  currentSizeKB: number;
  /** 現在のエントリ数 */
  currentEntries: number;
  /** 最後のローテーション時刻 */
  lastRotation?: string;
  /** 次のローテーション予定時刻 */
  nextRotation?: string;
  /** アーカイブファイル数 */
  archiveCount: number;
  /** ローテーション回数 */
  rotationCount: number;
}

class LogRotation {
  private config: RotationConfig = {
    enabled: true,
    maxSizeKB: 1024, // 1MB
    maxEntries: 1000,
    retentionDays: 30,
    checkIntervalMinutes: 60, // 1時間
    archiveFormat: 'json',
    enableCompression: false,
  };

  private checkTimer: NodeJS.Timeout | null = null;
  private rotationCount = 0;
  private lastRotation: string | null = null;
  private isActive = false;

  /**
   * ローテーションシステムを初期化
   */
  async initialize(): Promise<void> {
    try {
      await logger.info('LogRotation: ローテーションシステム初期化開始', 
        { component: 'LogRotation', action: 'initialize' }, 
        'LogRotation'
      );

      // 設定を読み込み
      await this.loadConfig();
      
      // 統計を読み込み
      await this.loadMetrics();

      // 自動チェックを開始
      if (this.config.enabled) {
        await this.startAutoRotationCheck();
      }

      this.isActive = true;

      await logger.info('LogRotation: ローテーションシステム初期化完了', 
        { 
          component: 'LogRotation', 
          action: 'initialize_complete',
          config: this.config,
          lastRotation: this.lastRotation,
          rotationCount: this.rotationCount
        }, 
        'LogRotation'
      );

    } catch (error) {
      await logger.error('LogRotation: 初期化エラー', 
        { 
          component: 'LogRotation', 
          action: 'initialize_error',
          error: error instanceof Error ? error.message : String(error)
        }, 
        'LogRotation'
      );
      throw error;
    }
  }

  /**
   * ローテーションを実行
   */
  async rotate(force = false): Promise<void> {
    if (!this.isActive && !force) {
      await logger.warn('LogRotation: 非アクティブ状態でのローテーション試行', 
        { component: 'LogRotation', action: 'rotate_inactive' }, 
        'LogRotation'
      );
      return;
    }

    try {
      await logger.info('LogRotation: ローテーション開始', 
        { 
          component: 'LogRotation', 
          action: 'rotate_start',
          force 
        }, 
        'LogRotation'
      );

      const logStorage = logger.getLogStorage();
      if (!logStorage) {
        throw new Error('ログストレージが利用できません');
      }

      // 現在の統計を取得
      const metrics = await this.getMetrics();
      
      // ローテーション条件をチェック
      const shouldRotate = force || this.shouldRotate(metrics);
      
      if (!shouldRotate) {
        await logger.debug('LogRotation: ローテーション条件未満、スキップ', 
          { 
            component: 'LogRotation', 
            action: 'rotate_skip',
            metrics 
          }, 
          'LogRotation'
        );
        return;
      }

      // 現在のログをアーカイブ
      await this.archiveCurrentLogs();
      
      // 古いアーカイブを清理
      await this.cleanupOldArchives();

      // ローテーション統計を更新
      this.rotationCount++;
      this.lastRotation = new Date().toISOString();
      await this.saveMetrics();

      await logger.info('LogRotation: ローテーション完了', 
        { 
          component: 'LogRotation', 
          action: 'rotate_complete',
          rotationCount: this.rotationCount,
          archivedEntries: metrics.currentEntries
        }, 
        'LogRotation'
      );

    } catch (error) {
      await logger.error('LogRotation: ローテーションエラー', 
        { 
          component: 'LogRotation', 
          action: 'rotate_error',
          error: error instanceof Error ? error.message : String(error)
        }, 
        'LogRotation'
      );
      throw error;
    }
  }

  /**
   * 現在のメトリクスを取得
   */
  async getMetrics(): Promise<RotationMetrics> {
    try {
      const logStorage = logger.getLogStorage();
      if (!logStorage) {
        throw new Error('ログストレージが利用できません');
      }

      const stats = await logStorage.getStorageStats();
      const archiveCount = await this.getArchiveCount();

      return {
        currentSizeKB: Math.round(stats.sizeEstimate / 1024),
        currentEntries: stats.totalLogs,
        lastRotation: this.lastRotation || undefined,
        nextRotation: this.calculateNextRotation(),
        archiveCount,
        rotationCount: this.rotationCount,
      };

    } catch (error) {
      await logger.error('LogRotation: メトリクス取得エラー', 
        { 
          component: 'LogRotation', 
          action: 'get_metrics_error',
          error: error instanceof Error ? error.message : String(error)
        }, 
        'LogRotation'
      );
      throw error;
    }
  }

  /**
   * ローテーション条件をチェック
   */
  private shouldRotate(metrics: RotationMetrics): boolean {
    // サイズチェック
    if (metrics.currentSizeKB >= this.config.maxSizeKB) {
      return true;
    }

    // エントリ数チェック
    if (metrics.currentEntries >= this.config.maxEntries) {
      return true;
    }

    // 日付チェック（24時間経過）
    if (this.lastRotation) {
      const lastRotationTime = new Date(this.lastRotation).getTime();
      const now = new Date().getTime();
      const hoursElapsed = (now - lastRotationTime) / (1000 * 60 * 60);
      
      if (hoursElapsed >= 24) {
        return true;
      }
    }

    return false;
  }

  /**
   * 現在のログをアーカイブ
   */
  private async archiveCurrentLogs(): Promise<void> {
    try {
      const logStorage = logger.getLogStorage();
      if (!logStorage) {
        throw new Error('ログストレージが利用できません');
      }

      const logs = await logStorage.getLogs();
      
      if (logs.length === 0) {
        await logger.debug('LogRotation: アーカイブ対象ログなし', 
          { component: 'LogRotation', action: 'archive_no_logs' }, 
          'LogRotation'
        );
        return;
      }

      // アーカイブファイル名を生成
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const filename = `archived-${timestamp}-${this.rotationCount + 1}.${this.config.archiveFormat}`;

      // アーカイブデータを準備
      const archiveData = {
        metadata: {
          createdAt: new Date().toISOString(),
          entryCount: logs.length,
          rotationCount: this.rotationCount + 1,
          originalSize: JSON.stringify(logs).length,
        },
        logs,
      };

      // LocalStorageにアーカイブを保存
      const archiveKey = `kanshi_chan_archive_${timestamp}`;
      localStorage.setItem(archiveKey, JSON.stringify(archiveData));

      // ファイルとしてダウンロード（オプション）
      if (this.config.archiveFormat === 'json') {
        await this.downloadArchive(
          JSON.stringify(archiveData, null, 2),
          filename,
          'application/json'
        );
      } else {
        const csv = this.convertLogsToCSV(logs);
        await this.downloadArchive(csv, filename, 'text/csv');
      }

      // 現在のログをクリア
      await logStorage.clearLogs();

      await logger.info('LogRotation: ログアーカイブ完了', 
        { 
          component: 'LogRotation', 
          action: 'archive_complete',
          filename,
          entryCount: logs.length,
          archiveKey
        }, 
        'LogRotation'
      );

    } catch (error) {
      await logger.error('LogRotation: アーカイブエラー', 
        { 
          component: 'LogRotation', 
          action: 'archive_error',
          error: error instanceof Error ? error.message : String(error)
        }, 
        'LogRotation'
      );
      throw error;
    }
  }

  /**
   * 古いアーカイブを削除
   */
  private async cleanupOldArchives(): Promise<void> {
    try {
      const cutoffDate = new Date();
      cutoffDate.setDate(cutoffDate.getDate() - this.config.retentionDays);
      const cutoffTime = cutoffDate.getTime();

      let removedCount = 0;
      const archiveKeys: string[] = [];

      // LocalStorage内のアーカイブキーを検索
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key?.startsWith('kanshi_chan_archive_')) {
          archiveKeys.push(key);
        }
      }

      for (const key of archiveKeys) {
        try {
          const archiveData = JSON.parse(localStorage.getItem(key) || '{}');
          const archiveTime = new Date(archiveData.metadata?.createdAt).getTime();

          if (archiveTime < cutoffTime) {
            localStorage.removeItem(key);
            removedCount++;
          }
        } catch {
          // 破損したアーカイブファイルは削除
          localStorage.removeItem(key);
          removedCount++;
        }
      }

      if (removedCount > 0) {
        await logger.info('LogRotation: 古いアーカイブ削除完了', 
          { 
            component: 'LogRotation', 
            action: 'cleanup_complete',
            removedCount,
            retentionDays: this.config.retentionDays
          }, 
          'LogRotation'
        );
      }

    } catch (error) {
      await logger.error('LogRotation: クリーンアップエラー', 
        { 
          component: 'LogRotation', 
          action: 'cleanup_error',
          error: error instanceof Error ? error.message : String(error)
        }, 
        'LogRotation'
      );
    }
  }

  /**
   * アーカイブファイル数を取得
   */
  private async getArchiveCount(): Promise<number> {
    try {
      let count = 0;
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key?.startsWith('kanshi_chan_archive_')) {
          count++;
        }
      }
      return count;
    } catch {
      return 0;
    }
  }

  /**
   * 次のローテーション時刻を計算
   */
  private calculateNextRotation(): string | undefined {
    if (!this.lastRotation) {
      return undefined;
    }

    const lastTime = new Date(this.lastRotation);
    const nextTime = new Date(lastTime.getTime() + 24 * 60 * 60 * 1000); // 24時間後
    return nextTime.toISOString();
  }

  /**
   * ログをCSVに変換
   */
  private convertLogsToCSV(logs: LogEntry[]): string {
    if (logs.length === 0) return '';

    const headers = ['timestamp', 'level', 'levelName', 'message', 'source', 'sessionId', 'context'];
    const csvRows = [headers.join(',')];

    logs.forEach(log => {
      const row = [
        `"${log.timestamp}"`,
        `"${log.level}"`,
        `"${LogLevel[log.level]}"`,
        `"${log.message.replace(/"/g, '""')}"`,
        `"${log.source || ''}"`,
        `"${log.sessionId}"`,
        `"${log.context ? JSON.stringify(log.context).replace(/"/g, '""') : ''}"`
      ];
      csvRows.push(row.join(','));
    });

    return csvRows.join('\n');
  }

  /**
   * アーカイブファイルをダウンロード
   */
  private async downloadArchive(content: string, filename: string, mimeType: string): Promise<void> {
    try {
      const blob = new Blob([content], { type: mimeType });
      const url = URL.createObjectURL(blob);
      
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      link.style.display = 'none';
      
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      URL.revokeObjectURL(url);
    } catch (error) {
      await logger.warn('LogRotation: アーカイブダウンロードエラー', 
        { 
          component: 'LogRotation', 
          action: 'download_error',
          filename,
          error: error instanceof Error ? error.message : String(error)
        }, 
        'LogRotation'
      );
    }
  }

  /**
   * 自動ローテーションチェックを開始
   */
  private async startAutoRotationCheck(): Promise<void> {
    if (this.checkTimer) {
      clearInterval(this.checkTimer);
    }

    const intervalMs = this.config.checkIntervalMinutes * 60 * 1000;
    
    this.checkTimer = setInterval(async () => {
      try {
        await this.rotate();
      } catch (error) {
        await logger.warn('LogRotation: 自動ローテーションエラー（継続）', 
          { 
            component: 'LogRotation', 
            action: 'auto_rotation_error',
            error: error instanceof Error ? error.message : String(error)
          }, 
          'LogRotation'
        );
      }
    }, intervalMs);

    await logger.info('LogRotation: 自動ローテーションチェック開始', 
      { 
        component: 'LogRotation', 
        action: 'auto_rotation_start',
        intervalMinutes: this.config.checkIntervalMinutes
      }, 
      'LogRotation'
    );
  }

  /**
   * 設定を読み込み
   */
  private async loadConfig(): Promise<void> {
    try {
      const savedConfig = localStorage.getItem('kanshi_chan_rotation_config');
      if (savedConfig) {
        this.config = { ...this.config, ...JSON.parse(savedConfig) };
      }
    } catch {
      await logger.debug('LogRotation: 設定読み込みエラー、デフォルト設定を使用', 
        { component: 'LogRotation', action: 'config_load_fallback' }, 
        'LogRotation'
      );
    }
  }

  /**
   * 統計を読み込み
   */
  private async loadMetrics(): Promise<void> {
    try {
      const savedMetrics = localStorage.getItem('kanshi_chan_rotation_metrics');
      if (savedMetrics) {
        const metrics = JSON.parse(savedMetrics);
        this.rotationCount = metrics.rotationCount || 0;
        this.lastRotation = metrics.lastRotation || null;
      }
    } catch {
      await logger.debug('LogRotation: 統計読み込みエラー', 
        { component: 'LogRotation', action: 'metrics_load_error' }, 
        'LogRotation'
      );
    }
  }

  /**
   * 統計を保存
   */
  private async saveMetrics(): Promise<void> {
    try {
      const metrics = {
        rotationCount: this.rotationCount,
        lastRotation: this.lastRotation,
      };
      localStorage.setItem('kanshi_chan_rotation_metrics', JSON.stringify(metrics));
    } catch {
      await logger.debug('LogRotation: 統計保存エラー', 
        { component: 'LogRotation', action: 'metrics_save_error' }, 
        'LogRotation'
      );
    }
  }

  /**
   * 設定を更新
   */
  updateConfig(newConfig: Partial<RotationConfig>): void {
    this.config = { ...this.config, ...newConfig };
    
    // 設定を保存
    try {
      localStorage.setItem('kanshi_chan_rotation_config', JSON.stringify(this.config));
    } catch {
      // LocalStorage保存失敗時は無視
    }
    
    // 自動チェックタイマーを再設定
    if (this.config.enabled && this.checkTimer) {
      void this.startAutoRotationCheck();
    }
    
    // 自動チェックが無効になった場合は停止
    if (!this.config.enabled && this.checkTimer) {
      clearInterval(this.checkTimer);
      this.checkTimer = null;
    }
  }

  /**
   * 現在の設定を取得
   */
  getConfig(): RotationConfig {
    return { ...this.config };
  }

  /**
   * システムを停止
   */
  dispose(): void {
    if (this.checkTimer) {
      clearInterval(this.checkTimer);
      this.checkTimer = null;
    }
    this.isActive = false;
  }
}

// グローバルローテーションインスタンス
export const logRotation = new LogRotation(); 
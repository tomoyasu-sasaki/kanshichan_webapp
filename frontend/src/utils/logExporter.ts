/**
 * ログファイルエクスポートユーティリティ
 * 
 * ブラウザ環境での制約を考慮し、仮想的なlogs/ディレクトリ構造で
 * ログファイルの管理とダウンロード機能を提供します。
 * 
 * @example
 * ```typescript
 * import { logExporter } from '@/utils/logExporter';
 * 
 * // 本日のログをダウンロード
 * await logExporter.downloadTodaysLogs();
 * 
 * // 特定期間のログをダウンロード
 * await logExporter.downloadLogsByDateRange(startDate, endDate);
 * ```
 */

import { LogEntry, LogLevel, LogQueryFilters } from './types';
import { LogStorage } from './logStorage';

export interface LogFileMetadata {
  /** ファイル名 */
  filename: string;
  /** ファイルパス（仮想） */
  path: string;
  /** ファイルサイズ（推定バイト数） */
  size: number;
  /** 作成日時 */
  createdAt: string;
  /** ログエントリ数 */
  entryCount: number;
  /** ログレベル分布 */
  levelDistribution: Record<LogLevel, number>;
}

class LogExporter {
  private storage: LogStorage;

  constructor() {
    this.storage = new LogStorage();
  }

  /**
   * ストレージを初期化
   */
  async initialize(): Promise<void> {
    await this.storage.initialize();
  }

  /**
   * 今日のログをダウンロード
   */
  async downloadTodaysLogs(format: 'json' | 'csv' = 'json'): Promise<void> {
    const today = new Date();
    const startOfDay = new Date(today.getFullYear(), today.getMonth(), today.getDate());
    const endOfDay = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 23, 59, 59);

    await this.downloadLogsByDateRange(startOfDay, endOfDay, format);
  }

  /**
   * 特定日付範囲のログをダウンロード
   */
  async downloadLogsByDateRange(
    startDate: Date,
    endDate: Date,
    format: 'json' | 'csv' = 'json'
  ): Promise<void> {
    const filters: LogQueryFilters = {
      startDate,
      endDate,
    };

    const logs = await this.storage.getLogs(filters);
    const dateRange = `${this.formatDate(startDate)}_to_${this.formatDate(endDate)}`;
    
    if (format === 'json') {
      await this.downloadAsFile(
        JSON.stringify(logs, null, 2),
        `${dateRange}-app.log.json`,
        'application/json'
      );
    } else {
      const csv = this.convertToCSV(logs);
      await this.downloadAsFile(
        csv,
        `${dateRange}-app.log.csv`,
        'text/csv'
      );
    }
  }

  /**
   * レベル別ログをダウンロード
   */
  async downloadLogsByLevel(
    level: LogLevel,
    format: 'json' | 'csv' = 'json'
  ): Promise<void> {
    const filters: LogQueryFilters = { level };
    const logs = await this.storage.getLogs(filters);
    const today = this.formatDate(new Date());
    const levelName = LogLevel[level].toLowerCase();
    
    if (format === 'json') {
      await this.downloadAsFile(
        JSON.stringify(logs, null, 2),
        `${today}-${levelName}.log.json`,
        'application/json'
      );
    } else {
      const csv = this.convertToCSV(logs);
      await this.downloadAsFile(
        csv,
        `${today}-${levelName}.log.csv`,
        'text/csv'
      );
    }
  }

  /**
   * 全ログのアーカイブをダウンロード
   */
  async downloadFullArchive(format: 'json' | 'csv' = 'json'): Promise<void> {
    const logs = await this.storage.getLogs();
    const timestamp = this.formatDateTime(new Date());
    
    if (format === 'json') {
      await this.downloadAsFile(
        JSON.stringify(logs, null, 2),
        `${timestamp}-full-archive.log.json`,
        'application/json'
      );
    } else {
      const csv = this.convertToCSV(logs);
      await this.downloadAsFile(
        csv,
        `${timestamp}-full-archive.log.csv`,
        'text/csv'
      );
    }
  }

  /**
   * ログファイルのメタデータ一覧を取得
   */
  async getLogFileList(): Promise<LogFileMetadata[]> {
    const logs = await this.storage.getLogs();
    const groupedByDate = this.groupLogsByDate(logs);
    
    return Object.entries(groupedByDate).map(([date, dateLogs]) => {
      const levelDistribution = this.calculateLevelDistribution(dateLogs);
      const content = JSON.stringify(dateLogs);
      
      return {
        filename: `${date}-app.log`,
        path: `frontend/logs/${date}-app.log`,
        size: new Blob([content]).size,
        createdAt: dateLogs[0]?.timestamp || new Date().toISOString(),
        entryCount: dateLogs.length,
        levelDistribution,
      };
    }).sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  }

  /**
   * エラーログのみを抽出してダウンロード
   */
  async downloadErrorLogs(format: 'json' | 'csv' = 'json'): Promise<void> {
    await this.downloadLogsByLevel(LogLevel.ERROR, format);
  }

  /**
   * 警告ログのみを抽出してダウンロード
   */
  async downloadWarningLogs(format: 'json' | 'csv' = 'json'): Promise<void> {
    await this.downloadLogsByLevel(LogLevel.WARN, format);
  }

  /**
   * ログサマリーレポートを生成・ダウンロード
   */
  async downloadLogSummaryReport(): Promise<void> {
    const logs = await this.storage.getLogs();
    const stats = await this.storage.getStorageStats();
    const levelDistribution = this.calculateLevelDistribution(logs);
    const sourceDistribution = this.calculateSourceDistribution(logs);
    
    const report = {
      generatedAt: new Date().toISOString(),
      summary: {
        totalLogs: stats.totalLogs,
        storageType: stats.storageType,
        sizeEstimate: `${Math.round(stats.sizeEstimate / 1024)} KB`,
        dateRange: {
          oldest: stats.oldestLog,
          newest: stats.newestLog,
        },
      },
      levelDistribution,
      sourceDistribution,
      recentErrors: logs
        .filter(log => log.level === LogLevel.ERROR)
        .slice(0, 10)
        .map(log => ({
          timestamp: log.timestamp,
          message: log.message,
          source: log.source,
        })),
    };

    const timestamp = this.formatDateTime(new Date());
    await this.downloadAsFile(
      JSON.stringify(report, null, 2),
      `${timestamp}-log-summary-report.json`,
      'application/json'
    );
  }

  /**
   * 日付別にログをグループ化
   */
  private groupLogsByDate(logs: LogEntry[]): Record<string, LogEntry[]> {
    return logs.reduce((groups, log) => {
      const date = log.timestamp.split('T')[0];
      if (!groups[date]) {
        groups[date] = [];
      }
      groups[date].push(log);
      return groups;
    }, {} as Record<string, LogEntry[]>);
  }

  /**
   * レベル分布を計算
   */
  private calculateLevelDistribution(logs: LogEntry[]): Record<LogLevel, number> {
    const distribution: Record<LogLevel, number> = {
      [LogLevel.ERROR]: 0,
      [LogLevel.WARN]: 0,
      [LogLevel.INFO]: 0,
      [LogLevel.DEBUG]: 0,
    };

    logs.forEach(log => {
      distribution[log.level]++;
    });

    return distribution;
  }

  /**
   * ソース分布を計算
   */
  private calculateSourceDistribution(logs: LogEntry[]): Record<string, number> {
    const distribution: Record<string, number> = {};

    logs.forEach(log => {
      const source = log.source || 'unknown';
      distribution[source] = (distribution[source] || 0) + 1;
    });

    return distribution;
  }

  /**
   * CSVに変換
   */
  private convertToCSV(logs: LogEntry[]): string {
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
   * 日付をフォーマット (YYYY-MM-DD)
   */
  private formatDate(date: Date): string {
    return date.toISOString().split('T')[0];
  }

  /**
   * 日時をフォーマット (YYYY-MM-DD_HH-mm-ss)
   */
  private formatDateTime(date: Date): string {
    return date.toISOString()
      .replace(/T/, '_')
      .replace(/:/g, '-')
      .split('.')[0];
  }

  /**
   * ファイルとしてダウンロード
   */
  private async downloadAsFile(
    content: string,
    filename: string,
    mimeType: string
  ): Promise<void> {
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
  }

  /**
   * リソースをクリーンアップ
   */
  dispose(): void {
    this.storage.dispose();
  }
}

// グローバルエクスポーターインスタンス
export const logExporter = new LogExporter(); 
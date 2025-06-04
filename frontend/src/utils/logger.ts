/**
 * フロントエンドログ管理システム
 * 
 * ログレベル管理、コンソール出力、ストレージ保存機能を提供します。
 * 本番環境と開発環境での設定切り替えに対応しています。
 * 
 * @example
 * ```typescript
 * import { logger } from '@/utils/logger';
 * 
 * logger.info('Application started', { version: '2.0.0' });
 * logger.error('Connection failed', { endpoint: '/api/data' });
 * ```
 */

import {
  LogLevel,
  type LogEntry,
  type LoggerConfig,
  type LogStorage
} from './types';
import { LogStorage as LogStorageClass } from './logStorage';

/** プライバシー保護のためのフィルタリング対象キー */
const SENSITIVE_KEYS = [
  'password', 'token', 'key', 'secret', 'email', 'phone', 'address',
  'name', 'username', 'userid', 'id', 'ip', 'location', 'gps'
];

/** デフォルト設定 */
const DEFAULT_CONFIG: LoggerConfig = {
  minLevel: process.env.NODE_ENV === 'production' ? LogLevel.WARN : LogLevel.INFO,
  enableConsole: true,
  enableStorage: true,
  maxStorageEntries: 1000,
  enablePrivacyFilter: true,
};

class Logger {
  private config: LoggerConfig;
  private sessionId: string;
  private logStorage: LogStorage | null = null;

  constructor(config: Partial<LoggerConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.sessionId = this.generateSessionId();
    void this.initializeStorage();
  }

  /**
   * セッションIDを生成
   */
  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * ストレージを初期化
   */
  private async initializeStorage(): Promise<void> {
    if (this.config.enableStorage) {
      try {
        this.logStorage = new LogStorageClass();
        if (this.logStorage) {
          await this.logStorage.initialize();
        }
      } catch (error) {
        console.warn('ログストレージの初期化に失敗しました:', error);
      }
    }
  }

  /**
   * プライバシー保護フィルタリング
   */
  private filterSensitiveData(data: unknown): unknown {
    if (!this.config.enablePrivacyFilter) {
      return data;
    }

    if (typeof data !== 'object' || data === null) {
      return data;
    }

    if (Array.isArray(data)) {
      return data.map(item => this.filterSensitiveData(item));
    }

    const filtered: Record<string, unknown> = {};
    Object.entries(data as Record<string, unknown>).forEach(([key, value]) => {
      const lowerKey = key.toLowerCase();
      const isSensitive = SENSITIVE_KEYS.some(sensitiveKey => 
        lowerKey.includes(sensitiveKey)
      );

      if (isSensitive) {
        filtered[key] = '[FILTERED]';
      } else if (typeof value === 'object' && value !== null) {
        filtered[key] = this.filterSensitiveData(value);
      } else {
        filtered[key] = value;
      }
    });

    return filtered;
  }

  /**
   * ログエントリを作成
   */
  private createLogEntry(
    level: LogLevel,
    message: string,
    context?: Record<string, unknown>,
    source?: string
  ): LogEntry {
    return {
      level,
      message,
      timestamp: new Date().toISOString(),
      context: context ? this.filterSensitiveData(context) as Record<string, unknown> : undefined,
      source,
      sessionId: this.sessionId,
    };
  }

  /**
   * ログを出力
   */
  private async log(
    level: LogLevel,
    message: string,
    context?: Record<string, unknown>,
    source?: string
  ): Promise<void> {
    // レベルチェック
    if (level > this.config.minLevel) {
      return;
    }

    const entry = this.createLogEntry(level, message, context, source);

    // コンソール出力
    if (this.config.enableConsole) {
      this.outputToConsole(entry);
    }

    // ストレージ保存
    if (this.config.enableStorage && this.logStorage) {
      try {
        await this.logStorage.saveLog(entry);
      } catch (error) {
        console.warn('ログの保存に失敗しました:', error);
      }
    }
  }

  /**
   * コンソールにログを出力
   */
  private outputToConsole(entry: LogEntry): void {
    const timestamp = new Date(entry.timestamp).toLocaleString('ja-JP');
    const levelStr = LogLevel[entry.level];
    const prefix = `[${timestamp}] [${levelStr}]`;

    let logMethod: typeof console.log;
    switch (entry.level) {
      case LogLevel.ERROR:
        logMethod = console.error;
        break;
      case LogLevel.WARN:
        logMethod = console.warn;
        break;
      case LogLevel.INFO:
        logMethod = console.info;
        break;
      default:
        logMethod = console.log;
    }

    if (entry.context) {
      logMethod(`${prefix} ${entry.message}`, entry.context);
    } else {
      logMethod(`${prefix} ${entry.message}`);
    }
  }

  /**
   * エラーレベルのログを出力
   */
  async error(
    message: string,
    context?: Record<string, unknown>,
    source?: string
  ): Promise<void> {
    await this.log(LogLevel.ERROR, message, context, source);
  }

  /**
   * 警告レベルのログを出力
   */
  async warn(
    message: string,
    context?: Record<string, unknown>,
    source?: string
  ): Promise<void> {
    await this.log(LogLevel.WARN, message, context, source);
  }

  /**
   * 情報レベルのログを出力
   */
  async info(
    message: string,
    context?: Record<string, unknown>,
    source?: string
  ): Promise<void> {
    await this.log(LogLevel.INFO, message, context, source);
  }

  /**
   * デバッグレベルのログを出力
   */
  async debug(
    message: string,
    context?: Record<string, unknown>,
    source?: string
  ): Promise<void> {
    await this.log(LogLevel.DEBUG, message, context, source);
  }

  /**
   * 設定を更新
   */
  updateConfig(newConfig: Partial<LoggerConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }

  /**
   * 現在の設定を取得
   */
  getConfig(): LoggerConfig {
    return { ...this.config };
  }

  /**
   * セッションIDを取得
   */
  getSessionId(): string {
    return this.sessionId;
  }

  /**
   * ログストレージインスタンスを取得
   */
  getLogStorage(): LogStorage | null {
    return this.logStorage;
  }
}

// グローバルロガーインスタンス
export const logger = new Logger();

// 型も再エクスポートして外部から使用可能に
export { LogLevel } from './types';
export type { LogEntry, LoggerConfig, LogQueryFilters, LogStorage } from './types'; 
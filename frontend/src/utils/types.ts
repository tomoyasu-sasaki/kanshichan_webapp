/**
 * ログシステム共通型定義
 * 
 * 循環参照を避けるため、ログ関連の型を集約しています。
 */

// enumは値として使用するため通常のexport
export enum LogLevel {
  ERROR = 0,
  WARN = 1,
  INFO = 2,
  DEBUG = 3,
}

// 型定義は明示的にtype export
export type LogEntry = {
  /** ログレベル */
  level: LogLevel;
  /** ログメッセージ */
  message: string;
  /** タイムスタンプ (ISO 8601) */
  timestamp: string;
  /** 追加のコンテキスト情報 */
  context?: Record<string, unknown>;
  /** ログを出力したソース（ファイル名等） */
  source?: string;
  /** セッションID（ブラウザセッション識別用） */
  sessionId: string;
};

export type LoggerConfig = {
  /** 最小ログレベル */
  minLevel: LogLevel;
  /** コンソール出力を有効にするか */
  enableConsole: boolean;
  /** ストレージ保存を有効にするか */
  enableStorage: boolean;
  /** 最大保存ログ数 */
  maxStorageEntries: number;
  /** 個人情報フィルタリングを有効にするか */
  enablePrivacyFilter: boolean;
};

export type LogQueryFilters = {
  level?: LogLevel;
  startDate?: Date;
  endDate?: Date;
  source?: string;
  limit?: number;
};

export type StorageStats = {
  totalLogs: number;
  sizeEstimate: number;
  oldestLog?: string;
  newestLog?: string;
  storageType: 'IndexedDB' | 'localStorage';
};

// ログストレージインターフェース
export interface LogStorage {
  initialize(): Promise<void>;
  saveLog(entry: LogEntry): Promise<void>;
  getLogs(filters?: LogQueryFilters): Promise<LogEntry[]>;
  clearLogs(): Promise<void>;
  exportLogs(format?: 'json' | 'csv'): Promise<void>;
  getStorageStats(): Promise<StorageStats>;
} 
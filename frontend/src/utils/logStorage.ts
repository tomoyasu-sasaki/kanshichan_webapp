/**
 * ログストレージ管理システム
 * 
 * IndexedDBとLocalStorageを使用してログデータを永続化し、
 * 日付ベースのログファイル生成とエクスポート機能を提供します。
 * 
 * @example
 * ```typescript
 * const storage = new LogStorage();
 * await storage.initialize();
 * await storage.saveLog(logEntry);
 * const logs = await storage.getLogs({ level: LogLevel.ERROR });
 * ```
 */

import type { LogEntry, LogQueryFilters, LogStorage as ILogStorage, StorageStats } from './types';

export class LogStorage implements ILogStorage {
  private dbName = 'KanshiChanLogs';
  private dbVersion = 1;
  private storeName = 'logs';
  private db: IDBDatabase | null = null;
  private maxEntries = 1000;

  /**
   * ストレージを初期化
   */
  async initialize(): Promise<void> {
    try {
      await this.initIndexedDB();
    } catch (error) {
      console.warn('IndexedDB初期化に失敗、LocalStorageを使用します:', error);
      this.setupLocalStorageFallback();
    }
  }

  /**
   * IndexedDBを初期化
   */
  private initIndexedDB(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!window.indexedDB) {
        reject(new Error('IndexedDB is not supported'));
        return;
      }

      const request = window.indexedDB.open(this.dbName, this.dbVersion);

      request.onerror = () => {
        reject(new Error(`IndexedDB error: ${request.error?.message}`));
      };

      request.onsuccess = () => {
        this.db = request.result;
        resolve();
      };

      request.onupgradeneeded = () => {
        const db = request.result;
        
        // ログストアを作成
        if (!db.objectStoreNames.contains(this.storeName)) {
          const store = db.createObjectStore(this.storeName, { 
            keyPath: 'id', 
            autoIncrement: true 
          });
          
          // インデックスを作成
          store.createIndex('timestamp', 'timestamp', { unique: false });
          store.createIndex('level', 'level', { unique: false });
          store.createIndex('sessionId', 'sessionId', { unique: false });
          store.createIndex('source', 'source', { unique: false });
        }
      };
    });
  }

  /**
   * LocalStorageフォールバック設定
   */
  private setupLocalStorageFallback(): void {
    // LocalStorageが利用可能かチェック
    try {
      const testKey = '__kanshi_chan_storage_test__';
      localStorage.setItem(testKey, 'test');
      localStorage.removeItem(testKey);
    } catch {
      throw new Error('Neither IndexedDB nor localStorage is available');
    }
  }

  /**
   * ログを保存
   */
  async saveLog(entry: LogEntry): Promise<void> {
    if (this.db) {
      await this.saveToIndexedDB(entry);
    } else {
      await this.saveToLocalStorage(entry);
    }
    
    // ストレージサイズ管理
    await this.manageStorageSize();
  }

  /**
   * IndexedDBにログを保存
   */
  private saveToIndexedDB(entry: LogEntry): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.db) {
        reject(new Error('IndexedDB is not initialized'));
        return;
      }

      const transaction = this.db.transaction([this.storeName], 'readwrite');
      const store = transaction.objectStore(this.storeName);
      
      const request = store.add({
        ...entry,
        savedAt: new Date().toISOString(),
      });

      request.onsuccess = () => resolve();
      request.onerror = () => reject(new Error(`Failed to save log: ${request.error?.message}`));
    });
  }

  /**
   * LocalStorageにログを保存
   */
  private async saveToLocalStorage(entry: LogEntry): Promise<void> {
    try {
      const logsKey = 'kanshi_chan_logs';
      const existingLogs = JSON.parse(localStorage.getItem(logsKey) || '[]') as LogEntry[];
      
      const newLog = {
        ...entry,
        savedAt: new Date().toISOString(),
      };
      
      existingLogs.push(newLog);
      
      // 最大エントリ数を超えた場合は古いログを削除
      if (existingLogs.length > this.maxEntries) {
        existingLogs.splice(0, existingLogs.length - this.maxEntries);
      }
      
      localStorage.setItem(logsKey, JSON.stringify(existingLogs));
    } catch (error) {
      throw new Error(`Failed to save log to localStorage: ${error}`);
    }
  }

  /**
   * ログを取得
   */
  async getLogs(filters?: LogQueryFilters): Promise<LogEntry[]> {
    let logs: LogEntry[];
    
    if (this.db) {
      logs = await this.getFromIndexedDB(filters);
    } else {
      logs = await this.getFromLocalStorage();
    }
    
    return this.applyFilters(logs, filters);
  }

  /**
   * IndexedDBからログを取得
   */
  private getFromIndexedDB(filters?: LogQueryFilters): Promise<LogEntry[]> {
    return new Promise((resolve, reject) => {
      if (!this.db) {
        reject(new Error('IndexedDB is not initialized'));
        return;
      }

      const transaction = this.db.transaction([this.storeName], 'readonly');
      const store = transaction.objectStore(this.storeName);
      
      let request: IDBRequest;
      
      // フィルタに応じてインデックスを使用
      if (filters?.level !== undefined) {
        const index = store.index('level');
        request = index.getAll(filters.level);
      } else if (filters?.source) {
        const index = store.index('source');
        request = index.getAll(filters.source);
      } else {
        request = store.getAll();
      }

      request.onsuccess = () => {
        const logs = request.result || [];
        resolve(logs.map((log: Record<string, unknown>) => ({
          level: log.level as number,
          message: log.message as string,
          timestamp: log.timestamp as string,
          context: log.context as Record<string, unknown> | undefined,
          source: log.source as string | undefined,
          sessionId: log.sessionId as string,
        })));
      };
      
      request.onerror = () => {
        reject(new Error(`Failed to get logs: ${request.error?.message}`));
      };
    });
  }

  /**
   * LocalStorageからログを取得
   */
  private async getFromLocalStorage(): Promise<LogEntry[]> {
    try {
      const logsKey = 'kanshi_chan_logs';
      const logs = JSON.parse(localStorage.getItem(logsKey) || '[]') as LogEntry[];
      return logs;
    } catch (error) {
      throw new Error(`Failed to get logs from localStorage: ${error}`);
    }
  }

  /**
   * フィルタを適用
   */
  private applyFilters(logs: LogEntry[], filters?: LogQueryFilters): LogEntry[] {
    if (!filters) return logs;

    let filteredLogs = logs;

    // レベルフィルタ
    if (filters.level !== undefined) {
      filteredLogs = filteredLogs.filter(log => log.level === filters.level);
    }

    // 日付範囲フィルタ
    if (filters.startDate) {
      const startTime = filters.startDate.getTime();
      filteredLogs = filteredLogs.filter(log => 
        new Date(log.timestamp).getTime() >= startTime
      );
    }

    if (filters.endDate) {
      const endTime = filters.endDate.getTime();
      filteredLogs = filteredLogs.filter(log => 
        new Date(log.timestamp).getTime() <= endTime
      );
    }

    // ソースフィルタ
    if (filters.source) {
      filteredLogs = filteredLogs.filter(log => log.source === filters.source);
    }

    // リミット適用
    if (filters.limit && filters.limit > 0) {
      filteredLogs = filteredLogs.slice(0, filters.limit);
    }

    return filteredLogs.sort((a, b) => 
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );
  }

  /**
   * ログをクリア
   */
  async clearLogs(): Promise<void> {
    if (this.db) {
      await this.clearIndexedDB();
    } else {
      await this.clearLocalStorage();
    }
  }

  /**
   * IndexedDBをクリア
   */
  private clearIndexedDB(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.db) {
        reject(new Error('IndexedDB is not initialized'));
        return;
      }

      const transaction = this.db.transaction([this.storeName], 'readwrite');
      const store = transaction.objectStore(this.storeName);
      
      const request = store.clear();
      
      request.onsuccess = () => resolve();
      request.onerror = () => reject(new Error(`Failed to clear logs: ${request.error?.message}`));
    });
  }

  /**
   * LocalStorageをクリア
   */
  private async clearLocalStorage(): Promise<void> {
    try {
      localStorage.removeItem('kanshi_chan_logs');
    } catch (error) {
      throw new Error(`Failed to clear localStorage: ${error}`);
    }
  }

  /**
   * ログをエクスポート
   */
  async exportLogs(format: 'json' | 'csv' = 'json'): Promise<void> {
    const logs = await this.getLogs();
    const today = new Date().toISOString().split('T')[0];
    
    if (format === 'json') {
      await this.downloadAsFile(
        JSON.stringify(logs, null, 2),
        `${today}-kanshi-chan-logs.json`,
        'application/json'
      );
    } else {
      const csv = this.convertToCSV(logs);
      await this.downloadAsFile(
        csv,
        `${today}-kanshi-chan-logs.csv`,
        'text/csv'
      );
    }
  }

  /**
   * CSVに変換
   */
  private convertToCSV(logs: LogEntry[]): string {
    if (logs.length === 0) return '';

    const headers = ['timestamp', 'level', 'message', 'source', 'sessionId', 'context'];
    const csvRows = [headers.join(',')];

    logs.forEach(log => {
      const row = [
        `"${log.timestamp}"`,
        `"${log.level}"`,
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
   * ファイルとしてダウンロード
   */
  private async downloadAsFile(content: string, filename: string, mimeType: string): Promise<void> {
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
   * ストレージサイズを管理
   */
  private async manageStorageSize(): Promise<void> {
    const logs = await this.getLogs();
    
    if (logs.length > this.maxEntries) {
      // 古いログを削除
      const logsToKeep = logs
        .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
        .slice(0, this.maxEntries);
      
      await this.clearLogs();
      
      // 保持するログを再保存
      for (const log of logsToKeep.reverse()) {
        if (this.db) {
          await this.saveToIndexedDB(log);
        } else {
          await this.saveToLocalStorage(log);
        }
      }
    }
  }

  /**
   * ストレージ統計を取得
   */
  async getStorageStats(): Promise<StorageStats> {
    const logs = await this.getLogs();
    const sortedLogs = logs.sort((a, b) => 
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );

    // サイズ推定（JSON文字列の長さベース）
    const sizeEstimate = JSON.stringify(logs).length;

    return {
      totalLogs: logs.length,
      sizeEstimate,
      oldestLog: sortedLogs[0]?.timestamp,
      newestLog: sortedLogs[sortedLogs.length - 1]?.timestamp,
      storageType: this.db ? 'IndexedDB' : 'localStorage',
    };
  }

  /**
   * リソースをクリーンアップ
   */
  dispose(): void {
    if (this.db) {
      this.db.close();
      this.db = null;
    }
  }
} 
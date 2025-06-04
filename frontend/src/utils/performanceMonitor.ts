/**
 * パフォーマンス監視ログシステム
 * 
 * アプリケーションのパフォーマンス指標を監視し、
 * 問題のある領域を特定するためのログを生成します。
 * 
 * @example
 * ```typescript
 * import { performanceMonitor } from '@/utils/performanceMonitor';
 * 
 * // API呼び出し監視
 * const timer = performanceMonitor.startTimer('api_call');
 * const result = await fetchData();
 * timer.end({ endpoint: '/api/data', status: 200 });
 * 
 * // メモリ使用量チェック
 * performanceMonitor.checkMemoryUsage();
 * ```
 */

import { logger } from './logger';
import { LogLevel } from './types';

export interface PerformanceMetrics {
  /** メモリ使用量（MB） */
  memoryUsage: {
    used: number;
    total: number;
    percentage: number;
  };
  /** ナビゲーションタイミング */
  navigationTiming: {
    pageLoadTime: number;
    domContentLoadedTime: number;
    resourceLoadTime: number;
  };
  /** リソース使用量 */
  resourceUsage: {
    activeConnections: number;
    cacheSize: number;
    storageUsage: number;
  };
  /** パフォーマンス警告 */
  warnings: string[];
}

export interface TimerResult {
  /** タイマー名 */
  name: string;
  /** 開始時刻 */
  startTime: number;
  /** 終了時刻 */
  endTime: number;
  /** 実行時間（ミリ秒） */
  duration: number;
  /** 追加コンテキスト */
  context?: Record<string, unknown>;
}

class Timer {
  constructor(
    private name: string,
    private startTime: number,
    private monitor: PerformanceMonitor
  ) {}

  /**
   * タイマーを終了し、ログを記録
   */
  async end(context?: Record<string, unknown>): Promise<TimerResult> {
    const endTime = performance.now();
    const duration = endTime - this.startTime;

    const result: TimerResult = {
      name: this.name,
      startTime: this.startTime,
      endTime,
      duration,
      context,
    };

    await this.monitor.logTimerResult(result);
    return result;
  }
}

class PerformanceMonitor {
  private config = {
    /** メモリ警告閾値（MB） */
    memoryWarningThreshold: 100,
    /** API応答時間警告閾値（ms） */
    apiResponseWarningThreshold: 3000,
    /** レンダリング時間警告閾値（ms） */
    renderWarningThreshold: 100,
    /** 監視間隔（分） */
    monitoringIntervalMinutes: 5,
    /** パフォーマンスログを有効にするか */
    enabled: true,
  };

  private monitoringTimer: NodeJS.Timeout | null = null;
  private isActive = false;
  private performanceObserver: PerformanceObserver | null = null;

  /**
   * パフォーマンス監視を初期化
   */
  async initialize(): Promise<void> {
    try {
      await logger.info('PerformanceMonitor: パフォーマンス監視初期化開始', 
        { component: 'PerformanceMonitor', action: 'initialize' }, 
        'PerformanceMonitor'
      );

      // 設定を読み込み
      this.loadConfig();

      if (this.config.enabled) {
        // Performance Observer を設定
        this.setupPerformanceObserver();
        
        // 定期監視を開始
        this.startPeriodicMonitoring();
        
        // ページ読み込み完了時の初期測定
        if (document.readyState === 'complete') {
          await this.measureInitialPerformance();
        } else {
          window.addEventListener('load', () => {
            void this.measureInitialPerformance();
          });
        }
      }

      this.isActive = true;

      await logger.info('PerformanceMonitor: パフォーマンス監視初期化完了', 
        { 
          component: 'PerformanceMonitor', 
          action: 'initialize_complete',
          config: this.config 
        }, 
        'PerformanceMonitor'
      );

    } catch (error) {
      await logger.error('PerformanceMonitor: 初期化エラー', 
        { 
          component: 'PerformanceMonitor', 
          action: 'initialize_error',
          error: error instanceof Error ? error.message : String(error)
        }, 
        'PerformanceMonitor'
      );
      throw error;
    }
  }

  /**
   * タイマーを開始
   */
  startTimer(name: string): Timer {
    const startTime = performance.now();
    return new Timer(name, startTime, this);
  }

  /**
   * タイマー結果をログに記録
   */
  async logTimerResult(result: TimerResult): Promise<void> {
    try {
      const level = this.determineLogLevel(result);
      const message = `Performance: ${result.name} completed in ${result.duration.toFixed(2)}ms`;

      switch (level) {
        case LogLevel.ERROR:
          await logger.error(message, {
            component: 'PerformanceMonitor',
            action: 'timer_result',
            timerName: result.name,
            duration: result.duration,
            ...result.context,
          }, 'PerformanceMonitor');
          break;
        case LogLevel.WARN:
          await logger.warn(message, {
            component: 'PerformanceMonitor',
            action: 'timer_result',
            timerName: result.name,
            duration: result.duration,
            ...result.context,
          }, 'PerformanceMonitor');
          break;
        case LogLevel.INFO:
          await logger.info(message, {
            component: 'PerformanceMonitor',
            action: 'timer_result',
            timerName: result.name,
            duration: result.duration,
            ...result.context,
          }, 'PerformanceMonitor');
          break;
        default:
          await logger.debug(message, {
            component: 'PerformanceMonitor',
            action: 'timer_result',
            timerName: result.name,
            duration: result.duration,
            ...result.context,
          }, 'PerformanceMonitor');
      }

    } catch (error) {
      console.warn('Performance timer logging failed:', error);
    }
  }

  /**
   * メモリ使用量をチェック
   */
  async checkMemoryUsage(): Promise<void> {
    try {
      if (!('memory' in performance)) {
        return; // メモリAPI非対応ブラウザ
      }

      const memory = (performance as { memory?: { usedJSHeapSize: number; totalJSHeapSize: number; jsHeapSizeLimit: number } }).memory;
      if (!memory) {
        return;
      }

      const usedMB = Math.round(memory.usedJSHeapSize / 1024 / 1024);
      const totalMB = Math.round(memory.totalJSHeapSize / 1024 / 1024);
      const limitMB = Math.round(memory.jsHeapSizeLimit / 1024 / 1024);
      const percentage = Math.round((usedMB / limitMB) * 100);

      const level = usedMB > this.config.memoryWarningThreshold ? LogLevel.WARN : LogLevel.DEBUG;
      const message = `Memory Usage: ${usedMB}MB used (${percentage}% of ${limitMB}MB limit)`;

      if (level === LogLevel.WARN) {
        await logger.warn(message, {
          component: 'PerformanceMonitor',
          action: 'memory_check',
          memoryUsage: {
            used: usedMB,
            total: totalMB,
            limit: limitMB,
            percentage,
          },
        }, 'PerformanceMonitor');
      } else {
        await logger.debug(message, {
          component: 'PerformanceMonitor',
          action: 'memory_check',
          memoryUsage: {
            used: usedMB,
            total: totalMB,
            limit: limitMB,
            percentage,
          },
        }, 'PerformanceMonitor');
      }

      // メモリ使用量が閾値を超えた場合の詳細ログ
      if (usedMB > this.config.memoryWarningThreshold) {
        await this.logMemoryWarning(usedMB, percentage);
      }

    } catch (error) {
      await logger.error('PerformanceMonitor: メモリチェックエラー', 
        { 
          component: 'PerformanceMonitor', 
          action: 'memory_check_error',
          error: error instanceof Error ? error.message : String(error)
        }, 
        'PerformanceMonitor'
      );
    }
  }

  /**
   * 現在のパフォーマンス指標を取得
   */
  async getPerformanceMetrics(): Promise<PerformanceMetrics> {
    const metrics: PerformanceMetrics = {
      memoryUsage: { used: 0, total: 0, percentage: 0 },
      navigationTiming: { pageLoadTime: 0, domContentLoadedTime: 0, resourceLoadTime: 0 },
      resourceUsage: { activeConnections: 0, cacheSize: 0, storageUsage: 0 },
      warnings: [],
    };

    try {
      // メモリ使用量
      if ('memory' in performance) {
        const memory = (performance as { memory?: { usedJSHeapSize: number; totalJSHeapSize: number; jsHeapSizeLimit: number } }).memory;
        if (memory) {
          metrics.memoryUsage = {
            used: Math.round(memory.usedJSHeapSize / 1024 / 1024),
            total: Math.round(memory.totalJSHeapSize / 1024 / 1024),
            percentage: Math.round((memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100),
          };
        }
      }

      // ナビゲーションタイミング
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      if (navigation) {
        metrics.navigationTiming = {
          pageLoadTime: navigation.loadEventEnd - navigation.fetchStart,
          domContentLoadedTime: navigation.domContentLoadedEventEnd - navigation.fetchStart,
          resourceLoadTime: navigation.loadEventEnd - navigation.domContentLoadedEventEnd,
        };
      }

      // ストレージ使用量
      if ('storage' in navigator && 'estimate' in navigator.storage) {
        const estimate = await navigator.storage.estimate();
        metrics.resourceUsage.storageUsage = Math.round((estimate.usage || 0) / 1024 / 1024);
      }

      // 警告をチェック
      this.checkPerformanceWarnings(metrics);

    } catch (error) {
      await logger.error('PerformanceMonitor: メトリクス取得エラー', 
        { 
          component: 'PerformanceMonitor', 
          action: 'get_metrics_error',
          error: error instanceof Error ? error.message : String(error)
        }, 
        'PerformanceMonitor'
      );
    }

    return metrics;
  }

  /**
   * API呼び出しのパフォーマンスを測定
   */
  async measureApiCall<T>(
    name: string,
    apiCall: () => Promise<T>,
    context?: Record<string, unknown>
  ): Promise<T> {
    const timer = this.startTimer(`api_${name}`);
    let result: T;
    let error: Error | null = null;

    try {
      result = await apiCall();
      await timer.end({
        ...context,
        success: true,
        status: 'success',
      });
      return result;
    } catch (err) {
      error = err instanceof Error ? err : new Error(String(err));
      await timer.end({
        ...context,
        success: false,
        status: 'error',
        error: error.message,
      });
      throw error;
    }
  }

  /**
   * レンダリング時間を測定
   */
  async measureRender(componentName: string, renderFn: () => void): Promise<void> {
    const timer = this.startTimer(`render_${componentName}`);
    
    try {
      renderFn();
      await timer.end({
        component: componentName,
        type: 'render',
      });
    } catch (error) {
      await timer.end({
        component: componentName,
        type: 'render',
        error: error instanceof Error ? error.message : String(error),
      });
      throw error;
    }
  }

  /**
   * Performance Observer を設定
   */
  private setupPerformanceObserver(): void {
    try {
      if ('PerformanceObserver' in window) {
        this.performanceObserver = new PerformanceObserver((list) => {
          void this.handlePerformanceEntries(list.getEntries());
        });

        // 監視対象を設定
        this.performanceObserver.observe({ 
          entryTypes: ['measure', 'navigation', 'resource', 'paint'] 
        });
      }
    } catch (error) {
      console.warn('Performance Observer setup failed:', error);
    }
  }

  /**
   * Performance entries を処理
   */
  private async handlePerformanceEntries(entries: PerformanceEntry[]): Promise<void> {
    for (const entry of entries) {
      try {
        if (entry.entryType === 'resource') {
          await this.logResourceTiming(entry as PerformanceResourceTiming);
        } else if (entry.entryType === 'paint') {
          await this.logPaintTiming(entry);
        }
      } catch (error) {
        console.warn('Performance entry handling failed:', error);
      }
    }
  }

  /**
   * リソース読み込み時間をログ
   */
  private async logResourceTiming(entry: PerformanceResourceTiming): Promise<void> {
    const duration = entry.responseEnd - entry.requestStart;
    const level = duration > 2000 ? LogLevel.WARN : LogLevel.DEBUG;

    if (level === LogLevel.WARN) {
      await logger.warn(`Resource loaded: ${entry.name}`, {
        component: 'PerformanceMonitor',
        action: 'resource_timing',
        resource: entry.name,
        duration,
        size: entry.transferSize,
        type: entry.initiatorType,
      }, 'PerformanceMonitor');
    } else {
      await logger.debug(`Resource loaded: ${entry.name}`, {
        component: 'PerformanceMonitor',
        action: 'resource_timing',
        resource: entry.name,
        duration,
        size: entry.transferSize,
        type: entry.initiatorType,
      }, 'PerformanceMonitor');
    }
  }

  /**
   * ペイント時間をログ
   */
  private async logPaintTiming(entry: PerformanceEntry): Promise<void> {
    await logger.debug(`Paint timing: ${entry.name} at ${entry.startTime.toFixed(2)}ms`, {
      component: 'PerformanceMonitor',
      action: 'paint_timing',
      paintType: entry.name,
      startTime: entry.startTime,
    }, 'PerformanceMonitor');
  }

  /**
   * 初期パフォーマンスを測定
   */
  private async measureInitialPerformance(): Promise<void> {
    try {
      const metrics = await this.getPerformanceMetrics();
      
      await logger.info('Initial performance metrics collected', {
        component: 'PerformanceMonitor',
        action: 'initial_metrics',
        metrics,
      }, 'PerformanceMonitor');

    } catch (error) {
      console.warn('Initial performance measurement failed:', error);
    }
  }

  /**
   * 定期監視を開始
   */
  private startPeriodicMonitoring(): void {
    if (this.monitoringTimer) {
      clearInterval(this.monitoringTimer);
    }

    const intervalMs = this.config.monitoringIntervalMinutes * 60 * 1000;
    
    this.monitoringTimer = setInterval(async () => {
      try {
        await this.checkMemoryUsage();
        
        const metrics = await this.getPerformanceMetrics();
        if (metrics.warnings.length > 0) {
          await logger.warn('Performance warnings detected', {
            component: 'PerformanceMonitor',
            action: 'periodic_check',
            warnings: metrics.warnings,
            metrics,
          }, 'PerformanceMonitor');
        }
      } catch (error) {
        console.warn('Periodic performance monitoring failed:', error);
      }
    }, intervalMs);
  }

  /**
   * パフォーマンス警告をチェック
   */
  private checkPerformanceWarnings(metrics: PerformanceMetrics): void {
    metrics.warnings = [];

    // メモリ使用量警告
    if (metrics.memoryUsage.percentage > 80) {
      metrics.warnings.push(`High memory usage: ${metrics.memoryUsage.percentage}%`);
    }

    // ページ読み込み時間警告
    if (metrics.navigationTiming.pageLoadTime > 5000) {
      metrics.warnings.push(`Slow page load: ${metrics.navigationTiming.pageLoadTime}ms`);
    }

    // ストレージ使用量警告
    if (metrics.resourceUsage.storageUsage > 50) {
      metrics.warnings.push(`High storage usage: ${metrics.resourceUsage.storageUsage}MB`);
    }
  }

  /**
   * メモリ警告をログ
   */
  private async logMemoryWarning(usedMB: number, percentage: number): Promise<void> {
    await logger.warn('High memory usage detected', {
      component: 'PerformanceMonitor',
      action: 'memory_warning',
      memoryUsed: usedMB,
      memoryPercentage: percentage,
      recommendation: 'Consider refreshing the page or closing unused tabs',
    }, 'PerformanceMonitor');
  }

  /**
   * ログレベルを決定
   */
  private determineLogLevel(result: TimerResult): LogLevel {
    // API呼び出しの場合
    if (result.name.startsWith('api_')) {
      if (result.duration > this.config.apiResponseWarningThreshold) {
        return LogLevel.WARN;
      }
      return LogLevel.DEBUG;
    }

    // レンダリングの場合
    if (result.name.startsWith('render_')) {
      if (result.duration > this.config.renderWarningThreshold) {
        return LogLevel.WARN;
      }
      return LogLevel.DEBUG;
    }

    // その他は時間に基づいて判定
    if (result.duration > 1000) {
      return LogLevel.WARN;
    }
    if (result.duration > 500) {
      return LogLevel.INFO;
    }
    return LogLevel.DEBUG;
  }

  /**
   * 設定を読み込み
   */
  private loadConfig(): void {
    try {
      const savedConfig = localStorage.getItem('kanshi_chan_performance_config');
      if (savedConfig) {
        this.config = { ...this.config, ...JSON.parse(savedConfig) };
      }
    } catch {
      // 設定読み込み失敗時はデフォルト設定を使用
    }
  }

  /**
   * 設定を更新
   */
  updateConfig(newConfig: Partial<typeof this.config>): void {
    this.config = { ...this.config, ...newConfig };
    
    try {
      localStorage.setItem('kanshi_chan_performance_config', JSON.stringify(this.config));
    } catch {
      // LocalStorage保存失敗時は無視
    }

    // 監視タイマーを再設定
    if (this.config.enabled && this.monitoringTimer) {
      this.startPeriodicMonitoring();
    }
    
    // 監視が無効になった場合は停止
    if (!this.config.enabled && this.monitoringTimer) {
      clearInterval(this.monitoringTimer);
      this.monitoringTimer = null;
    }
  }

  /**
   * 現在の設定を取得
   */
  getConfig(): typeof this.config {
    return { ...this.config };
  }

  /**
   * システムを停止
   */
  dispose(): void {
    if (this.monitoringTimer) {
      clearInterval(this.monitoringTimer);
      this.monitoringTimer = null;
    }
    
    if (this.performanceObserver) {
      this.performanceObserver.disconnect();
      this.performanceObserver = null;
    }
    
    this.isActive = false;
  }
}

// グローバルパフォーマンスモニターインスタンス
export const performanceMonitor = new PerformanceMonitor(); 
import { io, Socket } from 'socket.io-client';

// 型定義
export interface DetectionStatus {
  personDetected: boolean;
  smartphoneDetected: boolean;
  absenceTime: number;
  smartphoneUseTime: number;
  absenceAlert?: boolean;
  smartphoneAlert?: boolean;
}

export interface ScheduleAlert {
  type: 'schedule_alert';
  content: string;
  time: string;
}

// 接続状態の変化やエラーなどをリッスンするためのコールバック型
type SocketEventCallback<T = unknown> = (data?: T) => void;

// 単一のWebSocketインスタンスを管理するクラス
class WebSocketManager {
  private socket: Socket | null = null;
  private connectCallbacks: SocketEventCallback[] = [];
  private disconnectCallbacks: SocketEventCallback[] = [];
  private errorCallbacks: SocketEventCallback<Error>[] = [];
  private statusUpdateCallbacks: SocketEventCallback<DetectionStatus>[] = [];
  private scheduleAlertCallbacks: SocketEventCallback<ScheduleAlert>[] = [];

  // シングルトンパターン
  private static instance: WebSocketManager;
  
  private constructor() {}
  
  public static getInstance(): WebSocketManager {
    if (!WebSocketManager.instance) {
      WebSocketManager.instance = new WebSocketManager();
    }
    return WebSocketManager.instance;
  }

  // WebSocket接続を初期化
  public initialize() {
    if (this.socket) {
      return;
    }

    // WebSocketの設定
    this.socket = io('http://localhost:5001', {
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000
    });
    
    // 各種イベントのリスナーを設定
    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.connectCallbacks.forEach(callback => callback());
    });

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
      this.disconnectCallbacks.forEach(callback => callback());
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      this.errorCallbacks.forEach(callback => callback(error));
    });

    this.socket.on('status_update', (data: DetectionStatus) => {
      this.statusUpdateCallbacks.forEach(callback => callback(data));
    });
    
    this.socket.on('schedule_alert', (data: ScheduleAlert) => {
      console.log('Schedule alert received:', data);
      this.scheduleAlertCallbacks.forEach(callback => callback(data));
    });
  }

  // 接続切断
  public disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  // 各種イベントのリスナー登録メソッド
  public onConnect(callback: SocketEventCallback) {
    this.connectCallbacks.push(callback);
    return () => {
      this.connectCallbacks = this.connectCallbacks.filter(cb => cb !== callback);
    };
  }

  public onDisconnect(callback: SocketEventCallback) {
    this.disconnectCallbacks.push(callback);
    return () => {
      this.disconnectCallbacks = this.disconnectCallbacks.filter(cb => cb !== callback);
    };
  }

  public onError(callback: SocketEventCallback<Error>) {
    this.errorCallbacks.push(callback);
    return () => {
      this.errorCallbacks = this.errorCallbacks.filter(cb => cb !== callback);
    };
  }

  public onStatusUpdate(callback: SocketEventCallback<DetectionStatus>) {
    this.statusUpdateCallbacks.push(callback);
    return () => {
      this.statusUpdateCallbacks = this.statusUpdateCallbacks.filter(cb => cb !== callback);
    };
  }

  public onScheduleAlert(callback: SocketEventCallback<ScheduleAlert>) {
    this.scheduleAlertCallbacks.push(callback);
    return () => {
      this.scheduleAlertCallbacks = this.scheduleAlertCallbacks.filter(cb => cb !== callback);
    };
  }
}

// エクスポート用のシングルトンインスタンス
export const websocketManager = WebSocketManager.getInstance(); 
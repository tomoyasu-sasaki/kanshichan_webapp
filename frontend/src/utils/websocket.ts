import { io, Socket } from 'socket.io-client';

// WebAudio API の型拡張（ブラウザ互換性のため）
declare global {
  interface Window {
    webkitAudioContext?: typeof AudioContext;
  }
}

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

export interface AudioStreamData {
  audio_data: string;  // Base64エンコードされた音声データ
  metadata: {
    audio_id: string;
    file_id?: string;
    text_content: string;
    emotion: string;
    language: string;
    synthesis_timestamp: string;
    file_size: number;
    streaming_mode?: boolean;
    broadcast_mode?: boolean;
  };
  timestamp: string;
  format: string;  // 'audio/wav'
  encoding: string;  // 'base64'
}

export interface AudioNotification {
  type: 'tts_started' | 'tts_completed' | 'tts_error' | 'audio_ready' | 'broadcast_completed' | 'broadcast_error';
  message: string;
  audio_id?: string;
  timestamp: string;
}

export interface AudioStatusUpdate {
  client_id: string;
  audio_id: string;
  status: 'playing' | 'finished' | 'error';
}

// 接続状態の変化やエラーなどをリッスンするためのコールバック型
type SocketEventCallback<T = unknown> = (data?: T) => void;

// 音声管理クラス
class AudioManager {
  private audioContext: AudioContext | null = null;
  private audioQueue: AudioBuffer[] = [];
  private isPlaying: boolean = false;
  private currentSource: AudioBufferSourceNode | null = null;

  constructor() {
    this.initializeAudioContext();
  }

  private initializeAudioContext() {
    try {
      // ブラウザ互換性のためのAudioContext初期化
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (AudioContextClass) {
        this.audioContext = new AudioContextClass();
        console.log('AudioContext initialized');
      } else {
        console.warn('AudioContext not supported in this browser');
      }
    } catch (error) {
      console.error('Failed to initialize AudioContext:', error);
    }
  }

  async playAudioData(base64Data: string, metadata: AudioStreamData['metadata']): Promise<void> {
    if (!this.audioContext) {
      console.error('AudioContext not available');
      return;
    }

    try {
      // ユーザーアクティベーション確認
      if (this.audioContext.state === 'suspended') {
        await this.audioContext.resume();
      }

      // Base64データをArrayBufferに変換
      const binaryString = atob(base64Data);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }

      // AudioBufferにデコード
      const audioBuffer = await this.audioContext.decodeAudioData(bytes.buffer);

      // 再生
      await this.playAudioBuffer(audioBuffer, metadata);

    } catch (error) {
      console.error('Error playing audio:', error);
      throw error;
    }
  }

  private async playAudioBuffer(audioBuffer: AudioBuffer, metadata: AudioStreamData['metadata']): Promise<void> {
    if (!this.audioContext) return;

    try {
      // 現在の再生を停止
      if (this.currentSource) {
        this.currentSource.stop();
        this.currentSource = null;
      }

      // 新しいSourceNodeを作成
      this.currentSource = this.audioContext.createBufferSource();
      this.currentSource.buffer = audioBuffer;
      this.currentSource.connect(this.audioContext.destination);

      // 再生開始イベント
      this.currentSource.onended = () => {
        this.isPlaying = false;
        this.currentSource = null;
        
        // 再生完了をサーバーに通知
        websocketManager.notifyAudioPlaybackStatus(metadata.audio_id, 'finished');
        
        console.log(`Audio playback finished: ${metadata.audio_id}`);
      };

      // 再生開始
      this.isPlaying = true;
      this.currentSource.start();

      // 再生開始をサーバーに通知
      websocketManager.notifyAudioPlaybackStatus(metadata.audio_id, 'playing');

      console.log(`Audio playback started: ${metadata.text_content.substring(0, 30)}...`);

    } catch (error) {
      console.error('Error in playAudioBuffer:', error);
      this.isPlaying = false;
      this.currentSource = null;
      
      // エラーをサーバーに通知
      websocketManager.notifyAudioPlaybackStatus(metadata.audio_id, 'error');
      
      throw error;
    }
  }

  stopCurrentAudio(): void {
    if (this.currentSource) {
      this.currentSource.stop();
      this.currentSource = null;
      this.isPlaying = false;
    }
  }

  getPlaybackStatus(): { isPlaying: boolean; audioContext: AudioContext | null } {
    return {
      isPlaying: this.isPlaying,
      audioContext: this.audioContext
    };
  }
}

// 単一のWebSocketインスタンスを管理するクラス
class WebSocketManager {
  private socket: Socket | null = null;
  private connectCallbacks: SocketEventCallback[] = [];
  private disconnectCallbacks: SocketEventCallback[] = [];
  private errorCallbacks: SocketEventCallback<Error>[] = [];
  private statusUpdateCallbacks: SocketEventCallback<DetectionStatus>[] = [];
  private scheduleAlertCallbacks: SocketEventCallback<ScheduleAlert>[] = [];
  private audioStreamCallbacks: SocketEventCallback<AudioStreamData>[] = [];
  private audioNotificationCallbacks: SocketEventCallback<AudioNotification>[] = [];
  private audioStatusUpdateCallbacks: SocketEventCallback<AudioStatusUpdate>[] = [];
  
  private audioManager: AudioManager;

  // シングルトンパターン
  private static instance: WebSocketManager;
  
  private constructor() {
    this.audioManager = new AudioManager();
  }
  
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
    this.socket = io('http://localhost:8000', {
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000
    });
    
    // 既存イベントのリスナーを設定
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

    this.socket.on('audio_stream', (data: AudioStreamData) => {
      console.log('Audio stream received:', data.metadata);
      
      // 音声データを自動再生
      this.audioManager.playAudioData(data.audio_data, data.metadata)
        .catch(error => {
          console.error('Failed to play received audio:', error);
        });
      
      // コールバック実行
      this.audioStreamCallbacks.forEach(callback => callback(data));
    });

    this.socket.on('audio_notification', (data: AudioNotification) => {
      console.log('Audio notification received:', data);
      this.audioNotificationCallbacks.forEach(callback => callback(data));
    });

    this.socket.on('audio_status_update', (data: AudioStatusUpdate) => {
      console.log('Audio status update received:', data);
      this.audioStatusUpdateCallbacks.forEach(callback => callback(data));
    });
  }

  // 音声再生状態をサーバーに通知
  public notifyAudioPlaybackStatus(audioId: string, status: 'playing' | 'finished' | 'error'): void {
    if (this.socket) {
      this.socket.emit('audio_playback_status', {
        audio_id: audioId,
        status: status,
        timestamp: new Date().toISOString()
      });
      console.log(`Audio playback status sent: ${audioId} - ${status}`);
    }
  }

  // 接続切断
  public disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    
    // 音声再生停止
    this.audioManager.stopCurrentAudio();
  }

  // 既存のイベントリスナー登録メソッド
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
  public onAudioStream(callback: SocketEventCallback<AudioStreamData>) {
    this.audioStreamCallbacks.push(callback);
    return () => {
      this.audioStreamCallbacks = this.audioStreamCallbacks.filter(cb => cb !== callback);
    };
  }

  public onAudioNotification(callback: SocketEventCallback<AudioNotification>) {
    this.audioNotificationCallbacks.push(callback);
    return () => {
      this.audioNotificationCallbacks = this.audioNotificationCallbacks.filter(cb => cb !== callback);
    };
  }

  public onAudioStatusUpdate(callback: SocketEventCallback<AudioStatusUpdate>) {
    this.audioStatusUpdateCallbacks.push(callback);
    return () => {
      this.audioStatusUpdateCallbacks = this.audioStatusUpdateCallbacks.filter(cb => cb !== callback);
    };
  }

  // 音声管理機能へのアクセス
  public getAudioManager(): AudioManager {
    return this.audioManager;
  }

  // 接続状態確認
  public isConnected(): boolean {
    return this.socket?.connected || false;
  }
}

// エクスポート用のシングルトンインスタンス
export const websocketManager = WebSocketManager.getInstance(); 
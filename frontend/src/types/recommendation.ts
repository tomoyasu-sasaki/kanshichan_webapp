/**
 * 推奨事項（改善提案）に関する型定義
 * 
 * バックエンドのRecommendationSchemaと一致するように定義
 */

export type PriorityLevel = 'high' | 'medium' | 'low';

export interface Recommendation {
  // 必須フィールド
  type: string;
  priority: PriorityLevel;
  message: string;
  timestamp: string;

  // オプションフィールド
  action?: string;
  emotion?: string;
  source?: string;
  
  // 音声関連
  audio_url?: string;
  voice_text?: string;
  tts_requested?: boolean;

  // 追加情報
  metadata?: Record<string, unknown>;
}

export interface PaginationInfo {
  page: number;
  limit: number;
  total_items: number;
  total_pages: number;
}

export interface RecommendationResponse {
  status: string;
  data: {
    recommendations: Recommendation[];
    pagination: PaginationInfo;
  };
  timestamp: string;
  message?: string;
} 
// Behavior Insights Types
export interface BehaviorTrend {
  timeframe: string;
  period_start?: string;
  period_end?: string;
  total_logs: number;
  focus_analysis?: {
    average_focus?: number;
    trend_direction?: "up" | "down" | "stable";
    trend_percentage?: number;
    good_posture_percentage?: number;
    presence_rate?: number;
    smartphone_usage_rate?: number;
    total_sessions?: number;
    basic_statistics?: {
      mean?: number;
      high_focus_ratio?: number;
      low_focus_ratio?: number;
    };
    trend_analysis?: {
      trend?: "improving" | "declining" | "stable";
      trend_strength?: number;
    };
    hourly_patterns?: {
      hourly_statistics?: { [key: string]: number };
    };
  };
  anomalies?: unknown[];
  trend_summary?: unknown;
  message?: string;
  period_hours?: number;
  logs_count?: number;
}

export interface DailyInsight {
  target_date: string;
  logs_analyzed?: number;
  insights?: {
    focus_score?: number;
    productivity_score?: number;
    key_findings?: (string | InsightItem)[];
    improvement_areas?: (string | InsightItem)[];
  };
  summary?: {
    summary?: string;
  };
  message?: string;
  recommendations?: unknown[];
}

export interface BehaviorSummary {
  today?: {
    total_time?: number;
    focus_time?: number;
    break_time?: number;
    absence_time?: number;
    smartphone_usage_time?: number;
    posture_alerts?: number;
  };
  yesterday?: {
    total_time?: number;
    focus_time?: number;
    break_time?: number;
    absence_time?: number;
    smartphone_usage_time?: number;
    posture_alerts?: number;
  };
}

export interface InsightItem {
  message?: string;
  action?: string;
  [key: string]: unknown;
}

export interface BehaviorInsightsProps {
  refreshInterval?: number;
  onNavigate?: (view: string) => void;
}
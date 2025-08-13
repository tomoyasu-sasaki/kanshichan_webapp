import { Box, VStack, useToast, useColorModeValue } from "@chakra-ui/react";
import { useEffect, useState, useCallback, useRef } from "react";
import { logger } from "../../utils/logger";
import { Recommendation, PaginationInfo } from "../../types/recommendation";

// Types
import type {
  BehaviorTrend,
  DailyInsight,
  BehaviorSummary,
  BehaviorInsightsProps
} from "./types";

// Components
import { InsightsHeader } from "./components/InsightsHeader";
import { SummaryCards } from "./components/SummaryCards";
import { TrendsChart } from "./components/TrendsChart";
import { DailyInsightsCard } from "./components/DailyInsightsCard";
import { RecommendationsPanel } from "./components/RecommendationsPanel";
import { QuickActions } from "./components/QuickActions";



export const BehaviorInsights: React.FC<BehaviorInsightsProps> = ({
  refreshInterval = 300,
  onNavigate,
}) => {
  // Data states
  const [behaviorTrends, setBehaviorTrends] = useState<BehaviorTrend | null>(null);
  const [dailyInsights, setDailyInsights] = useState<DailyInsight | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [behaviorSummary, setBehaviorSummary] = useState<BehaviorSummary | null>(null);
  const [paginationInfo, setPaginationInfo] = useState<PaginationInfo>({
    page: 1,
    limit: 5,
    total_items: 0,
    total_pages: 1,
  });

  // UI states
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [insightsLoading, setInsightsLoading] = useState(true);
  const [trendsLoading, setTrendsLoading] = useState(true);
  const [recommendationsLoading, setRecommendationsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [timeframe, setTimeframe] = useState("today");
  const [priorityFilter, setPriorityFilter] = useState("all");
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const didInitRef = useRef(false);
  const toast = useToast();

  // Theme
  const bgGradient = useColorModeValue(
    'linear(to-br, gray.50, blue.50)',
    'linear(to-br, gray.900, blue.900)'
  );

  // --- 重複リクエスト防止のためのグローバルロック ---
  const acquireGlobalLock = (key: string): boolean => {
    if (typeof window === "undefined") return true;
    const w = window as unknown as { __kcLocks?: Set<string> };
    if (!w.__kcLocks) w.__kcLocks = new Set<string>();
    if (w.__kcLocks.has(key)) return false;
    w.__kcLocks.add(key);
    return true;
  };
  const releaseGlobalLock = (key: string): void => {
    if (typeof window === "undefined") return;
    const w = window as unknown as { __kcLocks?: Set<string> };
    w.__kcLocks?.delete(key);
  };

  // 行動サマリーを取得（最優先・高速）
  const fetchBehaviorSummary = useCallback(async () => {
    try {
      setSummaryLoading(true);
      setError(null);

      await logger.info(
        "BehaviorInsights: サマリーデータ取得開始",
        { component: "BehaviorInsights", action: "fetch_summary_start" },
        "BehaviorInsights",
      );

      const response = await fetch("/api/v1/behavior/summary/dashboard");

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      const data = await response.json();
      const isSuccess = data?.success === true || data?.status === "success";
      if (isSuccess) {
        setBehaviorSummary(data.data || data);
        await logger.info(
          "BehaviorInsights: サマリーデータ取得完了",
          {
            component: "BehaviorInsights",
            action: "fetch_summary_success",
            data_keys: Object.keys(data.data || {}),
          },
          "BehaviorInsights",
        );
      } else {
        throw new Error(data.error || "Unknown API error");
      }
    } catch (error) {
      console.error("Failed to fetch behavior summary:", error);
      const errorMessage =
        error instanceof Error ? error.message : "Unknown error";
      setError(`データ取得に失敗しました: ${errorMessage}`);

      await logger.error(
        "BehaviorInsights: サマリーデータ取得エラー",
        {
          component: "BehaviorInsights",
          action: "fetch_summary_error",
          error: errorMessage,
        },
        "BehaviorInsights",
      );

      toast({
        title: "データ取得エラー",
        description: `行動サマリーの取得に失敗しました: ${errorMessage}`,
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setSummaryLoading(false);
    }
  }, [toast]);

  // 行動トレンドデータを取得（中優先）
  const fetchBehaviorTrends = useCallback(async (selectedTimeframe: string) => {
    try {
      setTrendsLoading(true);

      await logger.info(
        "BehaviorInsights: トレンドデータ取得開始",
        {
          component: "BehaviorInsights",
          action: "fetch_trends_start",
          timeframe: selectedTimeframe,
        },
        "BehaviorInsights",
      );

      // フロントエンドの表示値をAPIパラメータにマッピング
      const timeframeMapping: { [key: string]: string } = {
        today: "daily",
        week: "weekly",
        month: "weekly", // 月次は現在のAPIでは週次で代用
      };

      const apiTimeframe = timeframeMapping[selectedTimeframe] || "daily";

      const response = await fetch(
        `/api/v1/analysis/trends?timeframe=${apiTimeframe}`,
      );
      if (response.ok) {
        const data = await response.json();
        const isSuccess2 = data?.success === true || data?.status === "success";
        if (isSuccess2) {
          setBehaviorTrends(data.data || data || null);
          await logger.info(
            "BehaviorInsights: トレンドデータ取得完了",
            {
              component: "BehaviorInsights",
              action: "fetch_trends_success",
              timeframe: selectedTimeframe,
            },
            "BehaviorInsights",
          );
        }
      }
    } catch (error) {
      console.error("Failed to fetch behavior trends:", error);
      await logger.error(
        "BehaviorInsights: トレンドデータ取得エラー",
        {
          component: "BehaviorInsights",
          action: "fetch_trends_error",
          error: error instanceof Error ? error.message : String(error),
        },
        "BehaviorInsights",
      );
    } finally {
      setTrendsLoading(false);
    }
  }, []);

  // 今日の洞察を取得（低優先・重い処理）
  const fetchDailyInsights = useCallback(async () => {
    try {
      setInsightsLoading(true);

      await logger.info(
        "BehaviorInsights: インサイトデータ取得開始",
        { component: "BehaviorInsights", action: "fetch_insights_start" },
        "BehaviorInsights",
      );

      const response = await fetch("/api/v1/analysis/insights");
      if (response.ok) {
        const data = await response.json();
        const isSuccess3 = data?.success === true || data?.status === "success";
        if (isSuccess3) {
          // API応答データの構造に合わせて設定
          const insights = data.data || data || {};

          // insights.summary.insights から focus_score と productivity_score を取得
          const summaryInsights = insights.summary?.insights || {};

          // DailyInsight型に適合するデータ構造を作成
          const dailyInsightData: DailyInsight = {
            target_date:
              insights.target_date || new Date().toISOString().split("T")[0],
            logs_analyzed: insights.logs_analyzed || 0,
            insights: {
              focus_score: summaryInsights.focus_score || 0,
              productivity_score: summaryInsights.productivity_score || 0,
              key_findings: summaryInsights.key_findings || [],
              improvement_areas: summaryInsights.improvement_areas || [],
            },
            summary: insights.summary || {},
          };

          setDailyInsights(dailyInsightData);

          await logger.info(
            "BehaviorInsights: インサイトデータ取得完了",
            {
              component: "BehaviorInsights",
              action: "fetch_insights_success",
              logs_analyzed: insights.logs_analyzed,
            },
            "BehaviorInsights",
          );
        }
      }
    } catch (error) {
      console.error("Failed to fetch daily insights:", error);
      await logger.error(
        "BehaviorInsights: インサイトデータ取得エラー",
        {
          component: "BehaviorInsights",
          action: "fetch_insights_error",
          error: error instanceof Error ? error.message : String(error),
        },
        "BehaviorInsights",
      );
    } finally {
      setInsightsLoading(false);
    }
  }, []);

  // 推奨事項を取得（低優先）
  const fetchRecommendations = useCallback(
    async (priority: string, page: number = 1, limit: number = 5) => {
      try {
        await logger.debug(
          "BehaviorInsights: 推奨事項取得開始",
          {
            component: "BehaviorInsights",
            action: "fetch_recommendations_start",
            priority,
            page,
            limit,
          },
          "BehaviorInsights",
        );

        // URLパラメータを構築
        let url = "/api/v1/analysis/recommendations";
        const params = new URLSearchParams();

        if (priority !== "all") {
          params.append("priority", priority);
        }

        params.append("page", page.toString());
        params.append("limit", limit.toString());

        // 音声合成オプション（将来の拡張用）
        // params.append('tts_enabled', 'false');

        // パラメータが存在する場合はURLに追加
        if (params.toString()) {
          url += `?${params.toString()}`;
        }

        const response = await fetch(url);
        if (response.ok) {
          const data = await response.json();
          if (data.status === "success") {
            const recs: Recommendation[] = (data.data?.recommendations || []).filter(
              (r: Recommendation) => (r.source || "llm_advice") === "llm_advice",
            );
            setRecommendations(recs);
            setPaginationInfo(
              data.data?.pagination || {
                page: 1,
                limit,
                total_items: 0,
                total_pages: 1,
              },
            );
          }
        }
      } catch (error) {
        console.error("Failed to fetch recommendations:", error);
      }
    },
    [],
  );

  // 高速データ更新（サマリーのみ）
  const refreshFastData = useCallback(async () => {
    await logger.info(
      "BehaviorInsights: 高速データ更新開始",
      { component: "BehaviorInsights", action: "refresh_fast_start" },
      "BehaviorInsights",
    );

    await fetchBehaviorSummary();
    setLastUpdated(new Date());

    await logger.info(
      "BehaviorInsights: 高速データ更新完了",
      { component: "BehaviorInsights", action: "refresh_fast_complete" },
      "BehaviorInsights",
    );
  }, [fetchBehaviorSummary]);

  // 全データ更新（段階的実行）
  const refreshAllData = useCallback(async () => {
    const lockKey = "BI:refreshAll";
    if (!acquireGlobalLock(lockKey)) {
      await logger.debug(
        "BehaviorInsights: 全データ更新スキップ（ロック中）",
        { component: "BehaviorInsights", action: "refresh_all_skip" },
        "BehaviorInsights",
      );
      return;
    }
    await logger.info(
      "BehaviorInsights: 全データ更新開始",
      { component: "BehaviorInsights", action: "refresh_all_start" },
      "BehaviorInsights",
    );

    try {
      await fetchBehaviorSummary();

      await Promise.all([
        fetchBehaviorTrends(timeframe),
        fetchRecommendations(priorityFilter),
      ]);

      void fetchDailyInsights(); // 非同期で実行、完了を待たない

      setLastUpdated(new Date());

      await logger.info(
        "BehaviorInsights: 全データ更新完了",
        { component: "BehaviorInsights", action: "refresh_all_complete" },
        "BehaviorInsights",
      );
    } catch (error) {
      await logger.error(
        "BehaviorInsights: 全データ更新エラー",
        {
          component: "BehaviorInsights",
          action: "refresh_all_error",
          error: error instanceof Error ? error.message : String(error),
        },
        "BehaviorInsights",
      );

      toast({
        title: "データ更新エラー",
        description: "データの更新に失敗しました",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    } finally {
      releaseGlobalLock(lockKey);
    }
  }, [
    timeframe,
    priorityFilter,
    fetchBehaviorSummary,
    fetchBehaviorTrends,
    fetchRecommendations,
    fetchDailyInsights,
    toast,
  ]);

  // 初期化とリフレッシュ（段階的実行）
  useEffect(() => {
    // React 18 StrictMode のダブルマウント対策
    if (didInitRef.current) {
      return;
    }
    didInitRef.current = true;

    refreshAllData();

    // 高速データは1分間隔、全データは5分間隔で更新
    const fastInterval = setInterval(refreshFastData, 60 * 1000); // 1分間隔
    const fullInterval = setInterval(refreshAllData, refreshInterval * 1000); // 5分間隔

    return () => {
      clearInterval(fastInterval);
      clearInterval(fullInterval);
    };
  }, [refreshAllData, refreshFastData, refreshInterval]);



  // Handler functions
  const handleTimeframeChange = useCallback((newTimeframe: string) => {
    setTimeframe(newTimeframe);
    fetchBehaviorTrends(newTimeframe);
  }, [fetchBehaviorTrends]);

  const handlePriorityFilterChange = useCallback((newPriority: string) => {
    setPriorityFilter(newPriority);
    fetchRecommendations(newPriority);
  }, [fetchRecommendations]);

  const handleLoadMoreRecommendations = useCallback(() => {
    setRecommendationsLoading(true);
    const nextPage = paginationInfo.page + 1;
    fetchRecommendations(priorityFilter, nextPage, paginationInfo.limit)
      .finally(() => setRecommendationsLoading(false));
  }, [fetchRecommendations, priorityFilter, paginationInfo]);

  const isAnyLoading = summaryLoading || trendsLoading || insightsLoading;
  const loadingProgress = {
    summary: summaryLoading,
    trends: trendsLoading,
    insights: insightsLoading
  };

  return (
    <Box
      minH="100vh"
      bgGradient={bgGradient}
      py={8}
      px={4}
    >
      <Box width="100%" maxWidth="1400px" mx="auto">
        <VStack spacing={8} align="stretch">
          {/* Header */}
          <InsightsHeader
            timeframe={timeframe}
            onTimeframeChange={handleTimeframeChange}
            onRefresh={refreshAllData}
            isLoading={isAnyLoading}
            lastUpdated={lastUpdated}
            loadingProgress={loadingProgress}
          />

          {/* Summary Cards */}
          <SummaryCards
            behaviorSummary={behaviorSummary}
            isLoading={summaryLoading}
            error={error}
          />

          {/* Trends Chart */}
          <TrendsChart
            behaviorTrends={behaviorTrends}
            isLoading={trendsLoading}
          />

          {/* Daily Insights */}
          <DailyInsightsCard
            dailyInsights={dailyInsights}
            isLoading={insightsLoading}
          />

          {/* Recommendations */}
          <RecommendationsPanel
            recommendations={recommendations}
            paginationInfo={paginationInfo}
            priorityFilter={priorityFilter}
            isLoading={recommendationsLoading}
            onPriorityChange={handlePriorityFilterChange}
            onLoadMore={handleLoadMoreRecommendations}
          />

          {/* Quick Actions */}
          <QuickActions onNavigate={onNavigate} />
        </VStack>
      </Box>
    </Box>
  );
};

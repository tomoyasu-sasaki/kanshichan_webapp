import {
  Box,
  VStack,
  HStack,
  Text,
  Card,
  CardBody,
  CardHeader,
  Heading,
  Badge,
  Progress,
  Alert,
  AlertIcon,
  Button,
  Select,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  Divider,
  List,
  ListItem,
  ListIcon,
  useToast,
  Grid,
  Skeleton,
  SkeletonText,
  Tabs,
  TabList,
  Tab,
  Collapse,
  IconButton,
} from "@chakra-ui/react";
import { useEffect, useState, useCallback } from "react";
import {
  FaChartLine,
  FaLightbulb,
  FaEye,
  FaExclamationTriangle,
  FaCheckCircle,
  FaArrowUp,
  FaArrowDown,
  FaMinus,
  FaVolumeUp,
  FaCopy,
} from "react-icons/fa";
import { logger } from "../utils/logger";
import { Recommendation, PaginationInfo } from "../types/recommendation";

interface BehaviorInsightsProps {
  refreshInterval?: number; // リフレッシュ間隔（秒）
  onNavigate?: (view: string) => void; // ナビゲーション関数
}

interface BehaviorTrend {
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

interface DailyInsight {
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

interface BehaviorSummary {
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

interface InsightItem {
  message?: string;
  action?: string;
  [key: string]: unknown;
}

export const BehaviorInsights: React.FC<BehaviorInsightsProps> = ({
  refreshInterval = 300, // 30秒 → 5分（300秒）に変更
  onNavigate,
}) => {
  // 分析データ状態
  const [behaviorTrends, setBehaviorTrends] = useState<BehaviorTrend | null>(
    null,
  );
  const [dailyInsights, setDailyInsights] = useState<DailyInsight | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [behaviorSummary, setBehaviorSummary] =
    useState<BehaviorSummary | null>(null);
  const [paginationInfo, setPaginationInfo] = useState<PaginationInfo>({
    page: 1,
    limit: 5,
    total_items: 0,
    total_pages: 1,
  });

  // UI状態（段階的ローディング対応）
  const [summaryLoading, setSummaryLoading] = useState(true); // サマリー専用ローディング
  const [insightsLoading, setInsightsLoading] = useState(true); // インサイト専用ローディング
  const [trendsLoading, setTrendsLoading] = useState(true); // トレンド専用ローディング
  const [recommendationsLoading, setRecommendationsLoading] = useState(false); // 推奨事項ローディング
  const [error, setError] = useState<string | null>(null);
  const [timeframe, setTimeframe] = useState("today"); // today, week, month
  const [priorityFilter, setPriorityFilter] = useState("all"); // all, high, medium, low
  const [expandedItems, setExpandedItems] = useState<Record<number, boolean>>(
    {},
  );
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const toast = useToast();

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

      const response = await fetch("/api/behavior/summary/dashboard");

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      const data = await response.json();
      if (data.status === "success") {
        setBehaviorSummary(data.data);
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
        `/api/analysis/trends?timeframe=${apiTimeframe}`,
      );
      if (response.ok) {
        const data = await response.json();
        if (data.status === "success") {
          setBehaviorTrends(data.data || null);
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

      const response = await fetch("/api/analysis/insights");
      if (response.ok) {
        const data = await response.json();
        if (data.status === "success") {
          // API応答データの構造に合わせて設定
          const insights = data.data || {};

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
        let url = "/api/analysis/recommendations";
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
            setRecommendations(data.data?.recommendations || []);
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
    refreshAllData();

    // 高速データは1分間隔、全データは5分間隔で更新
    const fastInterval = setInterval(refreshFastData, 60 * 1000); // 1分間隔
    const fullInterval = setInterval(refreshAllData, refreshInterval * 1000); // 5分間隔

    return () => {
      clearInterval(fastInterval);
      clearInterval(fullInterval);
    };
  }, [refreshAllData, refreshFastData, refreshInterval]);

  // 時間枠変更ハンドラ
  const handleTimeframeChange = useCallback(
    (newTimeframe: string) => {
      setTimeframe(newTimeframe);
      fetchBehaviorTrends(newTimeframe);
    },
    [fetchBehaviorTrends],
  );

  // 優先度フィルタ変更ハンドラ
  const handlePriorityFilterChange = useCallback(
    (newPriority: string) => {
      setPriorityFilter(newPriority);
      fetchRecommendations(newPriority);
    },
    [fetchRecommendations],
  );

  // 時間をフォーマット
  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}時間${minutes}分`;
  };

  // パーセンテージをフォーマット
  const formatPercentage = (value: number): string => {
    return `${Math.round(value * 100)}%`;
  };

  // トレンド方向のアイコンとカラーを取得
  const getTrendDisplay = (
    direction: "up" | "down" | "stable",
    percentage: number,
  ) => {
    switch (direction) {
      case "up":
        return {
          icon: <FaArrowUp />,
          color: "green",
          text: `+${percentage.toFixed(1)}%`,
        };
      case "down":
        return {
          icon: <FaArrowDown />,
          color: "red",
          text: `-${percentage.toFixed(1)}%`,
        };
      default:
        return {
          icon: <FaMinus />,
          color: "gray",
          text: "変化なし",
        };
    }
  };

  // 折りたたみ状態切り替え
  const toggleItemExpansion = (index: number) => {
    setExpandedItems((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
  };

  // 音声再生関数
  const playAudio = (url: string) => {
    const audio = new Audio(url);
    audio.play().catch((error) => {
      console.error("音声再生エラー:", error);
      toast({
        title: "音声再生エラー",
        description: "音声の再生に失敗しました",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    });
  };

  // 優先度の選択肢
  const priorities = ["all", "high", "medium", "low"];

  return (
    <Box width="100%" maxWidth="1200px" mx="auto">
      <VStack spacing={6} align="stretch">
        {/* ヘッダー */}
        <Card>
          <CardHeader>
            <HStack justify="space-between" align="center">
              <Heading size="md">行動分析インサイト</Heading>
              <HStack spacing={4}>
                <Select
                  value={timeframe}
                  onChange={(e) => handleTimeframeChange(e.target.value)}
                  size="sm"
                  width="120px"
                >
                  <option value="today">今日</option>
                  <option value="week">今週</option>
                  <option value="month">今月</option>
                </Select>
                <Button
                  onClick={refreshAllData}
                  size="sm"
                  isLoading={summaryLoading || trendsLoading || insightsLoading}
                >
                  更新
                </Button>
                {lastUpdated && (
                  <Text fontSize="xs" color="gray.500">
                    最終更新: {lastUpdated.toLocaleTimeString()}
                  </Text>
                )}
                {/* ローディング進捗インジケーター */}
                {(summaryLoading || trendsLoading || insightsLoading) && (
                  <VStack spacing={1} align="start">
                    <Text fontSize="xs" color="blue.500">
                      {summaryLoading && "📊 基本データ取得中..."}
                      {!summaryLoading &&
                        trendsLoading &&
                        "📈 トレンド分析中..."}
                      {!summaryLoading &&
                        !trendsLoading &&
                        insightsLoading &&
                        "🧠 AI洞察生成中..."}
                    </Text>
                    <Box
                      bg="gray.200"
                      height="2px"
                      width="100px"
                      borderRadius="full"
                      overflow="hidden"
                    >
                      <Box
                        bg="blue.400"
                        height="100%"
                        width={
                          !summaryLoading && !trendsLoading && !insightsLoading
                            ? "100%"
                            : !summaryLoading && !trendsLoading
                              ? "80%"
                              : !summaryLoading
                                ? "50%"
                                : "20%"
                        }
                        transition="width 0.3s ease"
                      />
                    </Box>
                  </VStack>
                )}
              </HStack>
            </HStack>
          </CardHeader>
        </Card>

        {/* サマリー統計 */}
        <Grid templateColumns="repeat(auto-fit, minmax(200px, 1fr))" gap={4}>
          {error ? (
            <Card gridColumn="1 / -1">
              <CardBody>
                <Alert status="error">
                  <AlertIcon />
                  {error}
                </Alert>
              </CardBody>
            </Card>
          ) : summaryLoading ? (
            Array.from({ length: 4 }).map((_, index) => (
              <Card key={index}>
                <CardBody>
                  <Skeleton height="60px" />
                  <Text fontSize="xs" color="blue.500" mt={2}>
                    高速データ取得中... 約1秒で表示されます
                  </Text>
                </CardBody>
              </Card>
            ))
          ) : behaviorSummary ? (
            <>
              <Card>
                <CardBody>
                  <Stat>
                    <StatLabel>今日の監視時間</StatLabel>
                    <StatNumber>
                      {formatTime(behaviorSummary.today?.total_time ?? 0)}
                    </StatNumber>
                    <StatHelpText>
                      {(behaviorSummary.today?.total_time ?? 0) >
                      (behaviorSummary.yesterday?.total_time ?? 0) ? (
                        <StatArrow type="increase" />
                      ) : (
                        <StatArrow type="decrease" />
                      )}
                      前日比:{" "}
                      {formatTime(
                        Math.abs(
                          (behaviorSummary.today?.total_time ?? 0) -
                            (behaviorSummary.yesterday?.total_time ?? 0),
                        ),
                      )}
                    </StatHelpText>
                  </Stat>
                </CardBody>
              </Card>

              <Card>
                <CardBody>
                  <Stat>
                    <StatLabel>今日の集中時間</StatLabel>
                    <StatNumber>
                      {formatTime(behaviorSummary.today?.focus_time ?? 0)}
                    </StatNumber>
                    <StatHelpText>
                      {(behaviorSummary.today?.focus_time ?? 0) >
                      (behaviorSummary.yesterday?.focus_time ?? 0) ? (
                        <StatArrow type="increase" />
                      ) : (
                        <StatArrow type="decrease" />
                      )}
                      前日比:{" "}
                      {formatTime(
                        Math.abs(
                          (behaviorSummary.today?.focus_time ?? 0) -
                            (behaviorSummary.yesterday?.focus_time ?? 0),
                        ),
                      )}
                    </StatHelpText>
                  </Stat>
                </CardBody>
              </Card>

              <Card>
                <CardBody>
                  <Stat>
                    <StatLabel>在席率</StatLabel>
                    <StatNumber>
                      {formatPercentage(
                        (behaviorSummary.today?.total_time ?? 0) > 0
                          ? ((behaviorSummary.today?.total_time ?? 0) -
                              (behaviorSummary.today?.absence_time ?? 0)) /
                              (behaviorSummary.today?.total_time ?? 0)
                          : 0,
                      )}
                    </StatNumber>
                    <StatHelpText>
                      不在時間:{" "}
                      {formatTime(behaviorSummary.today?.absence_time ?? 0)}
                    </StatHelpText>
                  </Stat>
                </CardBody>
              </Card>

              <Card>
                <CardBody>
                  <Stat>
                    <StatLabel>スマホ使用時間</StatLabel>
                    <StatNumber>
                      {formatTime(
                        behaviorSummary.today?.smartphone_usage_time ?? 0,
                      )}
                    </StatNumber>
                    <StatHelpText>
                      {(behaviorSummary.today?.smartphone_usage_time ?? 0) <
                      (behaviorSummary.yesterday?.smartphone_usage_time ??
                        0) ? (
                        <StatArrow type="decrease" />
                      ) : (
                        <StatArrow type="increase" />
                      )}
                      前日比:{" "}
                      {formatTime(
                        Math.abs(
                          (behaviorSummary.today?.smartphone_usage_time ?? 0) -
                            (behaviorSummary.yesterday?.smartphone_usage_time ??
                              0),
                        ),
                      )}
                    </StatHelpText>
                  </Stat>
                </CardBody>
              </Card>

              <Card>
                <CardBody>
                  <Stat>
                    <StatLabel>姿勢アラート</StatLabel>
                    <StatNumber>
                      {behaviorSummary.today?.posture_alerts ?? 0}回
                    </StatNumber>
                    <StatHelpText>
                      {(behaviorSummary.today?.posture_alerts ?? 0) <
                      (behaviorSummary.yesterday?.posture_alerts ?? 0) ? (
                        <StatArrow type="decrease" />
                      ) : (
                        <StatArrow type="increase" />
                      )}
                      前日: {behaviorSummary.yesterday?.posture_alerts ?? 0}回
                    </StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
            </>
          ) : (
            <Card gridColumn="1 / -1">
              <CardBody>
                <Alert status="info">
                  <AlertIcon />
                  データが不足しています。しばらく使用してからご確認ください。
                </Alert>
              </CardBody>
            </Card>
          )}
        </Grid>

        {/* 行動トレンド */}
        <Card>
          <CardHeader>
            <HStack>
              <FaChartLine />
              <Heading size="sm">行動トレンド</Heading>
            </HStack>
          </CardHeader>
          <CardBody>
            {trendsLoading ? (
              <SkeletonText noOfLines={4} spacing="4" />
            ) : behaviorTrends ? (
              <Grid
                templateColumns="repeat(auto-fit, minmax(250px, 1fr))"
                gap={6}
              >
                <Box>
                  <Text fontWeight="bold" mb={2}>
                    集中度トレンド
                  </Text>
                  <HStack justify="space-between">
                    <Text>平均集中度:</Text>
                    <HStack>
                      <Badge colorScheme="blue">
                        {formatPercentage(
                          behaviorTrends.focus_analysis?.average_focus ||
                            behaviorTrends.focus_analysis?.basic_statistics
                              ?.mean ||
                            0,
                        )}
                      </Badge>
                      {(() => {
                        const trendDirection =
                          behaviorTrends.focus_analysis?.trend_direction ||
                          (behaviorTrends.focus_analysis?.trend_analysis
                            ?.trend === "improving"
                            ? "up"
                            : behaviorTrends.focus_analysis?.trend_analysis
                                  ?.trend === "declining"
                              ? "down"
                              : "stable");
                        const trendPercentage =
                          behaviorTrends.focus_analysis?.trend_percentage ||
                          behaviorTrends.focus_analysis?.trend_analysis
                            ?.trend_strength ||
                          0;

                        const trend = getTrendDisplay(
                          trendDirection,
                          trendPercentage,
                        );
                        return (
                          <HStack color={trend.color}>
                            {trend.icon}
                            <Text fontSize="sm">{trend.text}</Text>
                          </HStack>
                        );
                      })()}
                    </HStack>
                  </HStack>
                </Box>

                <Box>
                  <Text fontWeight="bold" mb={2}>
                    姿勢トレンド
                  </Text>
                  <HStack justify="space-between">
                    <Text>良い姿勢:</Text>
                    <HStack>
                      <Badge colorScheme="green">
                        {formatPercentage(
                          behaviorTrends.focus_analysis
                            ?.good_posture_percentage ||
                            behaviorTrends.focus_analysis?.basic_statistics
                              ?.high_focus_ratio ||
                            0,
                        )}
                      </Badge>
                      {(() => {
                        const trendDirection =
                          behaviorTrends.focus_analysis?.trend_direction ||
                          (behaviorTrends.focus_analysis?.trend_analysis
                            ?.trend === "improving"
                            ? "up"
                            : behaviorTrends.focus_analysis?.trend_analysis
                                  ?.trend === "declining"
                              ? "down"
                              : "stable");

                        const trend = getTrendDisplay(trendDirection, 0);
                        return (
                          <HStack color={trend.color}>{trend.icon}</HStack>
                        );
                      })()}
                    </HStack>
                  </HStack>
                </Box>

                <Box>
                  <Text fontWeight="bold" mb={2}>
                    活動状況
                  </Text>
                  <VStack spacing={1} align="stretch" fontSize="sm">
                    <HStack justify="space-between">
                      <Text>在席率:</Text>
                      <Badge>
                        {formatPercentage(
                          behaviorTrends.focus_analysis?.presence_rate ||
                            1 -
                              (behaviorTrends.focus_analysis?.basic_statistics
                                ?.low_focus_ratio || 0),
                        )}
                      </Badge>
                    </HStack>
                    <HStack justify="space-between">
                      <Text>スマホ使用率:</Text>
                      <Badge colorScheme="orange">
                        {formatPercentage(
                          behaviorTrends.focus_analysis
                            ?.smartphone_usage_rate ||
                            behaviorTrends.focus_analysis?.basic_statistics
                              ?.low_focus_ratio ||
                            0,
                        )}
                      </Badge>
                    </HStack>
                    <HStack justify="space-between">
                      <Text>セッション数:</Text>
                      <Badge colorScheme="purple">
                        {behaviorTrends.focus_analysis?.total_sessions ||
                          Object.keys(
                            behaviorTrends.focus_analysis?.hourly_patterns
                              ?.hourly_statistics || {},
                          ).length}
                        回
                      </Badge>
                    </HStack>
                  </VStack>
                </Box>
              </Grid>
            ) : (
              <Alert status="info">
                <AlertIcon />
                トレンドデータが不足しています
              </Alert>
            )}
          </CardBody>
        </Card>

        {/* 今日の洞察 */}
        <Card>
          <CardHeader>
            <HStack>
              <FaLightbulb />
              <Heading size="sm">今日の洞察</Heading>
            </HStack>
          </CardHeader>
          <CardBody>
            {insightsLoading ? (
              <SkeletonText noOfLines={6} spacing="4" />
            ) : dailyInsights ? (
              <VStack spacing={4} align="stretch">
                <Text>{dailyInsights.summary?.summary || ""}</Text>

                <Divider />

                <Grid
                  templateColumns="repeat(auto-fit, minmax(200px, 1fr))"
                  gap={4}
                >
                  <Box>
                    <Text fontWeight="bold" mb={2}>
                      集中スコア
                    </Text>
                    <Progress
                      value={(dailyInsights.insights?.focus_score ?? 0) * 100}
                      colorScheme="blue"
                      size="lg"
                    />
                    <Text fontSize="sm" color="gray.600">
                      {Math.round(
                        (dailyInsights.insights?.focus_score ?? 0) * 100,
                      )}
                      /100
                    </Text>
                  </Box>

                  <Box>
                    <Text fontWeight="bold" mb={2}>
                      生産性スコア
                    </Text>
                    <Progress
                      value={
                        (dailyInsights.insights?.productivity_score ?? 0) * 100
                      }
                      colorScheme="green"
                      size="lg"
                    />
                    <Text fontSize="sm" color="gray.600">
                      {Math.round(
                        (dailyInsights.insights?.productivity_score ?? 0) * 100,
                      )}
                      /100
                    </Text>
                  </Box>
                </Grid>

                {(dailyInsights.insights?.key_findings?.length ?? 0) > 0 && (
                  <>
                    <Divider />
                    <Box>
                      <Text fontWeight="bold" mb={2}>
                        主な発見
                      </Text>
                      <List spacing={1}>
                        {(dailyInsights.insights?.key_findings ?? []).map(
                          (finding, index: number) => {
                            // 型安全な文字列変換
                            const findingText =
                              typeof finding === "string"
                                ? finding
                                : typeof finding === "object" &&
                                    finding !== null
                                  ? (finding as InsightItem).message ||
                                    JSON.stringify(finding)
                                  : String(finding);

                            return (
                              <ListItem key={index}>
                                <ListIcon as={FaEye} color="blue.500" />
                                <Text as="span">{findingText}</Text>
                              </ListItem>
                            );
                          },
                        )}
                      </List>
                    </Box>
                  </>
                )}

                {(dailyInsights.insights?.improvement_areas?.length ?? 0) >
                  0 && (
                  <>
                    <Divider />
                    <Box>
                      <Text fontWeight="bold" mb={2}>
                        改善領域
                      </Text>
                      <List spacing={1}>
                        {(dailyInsights.insights?.improvement_areas ?? []).map(
                          (area, index: number) => {
                            // 型安全な文字列変換
                            const areaText =
                              typeof area === "string"
                                ? area
                                : typeof area === "object" && area !== null
                                  ? (area as InsightItem).message ||
                                    (area as InsightItem).action ||
                                    JSON.stringify(area)
                                  : String(area);

                            return (
                              <ListItem key={index}>
                                <ListIcon
                                  as={FaExclamationTriangle}
                                  color="orange.500"
                                />
                                <Text as="span">{areaText}</Text>
                              </ListItem>
                            );
                          },
                        )}
                      </List>
                    </Box>
                  </>
                )}
              </VStack>
            ) : (
              <Alert status="info">
                <AlertIcon />
                十分なデータが蓄積されていません。継続的な使用で洞察が生成されます。
              </Alert>
            )}
          </CardBody>
        </Card>

        {/* 改善提案 */}
        <Card>
          <CardHeader>
            <HStack justify="space-between" align="center">
              <HStack>
                <FaCheckCircle />
                <Heading size="sm">改善提案</Heading>
              </HStack>
              <Tabs
                variant="soft-rounded"
                colorScheme="blue"
                size="sm"
                onChange={(index) => {
                  const priorities = ["all", "high", "medium", "low"];
                  handlePriorityFilterChange(priorities[index]);
                }}
                defaultIndex={priorities.indexOf(priorityFilter)}
              >
                <TabList>
                  <Tab px={3} py={1}>
                    すべて
                  </Tab>
                  <Tab px={3} py={1}>
                    重要
                  </Tab>
                  <Tab px={3} py={1}>
                    普通
                  </Tab>
                  <Tab px={3} py={1}>
                    軽微
                  </Tab>
                </TabList>
              </Tabs>
            </HStack>
          </CardHeader>
          <CardBody>
            {insightsLoading || recommendationsLoading ? (
              <SkeletonText noOfLines={4} spacing="4" />
            ) : recommendations.length > 0 ? (
              <VStack spacing={3} align="stretch">
                {recommendations.map((rec, index) => (
                  <Alert
                    key={index}
                    status={
                      rec.priority === "high"
                        ? "warning"
                        : rec.priority === "medium"
                          ? "info"
                          : "success"
                    }
                    variant="left-accent"
                  >
                    <AlertIcon />
                    <Box flex="1">
                      <Collapse
                        startingHeight={50}
                        in={expandedItems[index]}
                        animateOpacity
                      >
                        <Text fontSize="sm">{rec.message}</Text>
                        <Text fontSize="xs" color="gray.500" mt={1}>
                          {rec.source} •{" "}
                          {new Date(rec.timestamp).toLocaleString()}
                        </Text>
                      </Collapse>
                      {rec.message.length > 100 && (
                        <Button
                          size="xs"
                          variant="link"
                          onClick={() => toggleItemExpansion(index)}
                          mt={1}
                        >
                          {expandedItems[index] ? "折りたたむ" : "もっと見る"}
                        </Button>
                      )}
                    </Box>
                    <HStack spacing={2}>
                      {rec.audio_url && (
                        <IconButton
                          aria-label="音声再生"
                          icon={<FaVolumeUp />}
                          size="sm"
                          variant="ghost"
                          colorScheme="blue"
                          onClick={() => playAudio(rec.audio_url!)}
                        />
                      )}
                      <IconButton
                        aria-label="コピー"
                        icon={<FaCopy />}
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          navigator.clipboard.writeText(rec.message);
                          toast({
                            title: "コピーしました",
                            status: "success",
                            duration: 2000,
                            isClosable: true,
                          });
                        }}
                      />
                      <Badge
                        colorScheme={
                          rec.priority === "high"
                            ? "red"
                            : rec.priority === "medium"
                              ? "orange"
                              : "green"
                        }
                      >
                        {rec.priority === "high"
                          ? "重要"
                          : rec.priority === "medium"
                            ? "普通"
                            : "軽微"}
                      </Badge>
                    </HStack>
                  </Alert>
                ))}

                {/* ページネーション */}
                {paginationInfo.total_pages > 1 && (
                  <Box mt={4} display="flex" justifyContent="center">
                    <Button
                      isDisabled={
                        paginationInfo.page >= paginationInfo.total_pages
                      }
                      size="sm"
                      onClick={() => {
                        setRecommendationsLoading(true);
                        const nextPage = paginationInfo.page + 1;
                        fetchRecommendations(
                          priorityFilter,
                          nextPage,
                          paginationInfo.limit,
                        ).finally(() => setRecommendationsLoading(false));
                      }}
                      leftIcon={<FaArrowDown />}
                    >
                      もっと見る
                    </Button>
                  </Box>
                )}
              </VStack>
            ) : (
              <Alert status="info">
                <AlertIcon />
                現在利用可能な改善提案はありません
              </Alert>
            )}
          </CardBody>
        </Card>

        {/* 高度分析リンク */}
        <Card>
          <CardHeader>
            <Heading size="sm">🚀 高度分析機能</Heading>
          </CardHeader>
          <CardBody>
            <Text mb={4} color="gray.600">
              より詳細な分析機能を利用できます：
            </Text>
            <Grid
              templateColumns="repeat(auto-fit, minmax(200px, 1fr))"
              gap={4}
            >
              <Button
                leftIcon={<FaChartLine />}
                colorScheme="blue"
                variant="outline"
                onClick={() => {
                  if (onNavigate) {
                    onNavigate("analytics");
                  } else {
                    // Tab構造での使用時の代替処理
                    alert(
                      "統合ダッシュボード機能はIntegratedDashboard使用時のみ利用可能です。",
                    );
                  }
                }}
                size="sm"
              >
                高度分析ダッシュボード
              </Button>
              <Button
                leftIcon={<FaLightbulb />}
                colorScheme="purple"
                variant="outline"
                onClick={() => {
                  if (onNavigate) {
                    onNavigate("personalization");
                  } else {
                    alert(
                      "統合ダッシュボード機能はIntegratedDashboard使用時のみ利用可能です。",
                    );
                  }
                }}
                size="sm"
              >
                パーソナライゼーション
              </Button>
              <Button
                leftIcon={<FaEye />}
                colorScheme="green"
                variant="outline"
                onClick={() => {
                  if (onNavigate) {
                    onNavigate("predictions");
                  } else {
                    alert(
                      "統合ダッシュボード機能はIntegratedDashboard使用時のみ利用可能です。",
                    );
                  }
                }}
                size="sm"
              >
                予測インサイト
              </Button>
              <Button
                leftIcon={<FaCheckCircle />}
                colorScheme="orange"
                variant="outline"
                onClick={() => {
                  if (onNavigate) {
                    onNavigate("learning");
                  } else {
                    alert(
                      "統合ダッシュボード機能はIntegratedDashboard使用時のみ利用可能です。",
                    );
                  }
                }}
                size="sm"
              >
                学習進捗
              </Button>
            </Grid>
          </CardBody>
        </Card>
      </VStack>
    </Box>
  );
};

import React from 'react';
import {
  Card,
  CardHeader,
  CardBody,
  VStack,
  HStack,
  Text,
  Button,
  Grid,
  Box,
  useColorModeValue,
  Icon
} from '@chakra-ui/react';
import {
  FaChartLine,
  FaLightbulb,
  FaEye,
  FaCheckCircle,
  FaCog,
  FaDownload,
  FaShare,
  FaBell
} from 'react-icons/fa';

interface QuickActionsProps {
  onNavigate?: (view: string) => void;
}

interface ActionButtonProps {
  title: string;
  description: string;
  icon: React.ElementType;
  color: string;
  onClick: () => void;
  isDisabled?: boolean;
}

const ActionButton: React.FC<ActionButtonProps> = ({
  title,
  description,
  icon,
  color,
  onClick,
  isDisabled = false
}) => {
  const cardBg = useColorModeValue('white', 'gray.700');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  return (
    <Button
      onClick={onClick}
      isDisabled={isDisabled}
      variant="outline"
      size="lg"
      height="auto"
      p={4}
      bg={cardBg}
      border="1px"
      borderColor={borderColor}
      borderRadius="lg"
      _hover={{
        borderColor: `${color}.300`,
        bg: `${color}.50`,
        transform: 'translateY(-2px)',
        shadow: 'md'
      }}
      _active={{
        transform: 'translateY(0px)'
      }}
      transition="all 0.2s"
    >
      <VStack spacing={3} align="center">
        <Box
          p={3}
          bg={`${color}.100`}
          borderRadius="lg"
          color={`${color}.600`}
        >
          <Icon as={icon} boxSize={6} />
        </Box>
        <VStack spacing={1} align="center">
          <Text fontSize="sm" fontWeight="bold" color="gray.800">
            {title}
          </Text>
          <Text fontSize="xs" color="gray.600" textAlign="center" lineHeight="1.4">
            {description}
          </Text>
        </VStack>
      </VStack>
    </Button>
  );
};

export const QuickActions: React.FC<QuickActionsProps> = ({ onNavigate }) => {
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  const handleNavigation = (view: string) => {
    if (onNavigate) {
      onNavigate(view);
    } else {
      // フォールバック処理
      console.log(`Navigate to: ${view}`);
      alert(`統合ダッシュボード機能は IntegratedDashboard 使用時のみ利用可能です。`);
    }
  };

  const handleExport = () => {
    // データエクスポート機能（将来実装）
    alert('データエクスポート機能は今後実装予定です。');
  };

  const handleShare = () => {
    // 共有機能（将来実装）
    alert('共有機能は今後実装予定です。');
  };

  const handleNotifications = () => {
    // 通知設定（将来実装）
    alert('通知設定は今後実装予定です。');
  };

  const handleSettings = () => {
    // 設定画面への遷移
    handleNavigation('settings');
  };

  return (
    <Card bg={cardBg} border="1px" borderColor={borderColor} borderRadius="xl" shadow="sm">
      <CardHeader>
        <HStack spacing={3}>
          <Box
            p={2}
            bg="blue.100"
            borderRadius="lg"
            color="blue.600"
          >
            <Icon as={FaCog} boxSize={5} />
          </Box>
          <VStack align="start" spacing={0}>
            <Text fontSize="lg" fontWeight="bold" color="gray.800">
              クイックアクション
            </Text>
            <Text fontSize="sm" color="gray.600">
              よく使用する機能への素早いアクセス
            </Text>
          </VStack>
        </HStack>
      </CardHeader>

      <CardBody pt={0}>
        <VStack spacing={6} align="stretch">
          {/* メイン機能 */}
          <Box>
            <Text fontSize="sm" fontWeight="bold" color="gray.700" mb={3}>
              高度分析機能
            </Text>
            <Grid templateColumns="repeat(auto-fit, minmax(200px, 1fr))" gap={4}>
              <ActionButton
                title="詳細分析"
                description="高度な統計分析とグラフ表示"
                icon={FaChartLine}
                color="blue"
                onClick={() => handleNavigation('analytics')}
              />

              <ActionButton
                title="パーソナライゼーション"
                description="個人に最適化された設定"
                icon={FaLightbulb}
                color="purple"
                onClick={() => handleNavigation('personalization')}
              />

              <ActionButton
                title="予測インサイト"
                description="将来のパフォーマンス予測"
                icon={FaEye}
                color="green"
                onClick={() => handleNavigation('predictions')}
              />

              <ActionButton
                title="学習進捗"
                description="スキル向上の追跡と分析"
                icon={FaCheckCircle}
                color="orange"
                onClick={() => handleNavigation('learning')}
              />
            </Grid>
          </Box>

          {/* ユーティリティ機能 */}
          <Box>
            <Text fontSize="sm" fontWeight="bold" color="gray.700" mb={3}>
              ユーティリティ
            </Text>
            <Grid templateColumns="repeat(auto-fit, minmax(150px, 1fr))" gap={3}>
              <ActionButton
                title="データエクスポート"
                description="分析結果をCSV形式で出力"
                icon={FaDownload}
                color="teal"
                onClick={handleExport}
                isDisabled={true}
              />

              <ActionButton
                title="レポート共有"
                description="チームメンバーと結果を共有"
                icon={FaShare}
                color="pink"
                onClick={handleShare}
                isDisabled={true}
              />

              <ActionButton
                title="通知設定"
                description="アラートとリマインダー"
                icon={FaBell}
                color="yellow"
                onClick={handleNotifications}
                isDisabled={true}
              />

              <ActionButton
                title="設定"
                description="システム設定とカスタマイズ"
                icon={FaCog}
                color="gray"
                onClick={handleSettings}
              />
            </Grid>
          </Box>

          {/* ヘルプテキスト */}
          <Box
            p={4}
            bg={useColorModeValue('blue.50', 'blue.900')}
            borderRadius="lg"
            border="1px"
            borderColor={useColorModeValue('blue.200', 'blue.700')}
          >
            <VStack spacing={2} align="start">
              <Text fontSize="sm" fontWeight="bold" color="blue.800">
                💡 ヒント
              </Text>
              <Text fontSize="xs" color="blue.700" lineHeight="1.5">
                各機能は継続的な使用により精度が向上します。
                定期的にデータを確認し、提案された改善策を実践することで、
                より効果的な行動分析結果を得ることができます。
              </Text>
            </VStack>
          </Box>
        </VStack>
      </CardBody>
    </Card>
  );
};
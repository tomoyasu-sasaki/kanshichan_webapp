import React from 'react';
import { Card, CardHeader, CardBody, HStack, Heading, Icon, VStack, Box, Avatar, Text, Badge, Switch, SimpleGrid, useColorModeValue } from '@chakra-ui/react';
import { FaUser, FaToggleOn, FaToggleOff } from 'react-icons/fa';

interface LandmarkItem {
  key: string;
  name: string;
  enabled: boolean;
}

interface LandmarkSettingsGridProps {
  items: LandmarkItem[];
  enabledCount: number;
  totalCount: number;
  onToggle: (key: string) => void;
}

export const LandmarkSettingsGrid: React.FC<LandmarkSettingsGridProps> = ({ items, enabledCount, totalCount, onToggle }) => {
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderEnabled = useColorModeValue('green.200', 'green.600');
  const borderDisabled = useColorModeValue('gray.200', 'gray.600');
  const bgEnabled = useColorModeValue('green.50', 'green.900');
  const bgDisabled = useColorModeValue('gray.50', 'gray.700');
  const emptyBg = useColorModeValue('yellow.50', 'yellow.900');
  const emptyBorder = useColorModeValue('yellow.200', 'yellow.700');

  return (
    <Card bg={cardBg} shadow="lg">
      <CardHeader pb={2}>
        <HStack justify="space-between" align="center">
          <HStack spacing={3}>
            <Icon as={FaUser} color="blue.500" boxSize={5} />
            <VStack align="start" spacing={0}>
              <Heading size="md" color="gray.700" _dark={{ color: 'gray.100' }}>ランドマーク検知設定</Heading>
              <Text fontSize="sm" color="gray.500">人体の特徴点検知の有効/無効を設定</Text>
            </VStack>
          </HStack>
          <Badge colorScheme="blue" variant="subtle" px={3} py={1} borderRadius="full">{enabledCount}/{totalCount} 有効</Badge>
        </HStack>
      </CardHeader>
      <CardBody pt={2}>
        {items.length === 0 ? (
          <Box p={4} borderRadius="lg" bg={emptyBg} border="1px solid" borderColor={emptyBorder}>
            設定が見つかりません
          </Box>
        ) : (
          <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={4}>
            {items.map(item => (
              <Box key={item.key} p={4} borderRadius="lg" border="2px solid" borderColor={item.enabled ? borderEnabled : borderDisabled} bg={item.enabled ? bgEnabled : bgDisabled} transition="all 0.2s" _hover={{ transform: 'translateY(-2px)', shadow: 'md' }}>
                <VStack spacing={3} align="stretch">
                  <HStack justify="space-between" align="center">
                    <Avatar icon={<Icon as={item.enabled ? FaToggleOn : FaToggleOff} />} bg={item.enabled ? 'green.500' : 'gray.500'} size="sm" />
                    <Switch isChecked={item.enabled} onChange={() => onToggle(item.key)} colorScheme="green" size="lg" />
                  </HStack>
                  <VStack align="start" spacing={1}>
                    <Text fontWeight="semibold" fontSize="sm">{item.name}</Text>
                    <Badge colorScheme={item.enabled ? 'green' : 'gray'} variant="subtle" fontSize="xs">{item.enabled ? '有効' : '無効'}</Badge>
                  </VStack>
                </VStack>
              </Box>
            ))}
          </SimpleGrid>
        )}
      </CardBody>
    </Card>
  );
};



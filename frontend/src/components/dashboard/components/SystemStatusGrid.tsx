import React, { useMemo } from 'react';
import { SimpleGrid, Card, CardBody, VStack, HStack, Avatar, Icon, Badge, useColorModeValue } from '@chakra-ui/react';

interface SystemStatusGridProps<T> {
  items: Array<{
    key: keyof T & string;
    title: string;
    description: string;
    icon: any;
    color: string;
    status: 'active' | 'inactive' | 'error';
  }>;
}

export function SystemStatusGrid<T>({ items }: SystemStatusGridProps<T>) {
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  const statusMapping = useMemo(() => ({
    active: { color: 'green', label: 'アクティブ' },
    inactive: { color: 'yellow', label: '非アクティブ' },
    error: { color: 'red', label: 'エラー' }
  }), []);

  return (
    <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6}>
      {items.map((component) => {
        const statusInfo = statusMapping[component.status];
        return (
          <Card key={component.key} bg={cardBg} shadow="lg" border="1px solid" borderColor={borderColor} _hover={{ transform: 'translateY(-2px)', shadow: 'xl' }} transition="all 0.2s">
            <CardBody p={6}>
              <VStack spacing={4} align="stretch">
                <HStack justify="space-between" align="center">
                  <Avatar icon={<Icon as={component.icon} />} bg={component.color} size="md" />
                  <Icon as={component.icon} color={`${statusInfo.color}.500`} boxSize={5} />
                </HStack>
                <VStack align="start" spacing={2}>
                  <span style={{ fontWeight: 600 }}>{component.title}</span>
                  <span style={{ fontSize: '12px', color: 'var(--chakra-colors-gray-500)' }}>{component.description}</span>
                  <Badge colorScheme={statusInfo.color} variant="subtle" px={3} py={1} borderRadius="full" fontSize="xs">
                    {statusInfo.label}
                  </Badge>
                </VStack>
              </VStack>
            </CardBody>
          </Card>
        );
      })}
    </SimpleGrid>
  );
}



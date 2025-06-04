/**
 * ログ閲覧・管理コンポーネント
 * 
 * 蓄積されたログの閲覧、フィルタリング、エクスポート機能を提供します。
 * ログ機能の使用例とUIデモンストレーションも兼ねています。
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  Button,
  Badge,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Select,
  Input,
  Divider,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Stat,
  StatLabel,
  StatNumber,
  useToast,
} from '@chakra-ui/react';
import { LogLevel, LogEntry, LogQueryFilters } from '../utils/types';
import { logger } from '../utils/logger';
import { logExporter, LogFileMetadata } from '../utils/logExporter';

interface StorageStats {
  totalLogs: number;
  sizeEstimate: number;
  oldestLog?: string;
  newestLog?: string;
  storageType: 'IndexedDB' | 'localStorage';
}

export const LogViewer: React.FC = () => {
  const [filteredLogs, setFilteredLogs] = useState<LogEntry[]>([]);
  const [logFiles, setLogFiles] = useState<LogFileMetadata[]>([]);
  const [loading, setLoading] = useState(false);
  const [storageStats, setStorageStats] = useState<StorageStats | null>(null);
  
  // フィルタ状態
  const [levelFilter, setLevelFilter] = useState<LogLevel | ''>('');
  const [sourceFilter, setSourceFilter] = useState('');
  const [messageFilter, setMessageFilter] = useState('');
  const [dateFilter, setDateFilter] = useState('');
  
  const toast = useToast();

  /**
   * ログを読み込み
   */
  const loadLogs = useCallback(async () => {
    setLoading(true);
    try {
      const logStorage = logger.getLogStorage();
      if (logStorage) {
        const filters: LogQueryFilters = {};
        
        if (levelFilter !== '') {
          filters.level = levelFilter as LogLevel;
        }
        
        if (sourceFilter) {
          filters.source = sourceFilter;
        }
        
        if (dateFilter) {
          const selectedDate = new Date(dateFilter);
          filters.startDate = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), selectedDate.getDate());
          filters.endDate = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), selectedDate.getDate(), 23, 59, 59);
        }
        
        const allLogs = await logStorage.getLogs(filters);
        
        // メッセージフィルタを適用
        const filtered = messageFilter 
          ? allLogs.filter(log => 
              log.message.toLowerCase().includes(messageFilter.toLowerCase())
            )
          : allLogs;
          
        setFilteredLogs(filtered);
        
        // ストレージ統計を取得
        const stats = await logStorage.getStorageStats();
        setStorageStats(stats);
      }
    } catch (error) {
      console.error('ログの読み込みに失敗:', error);
      toast({
        title: 'エラー',
        description: 'ログの読み込みに失敗しました',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  }, [levelFilter, sourceFilter, messageFilter, dateFilter, toast]);

  /**
   * ログファイル一覧を読み込み
   */
  const loadLogFiles = useCallback(async () => {
    try {
      await logExporter.initialize();
      const files = await logExporter.getLogFileList();
      setLogFiles(files);
    } catch (error) {
      console.error('ログファイル一覧の読み込みに失敗:', error);
    }
  }, []);

  /**
   * サンプルログを生成
   */
  const generateSampleLogs = useCallback(async () => {
    const sampleMessages = [
      'アプリケーションが開始されました',
      'WebSocket接続が確立されました',
      'AI検出処理を開始しました',
      'フレーム処理に時間がかかっています',
      'メモリ使用量が増加しています',
      'ネットワーク接続エラーが発生しました',
      'ユーザー設定を保存しました',
      'ログローテーションを実行しました',
    ];

    const sources = ['MonitorView', 'WebSocket', 'AIDetector', 'SettingsPanel'];
    const levels = [LogLevel.INFO, LogLevel.WARN, LogLevel.ERROR, LogLevel.DEBUG];

    for (let i = 0; i < 20; i++) {
      const message = sampleMessages[Math.floor(Math.random() * sampleMessages.length)];
      const source = sources[Math.floor(Math.random() * sources.length)];
      const level = levels[Math.floor(Math.random() * levels.length)];
      
      const context = {
        sampleData: true,
        index: i,
        randomValue: Math.random(),
      };

      switch (level) {
        case LogLevel.ERROR:
          await logger.error(message, context, source);
          break;
        case LogLevel.WARN:
          await logger.warn(message, context, source);
          break;
        case LogLevel.INFO:
          await logger.info(message, context, source);
          break;
        case LogLevel.DEBUG:
          await logger.debug(message, context, source);
          break;
      }
    }

    toast({
      title: '完了',
      description: 'サンプルログを生成しました',
      status: 'success',
      duration: 2000,
      isClosable: true,
    });

    await loadLogs();
  }, [loadLogs, toast]);

  /**
   * ログをクリア
   */
  const clearLogs = useCallback(async () => {
    try {
      const logStorage = logger.getLogStorage();
      if (logStorage) {
        await logStorage.clearLogs();
        setFilteredLogs([]);
        
        toast({
          title: '完了',
          description: 'ログをクリアしました',
          status: 'success',
          duration: 2000,
          isClosable: true,
        });
        
        await loadLogs();
      }
    } catch (error) {
      console.error('ログのクリアに失敗:', error);
      toast({
        title: 'エラー',
        description: 'ログのクリアに失敗しました',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    }
  }, [loadLogs, toast]);

  /**
   * エクスポート処理
   */
  const handleExport = useCallback(async (format: 'json' | 'csv') => {
    try {
      await logExporter.downloadTodaysLogs(format);
      
      toast({
        title: '完了',
        description: `ログを${format.toUpperCase()}形式でダウンロードしました`,
        status: 'success',
        duration: 2000,
        isClosable: true,
      });
    } catch (error) {
      console.error('エクスポートに失敗:', error);
      toast({
        title: 'エラー',
        description: 'ログのエクスポートに失敗しました',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    }
  }, [toast]);

  /**
   * ログレベルの色を取得
   */
  const getLevelColor = (level: LogLevel): string => {
    switch (level) {
      case LogLevel.ERROR:
        return 'red';
      case LogLevel.WARN:
        return 'orange';
      case LogLevel.INFO:
        return 'blue';
      case LogLevel.DEBUG:
        return 'gray';
      default:
        return 'gray';
    }
  };

  /**
   * 日時をフォーマット
   */
  const formatTimestamp = (timestamp: string): string => {
    return new Date(timestamp).toLocaleString('ja-JP');
  };

  // 初期読み込み
  useEffect(() => {
    void loadLogs();
    void loadLogFiles();
  }, [loadLogs, loadLogFiles]);

  // フィルタ変更時の再読み込み
  useEffect(() => {
    void loadLogs();
  }, [loadLogs]);

  return (
    <Box p={6} maxW="1200px" mx="auto">
      <VStack spacing={6} align="stretch">
        <Box>
          <Text fontSize="2xl" fontWeight="bold" mb={4}>
            ログ閲覧・管理
          </Text>
          
          {/* アラート表示 */}
          <Alert status="info" mb={4}>
            <AlertIcon />
            <Box>
              <AlertTitle>フロントエンドログ機能デモ</AlertTitle>
              <AlertDescription>
                ブラウザのIndexedDB/LocalStorageを使用したログ管理システムです。
                ログは仮想的な frontend/logs/ ディレクトリ構造で管理されます。
              </AlertDescription>
            </Box>
          </Alert>
        </Box>

        <Tabs>
          <TabList>
            <Tab>ログ一覧</Tab>
            <Tab>ファイル管理</Tab>
            <Tab>統計情報</Tab>
          </TabList>

          <TabPanels>
            {/* ログ一覧タブ */}
            <TabPanel>
              <VStack spacing={4} align="stretch">
                {/* 操作ボタン */}
                <HStack spacing={4} wrap="wrap">
                  <Button 
                    onClick={generateSampleLogs}
                    colorScheme="blue"
                    size="sm"
                  >
                    サンプルログ生成
                  </Button>
                  <Button 
                    onClick={loadLogs}
                    isLoading={loading}
                    size="sm"
                  >
                    更新
                  </Button>
                  <Button 
                    onClick={() => handleExport('json')}
                    colorScheme="green"
                    size="sm"
                  >
                    JSON出力
                  </Button>
                  <Button 
                    onClick={() => handleExport('csv')}
                    colorScheme="green"
                    size="sm"
                  >
                    CSV出力
                  </Button>
                  <Button 
                    onClick={clearLogs}
                    colorScheme="red"
                    size="sm"
                  >
                    ログクリア
                  </Button>
                </HStack>

                {/* フィルタ */}
                <HStack spacing={4} wrap="wrap">
                  <Select 
                    placeholder="レベル選択"
                    value={levelFilter}
                    onChange={(e) => setLevelFilter(e.target.value as LogLevel | '')}
                    size="sm"
                    w="120px"
                  >
                    <option value={LogLevel.ERROR}>ERROR</option>
                    <option value={LogLevel.WARN}>WARN</option>
                    <option value={LogLevel.INFO}>INFO</option>
                    <option value={LogLevel.DEBUG}>DEBUG</option>
                  </Select>
                  
                  <Input
                    placeholder="ソース"
                    value={sourceFilter}
                    onChange={(e) => setSourceFilter(e.target.value)}
                    size="sm"
                    w="120px"
                  />
                  
                  <Input
                    placeholder="メッセージ検索"
                    value={messageFilter}
                    onChange={(e) => setMessageFilter(e.target.value)}
                    size="sm"
                    w="200px"
                  />
                  
                  <Input
                    type="date"
                    value={dateFilter}
                    onChange={(e) => setDateFilter(e.target.value)}
                    size="sm"
                    w="150px"
                  />
                </HStack>

                {/* ログテーブル */}
                <Box overflowX="auto">
                  <Table variant="simple" size="sm">
                    <Thead>
                      <Tr>
                        <Th>時刻</Th>
                        <Th>レベル</Th>
                        <Th>メッセージ</Th>
                        <Th>ソース</Th>
                        <Th>コンテキスト</Th>
                      </Tr>
                    </Thead>
                    <Tbody>
                      {filteredLogs.map((log, index) => (
                        <Tr key={`${log.timestamp}-${index}`}>
                          <Td fontSize="xs">
                            {formatTimestamp(log.timestamp)}
                          </Td>
                          <Td>
                            <Badge colorScheme={getLevelColor(log.level)}>
                              {LogLevel[log.level]}
                            </Badge>
                          </Td>
                          <Td maxW="300px" isTruncated>
                            {log.message}
                          </Td>
                          <Td>{log.source || '-'}</Td>
                          <Td maxW="200px" isTruncated fontSize="xs">
                            {log.context ? JSON.stringify(log.context) : '-'}
                          </Td>
                        </Tr>
                      ))}
                    </Tbody>
                  </Table>
                </Box>

                {filteredLogs.length === 0 && (
                  <Text textAlign="center" color="gray.500">
                    ログが見つかりません
                  </Text>
                )}
              </VStack>
            </TabPanel>

            {/* ファイル管理タブ */}
            <TabPanel>
              <VStack spacing={4} align="stretch">
                <Text fontSize="lg" fontWeight="bold">
                  ログファイル一覧（仮想 frontend/logs/ ディレクトリ）
                </Text>
                
                <Table variant="simple" size="sm">
                  <Thead>
                    <Tr>
                      <Th>ファイル名</Th>
                      <Th>パス</Th>
                      <Th>サイズ</Th>
                      <Th>エントリ数</Th>
                      <Th>作成日時</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {logFiles.map((file, index) => (
                      <Tr key={index}>
                        <Td>{file.filename}</Td>
                        <Td fontSize="xs" color="gray.600">{file.path}</Td>
                        <Td>{Math.round(file.size / 1024)} KB</Td>
                        <Td>{file.entryCount}</Td>
                        <Td fontSize="xs">
                          {formatTimestamp(file.createdAt)}
                        </Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
              </VStack>
            </TabPanel>

            {/* 統計情報タブ */}
            <TabPanel>
              <VStack spacing={4} align="stretch">
                <Text fontSize="lg" fontWeight="bold">
                  ストレージ統計
                </Text>
                
                {storageStats && (
                  <HStack spacing={8} wrap="wrap">
                    <Stat>
                      <StatLabel>総ログ数</StatLabel>
                      <StatNumber>{storageStats.totalLogs}</StatNumber>
                    </Stat>
                    
                    <Stat>
                      <StatLabel>推定サイズ</StatLabel>
                      <StatNumber>{Math.round(storageStats.sizeEstimate / 1024)} KB</StatNumber>
                    </Stat>
                    
                    <Stat>
                      <StatLabel>ストレージタイプ</StatLabel>
                      <StatNumber fontSize="md">{storageStats.storageType}</StatNumber>
                    </Stat>
                  </HStack>
                )}
                
                <Divider />
                
                <Text fontSize="md" fontWeight="bold">
                  レベル別ログ出力
                </Text>
                
                <HStack spacing={4}>
                  <Button 
                    onClick={() => logExporter.downloadErrorLogs('json')}
                    colorScheme="red"
                    size="sm"
                  >
                    エラーログ出力
                  </Button>
                  <Button 
                    onClick={() => logExporter.downloadWarningLogs('json')}
                    colorScheme="orange"
                    size="sm"
                  >
                    警告ログ出力
                  </Button>
                  <Button 
                    onClick={() => logExporter.downloadLogSummaryReport()}
                    colorScheme="purple"
                    size="sm"
                  >
                    サマリーレポート
                  </Button>
                </HStack>
              </VStack>
            </TabPanel>
          </TabPanels>
        </Tabs>
      </VStack>
    </Box>
  );
}; 
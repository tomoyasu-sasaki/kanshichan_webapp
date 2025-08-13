import React, { useState, useRef } from 'react';
import {
  Card,
  CardHeader,
  CardBody,
  VStack,
  FormControl,
  FormLabel,
  Select,
  HStack,
  Button,
  Input,
  Text,
  Progress,
  useToast,
  Heading
} from '@chakra-ui/react';
import { FaUpload } from 'react-icons/fa';
import type { VoiceSettings, AudioFile } from '../types';

interface VoiceSampleManagerProps {
  settings: VoiceSettings;
  availableFiles: AudioFile[];
  onSettingsChange: (settings: VoiceSettings) => void;
  onFilesUpdate: () => void;
}

export const VoiceSampleManager: React.FC<VoiceSampleManagerProps> = ({
  settings,
  availableFiles,
  onSettingsChange,
  onFilesUpdate
}) => {
  const [uploading, setUploading] = useState(false);
  const [sampleName, setSampleName] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const toast = useToast();

  // 音声サンプル選択ハンドラ
  const handleVoiceSampleChange = (sampleId: string) => {
    onSettingsChange({ 
      ...settings,
      voiceSampleId: sampleId === 'none' ? null : sampleId 
    });
  };

  // 音声ファイルアップロード
  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // ファイル検証
    if (!file.type.startsWith('audio/')) {
      toast({
        title: 'アップロードエラー',
        description: '音声ファイルを選択してください',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    if (file.size > 10 * 1024 * 1024) { // 10MB制限
      toast({
        title: 'ファイルサイズエラー',
        description: 'ファイルサイズは10MB以下にしてください',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    // ファイルを選択状態にセット
    setSelectedFile(file);
  };

  // 音声サンプル登録
  const handleRegisterSample = async () => {
    if (!selectedFile) {
      toast({
        title: '登録エラー',
        description: 'ファイルを選択してください',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    setUploading(true);

    try {
      const formData = new FormData();
      formData.append('audio_file', selectedFile);
      formData.append('text', 'これは音声サンプルです。');
      formData.append('emotion', settings.defaultEmotion);
      formData.append('language', settings.defaultLanguage);
      formData.append('return_url', 'true');
      
      // カスタム名前が設定されている場合は追加
      if (sampleName.trim()) {
        formData.append('custom_filename', sampleName.trim());
      }

      const response = await fetch('/api/v1/tts/upload_voice_sample', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          toast({
            title: '登録完了',
            description: `音声サンプル「${sampleName || selectedFile.name}」を登録しました`,
            status: 'success',
            duration: 3000,
            isClosable: true,
          });
          
          // 状態をリセット
          setSelectedFile(null);
          setSampleName('');
          if (fileInputRef.current) {
            fileInputRef.current.value = '';
          }
          
          // リストを更新
          onFilesUpdate();
        } else {
          throw new Error(data.error || 'アップロードに失敗しました');
        }
      } else {
        throw new Error('アップロードに失敗しました');
      }
    } catch (error) {
      toast({
        title: 'アップロードエラー',
        description: `ファイルアップロードに失敗しました: ${error}`,
        status: 'error',
        duration: 4000,
        isClosable: true,
      });
    } finally {
      setUploading(false);
    }
  };

  // 音声サンプル削除
  const handleDeleteSample = async (fileId: string, filename: string) => {
    if (!confirm(`音声サンプル「${filename}」を削除しますか？`)) {
      return;
    }
    
    setDeleting(fileId);

    try {
      const response = await fetch(`/api/v1/tts/voices/${fileId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        toast({
          title: '削除完了',
          description: `音声サンプル「${filename}」を削除しました`,
          status: 'success',
          duration: 3000,
          isClosable: true,
        });
        
        // 削除したサンプルが現在選択されている場合はリセット
        if (settings.voiceSampleId === fileId) {
          onSettingsChange({ ...settings, voiceSampleId: null });
        }
        
        // リストを更新
        onFilesUpdate();
      } else {
        throw new Error('削除に失敗しました');
      }
    } catch (error) {
      toast({
        title: '削除エラー',
        description: `削除に失敗しました: ${error}`,
        status: 'error',
        duration: 4000,
        isClosable: true,
      });
    } finally {
      setDeleting(null);
    }
  };

  return (
    <Card>
      <CardHeader>
        <Heading size="sm">音声サンプル</Heading>
      </CardHeader>
      <CardBody>
        <VStack spacing={4} align="stretch">
          {/* 使用する音声サンプル選択 */}
          <FormControl>
            <FormLabel>使用する音声サンプル</FormLabel>
            <Select
              value={settings.voiceSampleId || 'none'}
              onChange={(e) => handleVoiceSampleChange(e.target.value)}
            >
              <option value="none">デフォルト音声（sample.wav）</option>
              {availableFiles.map((file) => (
                <option key={file.file_id} value={file.file_id}>
                  {file.filename} ({(file.file_size / 1024 / 1024).toFixed(1)}MB)
                </option>
              ))}
            </Select>
          </FormControl>

          {/* 音声サンプル削除 */}
          {availableFiles.length > 0 && (
            <FormControl>
              <FormLabel>音声サンプル削除</FormLabel>
              <VStack spacing={2} align="stretch">
                {availableFiles.map((file) => (
                  <HStack key={file.file_id} justify="space-between" p={2} bg="gray.50" borderRadius="md">
                    <VStack align="start" spacing={0}>
                      <Text fontSize="sm" fontWeight="medium">{file.filename}</Text>
                      <Text fontSize="xs" color="gray.500">
                        {(file.file_size / 1024 / 1024).toFixed(1)}MB
                      </Text>
                    </VStack>
                    <Button
                      size="xs"
                      colorScheme="red"
                      variant="outline"
                      onClick={() => handleDeleteSample(file.file_id, file.filename)}
                      isLoading={deleting === file.file_id}
                      loadingText="削除中..."
                    >
                      削除
                    </Button>
                  </HStack>
                ))}
              </VStack>
            </FormControl>
          )}
          
          {/* 新しい音声サンプルのアップロード */}
          <FormControl>
            <FormLabel>新しい音声サンプルのアップロード</FormLabel>
            <VStack spacing={3} align="stretch">
              <FormControl>
                <FormLabel fontSize="sm">サンプル名（オプション）</FormLabel>
                <Input
                  placeholder="例: 自分の声サンプル、録音した音声など"
                  value={sampleName}
                  onChange={(e) => setSampleName(e.target.value)}
                  size="sm"
                  maxLength={50}
                />
                <Text fontSize="xs" color="gray.500">
                  名前を設定しない場合は、元のファイル名が使用されます
                </Text>
              </FormControl>
              
              <HStack spacing={3}>
                <Button
                  leftIcon={<FaUpload />}
                  onClick={() => fileInputRef.current?.click()}
                  size="sm"
                  variant="outline"
                >
                  ファイル選択
                </Button>
                
                <Button
                  colorScheme="blue"
                  onClick={handleRegisterSample}
                  isLoading={uploading}
                  loadingText="登録中..."
                  size="sm"
                  isDisabled={!selectedFile}
                >
                  登録
                </Button>
              </HStack>
              
              {selectedFile && (
                <Text fontSize="sm" color="green.600">
                  選択されたファイル: {selectedFile.name}
                </Text>
              )}
              
              <Text fontSize="sm" color="gray.500">
                WAV, MP3形式 (5-30秒推奨, 10MB以下)
              </Text>
            
              <Input
                ref={fileInputRef}
                type="file"
                accept="audio/*"
                onChange={handleFileUpload}
                display="none"
              />
            </VStack>
          </FormControl>

          {uploading && (
            <Progress size="sm" isIndeterminate colorScheme="blue" />
          )}
        </VStack>
      </CardBody>
    </Card>
  );
};
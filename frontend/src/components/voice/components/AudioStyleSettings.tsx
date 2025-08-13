import React, { useRef } from 'react';
import {
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Box,
  VStack,
  FormControl,
  FormLabel,
  Input,
  Text,
  Switch,
  Spacer,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  HStack,
  Button
} from '@chakra-ui/react';
import { FaUpload } from 'react-icons/fa';
import type { VoiceSettings } from '../types';

interface AudioStyleSettingsProps {
  settings: VoiceSettings;
  onSettingsChange: (updates: Partial<VoiceSettings>) => void;
}

export const AudioStyleSettings: React.FC<AudioStyleSettingsProps> = ({
  settings,
  onSettingsChange
}) => {
  const styleFileInputRef = useRef<HTMLInputElement>(null);

  const handleStyleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      // TODO: Handle style file upload
      console.log('Style file selected:', file.name);
    }
  };

  return (
    <Accordion allowToggle mt={2}>
      <AccordionItem>
        <AccordionButton>
          <Box as="span" flex='1' textAlign='left'>
            オーディオスタイル設定
          </Box>
          <AccordionIcon />
        </AccordionButton>
        <AccordionPanel pb={4}>
          <VStack spacing={4} align="stretch">
            {/* オーディオプレフィックス */}
            <FormControl>
              <FormLabel>音声プレフィックス</FormLabel>
              <Input 
                placeholder="例: うーん、あのー、えっと" 
                size="sm"
                value={settings.audioPrefix || ''}
                onChange={(e) => onSettingsChange({ 
                  audioPrefix: e.target.value || null 
                })}
              />
              <Text fontSize="xs" color="gray.500" mt={1}>
                生成音声の先頭に付与するフレーズ
              </Text>
            </FormControl>

            {/* スタイルチェックボックス */}
            <VStack spacing={2} align="stretch">
              <FormControl display="flex" alignItems="center">
                <FormLabel htmlFor="useBreathStyle" mb="0" fontSize="sm">
                  息継ぎスタイル
                </FormLabel>
                <Spacer />
                <Switch 
                  id="useBreathStyle"
                  colorScheme="blue"
                  isChecked={settings.useBreathStyle}
                  onChange={(e) => onSettingsChange({ 
                    useBreathStyle: e.target.checked 
                  })}
                />
              </FormControl>

              <FormControl display="flex" alignItems="center">
                <FormLabel htmlFor="useWhisperStyle" mb="0" fontSize="sm">
                  ささやきスタイル (Whisper風)
                </FormLabel>
                <Spacer />
                <Switch 
                  id="useWhisperStyle"
                  colorScheme="blue"
                  isChecked={settings.useWhisperStyle}
                  onChange={(e) => onSettingsChange({ 
                    useWhisperStyle: e.target.checked 
                  })}
                />
              </FormControl>
            </VStack>

            {/* スタイル強度 */}
            {(settings.useBreathStyle || settings.useWhisperStyle) && (
              <FormControl>
                <FormLabel>スタイル強度: {settings.styleIntensity.toFixed(2)}</FormLabel>
                <Slider
                  value={settings.styleIntensity}
                  onChange={(value) => onSettingsChange({ styleIntensity: value })}
                  min={0.1}
                  max={1.0}
                  step={0.05}
                >
                  <SliderTrack>
                    <SliderFilledTrack />
                  </SliderTrack>
                  <SliderThumb />
                </Slider>
                <Text fontSize="xs" color="gray.500">
                  スタイルの適用強度（高いほど特徴的）
                </Text>
              </FormControl>
            )}

            {/* スタイルファイルアップロード */}
            <FormControl>
              <FormLabel>スタイル参照ファイル</FormLabel>
              <HStack>
                <Input
                  type="file"
                  accept="audio/*"
                  onChange={handleStyleFileUpload}
                  size="sm"
                  display="none"
                  ref={styleFileInputRef}
                />
                <Button
                  onClick={() => styleFileInputRef.current?.click()}
                  size="sm"
                  leftIcon={<FaUpload />}
                >
                  ファイル選択
                </Button>
                <Text 
                  fontSize="sm" 
                  color="gray.500"
                >
                  未選択
                </Text>
              </HStack>
              <Text fontSize="xs" color="gray.500" mt={1}>
                特定のスタイルを参照するオーディオファイル
              </Text>
            </FormControl>
          </VStack>
        </AccordionPanel>
      </AccordionItem>
    </Accordion>
  );
};
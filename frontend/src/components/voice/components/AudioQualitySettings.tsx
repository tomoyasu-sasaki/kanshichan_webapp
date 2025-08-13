import React from 'react';
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
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  Text
} from '@chakra-ui/react';
import type { VoiceSettings } from '../types';

interface AudioQualitySettingsProps {
  settings: VoiceSettings;
  onSettingsChange: (updates: Partial<VoiceSettings>) => void;
}

export const AudioQualitySettings: React.FC<AudioQualitySettingsProps> = ({
  settings,
  onSettingsChange
}) => {
  return (
    <Accordion allowToggle mt={2}>
      <AccordionItem>
        <AccordionButton>
          <Box as="span" flex='1' textAlign='left'>
            音質詳細設定
          </Box>
          <AccordionIcon />
        </AccordionButton>
        <AccordionPanel pb={4}>
          <VStack spacing={4} align="stretch">
            {/* 最大周波数調整 */}
            <FormControl>
              <FormLabel>最大周波数: {settings.maxFrequency}Hz</FormLabel>
              <Slider
                value={settings.maxFrequency}
                onChange={(value) => onSettingsChange({ maxFrequency: value })}
                min={8000}
                max={24000}
                step={1000}
              >
                <SliderTrack>
                  <SliderFilledTrack />
                </SliderTrack>
                <SliderThumb />
              </Slider>
              <Text fontSize="xs" color="gray.500">
                低い値=柔らかい音質、高い値=クリアな音質（デフォルト:24000）
              </Text>
            </FormControl>

            {/* 音質スコア調整 */}
            <FormControl>
              <FormLabel>音質スコア: {settings.audioQuality.toFixed(1)}</FormLabel>
              <Slider
                value={settings.audioQuality}
                onChange={(value) => onSettingsChange({ audioQuality: value })}
                min={1.0}
                max={5.0}
                step={0.1}
              >
                <SliderTrack>
                  <SliderFilledTrack />
                </SliderTrack>
                <SliderThumb />
              </Slider>
              <Text fontSize="xs" color="gray.500">
                音声の明瞭さと自然さのバランス（デフォルト:4.0）
              </Text>
            </FormControl>

            {/* VQスコア調整 */}
            <FormControl>
              <FormLabel>VQスコア: {settings.vqScore.toFixed(2)}</FormLabel>
              <Slider
                value={settings.vqScore}
                onChange={(value) => onSettingsChange({ vqScore: value })}
                min={0.5}
                max={0.8}
                step={0.01}
              >
                <SliderTrack>
                  <SliderFilledTrack />
                </SliderTrack>
                <SliderThumb />
              </Slider>
              <Text fontSize="xs" color="gray.500">
                音声の音響品質（デフォルト:0.78）
              </Text>
            </FormControl>
          </VStack>
        </AccordionPanel>
      </AccordionItem>
    </Accordion>
  );
};
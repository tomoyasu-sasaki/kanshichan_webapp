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
  Text,
  HStack,
  Switch,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Button
} from '@chakra-ui/react';
import type { VoiceSettings } from '../types';

interface GenerationParameterSettingsProps {
  settings: VoiceSettings;
  onSettingsChange: (updates: Partial<VoiceSettings>) => void;
}

export const GenerationParameterSettings: React.FC<GenerationParameterSettingsProps> = ({
  settings,
  onSettingsChange
}) => {
  return (
    <Accordion allowToggle mt={2}>
      <AccordionItem>
        <AccordionButton>
          <Box as="span" flex='1' textAlign='left'>
            生成パラメータ設定
          </Box>
          <AccordionIcon />
        </AccordionButton>
        <AccordionPanel pb={4}>
          <VStack spacing={4} align="stretch">
            {/* CFGスケール調整 */}
            <FormControl>
              <FormLabel>CFGスケール: {settings.cfgScale.toFixed(2)}</FormLabel>
              <Slider
                value={settings.cfgScale}
                onChange={(value) => onSettingsChange({ cfgScale: value })}
                min={0.0}
                max={1.5}
                step={0.05}
              >
                <SliderTrack>
                  <SliderFilledTrack />
                </SliderTrack>
                <SliderThumb />
              </Slider>
              <Text fontSize="xs" color="gray.500">
                低い値=自由度高、高い値=一貫性重視（デフォルト:0.8）
              </Text>
            </FormControl>

            {/* Min-P調整 */}
            <FormControl>
              <FormLabel>Min-P: {settings.minP.toFixed(2)}</FormLabel>
              <Slider
                value={settings.minP}
                onChange={(value) => onSettingsChange({ minP: value })}
                min={0.0}
                max={1.0}
                step={0.05}
              >
                <SliderTrack>
                  <SliderFilledTrack />
                </SliderTrack>
                <SliderThumb />
              </Slider>
              <Text fontSize="xs" color="gray.500">
                最小確率サンプリング値（高いほど自然だが変化少）
              </Text>
            </FormControl>

            {/* シード設定 */}
            <FormControl>
              <HStack justify="space-between" align="center">
                <FormLabel mb={0}>乱数シード使用</FormLabel>
                <Switch
                  isChecked={settings.useSeed}
                  onChange={(e) => onSettingsChange({ useSeed: e.target.checked })}
                />
              </HStack>
              
              {settings.useSeed && (
                <HStack mt={2}>
                  <NumberInput 
                    value={settings.seed} 
                    min={0} 
                    max={2147483647}
                    onChange={(_, value) => onSettingsChange({ seed: value })}
                    size="sm"
                    flex={1}
                  >
                    <NumberInputField />
                    <NumberInputStepper>
                      <NumberIncrementStepper />
                      <NumberDecrementStepper />
                    </NumberInputStepper>
                  </NumberInput>
                  <Button 
                    size="sm"
                    onClick={() => onSettingsChange({ 
                      seed: Math.floor(Math.random() * 2147483647) 
                    })}
                  >
                    ランダム
                  </Button>
                </HStack>
              )}
              <Text fontSize="xs" color="gray.500" mt={1}>
                同じシードで同じ内容を生成すると同じ結果になります
              </Text>
            </FormControl>
          </VStack>
        </AccordionPanel>
      </AccordionItem>
    </Accordion>
  );
};
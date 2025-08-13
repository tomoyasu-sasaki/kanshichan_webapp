import React from 'react';
import {
  FormControl,
  FormLabel,
  VStack,
  Switch,
  Spacer,
  Text
} from '@chakra-ui/react';
import type { VoiceSettings } from '../types';

interface ProcessingOptionsProps {
  settings: VoiceSettings;
  onSettingsChange: (updates: Partial<VoiceSettings>) => void;
}

export const ProcessingOptions: React.FC<ProcessingOptionsProps> = ({
  settings,
  onSettingsChange
}) => {
  return (
    <FormControl mt={4}>
      <FormLabel>処理オプション</FormLabel>
      <VStack spacing={2} align="stretch">
        <FormControl display="flex" alignItems="center">
          <FormLabel htmlFor="useNoiseReduction" mb="0" fontSize="sm">
            ノイズ除去
          </FormLabel>
          <Spacer />
          <Switch 
            id="useNoiseReduction"
            colorScheme="blue"
            isChecked={settings.useNoiseReduction}
            onChange={(e) => onSettingsChange({ 
              useNoiseReduction: e.target.checked 
            })}
          />
        </FormControl>

        <FormControl display="flex" alignItems="center">
          <FormLabel htmlFor="useStreamingPlayback" mb="0" fontSize="sm">
            ストリーミング再生
          </FormLabel>
          <Spacer />
          <Switch 
            id="useStreamingPlayback"
            colorScheme="blue"
            isChecked={settings.useStreamingPlayback}
            onChange={(e) => onSettingsChange({ 
              useStreamingPlayback: e.target.checked 
            })}
          />
        </FormControl>
      </VStack>
      <Text fontSize="xs" color="gray.500" mt={1}>
        ストリーミング再生: リアルタイムで音声を再生します
      </Text>
    </FormControl>
  );
};
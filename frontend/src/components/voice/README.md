# Voice Settings Components

This directory contains the refactored Voice Settings components, organized for better maintainability and readability.

## Structure

```
voice/
├── components/           # UI Components
│   ├── AudioQualitySettings.tsx      # Audio quality controls
│   ├── AudioStyleSettings.tsx        # Audio style options
│   ├── BasicSettings.tsx             # Main settings panel
│   ├── EmotionSettings.tsx           # Emotion controls
│   ├── GenerationParameterSettings.tsx # Generation parameters
│   ├── ProcessingOptions.tsx         # Processing options
│   ├── VoicePreview.tsx              # Preview functionality
│   ├── VoiceSampleManager.tsx        # Voice sample management
│   ├── VoiceSettingsHeader.tsx       # Header component
│   └── VoiceSettingsSummary.tsx      # Settings summary display
├── hooks/               # Custom hooks
│   ├── useAudioFiles.ts              # Audio file management
│   ├── useTTSStatus.ts               # TTS service status
│   └── useVoicePreview.ts            # Voice preview logic
├── constants.ts         # Constants and default values
├── types.ts            # TypeScript type definitions
├── index.ts            # Barrel exports
├── VoiceSettings.tsx   # Main component
└── README.md           # This file
```

## Components

### Main Component
- **VoiceSettings**: The main container component that orchestrates all sub-components

### UI Components
- **VoiceSettingsHeader**: Displays TTS status and header information
- **BasicSettings**: Core voice settings (mode, speed, pitch, volume, etc.)
- **EmotionSettings**: Emotion presets and custom emotion vectors
- **AudioQualitySettings**: Audio quality parameters (frequency, quality scores)
- **GenerationParameterSettings**: AI generation parameters (CFG scale, seed, etc.)
- **AudioStyleSettings**: Audio style options (breath, whisper, prefix)
- **ProcessingOptions**: Processing flags (noise reduction, streaming)
- **VoiceSampleManager**: Voice sample upload/management (voice cloning mode)
- **VoicePreview**: Test voice synthesis with current settings
- **VoiceSettingsSummary**: Display current settings summary

### Custom Hooks
- **useTTSStatus**: Manages TTS service status and initialization
- **useAudioFiles**: Handles audio file listing and management
- **useVoicePreview**: Manages voice preview functionality with fallbacks

## Usage

```tsx
import { VoiceSettings } from '@/components/voice';

// Use the main component
<VoiceSettings onSettingsChange={handleSettingsChange} />

// Or import individual components
import { BasicSettings, EmotionSettings } from '@/components/voice';
```

## Benefits of This Structure

1. **Modularity**: Each component has a single responsibility
2. **Reusability**: Components can be used independently
3. **Maintainability**: Easier to locate and modify specific functionality
4. **Testing**: Smaller components are easier to test
5. **Performance**: Better code splitting and lazy loading potential
6. **Type Safety**: Centralized type definitions
7. **Clean Imports**: Barrel exports for cleaner import statements

## Migration Notes

The original monolithic VoiceSettings component has been split into:
- Logical UI sections (components/)
- Business logic (hooks/)
- Shared utilities (constants.ts, types.ts)

All functionality remains the same, but the code is now more organized and maintainable.
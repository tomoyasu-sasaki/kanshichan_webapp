export interface LandmarkSetting {
  enabled: boolean;
  name: string;
}

export interface DetectionObjectSetting {
  enabled: boolean;
  name: string;
  confidence_threshold: number;
  alert_threshold: number;
}

export interface Settings {
  absence_threshold: number;
  smartphone_threshold: number;
  landmark_settings: Record<string, LandmarkSetting>;
  detection_objects: Record<string, DetectionObjectSetting>;
}

export interface SettingsStats {
  totalLandmarks: number;
  enabledLandmarks: number;
  totalObjects: number;
  enabledObjects: number;
}



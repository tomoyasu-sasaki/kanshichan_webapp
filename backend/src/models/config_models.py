from sqlalchemy import CheckConstraint
from sqlalchemy import Integer, String, Text, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from . import db


class GeneralSettings(db.Model):
    __bind_key__ = 'config'
    __tablename__ = 'general_settings'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    server_port: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint('id = 1', name='ck_general_settings_singleton'),
    )


class LoggingSettings(db.Model):
    __bind_key__ = 'config'
    __tablename__ = 'logging_settings'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    enable_file_output: Mapped[bool] = mapped_column(Boolean, nullable=False)
    file_level: Mapped[str] = mapped_column(String(32), nullable=False)
    console_level: Mapped[str] = mapped_column(String(32), nullable=False)
    level: Mapped[str] = mapped_column(String(32), nullable=False)
    log_dir: Mapped[str] = mapped_column(Text, nullable=False)
    max_file_size_mb: Mapped[int | None] = mapped_column(Integer)
    backup_count: Mapped[int | None] = mapped_column(Integer)
    suppress_frequent_logs: Mapped[bool | None] = mapped_column(Boolean)
    frame_log_interval: Mapped[int | None] = mapped_column(Integer)
    detection_log_sampling: Mapped[int | None] = mapped_column(Integer)

    __table_args__ = (
        CheckConstraint('id = 1', name='ck_logging_settings_singleton'),
    )


class ModelsYolo(db.Model):
    __bind_key__ = 'config'
    __tablename__ = 'models_yolo'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_name: Mapped[str] = mapped_column(Text, nullable=False)
    models_dir: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        CheckConstraint('id = 1', name='ck_models_yolo_singleton'),
    )


class DetectorSettings(db.Model):
    __bind_key__ = 'config'
    __tablename__ = 'detector_settings'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    use_mediapipe: Mapped[bool] = mapped_column(Boolean, nullable=False)
    use_yolo: Mapped[bool] = mapped_column(Boolean, nullable=False)

    __table_args__ = (
        CheckConstraint('id = 1', name='ck_detector_settings_singleton'),
    )


class ConditionsSettings(db.Model):
    __bind_key__ = 'config'
    __tablename__ = 'conditions_settings'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    absence_threshold_seconds: Mapped[float | None] = mapped_column(Float)
    smartphone_threshold_seconds: Mapped[float | None] = mapped_column(Float)
    smartphone_grace_period_seconds: Mapped[float | None] = mapped_column(Float)

    __table_args__ = (
        CheckConstraint('id = 1', name='ck_conditions_settings_singleton'),
    )


class DetectionSmootherSettings(db.Model):
    __bind_key__ = 'config'
    __tablename__ = 'detection_smoother_settings'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)

    hysteresis_enabled: Mapped[bool | None] = mapped_column(Boolean)
    hysteresis_high: Mapped[float | None] = mapped_column(Float)
    hysteresis_low: Mapped[float | None] = mapped_column(Float)

    interpolation_enabled: Mapped[bool | None] = mapped_column(Boolean)
    interpolation_fade_out: Mapped[float | None] = mapped_column(Float)
    interpolation_max_missing: Mapped[int | None] = mapped_column(Integer)

    moving_avg_enabled: Mapped[bool | None] = mapped_column(Boolean)
    moving_avg_window: Mapped[int | None] = mapped_column(Integer)
    moving_avg_weight_recent: Mapped[float | None] = mapped_column(Float)

    __table_args__ = (
        CheckConstraint('id = 1', name='ck_detection_smoother_settings_singleton'),
    )


class DetectionObject(db.Model):
    __bind_key__ = 'config'
    __tablename__ = 'detection_objects'

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    class_name: Mapped[str] = mapped_column(Text, nullable=False)
    alert_message: Mapped[str | None] = mapped_column(Text)
    alert_sound: Mapped[str | None] = mapped_column(Text)
    alert_threshold: Mapped[float | None] = mapped_column(Float)
    confidence_threshold: Mapped[float | None] = mapped_column(Float)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    thickness: Mapped[int | None] = mapped_column(Integer)
    color_r: Mapped[int | None] = mapped_column(Integer)
    color_g: Mapped[int | None] = mapped_column(Integer)
    color_b: Mapped[int | None] = mapped_column(Integer)


class LandmarkSettings(db.Model):
    __bind_key__ = 'config'
    __tablename__ = 'landmark_settings'

    key: Mapped[str] = mapped_column(String(16), primary_key=True)
    name: Mapped[str | None] = mapped_column(Text)
    enabled: Mapped[bool | None] = mapped_column(Boolean)
    thickness: Mapped[int | None] = mapped_column(Integer)
    color_r: Mapped[int | None] = mapped_column(Integer)
    color_g: Mapped[int | None] = mapped_column(Integer)
    color_b: Mapped[int | None] = mapped_column(Integer)

    __table_args__ = (
        CheckConstraint("key in ('face','hands','pose')", name='ck_landmark_key_allowed'),
    )


class TtsSettings(db.Model):
    __bind_key__ = 'config'
    __tablename__ = 'tts_settings'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cache_dir: Mapped[str | None] = mapped_column(Text)
    cache_ttl_hours: Mapped[int | None] = mapped_column(Integer)
    enable_audio_cache: Mapped[bool | None] = mapped_column(Boolean)
    enable_voice_cloning: Mapped[bool | None] = mapped_column(Boolean)
    enable_mps: Mapped[bool | None] = mapped_column(Boolean)
    mps_half_precision: Mapped[bool | None] = mapped_column(Boolean)
    mps_memory_fraction: Mapped[float | None] = mapped_column(Float)
    gpu_memory_optimization: Mapped[bool | None] = mapped_column(Boolean)
    default_language: Mapped[str | None] = mapped_column(String(8))
    default_voice_mode: Mapped[str | None] = mapped_column(String(32))
    default_voice_sample_id: Mapped[str | None] = mapped_column(String(128))
    default_voice_sample_path: Mapped[str | None] = mapped_column(Text)
    default_audio_quality: Mapped[float | None] = mapped_column(Float)
    default_voice_pitch: Mapped[float | None] = mapped_column(Float)
    default_voice_speed: Mapped[float | None] = mapped_column(Float)
    default_voice_volume: Mapped[float | None] = mapped_column(Float)
    default_vq_score: Mapped[float | None] = mapped_column(Float)
    default_cfg_scale: Mapped[float | None] = mapped_column(Float)
    default_min_p: Mapped[float | None] = mapped_column(Float)
    default_max_frequency: Mapped[int | None] = mapped_column(Integer)
    default_use_seed: Mapped[bool | None] = mapped_column(Boolean)
    default_seed: Mapped[int | None] = mapped_column(Integer)
    default_fast_mode: Mapped[bool | None] = mapped_column(Boolean)
    default_use_breath_style: Mapped[bool | None] = mapped_column(Boolean)
    default_use_noise_reduction: Mapped[bool | None] = mapped_column(Boolean)
    default_use_streaming_playback: Mapped[bool | None] = mapped_column(Boolean)
    default_use_whisper_style: Mapped[bool | None] = mapped_column(Boolean)
    default_emotion: Mapped[str | None] = mapped_column(String(32))
    emotion_anger: Mapped[float | None] = mapped_column(Float)
    emotion_disgust: Mapped[float | None] = mapped_column(Float)
    emotion_fear: Mapped[float | None] = mapped_column(Float)
    emotion_happiness: Mapped[float | None] = mapped_column(Float)
    emotion_neutral: Mapped[float | None] = mapped_column(Float)
    emotion_other: Mapped[float | None] = mapped_column(Float)
    emotion_sadness: Mapped[float | None] = mapped_column(Float)
    emotion_surprise: Mapped[float | None] = mapped_column(Float)
    model: Mapped[str | None] = mapped_column(Text)
    verbose_logging: Mapped[bool | None] = mapped_column(Boolean)
    debug_mps: Mapped[bool | None] = mapped_column(Boolean)
    suppress_warnings: Mapped[bool | None] = mapped_column(Boolean)
    use_hybrid: Mapped[bool | None] = mapped_column(Boolean)
    max_worker_threads: Mapped[int | None] = mapped_column(Integer)
    max_cache_size_mb: Mapped[int | None] = mapped_column(Integer)
    max_generation_length: Mapped[int | None] = mapped_column(Integer)

    __table_args__ = (
        CheckConstraint('id = 1', name='ck_tts_settings_singleton'),
    )


class VoiceManagerSettings(db.Model):
    __bind_key__ = 'config'
    __tablename__ = 'voice_manager_settings'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    base_dir: Mapped[str | None] = mapped_column(Text)
    auto_cleanup_hours: Mapped[int | None] = mapped_column(Integer)
    enable_compression: Mapped[bool | None] = mapped_column(Boolean)
    compression_quality: Mapped[float | None] = mapped_column(Float)
    max_cache_size_mb: Mapped[int | None] = mapped_column(Integer)

    __table_args__ = (
        CheckConstraint('id = 1', name='ck_voice_manager_settings_singleton'),
    )


class MemoryCacheSettings(db.Model):
    __bind_key__ = 'config'
    __tablename__ = 'memory_cache_settings'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    threshold_percent: Mapped[float | None] = mapped_column(Float)
    gc_interval_seconds: Mapped[float | None] = mapped_column(Float)
    monitor_interval_seconds: Mapped[float | None] = mapped_column(Float)
    cache_max_memory_mb: Mapped[float | None] = mapped_column(Float)
    cache_max_size: Mapped[int | None] = mapped_column(Integer)

    __table_args__ = (
        CheckConstraint('id = 1', name='ck_memory_cache_settings_singleton'),
    )


class OptimizationSettings(db.Model):
    __bind_key__ = 'config'
    __tablename__ = 'optimization_settings'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    target_fps: Mapped[float | None] = mapped_column(Float)
    min_fps: Mapped[float | None] = mapped_column(Float)
    max_skip_rate: Mapped[int | None] = mapped_column(Integer)

    fps_smoothing_enabled: Mapped[bool | None] = mapped_column(Boolean)
    fps_window_size: Mapped[int | None] = mapped_column(Integer)

    frame_skipper_enabled: Mapped[bool | None] = mapped_column(Boolean)
    frame_skipper_adaptive: Mapped[bool | None] = mapped_column(Boolean)
    frame_skipper_adjust_interval: Mapped[float | None] = mapped_column(Float)

    batch_enabled: Mapped[bool | None] = mapped_column(Boolean)
    batch_size: Mapped[int | None] = mapped_column(Integer)
    batch_timeout_ms: Mapped[int | None] = mapped_column(Integer)

    preprocess_resize_enabled: Mapped[bool | None] = mapped_column(Boolean)
    preprocess_resize_width: Mapped[int | None] = mapped_column(Integer)
    preprocess_resize_height: Mapped[int | None] = mapped_column(Integer)
    preprocess_normalize_enabled: Mapped[bool | None] = mapped_column(Boolean)
    preprocess_roi_enabled: Mapped[bool | None] = mapped_column(Boolean)

    __table_args__ = (
        CheckConstraint('id = 1', name='ck_optimization_settings_singleton'),
    )



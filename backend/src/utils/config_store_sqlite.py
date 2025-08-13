"""
SQLite 設定ストア

フレームワーク非依存の軽量な設定ストア。`config.db` から辞書構造を読み出し、
一部の設定を書き戻します（アップサート対応）。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional


class SQLiteConfigStore:
    """
    Lightweight config store backed by SQLite (config.db).
    - read_all(): build nested config dict from normalized tables
    - write(config): persist supported keys back to tables
    Designed to work without Flask app context or SQLAlchemy session.
    """

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    # ---------- helpers ----------
    def _fetchone(self, cur, sql: str) -> Optional[sqlite3.Row]:
        cur.execute(sql)
        return cur.fetchone()

    def _fetcha(self, cur, sql: str) -> list[sqlite3.Row]:
        cur.execute(sql)
        return cur.fetchall()

    # ---------- public API ----------
    def read_all(self) -> Dict[str, Any]:
        cfg: Dict[str, Any] = {}
        con = sqlite3.connect(str(self.db_path))
        con.row_factory = sqlite3.Row
        try:
            cur = con.cursor()

            # general
            row = self._fetchone(cur, 'SELECT server_port FROM general_settings WHERE id=1')
            if row:
                cfg.setdefault('server', {})['port'] = row['server_port']

            # logging
            row = self._fetchone(cur, 'SELECT * FROM logging_settings WHERE id=1')
            if row:
                cfg['logging'] = {
                    'enable_file_output': bool(row['enable_file_output']) if row['enable_file_output'] is not None else True,
                    'file_level': row['file_level'],
                    'console_level': row['console_level'],
                    'level': row['level'],
                    'log_dir': row['log_dir'],
                    'max_file_size_mb': row['max_file_size_mb'],
                    'backup_count': row['backup_count'],
                    'suppress_frequent_logs': bool(row['suppress_frequent_logs']) if row['suppress_frequent_logs'] is not None else True,
                    'frame_log_interval': row['frame_log_interval'],
                    'detection_log_sampling': row['detection_log_sampling'],
                }

            # models.yolo
            row = self._fetchone(cur, 'SELECT * FROM models_yolo WHERE id=1')
            if row:
                cfg.setdefault('models', {})['yolo'] = {
                    'model_name': row['model_name'],
                    'models_dir': row['models_dir'],
                }

            # detector
            row = self._fetchone(cur, 'SELECT * FROM detector_settings WHERE id=1')
            if row:
                cfg['detector'] = {
                    'use_mediapipe': bool(row['use_mediapipe']) if row['use_mediapipe'] is not None else True,
                    'use_yolo': bool(row['use_yolo']) if row['use_yolo'] is not None else True,
                }

            # detection_smoother
            row = self._fetchone(cur, 'SELECT * FROM detection_smoother_settings WHERE id=1')
            if row:
                cfg['detection_smoother'] = {
                    'enabled': bool(row['enabled']) if row['enabled'] is not None else True,
                    'hysteresis': {
                        'enabled': bool(row['hysteresis_enabled']) if row['hysteresis_enabled'] is not None else None,
                        'high_threshold': row['hysteresis_high'],
                        'low_threshold': row['hysteresis_low'],
                    },
                    'interpolation': {
                        'enabled': bool(row['interpolation_enabled']) if row['interpolation_enabled'] is not None else None,
                        'fade_out_factor': row['interpolation_fade_out'],
                        'max_missing_frames': row['interpolation_max_missing'],
                    },
                    'moving_average': {
                        'enabled': bool(row['moving_avg_enabled']) if row['moving_avg_enabled'] is not None else None,
                        'window_size': row['moving_avg_window'],
                        'weight_recent': row['moving_avg_weight_recent'],
                    },
                }

            # conditions
            try:
                row = self._fetchone(cur, 'SELECT * FROM conditions_settings WHERE id=1')
                if row:
                    cfg.setdefault('conditions', {})
                    cfg['conditions'].setdefault('absence', {})['threshold_seconds'] = row['absence_threshold_seconds']
                    cfg['conditions'].setdefault('smartphone_usage', {})['threshold_seconds'] = row['smartphone_threshold_seconds']
                    cfg['conditions']['smartphone_usage']['grace_period_seconds'] = row['smartphone_grace_period_seconds']
            except sqlite3.DatabaseError:
                pass

            # tts
            row = self._fetchone(cur, 'SELECT * FROM tts_settings WHERE id=1')
            if row:
                tts: Dict[str, Any] = {}
                for k in row.keys():
                    if k == 'id':
                        continue
                    tts_key = k
                    # map emotion_* prefixed columns to default_emotion_* keys where expected by code
                    if k.startswith('emotion_'):
                        tts_key = f'default_{k}'
                    tts[tts_key] = row[k]
                cfg['tts'] = tts

            # voice_manager
            row = self._fetchone(cur, 'SELECT * FROM voice_manager_settings WHERE id=1')
            if row:
                cfg['voice_manager'] = {
                    'base_dir': row['base_dir'],
                    'auto_cleanup_hours': row['auto_cleanup_hours'],
                    'enable_compression': bool(row['enable_compression']) if row['enable_compression'] is not None else None,
                    'compression_quality': row['compression_quality'],
                    'max_cache_size_mb': row['max_cache_size_mb'],
                }

            # memory
            row = self._fetchone(cur, 'SELECT * FROM memory_cache_settings WHERE id=1')
            if row:
                cfg['memory'] = {
                    'threshold_percent': row['threshold_percent'],
                    'gc_interval_seconds': row['gc_interval_seconds'],
                    'monitor_interval_seconds': row['monitor_interval_seconds'],
                    'cache': {
                        'max_memory_mb': row['cache_max_memory_mb'],
                        'max_size': row['cache_max_size'],
                    },
                }

            # optimization
            row = self._fetchone(cur, 'SELECT * FROM optimization_settings WHERE id=1')
            if row:
                cfg['optimization'] = {
                    'target_fps': row['target_fps'],
                    'min_fps': row['min_fps'],
                    'max_skip_rate': row['max_skip_rate'],
                    'fps_counter': {
                        'smoothing_enabled': bool(row['fps_smoothing_enabled']) if row['fps_smoothing_enabled'] is not None else None,
                        'window_size': row['fps_window_size'],
                    },
                    'frame_skipper': {
                        'enabled': bool(row['frame_skipper_enabled']) if row['frame_skipper_enabled'] is not None else None,
                        'adaptive_mode': bool(row['frame_skipper_adaptive']) if row['frame_skipper_adaptive'] is not None else None,
                        'adjustment_interval': row['frame_skipper_adjust_interval'],
                    },
                    'preprocessing': {
                        'resize_enabled': bool(row['preprocess_resize_enabled']) if row['preprocess_resize_enabled'] is not None else None,
                        'resize_width': row['preprocess_resize_width'],
                        'resize_height': row['preprocess_resize_height'],
                        'normalize_enabled': bool(row['preprocess_normalize_enabled']) if row['preprocess_normalize_enabled'] is not None else None,
                        'roi_enabled': bool(row['preprocess_roi_enabled']) if row['preprocess_roi_enabled'] is not None else None,
                    },
                }

            # detection_objects
            rows = self._fetcha(cur, 'SELECT * FROM detection_objects')
            if rows:
                det: Dict[str, Any] = {}
                for r in rows:
                    det[r['key']] = {
                        'name': r['name'],
                        'class_name': r['class_name'],
                        'alert_message': r['alert_message'],
                        'alert_sound': r['alert_sound'],
                        'alert_threshold': r['alert_threshold'],
                        'confidence_threshold': r['confidence_threshold'],
                        'enabled': bool(r['enabled']) if r['enabled'] is not None else False,
                        'thickness': r['thickness'],
                        'color': [r['color_r'], r['color_g'], r['color_b']],
                    }
                cfg['detection_objects'] = det

            # landmark_settings
            rows = self._fetcha(cur, 'SELECT * FROM landmark_settings')
            if rows:
                lm: Dict[str, Any] = {}
                for r in rows:
                    lm[r['key']] = {
                        'name': r['name'],
                        'enabled': bool(r['enabled']) if r['enabled'] is not None else False,
                        'thickness': r['thickness'],
                        'color': [r['color_r'], r['color_g'], r['color_b']],
                    }
                cfg['landmark_settings'] = lm

        finally:
            con.close()

        return cfg

    def write(self, config: Dict[str, Any]) -> bool:
        con = sqlite3.connect(str(self.db_path))
        try:
            cur = con.cursor()

            # general.server.port
            server_port = self._dig(config, 'server.port')
            if server_port is not None:
                cur.execute('INSERT INTO general_settings(id, server_port) VALUES(1, ?) ON CONFLICT(id) DO UPDATE SET server_port=excluded.server_port', (int(server_port),))

            # detector
            med = self._dig(config, 'detector.use_mediapipe')
            yolo = self._dig(config, 'detector.use_yolo')
            if med is not None or yolo is not None:
                cur.execute('INSERT INTO detector_settings(id, use_mediapipe, use_yolo) VALUES(1, COALESCE(?, (SELECT use_mediapipe FROM detector_settings WHERE id=1)), COALESCE(?, (SELECT use_yolo FROM detector_settings WHERE id=1))) ON CONFLICT(id) DO UPDATE SET use_mediapipe=excluded.use_mediapipe, use_yolo=excluded.use_yolo', (int(bool(med)) if med is not None else None, int(bool(yolo)) if yolo is not None else None))

            # models.yolo
            mn = self._dig(config, 'models.yolo.model_name')
            md = self._dig(config, 'models.yolo.models_dir')
            if mn is not None or md is not None:
                cur.execute('INSERT INTO models_yolo(id, model_name, models_dir) VALUES(1, COALESCE(?, (SELECT model_name FROM models_yolo WHERE id=1)), COALESCE(?, (SELECT models_dir FROM models_yolo WHERE id=1))) ON CONFLICT(id) DO UPDATE SET model_name=excluded.model_name, models_dir=excluded.models_dir', (mn, md))

            # conditions
            absence = self._dig(config, 'conditions.absence.threshold_seconds')
            smart = self._dig(config, 'conditions.smartphone_usage.threshold_seconds')
            grace = self._dig(config, 'conditions.smartphone_usage.grace_period_seconds')
            if absence is not None or smart is not None or grace is not None:
                cur.execute('INSERT INTO conditions_settings(id, absence_threshold_seconds, smartphone_threshold_seconds, smartphone_grace_period_seconds) VALUES(1, COALESCE(?, (SELECT absence_threshold_seconds FROM conditions_settings WHERE id=1)), COALESCE(?, (SELECT smartphone_threshold_seconds FROM conditions_settings WHERE id=1)), COALESCE(?, (SELECT smartphone_grace_period_seconds FROM conditions_settings WHERE id=1))) ON CONFLICT(id) DO UPDATE SET absence_threshold_seconds=excluded.absence_threshold_seconds, smartphone_threshold_seconds=excluded.smartphone_threshold_seconds, smartphone_grace_period_seconds=excluded.smartphone_grace_period_seconds', (absence, smart, grace))

            # tts.* (generic mapping)
            tts = config.get('tts')
            if isinstance(tts, dict):
                # Build dynamic SET part
                # We'll upsert only known columns present in row pragma
                row_cols = self._columns(con, 'tts_settings')
                # Map default_emotion_* names to emotion_* columns
                values: Dict[str, Any] = {}
                for k, v in tts.items():
                    col = k
                    if k.startswith('default_emotion_'):
                        col = k.replace('default_', '')
                    if col in row_cols and col != 'id':
                        values[col] = v
                if values:
                    # Create update with COALESCE to keep others
                    cols = ', '.join(values.keys())
                    placeholders = ', '.join(['?'] * len(values))
                    # Build insert with COALESCE of existing values for missing columns
                    # For simplicity, merge existing values first then replace
                    cur.execute('SELECT * FROM tts_settings WHERE id=1')
                    existing = cur.fetchone()
                    merged = dict(zip([d[0] for d in cur.description], existing)) if existing else {'id': 1}
                    merged.update(values)
                    cols_all = [c for c in row_cols if c != 'id']
                    vals_all = [merged.get(c) for c in cols_all]
                    q = f"INSERT INTO tts_settings(id, {', '.join(cols_all)}) VALUES(1, {', '.join(['?']*len(cols_all))}) ON CONFLICT(id) DO UPDATE SET " + ', '.join([f"{c}=excluded.{c}" for c in cols_all])
                    cur.execute(q, vals_all)

            con.commit()
            return True
        finally:
            con.close()

    def _columns(self, con: sqlite3.Connection, table: str) -> list[str]:
        cur = con.execute(f'PRAGMA table_info({table})')
        return [r[1] for r in cur.fetchall()]

    def _dig(self, d: Dict[str, Any], path: str) -> Any:
        cur: Any = d
        for part in path.split('.'):
            if not isinstance(cur, dict) or part not in cur:
                return None
            cur = cur[part]
        return cur


__all__ = ['SQLiteConfigStore']



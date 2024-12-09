@echo off
echo Starting Monitor System...

REM config.yamlの存在確認
if not exist config.yaml (
    echo Error: config.yaml not found!
    echo Please ensure config.yaml exists in the same directory.
    pause
    exit /b 1
)

REM alert_sound.wavの存在確認
if not exist alert_sound.wav (
    echo Warning: alert_sound.wav not found!
    echo Please ensure alert_sound.wav exists in the same directory.
)

REM モニタリングシステムを起動
python monitor.py

pause 
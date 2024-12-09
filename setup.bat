@echo off
echo Checking Python installation...

python --version > nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit
)

echo Python is installed!
echo.
echo Installing required packages...
echo This may take a few minutes...
echo.

pip install opencv-python
pip install mediapipe
pip install pyyaml
pip install playsound
pip install ultralytics
pip install twilio
pip install requests

echo.
echo Downloading YOLOv8n model...
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

echo.
echo Checking if config.yaml exists...
if not exist config.yaml (
    echo Warning: config.yaml not found!
    echo Please ensure you have a valid config.yaml file
)

echo.
echo Checking if alert_sound.wav exists...
if not exist alert_sound.wav (
    echo Warning: alert_sound.wav not found!
    echo Please ensure you have an alert sound file
)

echo.
echo Setup completed!
echo If there were no errors, you can now run start_monitor.bat
pause
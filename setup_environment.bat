@echo off
echo Setting up Python environment for Monitor System...

REM Pythonが入っているか確認
python --version
if %ERRORLEVEL% neq 0 (
    echo Python is not installed. Please install Python 3.8 or later.
    pause
    exit /b 1
)

REM 必要なパッケージをインストール
echo Installing required packages...
pip install opencv-python
pip install mediapipe
pip install pyyaml
pip install requests
pip install twilio
pip install playsound==1.2.2
pip install ultralytics
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

echo Environment setup completed!
pause 
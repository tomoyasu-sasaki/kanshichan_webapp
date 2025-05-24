from setuptools import setup, find_packages
import platform

# OS共通の依存関係
common_requires = [
    "opencv-python",
    "mediapipe",
    "torch",
    "ultralytics",
    "transformers",
    "openai",
    "flask",
    "line-bot-sdk",
    "pyyaml",
    "Pillow",
    "screeninfo",
]

# OS固有の依存関係
if platform.system() == "Darwin":  # macOS
    platform_requires = [
        "pyobjc-framework-AVFoundation",
        "pyobjc-framework-CoreMedia",
        "playsound",
    ]
elif platform.system() == "Windows":
    platform_requires = [
        "winsound",  # Windowsの標準ライブラリ
    ]
else:  # Linux
    platform_requires = [
        "playsound",
    ]

setup(
    name="kanshichan-backend",
    version="0.1",
    packages=find_packages("backend/src"),
    package_dir={"": "backend/src"},
    package_data={
        "kanshichan": ["config/config.yaml"],
    },
    install_requires=common_requires + platform_requires,
)
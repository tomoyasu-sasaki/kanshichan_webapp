from setuptools import setup, find_packages

setup(
    name="kanshichan",
    version="0.1",
    packages=find_packages("src"),
    package_dir={"": "src"},
    package_data={
        "kanshichan": ["config/config.yaml"],
    },
    install_requires=[
        "opencv-python",
        "mediapipe",
        "torch",
        "ultralytics",
        "flask",
        "line-bot-sdk",
        "twilio",
        "simpleaudio",
        "pyyaml",
        "Pillow",
    ],
)
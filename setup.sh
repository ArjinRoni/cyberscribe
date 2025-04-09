#!/bin/bash

# Make sure we're in the right directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "===== CyberScribe Transcriptor Setup ====="
echo "This script will set up the virtual environment and install dependencies."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 not found. Please install Python 3.10 or later."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if (( $(echo "$PYTHON_VERSION < 3.10" | bc -l) )); then
    echo "Python version $PYTHON_VERSION detected. Version 3.10+ is recommended."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "FFmpeg not found. It's recommended for video file processing."
    echo "Please install FFmpeg from https://ffmpeg.org/ or your package manager."
    read -p "Continue without FFmpeg? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment. Please install venv package."
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing dependencies... (this may take a while)"
pip install -r requirements.txt

# Make the launcher executable
chmod +x transcriptor.sh

echo
echo "Setup complete! You can now run the application with:"
echo "./transcriptor.sh"
echo 
#!/bin/bash

# YouTube Audio Player - Fedora Launcher

echo "🎵 YouTube Audio Player"
echo "======================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    echo "Please install it: sudo dnf install python3"
    exit 1
fi

# Check if venv exists, if not create it
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📥 Checking dependencies..."
pip install -q -r requirements.txt

# Check if mpv is installed
if ! command -v mpv &> /dev/null; then
    echo ""
    echo "⚠️  WARNING: mpv is not installed"
    echo "To use audio playback, install it with:"
    echo "  sudo dnf install mpv"
    echo ""
    echo "The application will run in demo mode without audio."
    echo ""
fi

# Run the application
echo "🚀 Starting YouTube Audio Player..."
cd src
python3 main.py

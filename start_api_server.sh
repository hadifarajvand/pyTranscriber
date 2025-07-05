#!/bin/bash

# pyTranscriber REST API Server Startup Script
# (C) 2025 Raryel C. Souza

echo "pyTranscriber REST API Server"
echo "=============================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if FFmpeg is available
if ! command -v ffmpeg &> /dev/null; then
    echo "Warning: FFmpeg is not installed or not in PATH"
    echo "FFmpeg is required for audio/video processing"
    echo "Install FFmpeg:"
    echo "  macOS: brew install ffmpeg"
    echo "  Ubuntu/Debian: sudo apt install ffmpeg"
    echo "  Windows: Download from https://ffmpeg.org/download.html"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if required packages are installed
echo "Checking dependencies..."
python3 -c "import flask, flask_cors" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing required packages..."
    pip3 install -r api_requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install required packages"
        exit 1
    fi
fi

# Create necessary directories
echo "Creating directories..."
mkdir -p uploads outputs downloads

# Set environment variables
export FLASK_ENV=development
export MAX_CONTENT_LENGTH=524288000  # 500MB

# Check for Google Speech API key
if [ -z "$GOOGLE_SPEECH_API_KEY" ]; then
    echo "Note: GOOGLE_SPEECH_API_KEY not set. Autosub engine will not work."
    echo "Set it with: export GOOGLE_SPEECH_API_KEY='your-api-key'"
    echo ""
fi

echo "Starting API server..."
echo "Server will be available at: http://localhost:5000"
echo "Web client available at: http://localhost:5000/api_client.html"
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
python3 api_server.py 
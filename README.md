# 🎵 YouTube Audio Player - Fedora Setup Guide

## Quick Setup (3 steps)

### Step 1: Install System Dependencies
```bash
sudo dnf install python3 python3-pip mpv
```

### Step 2: Clone/Download Project
```bash
cd /path/to/youtube-audio-player
```

### Step 3: Run the Application
```bash
chmod +x run.sh
./run.sh
```

That's it! The script will automatically create the virtual environment and install Python dependencies.

---

## Manual Setup (if you prefer)

If you want to do it manually:

### 1. Install system dependencies
```bash
sudo dnf install python3 python3-pip mpv
```

### 2. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the application
```bash
cd src
python3 main.py
```

---

## Troubleshooting

### Error: "mpv: command not found"
**Solution:**
```bash
sudo dnf install mpv
```

### Error: Permission denied on run.sh
**Solution:**
```bash
chmod +x run.sh
./run.sh
```

### Error: "No module named 'PyQt6'"
**Solution:**
```bash
pip install PyQt6
```

### Audio not working
1. Make sure mpv is installed: `mpv --version`
2. Test mpv with: `mpv https://www.youtube.com/watch?v=VIDEO_ID`
3. If that doesn't work, install: `sudo dnf install libmpv`

### Application won't start
Run with debug info:
```bash
cd src
python3 main.py
```

---

## What This Application Does

- 🔍 Search for videos on YouTube
- 🎵 Stream audio directly without downloading
- ▶️ Play/Pause/Stop controls
- 🔊 Volume control
- 📊 Progress bar with time display

---

## How to Use

1. Type a song or artist name in the search bar
2. Double-click on a result to play
3. Use Play/Pause/Stop buttons to control playback
4. Adjust volume with the slider

---

## System Requirements

- **OS:** Fedora 38+
- **Python:** 3.8+
- **RAM:** 512 MB minimum
- **Internet:** Required for YouTube access

---

## Notes

- The app uses yt-dlp to fetch video URLs from YouTube
- All streaming is done through mpv, no files are downloaded
- The app respects YouTube's terms of service (audio streaming only)

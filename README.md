# YouTube Audio Player

A simple desktop audio player built with PyQt6. Search YouTube and stream audio using yt-dlp and mpv. The interface is available in English and Spanish; use the **EN/ES** button in the search bar to switch languages. Your selection is saved for the next launch.

## Features

- Search YouTube for songs and artists
- Stream audio without downloading files
- Create and manage playlists, including the default **Favorites** playlist
- Play playlists in order or randomly
- Playback controls: play, pause, stop, restart, repeat, and volume
- English and Spanish interface

## Requirements

- Python 3.10 or newer
- mpv and its `libmpv` library (or DLLs on Windows)
- Internet connection

## Windows 10/11

1. Install Python from [python.org](https://www.python.org/downloads/windows/) and enable **Add python.exe to PATH** during setup.
2. Install mpv and make sure its `libmpv` DLLs are available. You can use [Scoop](https://scoop.sh/) with `scoop install mpv`, or choose a build from the [mpv installation page](https://mpv.io/installation/).
3. Run `run.bat` from the project folder (double-click it or launch it from Command Prompt).

The launcher creates or repairs the `venv` virtual environment, installs the dependencies from `requirements.txt`, and starts the app. If mpv is missing, the app may open but audio playback will not work.

### Manual setup

From the project folder in Command Prompt:

```bat
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
cd src
..\venv\Scripts\python.exe main.py
```

## Fedora

Install the system dependencies and run the launcher:

```bash
sudo dnf install python3 python3-pip mpv
chmod +x run.sh
./run.sh
```

The script creates or repairs the virtual environment and installs the Python dependencies.

### Manual setup

```bash
sudo dnf install python3 python3-pip mpv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd src
python3 main.py
```

## Ubuntu and Linux Mint

Install the system dependencies, then run the Linux launcher:

```bash
sudo apt install python3 python3-venv python3-pip mpv
chmod +x run.sh
./run.sh
```

## Troubleshooting

### `mpv` or audio playback is unavailable

Confirm mpv is installed (`mpv --version`) and that its `libmpv` library is available to the application. On Fedora, install it with `sudo dnf install mpv`; on Ubuntu or Linux Mint, use `sudo apt install mpv`.

### `No module named 'PyQt6'` or another dependency is missing

Run the platform launcher again (`run.sh` on Linux or `run.bat` on Windows) to install the dependencies. For a manual installation, run `pip install -r requirements.txt` inside the project’s virtual environment.

### Linux says `Permission denied` when running `run.sh`

```bash
chmod +x run.sh
./run.sh
```

## System requirements

- **Operating systems:** Windows 10/11, Fedora, Ubuntu, or Linux Mint
- **Python:** 3.10 or newer
- **Memory:** 512 MB minimum
- **Audio playback:** mpv and its `libmpv` library/DLLs
- **Internet:** Required to search and stream audio from YouTube

## Notes

- yt-dlp fetches audio stream URLs from YouTube; mpv plays them.
- The application streams audio and does not download media files.
- PyQt6 provides Windows packages, and yt-dlp requires Python 3.10 or newer. See the [PyQt6 package page](https://pypi.org/project/PyQt6/) and [yt-dlp dependency documentation](https://github.com/yt-dlp/yt-dlp#dependencies).
- The Windows launcher is provided, but has not yet been verified on a Windows machine.

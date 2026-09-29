# 🎵 YouTube Audio Player

Reproductor de audio de YouTube con interfaz PyQt6. Busca temas y transmite audio con yt-dlp y mpv.

## Windows

La aplicación puede ejecutarse desde el código fuente en Windows 10/11.

### Requisitos

- Python 3.10 o posterior, instalado desde [python.org](https://www.python.org/downloads/windows/). Durante la instalación, activa **Add python.exe to PATH**.
- mpv y sus DLL de `libmpv` para reproducir audio. Puedes instalarlo con [Scoop](https://scoop.sh/) y `scoop install mpv`, o elegir una compilación desde la [página de instalación de mpv](https://mpv.io/installation/).
- Conexión a internet para buscar y transmitir audio.

### Inicio rápido

1. Clona o descarga el repositorio.
2. Ejecuta `run.bat` desde la carpeta del proyecto (doble clic o desde una consola).

El lanzador crea o repara el entorno virtual `venv`, instala las dependencias de `requirements.txt` y abre la aplicación. Si no encuentra mpv, la interfaz puede abrirse, pero no habrá reproducción de audio. Si falla la instalación de dependencias, el lanzador se detiene y muestra un error.

### Instalación manual

Desde la carpeta del proyecto, en `cmd.exe`:

```bat
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
cd src
..\venv\Scripts\python.exe main.py
```

## Fedora

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

El script crea o repara el entorno virtual e instala las dependencias de Python.

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

- **OS:** Windows 10/11, Fedora, Ubuntu o Linux Mint
- **Python:** 3.10+
- **RAM:** 512 MB minimum
- **Internet:** Required for YouTube access
- **Audio playback:** mpv and its `libmpv` library/DLLs

---

## Notes

- The app uses yt-dlp to fetch video URLs from YouTube
- All streaming is done through mpv, no files are downloaded
- The app respects YouTube's terms of service (audio streaming only)
- PyQt6 publica paquetes para Windows y yt-dlp requiere Python 3.10 o posterior; consulta sus requisitos actuales en [PyQt6](https://pypi.org/project/PyQt6/) y [yt-dlp](https://github.com/yt-dlp/yt-dlp#dependencies).
- El lanzador de Windows está preparado, pero todavía debe probarse en una máquina Windows real.

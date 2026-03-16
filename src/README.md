# 🎵 YouTube Audio Player

Reproductor de audio de YouTube sin anuncios para Linux. Busca y reproduce música directamente desde YouTube sin descargar archivos.

![Fase 1 - Prototipo Funcional](https://img.shields.io/badge/Fase-1%20Prototipo-green)

## ✨ Características (Fase 1)

- 🔍 **Búsqueda directa** en YouTube
- 🎵 **Reproducción sin anuncios** (stream directo de audio)
- ▶️ **Controles básicos**: Play/Pause/Stop
- 🔊 **Control de volumen**
- 📊 **Barra de progreso** con tiempo transcurrido
- 🎨 **Interfaz moderna** con PyQt6

## 📋 Requisitos previos

### Fedora con KDE
```bash
sudo dnf install python3 python3-pip mpv
```

### Ubuntu/Mint
```bash
sudo apt install python3 python3-pip mpv
```

### Arch Linux
```bash
sudo pacman -S python mpv
```

## 🚀 Instalación

1. **Clonar o descargar el proyecto**
```bash
cd youtube-audio-player
```

2. **Crear entorno virtual**
```bash
python3 -m venv venv
source venv/bin/activate  # En Linux/Mac
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

## ▶️ Uso

1. **Activar el entorno virtual** (si no está activado)
```bash
source venv/bin/activate
```

2. **Ejecutar la aplicación**
```bash
cd src
python3 main.py
```

O directamente:
```bash
./src/main.py
```

## 🎮 Cómo usar

1. **Buscar música**: Escribe el nombre de una canción o artista en la barra de búsqueda
2. **Seleccionar**: Haz doble clic en cualquier resultado de la lista
3. **Controlar**: Usa los botones de Play/Pause/Stop
4. **Ajustar volumen**: Usa el slider de volumen

## 🏗️ Estructura del proyecto

```
youtube-audio-player/
├── src/
│   ├── main.py              # Punto de entrada
│   ├── core/
│   │   ├── search.py        # Búsqueda con yt-dlp
│   │   └── player.py        # Reproducción con mpv
│   └── ui/
│       └── main_window.py   # Interfaz gráfica
├── requirements.txt         # Dependencias
└── README.md               # Este archivo
```

## 🔧 Tecnologías utilizadas

- **Python 3.10+**
- **PyQt6** - Framework de interfaz gráfica
- **yt-dlp** - Extracción de audio de YouTube
- **python-mpv** - Reproducción de audio
- **mpv** - Motor de reproducción

## 🐛 Solución de problemas

### Error: "No module named 'mpv'"
```bash
pip install python-mpv
sudo dnf install mpv  # o apt/pacman según tu distro
```

### Error: "yt-dlp no funciona / videos no disponibles"
```bash
pip install --upgrade yt-dlp
```

### La aplicación se congela al buscar
Esto es normal la primera vez. Asegúrate de que:
- Tienes conexión a internet
- yt-dlp está actualizado

## 🗺️ Roadmap

### ✅ Fase 1 - Prototipo Funcional (COMPLETADO)
- [x] Búsqueda en YouTube
- [x] Reproducción básica
- [x] Controles play/pause/stop
- [x] Interfaz funcional

### 🚧 Fase 2 - Interfaz mejorada (Siguiente)
- [ ] Thumbnails en los resultados
- [ ] Mejor visualización de la lista
- [ ] Indicadores de carga
- [ ] Diseño más pulido

### 📅 Fase 3 - Features avanzadas
- [ ] Cola de reproducción
- [ ] Historial de búsquedas
- [ ] Modo shuffle/repeat
- [ ] Atajos de teclado

### 📦 Fase 4 - Distribución
- [ ] Empaquetado con PyInstaller
- [ ] AppImage para distribución
- [ ] Flatpak (opcional)

## ⚖️ Legal

Este proyecto es solo para uso educativo y personal. YouTube tiene términos de servicio que prohíben el scraping. Usa esta aplicación bajo tu propia responsabilidad.

## 🤝 Contribuir

Este es un proyecto de aprendizaje. ¡Sugerencias y mejoras son bienvenidas!

## 📝 Licencia

Proyecto educativo - Uso personal solamente

---

**Desarrollado con ❤️ para la comunidad Linux**

# 🔧 Guía de Solución de Problemas - MPV

## Problema: "mpv no encontrado" o "libmpv not available"

### DIAGNÓSTICO RÁPIDO

Ejecuta el script de diagnóstico:
```bash
python3 diagnostico_mpv.py
```

Esto te dirá exactamente qué falta y cómo arreglarlo.

---

## SOLUCIONES POR SISTEMA OPERATIVO

### 🐧 FEDORA / RHEL

#### Problema: mpv no está instalado
```bash
# Instalar mpv y las librerías de desarrollo
sudo dnf install mpv mpv-libs-devel

# Verificar instalación
mpv --version

# Instalar python-mpv
pip install python-mpv
```

#### Problema: python-mpv no encuentra libmpv
```bash
# Reinstalar mpv con todas las dependencias
sudo dnf reinstall mpv mpv-libs

# Verificar que libmpv esté instalada
ldconfig -p | grep libmpv

# Si no aparece, instalar:
sudo dnf install mpv-libs-devel

# Reinstalar python-mpv
pip uninstall python-mpv
pip install python-mpv
```

---

### 🐧 UBUNTU / DEBIAN / MINT

#### Problema: mpv no está instalado
```bash
# Actualizar repositorios
sudo apt update

# Instalar mpv y librerías
sudo apt install mpv libmpv-dev

# Verificar instalación
mpv --version

# Instalar python-mpv
pip install python-mpv
```

#### Problema: "libmpv.so not found"
```bash
# Instalar la librería de desarrollo
sudo apt install libmpv-dev libmpv1

# Verificar que esté instalada
ldconfig -p | grep libmpv

# Reinstalar python-mpv
pip uninstall python-mpv
pip install python-mpv
```

---

### 🪟 WINDOWS

#### Opción 1: Scoop (Recomendado - Más fácil)
```powershell
# 1. Instalar Scoop (si no lo tienes)
# En PowerShell como administrador:
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
irm get.scoop.sh | iex

# 2. Instalar mpv
scoop install mpv

# 3. Verificar
mpv --version

# 4. Instalar python-mpv
pip install python-mpv
```

#### Opción 2: Manual
```
1. Descargar mpv de https://mpv.io/installation/
2. Buscar "Windows builds" → Descargar el .7z
3. Extraer en C:\Program Files\mpv\
4. Agregar al PATH:
   - Buscar "Variables de entorno" en Windows
   - Editar PATH del usuario
   - Agregar: C:\Program Files\mpv\
5. Reiniciar el terminal
6. pip install python-mpv
```

#### Opción 3: Chocolatey
```powershell
# En PowerShell como administrador
choco install mpv

# Verificar
mpv --version

# Instalar python-mpv
pip install python-mpv
```

#### Problema: "mpv-1.dll not found" o "mpv-2.dll not found"

```
Esto significa que mpv.exe está pero falta la DLL.

SOLUCIÓN:
1. Descargar el paquete COMPLETO de mpv (no solo el .exe)
2. Asegurarse de que estos archivos estén juntos:
   - mpv.exe
   - mpv-1.dll (o mpv-2.dll según versión)
   - Todos los archivos .dll de la carpeta

3. Si usaste scoop, reinstalar:
   scoop uninstall mpv
   scoop install mpv
```

---

### 🍎 macOS

#### Problema: mpv no está instalado
```bash
# Opción 1: Homebrew (Recomendado)
brew install mpv

# Opción 2: MacPorts
sudo port install mpv

# Verificar
mpv --version

# Instalar python-mpv
pip3 install python-mpv
```

---

## PROBLEMAS COMUNES Y SOLUCIONES

### 1. "python-mpv installed but still getting errors"

```bash
# Verificar que python-mpv esté realmente instalado
pip show python-mpv

# Si no aparece, instalar:
pip install python-mpv

# Si aparece pero sigue fallando, reinstalar:
pip uninstall python-mpv
pip install --no-cache-dir python-mpv
```

### 2. "ImportError: cannot import name 'MPV'"

```bash
# Hay un conflicto de nombres. Desinstalar todo relacionado con mpv:
pip uninstall mpv python-mpv

# Instalar solo python-mpv:
pip install python-mpv
```

### 3. "OSError: [Errno 2] No such file or directory: 'mpv'"

Esto significa que mpv no está en el PATH.

**Linux/macOS:**
```bash
# Encontrar dónde está mpv
which mpv

# Si no encuentra nada, mpv no está instalado
# Instalar según tu distro (ver arriba)

# Si lo encuentra pero python-mpv no lo ve:
export PATH="$PATH:/ruta/donde/esta/mpv"
```

**Windows:**
```powershell
# Encontrar mpv
where mpv

# Si no lo encuentra, agregarlo al PATH:
# Panel de Control → Sistema → Variables de entorno
# Editar PATH y agregar la carpeta donde está mpv.exe
```

### 4. "works in terminal but not in the app"

```bash
# El entorno virtual podría no tener acceso al mpv del sistema

# Solución 1: Activar el venv y reinstalar
source venv/bin/activate
pip install --force-reinstall python-mpv

# Solución 2: Usar mpv del sistema
# En player.py, agregar la ruta completa de mpv
```

### 5. "Everything installed but still no sound"

```bash
# Linux: verificar que el audio del sistema funcione
pactl list short sinks  # Ver dispositivos de audio

# Probar mpv directamente:
mpv --no-video https://www.youtube.com/watch?v=dQw4w9WgXcQ

# Si mpv funciona en terminal pero no en python:
# Verificar que python-mpv use el mismo mpv:
python3 -c "import mpv; print(mpv.__file__)"
```

---

## TEST FINAL

Después de aplicar las soluciones, ejecuta este test:

```python
# test_mpv.py
import mpv

print("Creando reproductor...")
player = mpv.MPV(video=False)

print("Intentando reproducir test...")
player.play("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

print("✅ Si escuchas música, todo funciona!")
print("Presiona Ctrl+C para salir")

import time
time.sleep(30)
player.terminate()
```

```bash
python3 test_mpv.py
```

Si escuchas música → **TODO FUNCIONA** ✅

---

## VERIFICACIÓN COMPLETA

```bash
# 1. ¿mpv está instalado?
mpv --version

# 2. ¿python-mpv está instalado?
pip show python-mpv

# 3. ¿Python puede importar mpv?
python3 -c "import mpv; print('OK')"

# 4. ¿Puede crear un objeto MPV?
python3 -c "import mpv; p = mpv.MPV(); print('OK')"

# Si todos dan OK → El problema está en otro lado
```

---

## ÚLTIMA ALTERNATIVA: Usar VLC en vez de MPV

Si definitivamente no puedes hacer funcionar mpv, puedes cambiar a VLC:

```bash
# Instalar VLC
# Fedora: sudo dnf install vlc
# Ubuntu: sudo apt install vlc
# Windows: descargar de videolan.org

# Instalar python-vlc
pip install python-vlc
```

Luego modifica `player.py` para usar VLC en vez de MPV (te puedo dar el código si hace falta).

---

## CONTACTO PARA AYUDA

Si ninguna solución funciona, ejecuta:
```bash
python3 diagnostico_mpv.py > reporte_mpv.txt
```

Y comparte el contenido de `reporte_mpv.txt` con el mensaje de error exacto que te aparece.
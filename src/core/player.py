"""
Módulo de reproducción de audio usando mpv
"""
import os
import sys
import subprocess
import shutil
from typing import Optional, Callable

# Configurar locale ANTES de importar mpv
# Esto soluciona el error "non-C locale detected"
os.environ['LC_ALL'] = 'C'
os.environ['LANG'] = 'C'

# Variable global para tracking de disponibilidad
MPV_AVAILABLE = False
MPV_ERROR = None
MPV_BINARY_PATH = None


def find_mpv_binary():
    """
    Encuentra el binario de mpv en el sistema
    Returns: (found: bool, path: str, error_msg: str)
    """
    # 1. Verificar si mpv está en PATH
    mpv_path = shutil.which('mpv')
    if mpv_path:
        return True, mpv_path, None
    
    # 2. Buscar en ubicaciones comunes según el sistema operativo
    if sys.platform == 'win32':
        # Windows
        common_paths = [
            r"C:\Program Files\mpv\mpv.exe",
            r"C:\Program Files (x86)\mpv\mpv.exe",
            os.path.expanduser(r"~\scoop\apps\mpv\current\mpv.exe"),
            os.path.expanduser(r"~\scoop\apps\mpv\current\bin\mpv.exe"),
            r"C:\mpv\mpv.exe",
        ]
        
        # También buscar en directorios del usuario
        user_home = os.path.expanduser("~")
        common_paths.extend([
            os.path.join(user_home, "scoop", "apps", "mpv", "current", "mpv.exe"),
            os.path.join(user_home, "scoop", "shims", "mpv.exe"),
        ])
        
        for path in common_paths:
            if os.path.exists(path):
                return True, path, None
        
        error_msg = """
mpv no encontrado en Windows.

SOLUCIONES:

Opción 1 - Scoop (Recomendado):
    1. Instalar Scoop: https://scoop.sh/
    2. En PowerShell: scoop install mpv

Opción 2 - Manual:
    1. Descargar de: https://mpv.io/installation/
    2. Extraer en C:\\Program Files\\mpv\\
    3. Agregar a PATH del sistema

Opción 3 - Chocolatey:
    choco install mpv

Después de instalar, reinicia la aplicación.
"""
        return False, None, error_msg
    
    elif sys.platform == 'linux':
        # Linux
        error_msg = """
mpv no encontrado en Linux.

INSTALAR mpv:

Fedora:
    sudo dnf install mpv

Ubuntu/Debian/Mint:
    sudo apt install mpv

Arch Linux:
    sudo pacman -S mpv

openSUSE:
    sudo zypper install mpv

Después de instalar, reinicia la aplicación.
"""
        return False, None, error_msg
    
    elif sys.platform == 'darwin':
        # macOS
        common_paths = [
            '/usr/local/bin/mpv',
            '/opt/homebrew/bin/mpv',
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return True, path, None
        
        error_msg = """
mpv no encontrado en macOS.

INSTALAR mpv:

Homebrew:
    brew install mpv

MacPorts:
    sudo port install mpv

Después de instalar, reinicia la aplicación.
"""
        return False, None, error_msg
    
    return False, None, "Sistema operativo no soportado"


def verify_mpv_works(mpv_path):
    """
    Verifica que mpv realmente funcione ejecutándolo
    """
    try:
        # Configurar locale para el subproceso también
        env = os.environ.copy()
        env['LC_ALL'] = 'C'
        env['LANG'] = 'C'
        
        result = subprocess.run(
            [mpv_path, '--version'],
            capture_output=True,
            text=True,
            timeout=5,
            env=env
        )
        return result.returncode == 0
    except Exception as e:
        return False


# Intentar encontrar mpv al importar el módulo
mpv_found, MPV_BINARY_PATH, find_error = find_mpv_binary()

if mpv_found:
    # Verificar que mpv realmente funcione
    if verify_mpv_works(MPV_BINARY_PATH):
        # En Windows, agregar el directorio de mpv al PATH
        if sys.platform == 'win32':
            mpv_dir = os.path.dirname(MPV_BINARY_PATH)
            if mpv_dir not in os.environ["PATH"]:
                os.environ["PATH"] = mpv_dir + os.pathsep + os.environ["PATH"]
        
        # Ahora intentar importar python-mpv
        try:
            import mpv
            MPV_AVAILABLE = True
            MPV_ERROR = None
            print(f"✅ mpv encontrado en: {MPV_BINARY_PATH}")
        except ImportError as e:
            MPV_AVAILABLE = False
            MPV_ERROR = f"""
python-mpv no instalado.

INSTALAR:
    pip install python-mpv

Error: {e}
"""
        except OSError as e:
            MPV_AVAILABLE = False
            MPV_ERROR = f"""
Error cargando libmpv.

En Windows: Asegúrate de que mpv.exe y mpv-1.dll o mpv-2.dll estén en la misma carpeta.
En Linux: Instala mpv y libmpv-dev:
    Fedora: sudo dnf install mpv mpv-libs-devel
    Ubuntu: sudo apt install mpv libmpv-dev

Error: {e}
"""
    else:
        MPV_AVAILABLE = False
        MPV_ERROR = f"mpv encontrado en {MPV_BINARY_PATH} pero no funciona correctamente."
else:
    MPV_AVAILABLE = False
    MPV_ERROR = find_error


class PlayerManager:
    """Maneja la reproducción de audio"""
    
    def __init__(self):
        self.player: Optional['mpv.MPV'] = None
        self.current_url: Optional[str] = None
        self.current_track_token = -1
        self.is_playing = False
        self.on_end_callback: Optional[Callable] = None
        
        self._init_player()
    
    def _init_player(self):
        """Inicializa el reproductor mpv"""
        if not MPV_AVAILABLE:
            print("=" * 70)
            print("⚠️  ERROR: MPV NO DISPONIBLE")
            print("=" * 70)
            print(MPV_ERROR)
            print("=" * 70)
            self.player = None
            return
        
        try:
            import mpv
            
            # Configuración de mpv con locale fijo
            config = {
                'video': False,  # Solo audio
                'ytdl': True,    # Usar youtube-dl/yt-dlp integrado
                'input_default_bindings': False,
                'input_vo_keyboard': False,
                'terminal': False,  # No output en terminal
                'msg_level': 'all=error',  # Solo mostrar errores
            }
            
            # En Linux, configuración adicional
            if sys.platform == 'linux':
                config['audio_device'] = 'auto'
            
            # Crear player con configuración de locale
            self.player = mpv.MPV(**config)
            
            # Callback cuando termina la reproducción
            @self.player.event_callback('end-file')
            def on_end(event):
                # mpv también emite end-file al parar o sustituir una pista.
                # Solo EOF indica que terminó de reproducirse con normalidad.
                event_data = getattr(event, 'data', None)
                if event_data is None or event_data.reason != event_data.EOF:
                    return

                self.is_playing = False
                if self.on_end_callback:
                    self.on_end_callback(self.current_track_token)
            
            print("✅ Reproductor mpv inicializado correctamente")
            
        except Exception as e:
            print(f"❌ Error inicializando mpv: {e}")
            print(f"   Tipo de error: {type(e).__name__}")
            
            # Dar más detalles si es error de locale
            if 'locale' in str(e).lower():
                print("\n   💡 SOLUCIÓN para error de locale:")
                print("   Este error ya debería estar solucionado.")
                print("   Si persiste, ejecuta la app así:")
                print("   Linux/Mac: LC_ALL=C python3 src/main.py")
                print("   Windows: set LC_ALL=C && python src\\main.py")
            
            self.player = None
    
    def play(self, url: str, track_token: int = -1):
        """
        Reproduce una URL de audio
        
        Args:
            url: URL del stream de audio
        """
        if not self.player:
            if not MPV_AVAILABLE:
                print("❌ No se puede reproducir: mpv no está disponible")
                print("   " + (MPV_ERROR or "Error desconocido").replace("\n", "\n   "))
            else:
                print("❌ Reproductor no disponible")
            return
        
        try:
            print(f"🎵 Intentando reproducir: {url[:80]}...")
            # mpv conserva el estado de pausa al cambiar de archivo.
            # Limpiarlo antes de cargar la nueva pista garantiza que arranque.
            self.player.pause = False
            self.current_track_token = track_token
            self.player.play(url)
            self.current_url = url
            self.is_playing = True
            print("✅ Reproducción iniciada")
            
        except Exception as e:
            print(f"❌ Error reproduciendo: {e}")
            print(f"   Tipo de error: {type(e).__name__}")
            self.is_playing = False
    
    def pause(self):
        """Pausa la reproducción"""
        if self.player and self.is_playing:
            try:
                self.player.pause = True
                self.is_playing = False
            except Exception as e:
                print(f"Error pausando: {e}")
    
    def resume(self):
        """Reanuda la reproducción"""
        if self.player and not self.is_playing:
            try:
                self.player.pause = False
                self.is_playing = True
            except Exception as e:
                print(f"Error reanudando: {e}")
    
    def stop(self):
        """Detiene la reproducción"""
        if self.player:
            try:
                self.player.stop()
                self.is_playing = False
                self.current_url = None
                self.current_track_token = -1
            except Exception as e:
                print(f"Error deteniendo: {e}")
    
    def toggle_pause(self):
        """Alterna entre play/pause"""
        if self.is_playing:
            self.pause()
        else:
            self.resume()

    def restart(self) -> bool:
        """Vuelve al inicio de la pista actual sin cambiar pausa/reproducción."""
        if not self.player or not self.current_url:
            return False
        try:
            self.player.seek(0, reference='absolute', precision='exact')
            return True
        except Exception as e:
            print(f"Error volviendo al inicio: {e}")
            return False

    def seek(self, seconds: float) -> bool:
        """Seek to an absolute time in the current track."""
        if not self.player or not self.current_url:
            return False
        try:
            self.player.seek(max(0, float(seconds)), reference='absolute', precision='exact')
            return True
        except Exception as e:
            print(f"Error buscando en la pista: {e}")
            return False
    
    def get_time_pos(self) -> float:
        """Retorna la posición actual en segundos"""
        if self.player:
            try:
                return self.player.time_pos or 0.0
            except:
                return 0.0
        return 0.0
    
    def get_duration(self) -> float:
        """Retorna la duración total en segundos"""
        if self.player:
            try:
                return self.player.duration or 0.0
            except:
                return 0.0
        return 0.0
    
    def set_volume(self, volume: int):
        """
        Establece el volumen
        
        Args:
            volume: Volumen de 0 a 100
        """
        if self.player:
            try:
                self.player.volume = max(0, min(100, volume))
            except Exception as e:
                print(f"Error ajustando volumen: {e}")
    
    def cleanup(self):
        """Limpia recursos del reproductor"""
        if self.player:
            try:
                self.player.terminate()
            except:
                pass


# Script de diagnóstico cuando se ejecuta directamente
if __name__ == "__main__":
    print("=" * 70)
    print("DIAGNÓSTICO DE MPV")
    print("=" * 70)
    print(f"\nSistema operativo: {sys.platform}")
    print(f"Python version: {sys.version}")
    print(f"Locale configurado: LC_ALL={os.environ.get('LC_ALL', 'not set')}")
    
    print("\n1. Buscando binario de mpv...")
    found, path, error = find_mpv_binary()
    if found:
        print(f"   ✅ mpv encontrado en: {path}")
        
        print("\n2. Verificando que mpv funcione...")
        if verify_mpv_works(path):
            print("   ✅ mpv funciona correctamente")
            
            # Mostrar versión
            try:
                env = os.environ.copy()
                env['LC_ALL'] = 'C'
                env['LANG'] = 'C'
                result = subprocess.run(
                    [path, '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    env=env
                )
                version_line = result.stdout.split('\n')[0]
                print(f"   Versión: {version_line}")
            except:
                pass
        else:
            print("   ❌ mpv no funciona correctamente")
    else:
        print(f"   ❌ mpv no encontrado")
        print(error)
    
    print("\n3. Verificando python-mpv...")
    if MPV_AVAILABLE:
        print("   ✅ python-mpv disponible")
        import mpv as mpv_module
        print(f"   Ubicación: {mpv_module.__file__}")
    else:
        print("   ❌ python-mpv no disponible")
        if MPV_ERROR:
            print(f"   Error: {MPV_ERROR}")
    
    print("\n4. Test de reproducción...")
    if MPV_AVAILABLE:
        print("   Intentando crear PlayerManager...")
        try:
            pm = PlayerManager()
            if pm.player:
                print("   ✅ PlayerManager creado exitosamente")
                print("\n   Puedes usar este módulo para reproducir audio.")
            else:
                print("   ❌ PlayerManager creado pero player es None")
        except Exception as e:
            print(f"   ❌ Error creando PlayerManager: {e}")
    else:
        print("   ⏭️  Saltado (mpv no disponible)")
    
    print("\n" + "=" * 70)
    print("FIN DEL DIAGNÓSTICO")
    print("=" * 70)

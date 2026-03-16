"""
Módulo de reproducción de audio usando mpv
"""
import mpv
from typing import Optional, Callable


class PlayerManager:
    """Maneja la reproducción de audio"""
    
    def __init__(self):
        self.player: Optional[mpv.MPV] = None
        self.current_url: Optional[str] = None
        self.is_playing = False
        self.on_end_callback: Optional[Callable] = None
        
        self._init_player()
    
    def _init_player(self):
        """Inicializa el reproductor mpv"""
        try:
            self.player = mpv.MPV(
                video=False,  # Solo audio
                ytdl=True,    # Usar youtube-dl/yt-dlp integrado
                input_default_bindings=False,
                input_vo_keyboard=False,
            )
            
            # Callback cuando termina la reproducción
            @self.player.event_callback('end-file')
            def on_end(event):
                self.is_playing = False
                if self.on_end_callback:
                    self.on_end_callback()
            
        except Exception as e:
            print(f"Error inicializando mpv: {e}")
            self.player = None
    
    def play(self, url: str):
        """
        Reproduce una URL de audio
        
        Args:
            url: URL del stream de audio
        """
        if not self.player:
            print("Reproductor no disponible")
            return
        
        try:
            self.player.play(url)
            self.current_url = url
            self.is_playing = True
            
        except Exception as e:
            print(f"Error reproduciendo: {e}")
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
            except Exception as e:
                print(f"Error deteniendo: {e}")
    
    def toggle_pause(self):
        """Alterna entre play/pause"""
        if self.is_playing:
            self.pause()
        else:
            self.resume()
    
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

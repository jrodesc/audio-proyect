"""
Módulo de búsqueda en YouTube usando yt-dlp
"""
import yt_dlp
from typing import List, Dict, Optional


class SearchManager:
    """Maneja las búsquedas en YouTube y extracción de información"""
    
    def __init__(self):
        self.ydl_opts_search = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'force_generic_extractor': False,
        }
        
        self.ydl_opts_extract = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
        }
    
    def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Busca videos en YouTube
        
        Args:
            query: Término de búsqueda
            max_results: Número máximo de resultados
            
        Returns:
            Lista de diccionarios con información de videos
        """
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts_search) as ydl:
                result = ydl.extract_info(
                    f"ytsearch{max_results}:{query}",
                    download=False
                )
                
                if not result or 'entries' not in result:
                    return []
                
                videos = []
                for entry in result['entries']:
                    if entry:
                        video_info = {
                            'id': entry.get('id', ''),
                            'title': entry.get('title', 'Sin título'),
                            'url': entry.get('url', ''),
                            'duration': entry.get('duration', 0),
                            'thumbnail': entry.get('thumbnail', ''),
                            'channel': entry.get('channel', 'Desconocido'),
                            'view_count': entry.get('view_count', 0),
                        }
                        videos.append(video_info)
                
                return videos
                
        except Exception as e:
            print(f"Error en búsqueda: {e}")
            return []
    
    def get_audio_url(self, video_id: str) -> Optional[str]:
        """
        Extrae la URL del stream de audio de un video
        
        Args:
            video_id: ID del video de YouTube
            
        Returns:
            URL del stream de audio o None si hay error
        """
        try:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            with yt_dlp.YoutubeDL(self.ydl_opts_extract) as ydl:
                info = ydl.extract_info(video_url, download=False)
                
                if info and 'url' in info:
                    return info['url']
                
                return None
                
        except Exception as e:
            print(f"Error extrayendo audio: {e}")
            return None
    
    def format_duration(self, seconds: int) -> str:
        """Formatea duración en segundos a MM:SS"""
        if not seconds:
            return "0:00"
        
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins}:{secs:02d}"

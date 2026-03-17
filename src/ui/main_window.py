"""
Ventana principal de la aplicación
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QLabel, QProgressBar, QSlider
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QIcon
from typing import List, Dict
import requests
from io import BytesIO

from core.search import SearchManager
from core.player import PlayerManager


class SearchThread(QThread):
    """Thread para realizar búsquedas sin bloquear la UI"""
    results_ready = pyqtSignal(list)
    
    def __init__(self, search_manager: SearchManager, query: str):
        super().__init__()
        self.search_manager = search_manager
        self.query = query
    
    def run(self):
        results = self.search_manager.search(self.query)
        self.results_ready.emit(results)


class ExtractAudioThread(QThread):
    """Thread para extraer URL de audio sin bloquear la UI"""
    url_ready = pyqtSignal(str, dict)
    
    def __init__(self, search_manager: SearchManager, video_info: Dict):
        super().__init__()
        self.search_manager = search_manager
        self.video_info = video_info
    
    def run(self):
        video_id = self.video_info.get('id', '')
        audio_url = self.search_manager.get_audio_url(video_id)
        if audio_url:
            self.url_ready.emit(audio_url, self.video_info)


class MainWindow(QMainWindow):
    """Ventana principal de la aplicación"""
    
    def __init__(self):
        super().__init__()
        
        # Managers
        self.search_manager = SearchManager()
        self.player_manager = PlayerManager()
        
        # Estado
        self.current_results = []
        self.current_video = None
        
        # Setup UI
        self.init_ui()
        
        # Timer para actualizar la barra de progreso
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_timer.start(1000)  # Actualizar cada segundo
    
    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        self.setWindowTitle("YouTube Audio Player")
        self.setMinimumSize(800, 600)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # === BARRA DE BÚSQUEDA ===
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar música en YouTube...")
        self.search_input.returnPressed.connect(self.perform_search)
        
        self.search_button = QPushButton("🔍 Buscar")
        self.search_button.clicked.connect(self.perform_search)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        
        main_layout.addLayout(search_layout)
        
        # === ESTADO DE BÚSQUEDA ===
        self.status_label = QLabel("Listo para buscar")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        main_layout.addWidget(self.status_label)
        
        # === LISTA DE RESULTADOS ===
        self.results_list = QListWidget()
        self.results_list.itemDoubleClicked.connect(self.play_selected)
        main_layout.addWidget(self.results_list)
        
        # === INFORMACIÓN DEL REPRODUCTOR ===
        self.now_playing_label = QLabel("Nada reproduciéndose")
        self.now_playing_label.setStyleSheet("""
            font-weight: bold;
            font-size: 14px;
            padding: 10px;
            background-color: #f0f0f0;
            border-radius: 5px;
        """)
        main_layout.addWidget(self.now_playing_label)
        
        # === BARRA DE PROGRESO ===
        progress_layout = QHBoxLayout()
        
        self.time_label = QLabel("0:00")
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.duration_label = QLabel("0:00")
        
        progress_layout.addWidget(self.time_label)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.duration_label)
        
        main_layout.addLayout(progress_layout)
        
        # === CONTROLES DE REPRODUCCIÓN ===
        controls_layout = QHBoxLayout()
        
        self.play_pause_button = QPushButton("▶️ Play")
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.play_pause_button.setEnabled(False)
        
        self.stop_button = QPushButton("⏹️ Stop")
        self.stop_button.clicked.connect(self.stop_playback)
        self.stop_button.setEnabled(False)
        
        # Control de volumen
        volume_label = QLabel("🔊")
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(80)
        self.volume_slider.valueChanged.connect(self.change_volume)
        self.volume_slider.setMaximumWidth(150)
        
        controls_layout.addWidget(self.play_pause_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addStretch()
        controls_layout.addWidget(volume_label)
        controls_layout.addWidget(self.volume_slider)
        
        main_layout.addLayout(controls_layout)
        
        # Aplicar estilos
        self.apply_styles()
    
    def apply_styles(self):
        """Aplica estilos CSS a la aplicación"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
            QLineEdit {
                padding: 10px;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 5px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
            QPushButton {
                padding: 10px 20px;
                font-size: 14px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QListWidget {
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #4CAF50;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #f0f0f0;
            }
            QProgressBar {
                border: 2px solid #ddd;
                border-radius: 5px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
    
    def perform_search(self):
        """Realiza una búsqueda en YouTube"""
        query = self.search_input.text().strip()
        
        if not query:
            self.status_label.setText("Por favor, escribe algo para buscar")
            return
        
        self.status_label.setText(f"🔍 Buscando '{query}'...")
        self.search_button.setEnabled(False)
        self.results_list.clear()
        
        # Buscar en thread separado
        self.search_thread = SearchThread(self.search_manager, query)
        self.search_thread.results_ready.connect(self.display_results)
        self.search_thread.start()
    
    def display_results(self, results: List[Dict]):
        """Muestra los resultados de la búsqueda"""
        self.current_results = results
        self.search_button.setEnabled(True)
        
        if not results:
            self.status_label.setText("❌ No se encontraron resultados")
            return
        
        self.status_label.setText(f"✅ Se encontraron {len(results)} resultados")
        
        for video in results:
            title = video.get('title', 'Sin título')
            channel = video.get('channel', 'Desconocido')
            duration = self.search_manager.format_duration(video.get('duration', 0))
            
            item_text = f"🎵 {title}\n   👤 {channel}  •  ⏱️ {duration}"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, video)
            
            self.results_list.addItem(item)
    
    def play_selected(self, item: QListWidgetItem):
        """Reproduce el video seleccionado"""
        video_info = item.data(Qt.ItemDataRole.UserRole)
        
        if not video_info:
            return
        
        self.status_label.setText(f"🎵 Cargando audio de '{video_info['title']}'...")
        
        # Extraer URL en thread separado
        self.extract_thread = ExtractAudioThread(self.search_manager, video_info)
        self.extract_thread.url_ready.connect(self.start_playback)
        self.extract_thread.start()
    
    def start_playback(self, audio_url: str, video_info: Dict):
        """Inicia la reproducción"""
        self.current_video = video_info
        
        try:
            self.player_manager.play(audio_url)
            
            title = video_info.get('title', 'Sin título')
            self.now_playing_label.setText(f"▶️ Reproduciendo: {title}")
            self.status_label.setText("✅ Reproducción iniciada")
            
            self.play_pause_button.setText("⏸️Pausar ")
            self.play_pause_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            
        except Exception as e:
            self.status_label.setText(f"❌ Error al reproducir: {str(e)}")
    
    def toggle_play_pause(self):
        """Alterna entre play y pause"""
        self.player_manager.toggle_pause()
        
        if self.player_manager.is_playing:
            self.play_pause_button.setText("⏸️ Pausar")
        else:
            self.play_pause_button.setText("▶️ Reproducir")
    
    def stop_playback(self):
        """Detiene la reproducción"""
        self.player_manager.stop()
        
        self.now_playing_label.setText("Nada reproduciéndose")
        self.play_pause_button.setText("▶️ Reproducir")
        self.play_pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.time_label.setText("0:00")
        self.status_label.setText("⏹️ Reproducción detenida")
    
    def change_volume(self, value: int):
        """Cambia el volumen del reproductor"""
        self.player_manager.set_volume(value)
    
    def update_progress(self):
        """Actualiza la barra de progreso"""
        if not self.player_manager.is_playing:
            return
        
        current_time = self.player_manager.get_time_pos()
        duration = self.player_manager.get_duration()
        
        if duration > 0:
            progress = int((current_time / duration) * 100)
            self.progress_bar.setValue(progress)
            
            # Formatear tiempo
            current_str = self.format_time(current_time)
            duration_str = self.format_time(duration)
            
            self.time_label.setText(current_str)
            self.duration_label.setText(duration_str)
    
    def format_time(self, seconds: float) -> str:
        """Formatea segundos a MM:SS"""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}:{secs:02d}"
    
    def closeEvent(self, event):
        """Maneja el cierre de la aplicación"""
        self.player_manager.cleanup()
        event.accept()

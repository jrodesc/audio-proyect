"""
Ventana principal de la aplicación
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QLabel, QProgressBar, QSlider, QTabWidget, QInputDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QObject, QStandardPaths
from PyQt6.QtGui import QPixmap, QIcon
from typing import List, Dict, Optional
import json
import os
import random
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
        self.url_ready.emit(audio_url or "", self.video_info)


class PlaybackSignals(QObject):
    """Puente seguro entre los eventos de mpv y el hilo de la interfaz."""
    track_ended = pyqtSignal()


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
        self.playlists = self.load_playlists()
        self.playlist_lists = {}
        self.playback_queue = []
        self.queue_position = -1
        self.queue_enabled = False
        self.playback_mode = "ordered"
        self.playback_playlist_name = None
        self.randomizer = random.SystemRandom()
        self.playback_signals = PlaybackSignals(self)
        self.playback_signals.track_ended.connect(self.play_next_in_queue)
        self.player_manager.on_end_callback = self.playback_signals.track_ended.emit
        
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
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(12, 12, 12, 12)
        
        # === BARRA DE BÚSQUEDA ===
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar música en YouTube...")
        self.search_input.returnPressed.connect(self.perform_search)
        
        self.search_button = QPushButton("Buscar")
        self.search_button.clicked.connect(self.perform_search)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        
        main_layout.addLayout(search_layout)
        
        # === ESTADO DE BÚSQUEDA ===
        self.status_label = QLabel("Listo para buscar")
        self.status_label.setStyleSheet("color: #333;")
        main_layout.addWidget(self.status_label)
        
        # === RESULTADOS Y LISTA DE REPRODUCCIÓN ===
        self.lists_tabs = QTabWidget()
        self.results_list = QListWidget()
        self.results_list.itemDoubleClicked.connect(self.play_selected)
        self.results_list.itemSelectionChanged.connect(self.update_list_action)
        self.lists_tabs.addTab(self.results_list, "Resultados")

        for playlist_name in self.playlists:
            self.add_playlist_tab(playlist_name)
        main_layout.addWidget(self.lists_tabs)

        list_controls = QHBoxLayout()
        self.favorite_action_button = QPushButton("+")
        self.favorite_action_button.setFixedWidth(36)
        self.favorite_action_button.setToolTip("Añadir a una lista")
        self.favorite_action_button.clicked.connect(self.handle_playlist_action)
        list_controls.addWidget(self.favorite_action_button)

        self.create_playlist_button = QPushButton("Nueva lista")
        self.create_playlist_button.clicked.connect(self.create_playlist)
        list_controls.addWidget(self.create_playlist_button)
        self.delete_playlist_button = QPushButton("Eliminar lista")
        self.delete_playlist_button.clicked.connect(self.delete_current_playlist)
        list_controls.addWidget(self.delete_playlist_button)
        list_controls.addStretch()

        self.play_order_button = QPushButton("Reproducir en orden")
        self.play_order_button.clicked.connect(self.play_current_playlist_ordered)
        list_controls.addWidget(self.play_order_button)
        self.play_random_button = QPushButton("Reproducir aleatorio")
        self.play_random_button.clicked.connect(self.play_current_playlist_random)
        list_controls.addWidget(self.play_random_button)
        main_layout.addLayout(list_controls)

        self.lists_tabs.currentChanged.connect(self.update_list_action)
        self.update_list_action()
        
        # === INFORMACIÓN DEL REPRODUCTOR ===
        self.now_playing_label = QLabel("Nada reproduciéndose")
        self.now_playing_label.setMinimumHeight(28)
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
        
        self.play_pause_button = QPushButton("Reproducir")
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.play_pause_button.setEnabled(False)
        
        self.stop_button = QPushButton("Detener")
        self.stop_button.clicked.connect(self.stop_playback)
        self.stop_button.setEnabled(False)
        
        # Control de volumen
        volume_label = QLabel("Volumen:")
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
            QWidget {
                background-color: #d4d0c8;
                color: #000000;
                font-family: Tahoma, Arial, sans-serif;
                font-size: 9pt;
            }
            QLineEdit, QListWidget {
                background-color: #ffffff;
                border: 1px solid #7f9db9;
                padding: 3px;
                selection-background-color: #316ac5;
                selection-color: #ffffff;
            }
            QLineEdit { min-height: 22px; }
            QPushButton {
                background-color: #e1e1e1;
                border: 1px solid #7f7f7f;
                border-top-color: #ffffff;
                border-left-color: #ffffff;
                padding: 4px 12px;
                min-height: 23px;
            }
            QPushButton:hover { background-color: #eeeeee; }
            QPushButton:pressed {
                background-color: #c8c8c8;
                border-top-color: #7f7f7f;
                border-left-color: #7f7f7f;
                border-bottom-color: #ffffff;
                border-right-color: #ffffff;
            }
            QPushButton:disabled {
                background-color: #d4d0c8;
                color: #777777;
            }
            QListWidget {
                font-size: 9pt;
                outline: 0;
            }
            QListWidget::item {
                padding: 6px 5px;
                border-bottom: 1px solid #c8c8c8;
            }
            QListWidget::item:hover {
                background-color: #e8e8e8;
                color: #000000;
            }
            QListWidget::item:selected {
                background-color: #d6d6d6;
                color: #000000;
            }
            QTabWidget::pane {
                border: 1px solid #7f7f7f;
                background-color: #d4d0c8;
            }
            QTabBar::tab {
                background-color: #d4d0c8;
                border: 1px solid #7f7f7f;
                padding: 4px 10px;
                margin-right: 2px;
            }
            QTabBar::tab:selected { background-color: #ffffff; }
            QProgressBar {
                background-color: #ffffff;
                border: 1px solid #7f7f7f;
                text-align: center;
                min-height: 16px;
            }
            QProgressBar::chunk { background-color: #808080; }
            QSlider::groove:horizontal {
                height: 4px;
                background-color: #a0a0a0;
                border: 1px solid #808080;
            }
            QSlider::handle:horizontal {
                width: 12px;
                margin: -5px 0;
                background-color: #e1e1e1;
                border: 1px solid #666666;
            }
        """)
    
    def perform_search(self):
        """Realiza una búsqueda en YouTube"""
        query = self.search_input.text().strip()
        
        if not query:
            self.status_label.setText("Por favor, escribe algo para buscar")
            return
        
        self.status_label.setText(f"Buscando '{query}'...")
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
            self.status_label.setText("No se encontraron resultados")
            return
        
        self.status_label.setText(f"Se encontraron {len(results)} resultados")
        
        for video in results:
            title = video.get('title', 'Sin título')
            channel = video.get('channel', 'Desconocido')
            duration = self.search_manager.format_duration(video.get('duration', 0))
            
            item_text = f"{title}\n{channel}  |  {duration}"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, video)
            
            self.results_list.addItem(item)
        self.update_list_action()

    def playlists_file_path(self) -> str:
        """Ruta de almacenamiento persistente de las listas."""
        data_dir = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppDataLocation
        )
        if not data_dir:
            data_dir = os.path.join(os.path.expanduser("~"), ".youtube-audio-player")
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, "favoritas.json")

    def load_playlists(self) -> Dict[str, List[Dict]]:
        try:
            with open(self.playlists_file_path(), "r", encoding="utf-8") as file:
                saved = json.load(file)
            if isinstance(saved, list):
                # Compatibilidad con la versión anterior, que guardaba solo Favoritas.
                return {"Favoritas": self.valid_songs(saved)}
            if isinstance(saved, dict):
                playlists = {
                    name: self.valid_songs(songs)
                    for name, songs in saved.items()
                    if isinstance(name, str) and name.strip() and isinstance(songs, list)
                }
                playlists.setdefault("Favoritas", [])
                return playlists
        except (OSError, ValueError, TypeError):
            pass
        return {"Favoritas": []}

    @staticmethod
    def valid_songs(songs) -> List[Dict]:
        return [song for song in songs if isinstance(song, dict) and song.get("id")]

    def save_playlists(self):
        try:
            with open(self.playlists_file_path(), "w", encoding="utf-8") as file:
                json.dump(self.playlists, file, ensure_ascii=False, indent=2)
        except OSError as error:
            self.status_label.setText(f"No se pudieron guardar las listas: {error}")

    def add_playlist_tab(self, playlist_name: str):
        playlist_list = QListWidget()
        playlist_list.itemDoubleClicked.connect(self.play_playlist_item)
        playlist_list.itemSelectionChanged.connect(self.update_list_action)
        playlist_list.setProperty("playlist_name", playlist_name)
        self.playlist_lists[playlist_name] = playlist_list
        self.lists_tabs.addTab(playlist_list, self.playlist_tab_title(playlist_name))
        self.refresh_playlist_list(playlist_name)

    def playlist_tab_title(self, playlist_name: str) -> str:
        return f"{playlist_name} ({len(self.playlists[playlist_name])})"

    def refresh_playlist_list(self, playlist_name: str):
        playlist_list = self.playlist_lists.get(playlist_name)
        if playlist_list is None:
            return
        playlist_list.clear()
        for video in self.playlists[playlist_name]:
            item = self.make_video_item(video)
            playlist_list.addItem(item)
        tab_index = self.lists_tabs.indexOf(playlist_list)
        if tab_index >= 0:
            self.lists_tabs.setTabText(tab_index, self.playlist_tab_title(playlist_name))

    def make_video_item(self, video: Dict) -> QListWidgetItem:
        title = video.get("title", "Sin título")
        channel = video.get("channel", "Desconocido")
        duration = self.search_manager.format_duration(video.get("duration", 0))
        item = QListWidgetItem(f"{title}\n{channel}  |  {duration}")
        item.setData(Qt.ItemDataRole.UserRole, video)
        return item

    def playlist_name_for_widget(self, widget) -> Optional[str]:
        return next(
            (name for name, playlist_widget in self.playlist_lists.items()
             if playlist_widget is widget),
            None,
        )

    def update_list_action(self, *_):
        current_widget = self.lists_tabs.currentWidget()
        playlist_name = self.playlist_name_for_widget(current_widget)
        is_playlist_tab = playlist_name is not None
        current_list = current_widget if is_playlist_tab else self.results_list
        selected = current_list.currentItem()
        self.delete_playlist_button.setEnabled(
            is_playlist_tab and playlist_name != "Favoritas"
        )
        self.delete_playlist_button.setToolTip(
            "Favoritas es la lista predeterminada"
            if is_playlist_tab and playlist_name == "Favoritas"
            else "Eliminar esta lista"
        )
        self.play_order_button.setEnabled(is_playlist_tab)
        self.play_random_button.setEnabled(is_playlist_tab)
        if not selected:
            action_symbol = "-" if is_playlist_tab else "+"
            self.favorite_action_button.setText(action_symbol)
            self.favorite_action_button.setEnabled(False)
            self.favorite_action_button.setToolTip(
                f"Eliminar de {playlist_name}" if is_playlist_tab else "Añadir a una lista"
            )
            return

        self.favorite_action_button.setText("-" if is_playlist_tab else "+")
        self.favorite_action_button.setEnabled(True)
        self.favorite_action_button.setToolTip(
            f"Eliminar de {playlist_name}" if is_playlist_tab else "Añadir a una lista"
        )

    def handle_playlist_action(self):
        current_widget = self.lists_tabs.currentWidget()
        playlist_name = self.playlist_name_for_widget(current_widget)
        is_playlist_tab = playlist_name is not None
        current_list = current_widget if is_playlist_tab else self.results_list
        item = current_list.currentItem()
        if not item:
            return
        video = item.data(Qt.ItemDataRole.UserRole)
        video_id = video.get("id")
        if is_playlist_tab:
            playlist = self.playlists[playlist_name]
            existing_index = next(
                (i for i, song in enumerate(playlist) if song.get("id") == video_id),
                None,
            )
            if existing_index is not None:
                del playlist[existing_index]
                self.save_playlists()
                self.refresh_playlist_list(playlist_name)
                self.status_label.setText(f"Eliminada de {playlist_name}")
                self.update_list_action()
            return

        playlist_names = list(self.playlists)
        playlist_name, accepted = QInputDialog.getItem(
            self,
            "Añadir canción",
            "¿En qué lista deseas incluir esta canción?",
            playlist_names,
            0,
            False,
        )
        if not accepted or not playlist_name:
            return

        playlist = self.playlists[playlist_name]
        if any(song.get("id") == video_id for song in playlist):
            self.status_label.setText(f"La canción ya está en {playlist_name}")
            return

        # La canción recién añadida se coloca arriba y se reproducirá primero.
        playlist.insert(0, {
            "id": video_id,
            "title": video.get("title", "Sin título"),
            "channel": video.get("channel", "Desconocido"),
            "duration": video.get("duration", 0),
        })
        self.save_playlists()
        self.refresh_playlist_list(playlist_name)
        self.status_label.setText(f"Añadida a {playlist_name}")
        self.update_list_action()

    def create_playlist(self):
        name, accepted = QInputDialog.getText(self, "Nueva lista", "Nombre de la lista:")
        name = name.strip()
        if not accepted or not name:
            return
        if name.casefold() == "resultados":
            self.status_label.setText("Ese nombre está reservado")
            return
        if any(existing.casefold() == name.casefold() for existing in self.playlists):
            self.status_label.setText("Ya existe una lista con ese nombre")
            return
        self.playlists[name] = []
        self.save_playlists()
        self.add_playlist_tab(name)
        self.lists_tabs.setCurrentWidget(self.playlist_lists[name])
        self.status_label.setText(f"Lista '{name}' creada")
        self.update_list_action()

    def delete_current_playlist(self):
        current_widget = self.lists_tabs.currentWidget()
        playlist_name = self.playlist_name_for_widget(current_widget)
        if playlist_name is None or playlist_name == "Favoritas":
            return
        if self.playlists[playlist_name]:
            answer = QMessageBox.question(
                self,
                "Eliminar lista",
                f"¿Eliminar la lista '{playlist_name}' y todas sus canciones?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        if self.queue_enabled and self.playback_playlist_name == playlist_name:
            self.stop_playback()
        playlist_list = self.playlist_lists.pop(playlist_name)
        self.playlists.pop(playlist_name, None)
        self.lists_tabs.removeTab(self.lists_tabs.indexOf(playlist_list))
        playlist_list.deleteLater()
        self.save_playlists()
        self.status_label.setText(f"Lista '{playlist_name}' eliminada")
        self.update_list_action()

    def current_playlist_name(self):
        current_widget = self.lists_tabs.currentWidget()
        playlist_name = self.playlist_name_for_widget(current_widget)
        return playlist_name if playlist_name in self.playlists else None

    def play_current_playlist_ordered(self):
        self.start_playlist_queue(shuffle=False)

    def play_current_playlist_random(self):
        self.start_playlist_queue(shuffle=True)

    def start_playlist_queue(self, shuffle: bool):
        playlist_name = self.current_playlist_name()
        if playlist_name is None:
            return
        playlist = self.playlists[playlist_name]
        if not playlist:
            self.status_label.setText(f"La lista '{playlist_name}' está vacía")
            return
        self.playback_playlist_name = playlist_name
        self.playback_queue = list(playlist)
        self.playback_mode = "random" if shuffle else "ordered"
        if shuffle and len(self.playback_queue) > 1:
            first_index = self.randomizer.randrange(len(self.playback_queue))
            self.playback_queue[0], self.playback_queue[first_index] = (
                self.playback_queue[first_index], self.playback_queue[0]
            )
        self.queue_enabled = True
        self.queue_position = 0
        self.play_queue_position()

    def play_playlist_item(self, item: QListWidgetItem):
        playlist_name = self.current_playlist_name()
        if playlist_name is None:
            return
        video = item.data(Qt.ItemDataRole.UserRole)
        if not video:
            return
        index = next(
            (i for i, song in enumerate(self.playlists[playlist_name]) if song.get("id") == video.get("id")),
            0,
        )
        self.playback_playlist_name = playlist_name
        self.playback_queue = list(self.playlists[playlist_name])
        self.playback_mode = "ordered"
        self.queue_enabled = True
        self.queue_position = index
        self.play_queue_position()

    def play_queue_position(self):
        if not self.queue_enabled or not (0 <= self.queue_position < len(self.playback_queue)):
            self.finish_queue()
            return
        video = self.playback_queue[self.queue_position]
        self.status_label.setText(f"Cargando audio de '{video.get('title', 'Sin título')}'...")
        self.extract_thread = ExtractAudioThread(self.search_manager, video)
        self.extract_thread.url_ready.connect(self.start_playback)
        self.extract_thread.start()

    def play_next_in_queue(self):
        if not self.queue_enabled:
            return
        next_position = self.queue_position + 1
        if self.playback_mode == "random" and next_position < len(self.playback_queue):
            remaining = len(self.playback_queue) - next_position
            random_index = next_position + self.randomizer.randrange(remaining)
            self.playback_queue[next_position], self.playback_queue[random_index] = (
                self.playback_queue[random_index], self.playback_queue[next_position]
            )
        self.queue_position = next_position
        if self.queue_position >= len(self.playback_queue):
            self.finish_queue()
        else:
            self.play_queue_position()

    def finish_queue(self):
        self.queue_enabled = False
        self.playback_queue = []
        self.queue_position = -1
        self.status_label.setText(
            f"Lista '{self.playback_playlist_name}' finalizada"
            if self.playback_playlist_name else "Lista finalizada"
        )
        self.now_playing_label.setText("Nada reproduciéndose")
        self.play_pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.time_label.setText("0:00")
    
    def play_selected(self, item: QListWidgetItem):
        """Reproduce el video seleccionado"""
        video_info = item.data(Qt.ItemDataRole.UserRole)
        
        if not video_info:
            return

        self.queue_enabled = False
        self.playback_queue = []
        
        self.status_label.setText(f"Cargando audio de '{video_info['title']}'...")
        
        # Extraer URL en thread separado
        self.extract_thread = ExtractAudioThread(self.search_manager, video_info)
        self.extract_thread.url_ready.connect(self.start_playback)
        self.extract_thread.start()
    
    def start_playback(self, audio_url: str, video_info: Dict):
        """Inicia la reproducción"""
        if not audio_url:
            self.status_label.setText("No se pudo obtener el audio")
            if self.queue_enabled:
                self.play_next_in_queue()
            return

        self.current_video = video_info
        
        try:
            self.player_manager.play(audio_url)
            self.progress_bar.setValue(0)
            self.time_label.setText("0:00")
            self.duration_label.setText(self.format_time(video_info.get("duration") or 0))
            
            title = video_info.get('title', 'Sin título')
            self.now_playing_label.setText(f"Reproduciendo: {title}")
            self.status_label.setText("Reproducción iniciada")
            
            self.play_pause_button.setText("Pausar")
            self.play_pause_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            
        except Exception as e:
            self.status_label.setText(f"Error al reproducir: {str(e)}")
    
    def toggle_play_pause(self):
        """Alterna entre play y pause"""
        self.player_manager.toggle_pause()
        
        if self.player_manager.is_playing:
            self.play_pause_button.setText("Pausar")
        else:
            self.play_pause_button.setText("Reproducir")
    
    def stop_playback(self):
        """Detiene la reproducción"""
        self.queue_enabled = False
        self.playback_queue = []
        self.queue_position = -1
        self.player_manager.stop()
        
        self.now_playing_label.setText("Nada reproduciéndose")
        self.play_pause_button.setText("Reproducir")
        self.play_pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.time_label.setText("0:00")
        self.status_label.setText("Reproducción detenida")
    
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

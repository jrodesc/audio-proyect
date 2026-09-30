"""
Ventana principal de la aplicación
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QLabel, QProgressBar, QSlider, QTabWidget, QInputDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QObject, QStandardPaths, QEvent, QSettings
from PyQt6.QtGui import QPixmap, QIcon, QKeySequence, QShortcut
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

        self.settings = QSettings("YT Audio", "YouTube Audio Player")
        self.language = self.settings.value("language", "en")
        if self.language not in ("en", "es"):
            self.language = "en"
        
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

        self.space_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        self.space_shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
        self.space_shortcut.activated.connect(self.toggle_play_pause)
        self.search_input.installEventFilter(self)
        
        self.search_button = QPushButton("Buscar")
        self.search_button.clicked.connect(self.perform_search)

        self.language_button = QPushButton()
        self.language_button.setFixedWidth(42)
        self.language_button.clicked.connect(self.toggle_language)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        search_layout.addWidget(self.language_button)
        
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

        self.repeat_button = QPushButton("Repetir: No")
        self.repeat_button.setCheckable(True)
        self.repeat_button.toggled.connect(self.update_repeat_button)

        self.restart_button = QPushButton("Reiniciar")
        self.restart_button.clicked.connect(self.restart_track)
        self.restart_button.setEnabled(False)

        self.play_pause_button = QPushButton("Reproducir")
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.play_pause_button.setEnabled(False)
        
        self.stop_button = QPushButton("Detener")
        self.stop_button.clicked.connect(self.stop_playback)
        self.stop_button.setEnabled(False)
        
        # Control de volumen
        self.volume_label = QLabel("Volumen:")
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(80)
        self.volume_slider.valueChanged.connect(self.change_volume)
        self.volume_slider.setMaximumWidth(150)
        
        controls_layout.addWidget(self.repeat_button)
        controls_layout.addWidget(self.restart_button)
        controls_layout.addWidget(self.play_pause_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addStretch()
        controls_layout.addWidget(self.volume_label)
        controls_layout.addWidget(self.volume_slider)
        
        main_layout.addLayout(controls_layout)
        
        # Aplicar estilos
        self.apply_styles()
        self.update_language()

    def text(self, key: str, **values) -> str:
        strings = {
            "en": {
                "search_placeholder": "Search YouTube for music...", "search": "Search",
                "ready": "Ready to search", "results": "Results", "add_to_list": "Add to a playlist",
                "new_playlist": "New playlist", "delete_playlist": "Delete playlist",
                "play_order": "Play in order", "play_random": "Play randomly",
                "nothing_playing": "Nothing is playing", "repeat_off": "Repeat: Off",
                "default_list_name": "Favorites",
                "repeat_on": "Repeat: On", "restart": "Restart", "play": "Play",
                "pause": "Pause", "stop": "Stop", "volume": "Volume:",
                "please_search": "Please enter something to search for",
                "searching": "Searching '{query}'...", "not_found": "No results found",
                "found": "Found {count} results", "untitled": "Untitled", "unknown": "Unknown",
                "save_error": "Could not save playlists: {error}", "default_list": "Favorites is the default playlist",
                "delete_this_list": "Delete this playlist", "remove_from": "Remove from {name}",
                "add_to_list_tip": "Add to a playlist", "removed_from": "Removed from {name}",
                "add_song": "Add song", "which_list": "Which playlist would you like to add this song to?",
                "already_in": "This song is already in {name}", "added_to": "Added to {name}",
                "create_title": "New playlist", "playlist_name": "Playlist name:",
                "reserved": "That name is reserved", "duplicate": "A playlist with that name already exists",
                "created": "Playlist '{name}' created", "delete_title": "Delete playlist",
                "confirm_delete": "Delete playlist '{name}' and all its songs?",
                "deleted": "Playlist '{name}' deleted", "empty": "Playlist '{name}' is empty",
                "loading": "Loading audio for '{title}'...", "list_finished": "Playlist '{name}' finished",
                "queue_finished": "Playlist finished", "audio_error": "Could not retrieve audio",
                "started": "Playback started", "playing": "Playing: {title}",
                "play_error": "Playback error: {error}", "restart_error": "Could not restart the track",
                "stopped": "Playback stopped",
            },
            "es": {
                "search_placeholder": "Buscar música en YouTube...", "search": "Buscar",
                "ready": "Listo para buscar", "results": "Resultados", "add_to_list": "Añadir a una lista",
                "new_playlist": "Nueva lista", "delete_playlist": "Eliminar lista",
                "play_order": "Reproducir en orden", "play_random": "Reproducir aleatorio",
                "nothing_playing": "Nada reproduciéndose", "repeat_off": "Repetir: No",
                "default_list_name": "Favoritas",
                "repeat_on": "Repetir: Sí", "restart": "Reiniciar", "play": "Reproducir",
                "pause": "Pausar", "stop": "Detener", "volume": "Volumen:",
                "please_search": "Por favor, escribe algo para buscar", "searching": "Buscando '{query}'...",
                "not_found": "No se encontraron resultados", "found": "Se encontraron {count} resultados",
                "untitled": "Sin título", "unknown": "Desconocido",
                "save_error": "No se pudieron guardar las listas: {error}",
                "default_list": "Favoritas es la lista predeterminada", "delete_this_list": "Eliminar esta lista",
                "remove_from": "Eliminar de {name}", "add_to_list_tip": "Añadir a una lista",
                "removed_from": "Eliminada de {name}", "add_song": "Añadir canción",
                "which_list": "¿En qué lista deseas incluir esta canción?", "already_in": "La canción ya está en {name}",
                "added_to": "Añadida a {name}", "create_title": "Nueva lista", "playlist_name": "Nombre de la lista:",
                "reserved": "Ese nombre está reservado", "duplicate": "Ya existe una lista con ese nombre",
                "created": "Lista '{name}' creada", "delete_title": "Eliminar lista",
                "confirm_delete": "¿Eliminar la lista '{name}' y todas sus canciones?",
                "deleted": "Lista '{name}' eliminada", "empty": "La lista '{name}' está vacía",
                "loading": "Cargando audio de '{title}'...", "list_finished": "Lista '{name}' finalizada",
                "queue_finished": "Lista finalizada", "audio_error": "No se pudo obtener el audio",
                "started": "Reproducción iniciada", "playing": "Reproduciendo: {title}",
                "play_error": "Error al reproducir: {error}", "restart_error": "No se pudo reiniciar la canción",
                "stopped": "Reproducción detenida",
            },
        }
        return strings[self.language][key].format(**values)

    def toggle_language(self):
        self.language = "es" if self.language == "en" else "en"
        self.settings.setValue("language", self.language)
        self.update_language()

    def update_language(self):
        """Refresh all visible controls after changing the interface language."""
        self.setWindowTitle("YouTube Audio Player")
        self.language_button.setText("EN" if self.language == "en" else "ES")
        self.language_button.setToolTip("Switch language / Cambiar idioma")
        self.search_input.setPlaceholderText(self.text("search_placeholder"))
        self.search_button.setText(self.text("search"))
        self.lists_tabs.setTabText(0, self.text("results"))
        for name, widget in self.playlist_lists.items():
            index = self.lists_tabs.indexOf(widget)
            if index >= 0:
                display_name = self.text("default_list_name") if name == "Favoritas" else name
                self.lists_tabs.setTabText(index, f"{display_name} ({len(self.playlists[name])})")
        self.create_playlist_button.setText(self.text("new_playlist"))
        self.delete_playlist_button.setText(self.text("delete_playlist"))
        self.play_order_button.setText(self.text("play_order"))
        self.play_random_button.setText(self.text("play_random"))
        self.now_playing_label.setText(self.text("nothing_playing") if not self.current_video else self.text("playing", title=self.current_video.get("title", self.text("untitled"))))
        self.repeat_button.setText(self.text("repeat_on" if self.repeat_button.isChecked() else "repeat_off"))
        self.restart_button.setText(self.text("restart"))
        self.play_pause_button.setText(self.text("pause" if self.player_manager.is_playing else "play"))
        self.stop_button.setText(self.text("stop"))
        self.volume_label.setText(self.text("volume"))
        self.update_list_action()
        self.status_label.setText(self.text("started") if self.current_video else self.text("ready"))
    
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

    def eventFilter(self, watched, event):
        if watched is self.search_input:
            if event.type() == QEvent.Type.FocusIn:
                self.space_shortcut.setEnabled(False)
            elif event.type() == QEvent.Type.FocusOut:
                self.space_shortcut.setEnabled(True)
        return super().eventFilter(watched, event)
    
    def perform_search(self):
        """Realiza una búsqueda en YouTube"""
        query = self.search_input.text().strip()
        
        if not query:
            self.status_label.setText(self.text("please_search"))
            return
        
        self.status_label.setText(self.text("searching", query=query))
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
            self.status_label.setText(self.text("not_found"))
            return
        
        self.status_label.setText(self.text("found", count=len(results)))
        
        for video in results:
            title = video.get('title', self.text("untitled"))
            channel = video.get('channel', self.text("unknown"))
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
            self.status_label.setText(self.text("save_error", error=error))

    def add_playlist_tab(self, playlist_name: str):
        playlist_list = QListWidget()
        playlist_list.itemDoubleClicked.connect(self.play_playlist_item)
        playlist_list.itemSelectionChanged.connect(self.update_list_action)
        playlist_list.setProperty("playlist_name", playlist_name)
        self.playlist_lists[playlist_name] = playlist_list
        self.lists_tabs.addTab(playlist_list, self.playlist_tab_title(playlist_name))
        self.refresh_playlist_list(playlist_name)

    def playlist_tab_title(self, playlist_name: str) -> str:
        display_name = self.text("default_list_name") if playlist_name == "Favoritas" else playlist_name
        return f"{display_name} ({len(self.playlists[playlist_name])})"

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
        title = video.get("title", self.text("untitled"))
        channel = video.get("channel", self.text("unknown"))
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
            self.text("default_list")
            if is_playlist_tab and playlist_name == "Favoritas"
            else self.text("delete_this_list")
        )
        self.play_order_button.setEnabled(is_playlist_tab)
        self.play_random_button.setEnabled(is_playlist_tab)
        if not selected:
            action_symbol = "-" if is_playlist_tab else "+"
            self.favorite_action_button.setText(action_symbol)
            self.favorite_action_button.setEnabled(False)
            self.favorite_action_button.setToolTip(
                self.text("remove_from", name=playlist_name) if is_playlist_tab else self.text("add_to_list_tip")
            )
            return

        self.favorite_action_button.setText("-" if is_playlist_tab else "+")
        self.favorite_action_button.setEnabled(True)
        self.favorite_action_button.setToolTip(
            self.text("remove_from", name=playlist_name) if is_playlist_tab else self.text("add_to_list_tip")
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
                self.status_label.setText(self.text("removed_from", name=playlist_name))
                self.update_list_action()
            return

        playlist_names = list(self.playlists)
        playlist_name, accepted = QInputDialog.getItem(
            self,
            self.text("add_song"),
            self.text("which_list"),
            playlist_names,
            0,
            False,
        )
        if not accepted or not playlist_name:
            return

        playlist = self.playlists[playlist_name]
        if any(song.get("id") == video_id for song in playlist):
            self.status_label.setText(self.text("already_in", name=playlist_name))
            return

        # La canción recién añadida se coloca arriba y se reproducirá primero.
        playlist.insert(0, {
            "id": video_id,
            "title": video.get("title", self.text("untitled")),
            "channel": video.get("channel", self.text("unknown")),
            "duration": video.get("duration", 0),
        })
        self.save_playlists()
        self.refresh_playlist_list(playlist_name)
        self.status_label.setText(self.text("added_to", name=playlist_name))
        self.update_list_action()

    def create_playlist(self):
        name, accepted = QInputDialog.getText(self, self.text("create_title"), self.text("playlist_name"))
        name = name.strip()
        if not accepted or not name:
            return
        if name.casefold() in {"resultados", "results"}:
            self.status_label.setText(self.text("reserved"))
            return
        if any(existing.casefold() == name.casefold() for existing in self.playlists):
            self.status_label.setText(self.text("duplicate"))
            return
        self.playlists[name] = []
        self.save_playlists()
        self.add_playlist_tab(name)
        self.lists_tabs.setCurrentWidget(self.playlist_lists[name])
        self.status_label.setText(self.text("created", name=name))
        self.update_list_action()

    def delete_current_playlist(self):
        current_widget = self.lists_tabs.currentWidget()
        playlist_name = self.playlist_name_for_widget(current_widget)
        if playlist_name is None or playlist_name == "Favoritas":
            return
        if self.playlists[playlist_name]:
            answer = QMessageBox.question(
                self,
                self.text("delete_title"),
                self.text("confirm_delete", name=playlist_name),
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
        self.status_label.setText(self.text("deleted", name=playlist_name))
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
            self.status_label.setText(self.text("empty", name=playlist_name))
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
        self.request_track_playback(video)

    def request_track_playback(self, video: Dict):
        self.status_label.setText(self.text("loading", title=video.get('title', self.text("untitled"))))
        self.extract_thread = ExtractAudioThread(self.search_manager, video)
        self.extract_thread.url_ready.connect(self.start_playback)
        self.extract_thread.start()

    def play_next_in_queue(self, allow_repeat: bool = True):
        if allow_repeat and self.repeat_button.isChecked() and self.current_video:
            if self.queue_enabled:
                # Conserva el elemento actual de la cola y vuelve a cargarlo.
                self.play_queue_position()
            else:
                self.request_track_playback(self.current_video)
            return
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
            self.text("list_finished", name=self.playback_playlist_name)
            if self.playback_playlist_name else self.text("queue_finished")
        )
        self.now_playing_label.setText(self.text("nothing_playing"))
        self.play_pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.restart_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.time_label.setText("0:00")
    
    def play_selected(self, item: QListWidgetItem):
        """Reproduce el video seleccionado"""
        video_info = item.data(Qt.ItemDataRole.UserRole)
        
        if not video_info:
            return

        self.queue_enabled = False
        self.playback_queue = []
        self.playback_playlist_name = None
        
        self.request_track_playback(video_info)
    
    def start_playback(self, audio_url: str, video_info: Dict):
        """Inicia la reproducción"""
        if not audio_url:
            self.status_label.setText(self.text("audio_error"))
            if self.queue_enabled:
                self.play_next_in_queue(allow_repeat=False)
            return

        self.current_video = video_info
        
        try:
            self.player_manager.play(audio_url)
            self.progress_bar.setValue(0)
            self.time_label.setText("0:00")
            self.duration_label.setText(self.format_time(video_info.get("duration") or 0))
            
            title = video_info.get('title', self.text("untitled"))
            self.now_playing_label.setText(self.text("playing", title=title))
            self.status_label.setText(self.text("started"))
            
            self.play_pause_button.setText(self.text("pause"))
            self.play_pause_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            self.restart_button.setEnabled(True)
            
        except Exception as e:
            self.status_label.setText(self.text("play_error", error=str(e)))
    
    def toggle_play_pause(self):
        """Alterna entre play y pause"""
        if not self.play_pause_button.isEnabled():
            return
        self.player_manager.toggle_pause()
        
        if self.player_manager.is_playing:
            self.play_pause_button.setText(self.text("pause"))
        else:
            self.play_pause_button.setText(self.text("play"))

    def restart_track(self):
        """Vuelve al inicio de la canción actual."""
        if not self.restart_button.isEnabled():
            return
        if self.player_manager.restart():
            self.progress_bar.setValue(0)
            self.time_label.setText("0:00")
        else:
            self.status_label.setText(self.text("restart_error"))

    def update_repeat_button(self, enabled: bool):
        self.repeat_button.setText(self.text("repeat_on" if enabled else "repeat_off"))
    
    def stop_playback(self):
        """Detiene la reproducción"""
        self.queue_enabled = False
        self.playback_queue = []
        self.queue_position = -1
        self.player_manager.stop()
        
        self.now_playing_label.setText(self.text("nothing_playing"))
        self.play_pause_button.setText(self.text("play"))
        self.play_pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.restart_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.time_label.setText("0:00")
        self.status_label.setText(self.text("stopped"))
    
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

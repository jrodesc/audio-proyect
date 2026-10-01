"""Validated, atomic persistence for playlists."""
import json
import os


class PlaylistStore:
    DEFAULT_NAME = "Favoritas"

    def __init__(self, path):
        self.path = path

    @staticmethod
    def valid_songs(songs):
        return [song for song in songs if isinstance(song, dict) and song.get("id")]

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as file:
                saved = json.load(file)
            if isinstance(saved, list):
                return {self.DEFAULT_NAME: self.valid_songs(saved)}
            if isinstance(saved, dict):
                playlists = {name: self.valid_songs(songs) for name, songs in saved.items()
                             if isinstance(name, str) and name.strip() and isinstance(songs, list)}
                if "Favorites" in playlists:
                    favorites = playlists.pop("Favorites")
                    default = playlists.setdefault(self.DEFAULT_NAME, [])
                    known_ids = {song["id"] for song in default}
                    default.extend(song for song in favorites if song["id"] not in known_ids)
                playlists.setdefault(self.DEFAULT_NAME, [])
                return playlists
            raise ValueError("El formato de las listas no es válido")
        except FileNotFoundError:
            return {self.DEFAULT_NAME: []}
        except (OSError, ValueError, TypeError) as error:
            if os.path.exists(self.path):
                backup = self.path + ".bak"
                if os.path.exists(backup):
                    backup += ".1"
                try:
                    os.replace(self.path, backup)
                except OSError:
                    raise error
            return {self.DEFAULT_NAME: []}

    def save(self, playlists):
        directory = os.path.dirname(self.path)
        os.makedirs(directory, exist_ok=True)
        temporary = self.path + ".tmp"
        try:
            with open(temporary, "w", encoding="utf-8") as file:
                json.dump(playlists, file, ensure_ascii=False, indent=2)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

"""Validated, atomic persistence for playlists."""
import json
import os


class PlaylistStore:
    DEFAULT_NAME = "Favoritas"

    def __init__(self, path):
        self.path = path

    @staticmethod
    def valid_songs(songs):
        valid = []
        for song in songs:
            if not isinstance(song, dict) or not song.get("id"):
                continue
            try:
                hash(song["id"])
            except TypeError:
                continue
            valid.append(song)
        return valid

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as file:
                saved = json.load(file)
            if isinstance(saved, list):
                return {self.DEFAULT_NAME: self.valid_songs(saved)}
            if isinstance(saved, dict):
                playlists = {name: self.valid_songs(songs) for name, songs in saved.items()
                             if isinstance(name, str) and name.strip() and isinstance(songs, list)}
                legacy_names = [name for name in playlists if name.casefold() == "favorites"]
                if legacy_names:
                    default = playlists.setdefault(self.DEFAULT_NAME, [])
                    known_ids = {song["id"] for song in default}
                    for name in legacy_names:
                        for song in playlists.pop(name):
                            if song["id"] not in known_ids:
                                default.append(song)
                                known_ids.add(song["id"])
                playlists.setdefault(self.DEFAULT_NAME, [])
                return playlists
            raise ValueError("El formato de las listas no es válido")
        except FileNotFoundError:
            return {self.DEFAULT_NAME: []}
        except (OSError, ValueError, TypeError) as error:
            if os.path.exists(self.path):
                backup_base = self.path + ".bak"
                backup = backup_base
                suffix = 1
                while os.path.exists(backup):
                    backup = f"{backup_base}.{suffix}"
                    suffix += 1
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

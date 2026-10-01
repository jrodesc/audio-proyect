import json

import pytest

from src.core.playlist_store import PlaylistStore


def test_missing_file_returns_empty_default_playlist(tmp_path):
    store = PlaylistStore(str(tmp_path / "playlists.json"))

    assert store.load() == {"Favoritas": []}


def test_loads_legacy_list_and_filters_invalid_songs(tmp_path):
    path = tmp_path / "playlists.json"
    path.write_text(json.dumps([{"id": "one"}, {"id": ["unhashable"]}, None,
                                {"title": "no id"}, "bad"]), encoding="utf-8")

    assert PlaylistStore(str(path)).load() == {"Favoritas": [{"id": "one"}]}


def test_loads_named_playlists_and_keeps_only_valid_songs(tmp_path):
    path = tmp_path / "playlists.json"
    path.write_text(json.dumps({"Mix": [{"id": "one"}, {}, None], "": [{"id": "bad"}], "Broken": "bad"}), encoding="utf-8")

    assert PlaylistStore(str(path)).load() == {"Mix": [{"id": "one"}], "Favoritas": []}


def test_legacy_favorites_names_merge_without_duplicate_songs(tmp_path):
    path = tmp_path / "playlists.json"
    data = {
        "Favoritas": [{"id": "shared"}, {"id": "spanish"}],
        "Favorites": [{"id": "shared"}, {"id": "english"}],
        "favorites": [{"id": "other"}],
    }
    path.write_text(json.dumps(data), encoding="utf-8")

    loaded = PlaylistStore(str(path)).load()

    assert loaded == {"Favoritas": [
        {"id": "shared"}, {"id": "spanish"}, {"id": "english"}, {"id": "other"}
    ]}


def test_corrupt_json_is_backed_up_and_default_is_returned(tmp_path):
    path = tmp_path / "playlists.json"
    corrupt = "{ this is not json"
    path.write_text(corrupt, encoding="utf-8")

    assert PlaylistStore(str(path)).load() == {"Favoritas": []}
    assert (tmp_path / "playlists.json.bak").read_text(encoding="utf-8") == corrupt
    assert not path.exists()


def test_corrupt_file_does_not_overwrite_existing_backups(tmp_path):
    path = tmp_path / "playlists.json"
    path.write_text("not json", encoding="utf-8")
    (tmp_path / "playlists.json.bak").write_text("old backup", encoding="utf-8")
    (tmp_path / "playlists.json.bak.1").write_text("older backup", encoding="utf-8")

    PlaylistStore(str(path)).load()

    assert (tmp_path / "playlists.json.bak").read_text(encoding="utf-8") == "old backup"
    assert (tmp_path / "playlists.json.bak.1").read_text(encoding="utf-8") == "older backup"
    assert (tmp_path / "playlists.json.bak.2").read_text(encoding="utf-8") == "not json"


def test_save_writes_json_and_cleans_temporary_file(tmp_path):
    path = tmp_path / "nested" / "playlists.json"
    playlists = {"Favoritas": [{"id": "song", "title": "Música"}]}

    PlaylistStore(str(path)).save(playlists)

    assert json.loads(path.read_text(encoding="utf-8")) == playlists
    assert not (tmp_path / "nested" / "playlists.json.tmp").exists()


def test_failed_atomic_replace_preserves_old_file_and_cleans_temp(tmp_path, monkeypatch):
    path = tmp_path / "playlists.json"
    original = '{"Favoritas": []}'
    path.write_text(original, encoding="utf-8")

    def fail_replace(source, destination):
        raise OSError("simulated replace failure")

    monkeypatch.setattr("src.core.playlist_store.os.replace", fail_replace)
    with pytest.raises(OSError, match="simulated replace failure"):
        PlaylistStore(str(path)).save({"Favoritas": [{"id": "new"}]})

    assert path.read_text(encoding="utf-8") == original
    assert not (tmp_path / "playlists.json.tmp").exists()

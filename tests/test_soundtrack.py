"""Soundtrack discovery, optional metadata and pre-login entry integration."""
import json

from werkzeug.test import Client
from werkzeug.wrappers import Response

from app.office import soundtrack
from app.office.web import application, office_app


def test_track_uploads_are_discovered_and_metadata_orders_only_real_files(tmp_path, monkeypatch):
    monkeypatch.setattr(soundtrack, "AUDIO_ROOT", tmp_path)
    for name in ("second-track.mp3", "First Song.m4a", "README.md", ".hidden.mp3"):
        (tmp_path / name).write_bytes(b"fixture")
    (tmp_path / "playlist.json").write_text(json.dumps({
        "artist": "SILVR∆TIK", "artist_url": "https://example.test/artist",
        "tracks": [{"file": "second-track.mp3", "title": "Second"},
                   {"file": "../private.mp3"}, {"file": "missing.mp3"},
                   {"file": "second-track.mp3"}],
    }))
    catalogue = soundtrack.soundtrack_catalogue()
    assert [t["title"] for t in catalogue["tracks"]] == ["Second", "First Song"]
    assert catalogue["tracks"][1]["url"] == "/static/audio/First%20Song.m4a"
    assert catalogue["artist_url"] == "https://example.test/artist"


def test_missing_tracks_and_broken_optional_metadata_do_not_break_office(tmp_path, monkeypatch):
    monkeypatch.setattr(soundtrack, "AUDIO_ROOT", tmp_path)
    for metadata in ('{broken', '[]', '{"artist_url":"javascript:alert(1)","tracks":[null,7]}'):
        (tmp_path / "playlist.json").write_text(metadata)
        result = soundtrack.soundtrack_catalogue()
        assert result["tracks"] == [] and result["artist_url"] == ""
    response = Client(application, Response).get("/login")
    assert response.status_code == 200
    assert b"Tracks will appear here when added" in response.data


def test_launch_and_player_mount_before_auth_and_across_specialist_apps(monkeypatch):
    monkeypatch.setitem(office_app.config, "GBO_AUTH_REQUIRED", True)
    client = Client(application, Response)
    redirected = client.get("/")
    assert redirected.status_code == 302 and "/login" in redirected.headers["Location"]
    login = client.get(redirected.headers["Location"]).get_data(as_text=True)
    assert login.index("data-gbo-launch-root") < login.index("auth-shell")
    assert login.count("data-gbo-splash ") == 1
    assert login.count('src="/static/gbo.js"') == 1
    assert "data-sound-projector" in login and "∆ΩT" in login
    for path in ("/static/office-entry.js", "/static/office-projector.js", "/static/office-projector.css"):
        assert client.get(path).status_code == 200
    monkeypatch.setitem(office_app.config, "GBO_AUTH_REQUIRED", False)
    for path in ("/", "/ledgergut/", "/signor/", "/squarmish/"):
        response = client.get(path)
        assert response.status_code == 200
        assert response.data.count(b"data-sound-projector") == 1
        assert response.data.count(b"data-gbo-splash ") == 1

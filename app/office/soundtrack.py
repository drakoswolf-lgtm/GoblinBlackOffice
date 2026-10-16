"""Discover owner-supplied soundtrack files without hard-coded track URLs."""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote, urlsplit


AUDIO_ROOT = Path(__file__).parent / "static" / "audio"
EXTENSIONS = {".mp3", ".m4a", ".ogg", ".opus", ".wav", ".flac"}


def soundtrack_catalogue() -> dict:
    files = {
        p.name: p for p in AUDIO_ROOT.iterdir()
        if p.is_file() and not p.name.startswith(".") and p.suffix.lower() in EXTENSIONS
    } if AUDIO_ROOT.is_dir() else {}
    manifest = {}
    try:
        manifest = json.loads((AUDIO_ROOT / "playlist.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    if not isinstance(manifest, dict):
        manifest = {}
    artist = manifest.get("artist")
    artist = artist.strip()[:100] if isinstance(artist, str) and artist.strip() else "SILVR∆TIK"
    artist_url = manifest.get("artist_url", "")
    if not isinstance(artist_url, str):
        artist_url = ""
    try:
        parsed = urlsplit(artist_url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            artist_url = ""
    except ValueError:
        artist_url = ""
    tracks, used = [], set()
    entries = manifest.get("tracks", [])
    if not isinstance(entries, list):
        entries = []
    entries += [{"file": name} for name in sorted(files, key=str.casefold)]
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        name = entry.get("file")
        if not isinstance(name, str) or name not in files or name in used:
            continue
        title = entry.get("title")
        title = title.strip()[:160] if isinstance(title, str) and title.strip() else Path(name).stem.replace("_", " ").replace("-", " ").title()
        tracks.append({"title": title, "url": "/static/audio/" + quote(name, safe="")})
        used.add(name)
    return {"artist": artist, "artist_url": artist_url, "tracks": tracks}

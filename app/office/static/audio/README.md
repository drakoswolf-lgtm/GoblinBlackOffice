# GBO soundtrack assets

Drop browser-ready MP3s directly into this folder on `feature/ambient-music-assets`.
Descriptive filenames are sufficient; tracks are discovered automatically after
deployment. MP3 is recommended. M4A, OGG, Opus, WAV and FLAC are also discovered,
but playback depends on browser codec support. Keep lossless masters outside the
repository to reduce build size. No demo music is shipped or presented as yours.

Optional `playlist.json` controls track order, display titles and artist credit:

```json
{
  "artist": "SILVR∆TIK",
  "artist_url": "https://your-artist-page.example/",
  "tracks": [
    {"file": "one-calculator-one-pen.mp3", "title": "One Calculator, One Pen"},
    {"file": "another-track.mp3", "title": "Another Track"}
  ]
}
```

Replace the example artist URL with the real HTTPS artist-page link, or omit it.
Unlisted audio files are appended alphabetically. Missing/duplicate filenames,
unsafe artist links and malformed optional metadata do not break the Office.

The ∆ΩT holoprojector expands to playback, track, seek, mute, volume, startup sound
and projection-motion controls. Music and startup sound are enabled at **12%**
by default, per the owner's 2026-10-16 instruction, superseding the earlier opt-in
plan. Settings persist locally. Browsers may require a tap before audible
playback; the UI reports this rather than claiming to be playing.

Music pauses for startup/intro films and hidden tabs. It loops through available
tracks. Page changes save track/position and restore it; this server-rendered app
does not promise uninterrupted audio across full page loads. The original
opening plays once per tab session, before the first page (including login),
with a skip button and silent fallback when sound autoplay is blocked.

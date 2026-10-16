# ∆ΩT soundtrack projector and app entry

The soundtrack uses native HTML audio and custom accessible controls. No player
package, CDN, framework, canvas or WebGL dependency is introduced. The small
graphite emitter projects a slowly rotating cyan ∆ΩT glyph; inspection expands
track selection, playback, mute, seeking, music/startup volume, startup sound and
projection-motion settings. Motion honors reduced-motion preferences and can be
paused explicitly. Display modes include forced colors and reduced transparency.

## Tracks and preferences

Add MP3s to `app/office/static/audio/`. The server discovers local audio files;
optional `playlist.json` supplies titles, order and an HTTPS artist-page link.
The default credit is SILVR∆TIK. The empty state remains functional without
attempting a missing audio URL. No test tone or fabricated music is shipped.

Per the owner's October 16 instruction, music and startup sound default to enabled
at 12% volume. Pausing, muting, volume and rotation choices persist locally.
Audible autoplay is attempted; browser denial produces an honest tap-to-enable
state. The startup film falls back to muted playback with a sound button.
Music pauses during startup/character films and while the tab is hidden.
The selected track and position are restored across page loads. Full server page
navigation can briefly interrupt audio; no seamless SPA navigation is claimed.

## Opening sequence

All full HTML screens mount the same shared entry component, including public
login and registration. A small head script reserves the opening before login
content can flash. While the opening is visible, underlying content is inert;
keyboard focus stays in the opening, with Skip/Escape available.

Completion/skip records `gbo.startup.seen` in sessionStorage. Subsequent login,
character introduction, onboarding and desk navigation do not replay it. A fresh
tab session opens it again; `?splash=1` explicitly replays it. A browser restoring
an existing tab can retain that tab's session state. This is a per-tab opening,
not an operating-system app-launch detector. The character introduction waits
for the opening if it is the first page reached.

## Verification

- Python suite: 207 passed, including discovery/metadata validation, empty state,
  root-relative media links, pre-login entry and all mounted specialist apps.
- Focused Chromium test uses real decoded test-only PCM audio, exercising quiet
  defaults, blocked autoplay recovery, playback, mute, volume, track switching,
  saved position/settings, pause restoration, film priority and entry sequencing.
- Four viewport widths (1440, 768, 390, 320), 200% text, keyboard focus, reduced
  motion, forced colors and scoped axe accessibility are covered.
- The committed browser suite retains real canonical opening/intro film decoding;
  its sound assertion now accepts either quiet sound or a muted policy fallback.
- Existing PostgreSQL/authentication release checks remain enabled.

The two owner-supplied MP3s were preserved and verified through the real browser
player at 12% volume: One Calculator, One Pen (217.92 s) and The Command Room
(223.752 s). The mistakenly uploaded M4A is omitted at the owner’s request. The
browser suite checks every actual shipped track in addition to its synthetic fixture.
Physical Android audio acceptance remains a release check. No production
deployment is performed by this change.

## Source review

- Native custom audio controls: <https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/audio>
- Chrome autoplay policy: <https://developer.chrome.com/blog/autoplay/>
- Plyr's current repository marks it deprecated in favor of Video.js 10:
  <https://github.com/sampotts/plyr>. A larger video-player dependency is unnecessary
  for this background-audio interface.

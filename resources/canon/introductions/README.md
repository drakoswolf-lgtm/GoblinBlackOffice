# Æterna first-entry films

This folder contains the **one-time character introductions** played after successful account creation and **before Curriculum VitÆ**.

They are deliberately **not** part of the command desk, the account login, or the CV interview UI.

## Media required before merging Pass C

| Destination (under this directory) | Target | Duration | Resolution | SHA-256 |
| --- | --- | ---: | --- | --- |
| `aeterna-first-entry-desktop.mp4` | Desktop | 4.010 s | 1280×720 | `0aa05800dd1f00fe9610...` |
| `aeterna-first-entry-mobile.mp4` | Portrait/mobile | 6.016 s | 720×1280 | `20faa02ef732c8ccf79a...` |

Masters have been furnished in the chat attachment `GBO_Pass_C_First_Entry_Assets.zip`. Extract, then upload the **two MP4s**, not the ZIP, to this directory. The archive's `PASS_C_ASSET_MANIFEST.json` contains the full hashes for matching sources.

### UX contract

- Successful registration sets a one-time, account-and-session-scoped welcome flag.
- A normal login **clears the flag**. Even an account that has not finished onboarding goes directly to CV on returning login.
- The welcome URL is restricted to the fresh registration session; completing or skipping consumes the flag.
- Welcome film chooses the desktop or portrait master according to viewport width, not by cropping the opposite one.
- It autoplays muted for browser compatibility. A user gesture can replay it from the start with sound.
- On video end the app proceeds to Curriculum VitÆ. A manual Continue action is always available.
- Video-load failure keeps Continue available; it must not block onboarding.
- No subtitles, copy, or business input overlays are added by the app.
- The **original desktop footage includes embedded/burned subtitles**. These cannot be disabled in a browser player. A clean exported master would be needed to remove them without changing the footage.
- The existing cinematic Office splash is not repeated between this film and Curriculum VitÆ.
- A future conversational SVG commander for CV is intentionally **not** implemented here.

### Release acceptance

Do not merge or deploy as finished until both masters are present, serve as `video/mp4`, and decode on desktop/mobile Chromium. Verify signed-in user flow and audio controls on Android/Samsung and desktop browsers.

## Pass C companion: ambient Æterna portrait

The separate user-supplied `Add_animation_to_portrait_20261010212551.mp4`
is an animated **portrait**, not another onboarding entrance.

For command desk, Æterna command intelligence and Curriculum VitÆ, an edited
silent/ping-pong portrait loop and a static poster have been prepared in the
conversation attachment `GBO_Pass_C_Animated_Aeterna_Portrait.zip`.

Extract and upload the **two binary files** to `resources/canon/characters/`:

- `aeterna-ambient-portrait.mp4` (H.264, 360×640, 20 fps, 10 s, no audio;
  SHA-256 `b88e1dbe83e5ebdfa12dc238c1638d98c37b49d5f27a05d8a64d829287ad0f57`).
- `aeterna-ambient-poster.webp` (360×640; SHA-256
  `4e655c1c96c3ae2ba286f6da61bbb65eab486f2639ddc15db0b3b97beedab204`).

The original image is not replaced. The DOM always retains the approved
`canon-aeterna-headshot.webp`; if the portrait MP4 is missing, unsupported,
or blocked by browser policies, the still remains visible.

The loop is muted, loads only when visible, and is disabled for reduced-motion
or data-saver preferences. It plays no spoken business prompts. The scene is
deliberately framed as a command portrait, not transparent compositing over the desk.

**Do not merge as complete until the MP4 and poster have been uploaded** and
the browser playback checked on desktop/mobile. The files are a human upload
step because the available GitHub connector cannot write binary repository assets.

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

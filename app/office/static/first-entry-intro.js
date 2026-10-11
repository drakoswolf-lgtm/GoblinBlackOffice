/* First-entry Æterna film. It is an introduction, never the command UI. */
(() => {
  const stage = document.querySelector("[data-first-entry]");
  if (!stage) return;
  const video = stage.querySelector("[data-first-entry-video]");
  const sound = stage.querySelector("[data-intro-sound]");
  const advance = stage.querySelector("[data-intro-continue]");
  const status = stage.querySelector("[data-intro-status]");
  const mobile = window.matchMedia("(max-width: 700px)").matches;

  // The desktop and portrait films are different edits, not crops.
  const path = mobile
    ? "/canon/introductions/aeterna-first-entry-mobile.mp4"
    : "/canon/introductions/aeterna-first-entry-desktop.mp4";
  video.src = path;
  video.muted = true; // Browser-safe autoplay, with one-click sound replay.
  video.load();
  let advancing = false;
  let completionTimer = null;

  const show = (value) => { status.textContent = value; };
  const continueToIntel = () => {
    if (advancing) return;
    advancing = true;
    advance.requestSubmit();
  };

  video.addEventListener("playing", () => {
    stage.classList.add("is-playing");
    stage.classList.remove("is-finished", "is-unavailable");
    show("CMDR. ÆTERNA SKYEWARD // FIRST CONTACT");
  });

  video.addEventListener("ended", () => {
    stage.classList.add("is-finished");
    show("COMMAND LINK ESTABLISHED");
    completionTimer = window.setTimeout(continueToIntel, 1800);
  });

  video.addEventListener("error", () => {
    stage.classList.add("is-unavailable");
    show("INTRODUCTION UNAVAILABLE // CONTINUE TO INTEL");
    sound.disabled = true;
  });

  // A real user gesture unlocks audio and restarts from the beginning, even if
  // the silent autoplay finished before the visitor found the sound control.
  sound.addEventListener("click", async () => {
    if (completionTimer !== null) window.clearTimeout(completionTimer);
    stage.classList.remove("is-finished");
    video.currentTime = 0;
    video.muted = false;
    sound.textContent = "REPLAYING WITH SOUND";
    try {
      await video.play();
    } catch (_) {
      show("TAP CONTINUE TO ENTER INTEL");
      sound.textContent = "REPLAY WITH SOUND";
    }
  });

  video.play().catch(() => {
    // On hardened browsers the user may press Replay or Continue.
    show("PRESS REPLAY WITH SOUND OR CONTINUE");
  });
})();
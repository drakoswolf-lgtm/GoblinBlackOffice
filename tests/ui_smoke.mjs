import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";

const base = process.env.GBO_BASE_URL || "http://127.0.0.1:8080";
await mkdir("artifacts/ui", { recursive: true });
const browser = await chromium.launch({ headless: true });

try {
  for (const spec of [
    { name: "desktop", width: 1440, height: 900 },
    { name: "mobile", width: 390, height: 844 },
  ]) {
    const context = await browser.newContext({
      viewport: { width: spec.width, height: spec.height },
      deviceScaleFactor: 1,
      reducedMotion: "reduce",
    });
    const page = await context.newPage();
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));

    const response = await page.goto(base + "/?splash=1", {
      waitUntil: "networkidle",
      timeout: 30000,
    });
    if (!response?.ok()) throw Error(spec.name + ": Office GET failed");

    const splash = page.locator("[data-gbo-splash]");
    if (!(await splash.isVisible())) {
      throw Error(spec.name + ": First-run splash failed to display");
    }
    const expectedFilm = spec.name === "mobile"
      ? "gbo-opening-mobile.mp4"
      : "gbo-opening-desktop.mp4";
    await page.waitForFunction(() => {
      const film = document.querySelector("[data-gbo-film]");
      return film && film.readyState >= 2 && film.videoWidth > 0 && film.videoHeight > 0;
    }, null, { timeout: 12000 });
    const filmStatus = await page.locator("[data-gbo-film]").evaluate((film) => ({
      src: film.currentSrc,
      width: film.videoWidth,
      height: film.videoHeight,
      duration: film.duration,
      muted: film.muted,
      paused: film.paused,
      currentTime: film.currentTime,
    }));
    if (!filmStatus.src.endsWith(expectedFilm)) {
      throw Error(spec.name + ": Wrong cinematic master: " + JSON.stringify(filmStatus));
    }
    if (filmStatus.paused || filmStatus.duration < 8 || filmStatus.duration > 15) {
      throw Error(spec.name + ": Cinematic film did not start and decode: " + JSON.stringify(filmStatus));
    }
    if ((spec.name === "mobile") !== (filmStatus.height > filmStatus.width)) {
      throw Error(spec.name + ": Master aspect ratio is incorrect: " + JSON.stringify(filmStatus));
    }
    if (!filmStatus.muted || !(await splash.evaluate((node) => node.classList.contains("is-film")))) {
      throw Error(spec.name + ": Video autoplay setup or cinematic overlay failed");
    }
    const startupSize = await page.locator(".gbo-charge").evaluate(
      (node) => getComputedStyle(node).backgroundSize,
    );
    if (spec.name === "mobile" && startupSize !== "cover") {
      throw Error("Mobile ignition art is letterboxed: " + startupSize);
    }
    await page.screenshot({ path: "artifacts/ui/" + spec.name + "-startup.png" });

    await page.waitForFunction(
      () => document.querySelector("[data-gbo-splash]")?.hidden === true,
      { timeout: 15000 },
    );
    const command = page.locator(".command-heading h1");
    if ((await command.innerText()).trim() !== "Command Desk") {
      throw Error(spec.name + ": Command surface was not mounted");
    }

    const visual = await page.evaluate(() => {
      const panel = document.querySelector(".command-environment");
      const stage = document.querySelector(".command-stage");
      const images = [...document.querySelectorAll("img")];
      return {
        background: getComputedStyle(panel).backgroundImage,
        environmentZ: getComputedStyle(panel).zIndex,
        stageZ: getComputedStyle(stage).zIndex,
        bodyWidth: document.documentElement.scrollWidth,
        viewportWidth: window.innerWidth,
        failedImages: images.filter((img) => !img.complete || img.naturalWidth <= 0)
          .map((img) => img.src),
      };
    });

    const backgroundName = "canon-black-office-" + spec.name + ".webp";
    if (!visual.background.includes(backgroundName)) {
      throw Error(spec.name + ": Approved physical office plate was not applied");
    }
    const backgroundResponse = await page.request.get(
      base + "/canon/environments/" + backgroundName,
    );
    if (!backgroundResponse.ok() ||
        !backgroundResponse.headers()["content-type"]?.includes("image/webp")) {
      throw Error(spec.name + ": Approved office plate request failed: " +
        JSON.stringify({ status: backgroundResponse.status(), contentType:
          backgroundResponse.headers()["content-type"], url: backgroundResponse.url(),
          body: (await backgroundResponse.text()).slice(0, 180) }));
    }
    const decode = await page.evaluate(async (url) => {
      const art = new Image();
      art.src = url;
      await art.decode();
      return { width: art.naturalWidth, height: art.naturalHeight };
    }, "/canon/environments/" + backgroundName);
    if ((spec.name === "mobile") !== (decode.height > decode.width)) {
      throw Error(spec.name + ": Background orientation is incorrect");
    }
    if (spec.name === "mobile") {
      const commander = await page.locator(".command-aeterna").boundingBox();
      const workspace = await page.locator(".command-workspace").boundingBox();
      if (!commander || !workspace || commander.y >= workspace.y) {
        throw Error("On mobile, Æterna must appear above the project directory");
      }
    }
    if (visual.environmentZ !== "0" || visual.stageZ !== "1") {
      throw Error(spec.name + ": Incorrect command surface stacking");
    }
    if (visual.bodyWidth > visual.viewportWidth + 2) {
      throw Error(spec.name + ": Horizontal layout overflow: " + JSON.stringify(visual));
    }
    if (visual.failedImages.length) {
      throw Error(spec.name + ": Unreadable images: " + visual.failedImages.join(", "));
    }

    const toggle = page.locator("[data-aeterna-toggle]");
    await toggle.click();
    if ((await toggle.getAttribute("aria-expanded")) !== "false") {
      throw Error(spec.name + ": Æterna advisory panel did not collapse");
    }
    await toggle.click();
    if ((await toggle.getAttribute("aria-expanded")) !== "true") {
      throw Error(spec.name + ": Æterna advisory panel did not reopen");
    }

    await page.screenshot({
      path: "artifacts/ui/" + spec.name + "-command.png",
      fullPage: true,
    });


    // Beta Mk.III Pass A: verify the staged receipt UI, not just the desk artwork.
    const receiptResponse = await page.goto(base + "/ledgergut/", { waitUntil: "domcontentloaded" });
    if (!receiptResponse?.ok()) throw Error(spec.name + ": Ledgergut route failed");
    if (!(await page.locator("[data-receipt-choices]").isVisible())) {
      throw Error(spec.name + ": Receipt intake choices must be visible before scanning");
    }
    if (await page.locator("[data-receipt-review]").first().isVisible()) {
      throw Error(spec.name + ": Receipt review fields appeared before intake choice");
    }
    await page.locator("[data-manual-start]").click();
    if (!(await page.locator("[data-receipt-review]").first().isVisible())) {
      throw Error(spec.name + ": Manual entry did not expose review fields");
    }
    const receiptRows = page.locator(".beta-line-row.receipt-line");
    await page.locator("[data-add-row]").click();
    if ((await receiptRows.count()) !== 2) {
      throw Error(spec.name + ": Add Item did not append a structured receipt row");
    }
    await page.screenshot({ path: "artifacts/ui/" + spec.name + "-ledgergut-entry.png", fullPage: true });
    const brandResponse = await page.goto(base + "/settings/documents", { waitUntil: "domcontentloaded" });
    if (!brandResponse?.ok() || !(await page.locator("#document_style").isVisible())) {
      throw Error(spec.name + ": Document branding settings did not load");
    }


    // Æterna Pass B: project-scoped command intelligence must render in both layouts.
    const commandResponse = await page.goto(base + "/aeterna/command", { waitUntil: "domcontentloaded" });
    if (!commandResponse?.ok() || !(await page.getByRole("heading", { name: "Command Intelligence" }).isVisible())) {
      throw Error(spec.name + ": Æterna command console failed to render");
    }
    if (!(await page.locator("#aeterna-project").isVisible())) {
      throw Error(spec.name + ": Project selector unavailable");
    }
    await page.locator("#aeterna-question").fill("What is outstanding?");
    await page.getByRole("button", { name: "RUN BRIEFING" }).click();
    if (!(await page.getByText("FINANCIAL RECORDS").isVisible())) {
      throw Error(spec.name + ": Æterna did not route financial questions");
    }
    const commandOverflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    if (commandOverflow > 2) {
      throw Error(spec.name + ": Æterna command horizontal overflow: " + commandOverflow);
    }
    const ambientOnCommand = page.locator("[data-aeterna-ambient]");
    if ((await ambientOnCommand.count()) !== 1) {
      throw Error(spec.name + ": Ambient portrait not mounted on command screen");
    }
    if (!await ambientOnCommand.evaluate(v => v.muted && v.loop && v.playsInline)) {
      throw Error(spec.name + ": Ambient portrait must be silent, looping and inline");
    }
    if (!await page.locator(".aeterna-command-officer img[alt='Cmdr. Æterna Skyeward']").isVisible()) {
      throw Error(spec.name + ": Canon still image missing as portrait fallback");
    }
    // Smoke tests request reduced-motion; the portrait must stay static.
    const reducedPortraitStyle = await ambientOnCommand.evaluate(v => getComputedStyle(v).display);
    if (reducedPortraitStyle !== "none") {
      throw Error(spec.name + ": Reduced-motion preference is not respected");
    }
    await page.screenshot({ path: "artifacts/ui/" + spec.name + "-aeterna-command.png", fullPage: true });
    await page.getByRole("link", { name: "GOBLIN CHECKS" }).click();
    if (!(await page.getByText("Office-wide checks summarize saved records").isVisible()) || !(await page.getByText("NOT AUTOMATED").isVisible())) {
      throw Error(spec.name + ": Office-wide specialist checks missing");
    }


    // Pass C: the first-registration film is an introduction only.
    // Media existence/decode becomes a release gate when masters are committed.
    await page.goto(base + "/register", { waitUntil: "domcontentloaded" });
    await page.locator("#display-name").fill("Intro Test " + spec.name);
    await page.locator("#email").fill("cinema-" + spec.name + "@example.test");
    await page.locator("#password").fill("a-passphrase-longer-than-ten");
    await page.getByRole("button", { name: "Create account" }).click();
    await page.waitForURL("**/welcome");
    const welcomeVideo = page.locator("[data-first-entry-video]");
    if (!(await welcomeVideo.isVisible())) throw Error(spec.name + ": Welcome film missing");
    const expectedIntroName = "aeterna-first-entry-" + spec.name + ".mp4";
    const actualIntroSrc = await welcomeVideo.evaluate(video => video.currentSrc || video.src);
    if (!actualIntroSrc.endsWith(expectedIntroName)) {
      throw Error(spec.name + ": Wrong first-entry master selected: " + actualIntroSrc);
    }
    // Once the binary masters arrive, CI verifies their actual decoding,
    // not merely a correct-looking URL. Drafts without assets stay identifiable.
    const mediaResponse = await page.request.get(base + "/canon/introductions/" + expectedIntroName);
    if (mediaResponse.ok()) {
      if (!mediaResponse.headers()["content-type"]?.includes("video/mp4")) {
        throw Error(spec.name + ": Introduction is not served as MP4");
      }
      await page.waitForFunction(() => {
        const film = document.querySelector("[data-first-entry-video]");
        return film && film.readyState >= 2 && film.videoWidth > 0 && film.videoHeight > 0;
      }, null, { timeout: 12000 });
      const dimensions = await welcomeVideo.evaluate(film => ({
        width: film.videoWidth,
        height: film.videoHeight,
        duration: film.duration,
      }));
      const correct = spec.name === "mobile"
        ? dimensions.width === 720 && dimensions.height === 1280 &&
          dimensions.duration >= 5.5 && dimensions.duration < 7
        : dimensions.width === 1280 && dimensions.height === 720 &&
          dimensions.duration >= 3.5 && dimensions.duration < 5;
      if (!correct) {
        throw Error(spec.name + ": Intro master wrong geometry or runtime: " +
          JSON.stringify(dimensions));
      }
    } else if (process.env.GBO_REQUIRE_FIRST_ENTRY_ASSETS === "1") {
      throw Error(spec.name + ": Release build missing first-entry master " + expectedIntroName);
    }
    if (!(await page.locator("[data-intro-sound]").isVisible())) {
      throw Error(spec.name + ": Film sound replay control is missing");
    }
    const introHorizontalOverflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    if (introHorizontalOverflow > 2) throw Error(spec.name + ": Intro causes horizontal overflow");
    await page.screenshot({ path: "artifacts/ui/" + spec.name + "-first-entry.png" });
    await page.getByRole("button", { name: /CONTINUE TO CURRICULUM VITÆ/i }).click();
    await page.waitForURL("**/onboarding");
    if ((await page.locator(".aeterna-holo-frame [data-aeterna-ambient]").count()) !== 1) {
      throw Error(spec.name + ": CV briefing is missing Aeterna ambient portrait");
    }
    if (!(await page.getByText("CURRICULUM VITÆ").first().isVisible())) {
      throw Error(spec.name + ": CV did not follow first-entry video");
    }
    await page.goto(base + "/welcome", { waitUntil: "domcontentloaded" });
    if (!page.url().endsWith("/onboarding")) {
      throw Error(spec.name + ": First-entry can replay after completion");
    }

    if (errors.length) throw Error(spec.name + ": Browser errors: " + errors.join("; "));
    console.log("PASS " + spec.name + " visual smoke", visual);
    await context.close();
  }
} finally {
  await browser.close();
}

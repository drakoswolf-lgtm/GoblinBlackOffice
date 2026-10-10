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

    if (errors.length) throw Error(spec.name + ": Browser errors: " + errors.join("; "));
    console.log("PASS " + spec.name + " visual smoke", visual);
    await context.close();
  }
} finally {
  await browser.close();
}

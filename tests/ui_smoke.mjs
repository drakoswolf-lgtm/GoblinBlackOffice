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

    if (!visual.background.includes("canon-black-office-command.svg")) {
      throw Error(spec.name + ": Canon environment was not applied");
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

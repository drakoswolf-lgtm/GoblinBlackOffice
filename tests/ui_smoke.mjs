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


    // Beta business-first pass: the portraits are subdued behind functional labels.
    const channels = page.locator(".command-channel.business-specialist-link");
    if (await channels.count() !== 6) throw Error(spec.name + ": Missing six business specialist channels");
    for (const label of ["Receipt Log", "Agreements", "Invoices & Payments", "Materials", "Work Log", "Risk Review"]) {
      if (!await channels.getByText(label, { exact: true }).isVisible()) {
        throw Error(spec.name + ": Missing business section " + label);
      }
    }
    const spriteSource = "/canon/characters/canon-goblin-specialist-sprite.webp";
    const spriteResponse = await page.request.get(base + spriteSource);
    if (!spriteResponse.ok() || !spriteResponse.headers()["content-type"]?.includes("image/webp")) {
      throw Error(spec.name + ": Canon six-goblin portrait sprite missing");
    }
    const spriteDimensions = await page.evaluate(async url => {
      const img = new Image(); img.src = url; await img.decode();
      return { width: img.naturalWidth, height: img.naturalHeight };
    }, spriteSource);
    if (spriteDimensions.width < 300 || spriteDimensions.height < 75) {
      throw Error(spec.name + ": Portrait sprite failed to decode");
    }
    const firstPortrait = await channels.first().locator(".office-scope-portrait").evaluate(node => {
      const s = getComputedStyle(node);
      return { source:s.backgroundImage, opacity:Number(s.opacity), z:s.zIndex };
    });
    if (!firstPortrait.source.includes("canon-goblin-specialist-sprite.webp") ||
        firstPortrait.opacity > .5) {
      throw Error(spec.name + ": Portrait must be an unobtrusive background image");
    }

    const records = await page.goto(base + "/records", { waitUntil: "domcontentloaded" });
    if (!records?.ok() || !await page.getByRole("heading", { name:"Clients & Projects" }).isVisible()) {
      throw Error(spec.name + ": Client and project records did not render");
    }
    await page.locator("#add-client summary").click();
    await page.locator("#client-name").fill("UX Test " + spec.name);
    await page.locator("#add-client button[type=submit]").click();
    await page.waitForURL("**/records");
    const clientLink = page.locator('.office-client-row[href*="client_id="]').filter({ hasText:"UX Test " + spec.name }).first();
    if (!await clientLink.isVisible()) throw Error(spec.name + ": Client not listed after creation");
    await clientLink.click();
    if (!await page.getByText("CLIENT CONTACT").isVisible()) {
      throw Error(spec.name + ": Client details not shown after selection");
    }
    await page.screenshot({ path:"artifacts/ui/" + spec.name + "-clients.png", fullPage:true });
    await page.locator("#add-project summary").click();
    await page.locator("#project-name").fill("Business-first test job " + spec.name);
    await page.locator("#record-pricing").selectOption("hourly");
    await page.locator("#add-project button[type=submit]").click();
    await page.waitForURL("**/records");
    const jobRow = page.locator(".office-project-row").filter({ hasText:"Business-first test job " + spec.name }).first();
    if (!await jobRow.isVisible()) throw Error(spec.name + ": New project missing from business records");
    await jobRow.click();
    await page.waitForURL("**/jobs/*");
    if (await page.locator(".office-scope-panel").count() !== 6) {
      throw Error(spec.name + ": Project workbench missing six functional panels");
    }
    if (!await page.getByRole("link", { name:/Draft agreement/ }).first().isVisible()) {
      throw Error(spec.name + ": Agreement workflow link lost");
    }
    for (const area of ["project-agreements", "packrat-shopping", "project-work", "project-invoices"]) {
      if (await page.locator("#" + area).count() !== 1) throw Error(spec.name + ": Project section missing: " + area);
    }
    const betaOverflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    if (betaOverflow > 2) throw Error(spec.name + ": Project UI horizontal overflow: " + betaOverflow);
    await page.screenshot({ path:"artifacts/ui/" + spec.name + "-project-business-first.png", fullPage:true });

    // Ledgergut mobile hotfix: exercise the actual native file chooser,
    // multipart POST and real Tesseract parsing rather than just button presence.
    const slip = await context.newPage();
    await slip.setContent(`<!doctype html><html><body style="margin:0;background:#faf9ee">
      <div id="slip" style="width:840px;height:940px;padding:48px;box-sizing:border-box;background:#faf9ee;color:#141414;font:33px Arial,sans-serif;line-height:2">
      HOME HARDWARE<br>123 MAIN STREET<br>DATE 2026-10-11<br>
      CEDAR BOARD 24.00<br>SUBTOTAL 24.00<br>GST 1.20<br>PST 1.68<br>TOTAL 26.88</div>
    </body></html>`);
    const receiptPhoto = await slip.locator("#slip").screenshot({ type:"png" });
    await slip.close();
    const scanHome = await page.goto(base + "/ledgergut/", { waitUntil:"domcontentloaded" });
    if (!scanHome?.ok()) throw Error(spec.name + ": Ledgergut entry unavailable");
    const fileChoiceEvent = page.waitForEvent("filechooser", { timeout:12000 });
    await page.locator("label.beta-upload-choice").click();
    const fileChooser = await fileChoiceEvent;
    await fileChooser.setFiles({ name:"receipt-test.png", mimeType:"image/png", buffer:receiptPhoto });
    await page.waitForURL("**/ledgergut/receipts/scan", { timeout:60000 });
    if (!await page.locator("[data-receipt-review]").first().isVisible()) {
      throw Error(spec.name + ": OCR review did not appear after image selection");
    }
    if (!await page.locator("#vendor_name").inputValue() ||
        (await page.locator("#total_amount").inputValue()) !== "26.88") {
      throw Error(spec.name + ": OCR failed to recognize a legible receipt photo");
    }
    const retainedToken = await page.locator('input[name="pending_image_token"]').inputValue();
    if (!retainedToken) throw Error(spec.name + ": Scanned image was not retained for human review");
    const pendingPhoto = await page.request.get(base + "/ledgergut/receipts/pending/" + retainedToken);
    if (!pendingPhoto.ok() || !pendingPhoto.headers()["content-type"]?.includes("image/png")) {
      throw Error(spec.name + ": Review photo not retrievable after scan");
    }
    await page.screenshot({ path: "artifacts/ui/" + spec.name + "-ledgergut-ocr-upload.png", fullPage:true });

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
    if (spec.name === "mobile") {
      const card = await page.locator(".aeterna-command-officer").evaluate(node => {
        const box = el => {
          const b = el.getBoundingClientRect();
          return { x:b.x,y:b.y,right:b.right,bottom:b.bottom,width:b.width,height:b.height };
        };
        return {
          heading:box(node.querySelector(".aeterna-officer-heading")),
          portrait:box(node.querySelector(".command-aeterna-frame")),
          intro:box(node.querySelector(".aeterna-officer-intro")),
          boundary:box(node.querySelector(".aeterna-officer-boundary")),
        };
      });
      const overlaps = (a,b) => a.x < b.right - 2 && a.right > b.x + 2 &&
        a.y < b.bottom - 2 && a.bottom > b.y + 2;
      if (card.heading.width < 115 || overlaps(card.heading,card.portrait) ||
          overlaps(card.intro,card.portrait) || overlaps(card.boundary,card.intro)) {
        throw Error("Mobile Aeterna card content overlaps or compresses: " + JSON.stringify(card));
      }
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
    // Prevent the exact release defect captured on Android: absolute controls
    // cover the Deployment cards, and the CV displays a synthetic room.
    const cvBg = await page.locator(".black-office-environment").evaluate(
      node => getComputedStyle(node).backgroundImage
    );
    const expectedRoom = spec.name === "mobile" ?
      "canon-black-office-mobile.webp" : "canon-black-office-desktop.webp";
    if (!cvBg.includes(expectedRoom)) {
      throw Error(spec.name + ": Curriculum doesn't use approved room image: " + cvBg);
    }
    if (spec.name === "desktop") {
      const readout = await page.evaluate(() => {
        const right = document.querySelector(".curriculum-statusbar .status-readout").getBoundingClientRect().right;
        const portraitLeft = document.querySelector(".aeterna-briefing").getBoundingClientRect().left;
        return {right, portraitLeft};
      });
      if (readout.right > readout.portraitLeft - 5) {
        throw Error("Desktop CV status readout obscured by Æterna: " + JSON.stringify(readout));
      }
    }
    if (spec.name === "mobile") {
      const firstState = await page.evaluate(() => ({
        planeTransform:getComputedStyle(document.querySelector(".intel-table-plane")).transform,
        controlsPosition:getComputedStyle(document.querySelector(".curriculum-controls")).position,
        dialoguePosition:getComputedStyle(document.querySelector(".aeterna-dialogue")).position,
        bgPosition:getComputedStyle(document.querySelector(".black-office-environment")).position
      }));
      if (firstState.planeTransform !== "none" || firstState.controlsPosition !== "static" ||
          firstState.dialoguePosition !== "relative" || firstState.bgPosition !== "fixed") {
        throw Error("CV geometry is not stable on mobile: " + JSON.stringify(firstState));
      }
    }
    await page.screenshot({path:"artifacts/ui/"+spec.name+"-curriculum-first.png", fullPage:true});
    for (let step=0;step<5;step++) {
      if (step === 1) {
        await page.locator('input[name="business_name"]').fill("Layout Test Company");
        await page.locator('input[name="business_type"]').fill("Contracting");
      }
      await page.locator("[data-curriculum-next]").click();
      await page.locator('[data-screen="'+(step+1)+'"]').waitFor({state:"visible", timeout:4000});
    }
    if (!await page.locator("[data-curriculum-deploy]").isVisible()) {
      throw Error(spec.name + ": Curriculum deployment button isn't visible");
    }
    {
      const metrics = await page.evaluate(() => {
        const r = sel => {
          const v = document.querySelector(sel).getBoundingClientRect();
          return {y:v.y,bottom:v.bottom,height:v.height,x:v.x,right:v.right};
        };
        const cards = [...document.querySelectorAll(".deployment-card")].map(n => n.getBoundingClientRect());
        const button = document.querySelector("[data-curriculum-deploy]");
        return {
          lastCardBottom:Math.max(...cards.map(n => n.bottom)),
          deploymentNote:r(".deployment-note"),
          controls:r(".curriculum-controls"),
          dialogue:r(".aeterna-dialogue"),
          buttonFits:button.scrollWidth <= button.clientWidth + 2,
          overflow:document.documentElement.scrollWidth - window.innerWidth,
        };
      });
      if (metrics.controls.y < metrics.deploymentNote.bottom - 2 ||
          metrics.deploymentNote.y < metrics.lastCardBottom - 2 ||
          metrics.dialogue.y < metrics.controls.bottom - 2 ||
          !metrics.buttonFits || metrics.overflow > 2) {
        throw Error(spec.name + ": CV deployment content or action overlaps: "+JSON.stringify(metrics));
      }
    }
    await page.screenshot({path:"artifacts/ui/"+spec.name+"-curriculum-deployment.png", fullPage:true});

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

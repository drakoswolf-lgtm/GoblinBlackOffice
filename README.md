# GoblinBlackOffice
A personal workforce of disgruntled goblins dedicated to saving you time, making you money, and leaving suspicious slime and coffee stains on your TPS reports.

## Ledgergut — Receipt Entry UI

Ledgergut is a mobile-first PWA (Progressive Web App). You can **install it as an icon on your Android home screen** by deploying the backend to any HTTPS host — no Python, Termux, or Tesseract installation required on your phone.

---

### Android quick-start (recommended — Render.com free tier)

> **Prerequisites on your computer** (one-time setup): a GitHub account and a free [Render.com](https://render.com) account.

#### 1. Deploy the backend

1. Fork or push this repository to your GitHub account.
2. Log in at [dashboard.render.com](https://dashboard.render.com) → **New → Web Service**.
3. Connect your GitHub repo. Render auto-detects `render.yaml`.
4. Click **Create Web Service** — Render installs Python, Tesseract, and all dependencies automatically.
5. Wait ~3 minutes for the first build. Copy your public URL (e.g. `https://ledgergut.onrender.com`).

> **Free-tier note:** Render free instances spin down after 15 minutes of inactivity. The first request after a sleep takes ~30 s. Upgrade to the $7/month Starter plan to keep it always-on.

#### 2. Install on Android as a home screen icon

1. Open Chrome on your Android phone and navigate to your Render URL.
2. Tap the **⋮ menu → Add to Home screen** (Chrome shows an install banner automatically on HTTPS).
3. Tap **Add** — a Ledgergut icon appears on your home screen.
4. Launch from the icon: the app opens full-screen, like a native app.

#### 3. Use Ledgergut on Android

| Feature | How |
|---------|-----|
| Photograph a receipt | Tap **Upload or photograph receipt** → your camera opens directly |
| Upload from gallery | Same button → choose **Gallery / Files** |
| OCR | Tap **🔎 Scan Receipt** — extracted fields are pre-filled |
| Review & correct | Edit any field before saving |
| Save | Tap **💾 Save Receipt** |
| Export CSV | Tap **⬇ Export CSV** in the Saved Receipts section |

---

### Alternative: self-hosted Docker deployment

```bash
# Build and run locally (requires Docker)
docker build -t ledgergut .
docker run -p 8080:8080 -v ledgergut-data:/data ledgergut
# Then open http://localhost:8080
```

For a persistent VPS (DigitalOcean, Fly.io, Railway, etc.) deploy the container image and mount a volume at `/data`. Set the `LEDGERGUT_SECRET` env var to a random string.

---

### Local desktop quick-start (Python)

```bash
# 1. Install Python dependencies (Python 3.10+ required)
pip install flask pillow pytesseract gunicorn

# 2. Launch Ledgergut
python run_ledgergut.py
```

Then open **http://localhost:5000** in your browser.

Saved receipts go to `runtime/ledgergut/receipts.json`. Uploaded images go to `runtime/ledgergut/images/` (gitignored).

### Local OCR dependency

Ledgergut uses **Tesseract OCR** (via `pytesseract`) when running locally. It is pre-installed in the Render and Docker deployments. For local use:

**Windows (Chocolatey)**

```powershell
choco install tesseract
```

**macOS (Homebrew)**

```bash
brew install tesseract
```

**Ubuntu**

```bash
sudo apt-get install -y tesseract-ocr
```

If Tesseract is missing, Ledgergut still supports full manual entry.

### Running tests

```bash
PYTHONPATH=. python -m pytest tests/
```

---

## Goblin Workflows

- [GBO-001: Ledgergut Founder/Operator Receipt Intelligence Workflow](docs/goblins/GBO-001-ledgergut-workflow.md)
- [GBO-002: Squarmish Invoice Workflow](docs/goblins/GBO-002-squarmish-invoice-workflow.md)

## Library

- [Scroll 001 — Living Codex](docs/library/01-living-codex.md) — Master index of agents, scrolls, and documents
- [Scroll 002 — Character Bible](docs/library/02-character-bible.md) — Canonical character and role definitions for all goblins

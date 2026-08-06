# GoblinBlackOffice
A personal workforce of disgruntled goblins dedicated to saving you time, making you money, and leaving suspicious slime and coffee stains on your TPS reports.

## Ledgergut — Receipt Entry UI

Ledgergut is a mobile-first PWA (Progressive Web App). You can **install it as an icon on your Android home screen** with no Python, Termux, or Tesseract required on your phone.

The recommended setup runs Ledgergut in Docker on a Windows PC and exposes it privately to your phone over **Tailscale**.

---

### Android quick-start (recommended — Windows PC + Docker Desktop + Tailscale)

> **Prerequisites (one-time setup on the PC):**
> - [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/) — installed and running
> - [Tailscale](https://tailscale.com/download/windows) — installed and signed in on both the PC and the Android phone
> - Tailscale **Serve** configured to expose port 8080 over HTTPS (see step 3 below)

#### 1. Build and run the container

Open **PowerShell** on the Windows PC:

```powershell
# Clone the repo (or cd into an existing checkout)
cd C:\path\to\GoblinBlackOffice

# Build the image
docker build -t ledgergut .

# Create a named volume for all persistent data (receipts + images)
docker volume create ledgergut-data

# Run the container — binds to localhost only; Tailscale Serve proxies HTTPS
docker run -d --name ledgergut `
    -p 127.0.0.1:8080:8080 `
    -v ledgergut-data:/data `
    --restart unless-stopped `
    -e LEDGERGUT_SECRET="$(New-Guid)" `
    ledgergut
```

> All receipt records and uploaded images are stored in the `ledgergut-data` Docker volume, mounted at `/data` inside the container.

#### 2. Expose over Tailscale HTTPS (Tailscale Serve)

In PowerShell (the PC must already be signed in to Tailscale):

```powershell
tailscale serve https / http://127.0.0.1:8080
```

Tailscale Serve issues a trusted HTTPS certificate and makes the app reachable at your PC's Tailscale hostname — something like `https://my-pc.tail12345.ts.net`. PWA install in Chrome requires HTTPS, which Tailscale Serve provides automatically.

> To find your PC's Tailscale hostname: `tailscale status` — look for your machine's entry.

#### 3. Install on Android as a home screen icon

1. Make sure Tailscale is running on your Android phone.
2. Open **Chrome** and navigate to `https://<your-pc-tailscale-hostname>` (e.g. `https://my-pc.tail12345.ts.net`).
3. Tap **⋮ menu → Add to Home screen** (Chrome shows an install banner automatically on HTTPS).
4. Tap **Add** — a Ledgergut icon appears on your home screen.
5. Launch from the icon: the app opens full-screen, camera-ready.

#### 4. Use Ledgergut on Android

| Feature | How |
|---------|-----|
| Photograph a receipt | Tap **Upload or photograph receipt** → camera opens directly |
| Upload from gallery | Same button → choose **Gallery / Files** |
| OCR | Tap **🔎 Scan Receipt** — extracted fields are pre-filled |
| Review & correct | Edit any field before saving |
| Save | Tap **💾 Save Receipt** |
| Export CSV | Tap **⬇ Export CSV** in the Saved Receipts section |

#### Useful container management commands

```powershell
# View logs
docker logs ledgergut

# Stop / start
docker stop ledgergut
docker start ledgergut

# Update to a new build
docker build -t ledgergut .
docker stop ledgergut && docker rm ledgergut
docker run -d --name ledgergut `
    -p 127.0.0.1:8080:8080 `
    -v ledgergut-data:/data `
    --restart unless-stopped `
    -e LEDGERGUT_SECRET="$(New-Guid)" `
    ledgergut
```

---

### Local desktop quick-start (Python, no Docker)

```bash
# 1. Install Python dependencies (Python 3.10+ required)
pip install flask pillow pytesseract gunicorn

# 2. Launch Ledgergut
python run_ledgergut.py
```

Then open **http://localhost:5000** in your browser.

Saved receipts go to `runtime/ledgergut/receipts.json`. Uploaded images go to `runtime/ledgergut/images/` (gitignored).

### Local OCR dependency

Ledgergut uses **Tesseract OCR** (via `pytesseract`) when running locally. It is pre-installed in the Docker image. For local use:

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

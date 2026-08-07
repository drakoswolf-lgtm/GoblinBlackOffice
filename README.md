# GoblinBlackOffice
A personal workforce of disgruntled goblins dedicated to saving you time, making you money, and leaving suspicious slime and coffee stains on your TPS reports.

## Ledgergut — Receipt Entry UI

Ledgergut is a mobile-first PWA (Progressive Web App). You can **install it as an icon on your Android home screen** with no Python, Termux, or Tesseract required on your phone.

The recommended setup runs Ledgergut in Docker on a Windows PC and exposes it privately to your phone over **Tailscale**.

---

> ⚠️ **Security: keep Ledgergut private**
>
> - **Do not** enable Tailscale Funnel.
> - **Do not** configure router port forwarding to the PC.
> - **Do not** bind Docker to `0.0.0.0` or any LAN/public interface — always use `-p 127.0.0.1:8080:8080`.
> - Ledgergut must only be reachable through the Tailscale private network.

---

### Android quick-start (recommended — Windows PC + Docker Desktop + Tailscale)

> **Prerequisites (one-time setup on the PC):**
> - [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/) — installed and running
> - [Tailscale](https://tailscale.com/download/windows) — installed and signed in on both the PC and the Android phone

#### 1. Make the PC always-on

Before deploying, configure the PC so Ledgergut stays reachable:

1. **Docker Desktop → Settings → General → Start Docker Desktop when you sign in to your computer** ✓
2. **Tailscale runs as a Windows service by default** — verify with `Get-Service Tailscale` in PowerShell.
3. **Disable automatic sleep while plugged in** (Power & sleep settings → Sleep → Never when plugged in).
4. Confirm that `--restart unless-stopped` is set on the container (see step 2) so Docker restarts Ledgergut after reboot.

#### 2. Build and run the container

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
    -e LEDGERGUT_ENV=production `
    -e LEDGERGUT_SECRET="$(New-Guid)" `
    -e LEDGERGUT_USERNAME="yourUsername" `
    -e LEDGERGUT_PASSWORD="yourStrongPassword" `
    ledgergut
```

> All receipt records and uploaded images are stored in the `ledgergut-data` Docker volume, mounted at `/data` inside the container. Container recreation does **not** back up the volume — see [Backup & restore](#backup--restore-ledgergut-data) below.

> **Required environment variables in production:**
> - `LEDGERGUT_ENV=production` — enables production-mode enforcement
> - `LEDGERGUT_SECRET` — random string for Flask session signing
> - `LEDGERGUT_USERNAME` and `LEDGERGUT_PASSWORD` — HTTP Basic auth credentials

#### 3. Expose over Tailscale HTTPS (Tailscale Serve)

In PowerShell (the PC must already be signed in to Tailscale):

```powershell
# Start Tailscale Serve persistently (survives reboots)
tailscale serve --bg http://127.0.0.1:8080

# Verify the serve configuration
tailscale serve status

# To remove the Tailscale Serve rule later
tailscale serve reset
```

Tailscale Serve issues a trusted HTTPS certificate and makes the app reachable at your PC's Tailscale hostname — something like `https://my-pc.tail12345.ts.net`. PWA install in Chrome requires HTTPS, which Tailscale Serve provides automatically.

> To find your PC's Tailscale hostname: `tailscale status` — look for your machine's entry.

#### 4. Install on Android as a home screen icon

1. Make sure Tailscale is running on your Android phone.
2. Open **Chrome** and navigate to `https://<your-pc-tailscale-hostname>` (e.g. `https://my-pc.tail12345.ts.net`).
3. Enter your username and password when prompted.
4. Tap **⋮ menu → Add to Home screen** (Chrome shows an install banner automatically on HTTPS).
5. Tap **Add** — a Ledgergut icon appears on your home screen.
6. Launch from the icon: the app opens full-screen, camera-ready.

#### 5. Verify after reboot

After rebooting the PC, confirm Ledgergut is running:

```powershell
# Check the health endpoint (no auth required)
Invoke-WebRequest http://127.0.0.1:8080/health
# Expected: {"status": "ok"}
```

#### 6. Use Ledgergut on Android

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

# Update to a new build (volume data is preserved)
docker build -t ledgergut .
docker stop ledgergut && docker rm ledgergut
docker run -d --name ledgergut `
    -p 127.0.0.1:8080:8080 `
    -v ledgergut-data:/data `
    --restart unless-stopped `
    -e LEDGERGUT_ENV=production `
    -e LEDGERGUT_SECRET="$(New-Guid)" `
    -e LEDGERGUT_USERNAME="yourUsername" `
    -e LEDGERGUT_PASSWORD="yourStrongPassword" `
    ledgergut
```

---

### Backup & restore Ledgergut data

> ⚠️ **Container recreation does not back up the `ledgergut-data` named volume.** Always back up the volume separately before recreating or removing the container.

#### Back up (command line)

```powershell
# Export the entire /data volume to a compressed archive
docker run --rm `
    -v ledgergut-data:/data:ro `
    -v "$PWD:/backup" `
    alpine tar czf /backup/ledgergut-backup.tar.gz -C / data

# The archive is saved as ledgergut-backup.tar.gz in the current directory.
```

#### Restore from archive

```powershell
# Restore into a (new or existing) volume
docker run --rm `
    -v ledgergut-data:/data `
    -v "$PWD:/backup" `
    alpine sh -c "cd / && tar xzf /backup/ledgergut-backup.tar.gz"
```

#### Back up using Docker Desktop

1. Open Docker Desktop → **Volumes** → `ledgergut-data`.
2. Click **Export** → choose a destination folder.
3. Docker Desktop saves a `.tar.gz` archive of the volume contents.

#### Restore using Docker Desktop

1. Open Docker Desktop → **Volumes** → create or select `ledgergut-data`.
2. Click **Import** → select the previously exported `.tar.gz` file.

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

# 🌐 MANAS: Complete Beginner's Website Deployment & Testing Guide

Welcome! If this is your **first time** deploying and running a modern web application, this guide will walk you through everything step by step — in plain English, with exact commands you can copy and paste.

---

## 🧠 1. How MANAS Works as a Website

Before running commands, here is how the website is built under the hood:

```
                  ┌─────────────────────────────────────────┐
                  │          Your Web Browser               │
                  │       (http://localhost:3000)           │
                  └──────────────────┬──────────────────────┘
                                     │
                    User clicks, views charts, tables
                                     │
                                     ▼
                  ┌─────────────────────────────────────────┐
                  │        1. FRONTEND (Next.js 15)         │
                  │   Renders visual pages, brain maps,     │
                  │   interactive tables, and navigation.   │
                  └──────────────────┬──────────────────────┘
                                     │
                    Fetches data via REST API (/api/...)
                                     │
                                     ▼
                  ┌─────────────────────────────────────────┐
                  │        2. BACKEND (FastAPI / Python)    │
                  │   Runs statistical models, QC filters,   │
                  │   biomarker ratios, and pTau analyses.  │
                  └──────────────────┬──────────────────────┘
                                     │
                    Queries and stores research records
                                     │
                                     ▼
                  ┌─────────────────────────────────────────┐
                  │        3. DATABASE (SQLite / Postgres)   │
                  │   Holds 107 donors, 11,040 measurements,│
                  │   canonical brain regions, & benchmarks.│
                  └─────────────────────────────────────────┘
```

---

## 🚀 2. Run & Test the Website on Your Computer (Easiest Method)

You can launch the entire website locally right now without installing any cloud tools or Docker.

### Step 1: Open Two Terminal Windows
Open two PowerShell or Command Prompt windows on your computer.

---

### Step 2: Start the Backend (Terminal 1)

In your first terminal, navigate to the `manas` folder and start the Python server:

```powershell
cd C:\Users\abhinav\.gemini\antigravity-ide\scratch\manas
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

**What you will see:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     MANAS 1.0.0 starting in development mode
INFO:     Database tables verified/created.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```
> ✅ **The Backend is now live!**

---

### Step 3: Start the Frontend Website (Terminal 2)

In your second terminal, navigate to the `frontend` folder and start the Next.js development server:

```powershell
cd C:\Users\abhinav\.gemini\antigravity-ide\scratch\manas\frontend
npm run dev
```

**What you will see:**
```
   ▲ Next.js 15.1.0
   - Local:        http://localhost:3000
   - Network:      http://192.168.x.x:3000

 ✓ Starting...
 ✓ Ready in 1500ms
```
> ✅ **The Website is now live!**

---

### Step 4: Open Your Browser!

Open Google Chrome, Edge, or Firefox and go to:
👉 **[http://localhost:3000](http://localhost:3000)**

You will see the **MANAS — Computational Brain Disease Mapping** web interface!

---

## 🧪 3. Step-by-Step Website Testing Checklist

Once the website opens in your browser, test each section to verify everything is working smoothly:

| Page / Feature | URL to Visit | What to Look For |
|---|---|---|
| **1. Executive Dashboard** | `http://localhost:3000` | Header with MANAS logo, quick metric cards, navigation bar, research disclaimer banner. |
| **2. Regional Mapping** | `http://localhost:3000/regions` | Canonical Allen Reference Atlas (ARA) structures, anatomical hierarchy, and regional mapping table. |
| **3. Biomarkers & Statistics** | `http://localhost:3000/biomarkers` | Summary of pTau ($pTau_{181}$, AT8), amyloid beta ($A\beta_{42}$), composite Z-scores, and Braak staging. |
| **4. Analysis Explorer** | `http://localhost:3000/analyses` | Regional benchmark run `MANAS-AD-2026-00001` showing 4 tested regions (TCx, PCx, FWM, HIP) with FDR-adjusted p-values and effect sizes. |
| **5. Literature Concordance** | `http://localhost:3000/literature` | Benchmark comparison against published landmark literature (Braak 1991, Miller 2017, Jack 2018). |
| **6. Reproducibility & Provenance** | `http://localhost:3000/reproducibility` | Exact SHA-256 pipeline hash, Python version, platform configuration, and download audit trail. |
| **7. Interactive API Documentation** | `http://localhost:8000/api/docs` | Swagger UI showing live interactive endpoints (`/api/health`, `/api/analyses`, `/api/regions`). Click **Try it out** to execute live queries. |

---

## 🐳 4. Deploying with Docker (Production Grade, Single Command)

When you are ready to bundle everything together like a commercial website behind an Nginx gateway on port 80:

### Step 1: Install Docker Desktop (if not already installed)
Download and install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/). Make sure Docker Desktop is open and running.

### Step 2: Prepare Environment File
In your terminal, copy the production template:

```powershell
cd C:\Users\abhinav\.gemini\antigravity-ide\scratch\manas
copy .env.production.example .env.production
```

### Step 3: Run the Automated Deployment Script
We created a 1-click script that does everything for you:

```powershell
.\scripts\deploy.ps1
```
*(Or on Linux / macOS: `chmod +x scripts/deploy.sh && ./scripts/deploy.sh`)*

**What this script does automatically:**
1. Verifies Docker engine is active.
2. Builds the optimized Next.js frontend standalone container.
3. Builds the secure, multi-stage Python backend container.
4. Starts PostgreSQL with automated healthchecks.
5. Launches Nginx as the reverse proxy gateway.
6. Automatically checks `http://localhost/api/health` until all services report green.

Once finished, simply open:
👉 **[http://localhost](http://localhost)** (No port number needed — it serves on standard web port 80!)

---

## ☁️ 5. Deploying to the Public Internet (Real Cloud Website)

To let colleagues or the public access your website with a real domain (e.g. `https://your-manas-site.com`):

### Standard Cloud Server (DigitalOcean / AWS Lightsail / Linode / Hetzner)
This is the most standard, cost-effective way ($5 to $10/month):

1. **Create a Cloud Server**:
   - Go to [DigitalOcean](https://www.digitalocean.com) or [AWS Lightsail](https://aws.amazon.com/lightsail/).
   - Choose **Ubuntu 24.04 LTS** (2 GB RAM, 1 vCPU is plenty).
2. **Connect via SSH**:
   ```bash
   ssh root@YOUR_SERVER_IP
   ```
3. **Install Docker on the Server** (Run this single command):
   ```bash
   curl -fsSL https://get.docker.com | sh
   ```
4. **Copy Your MANAS Project to the Server**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/manas.git /opt/manas
   cd /opt/manas
   ```
5. **Run the Production Deploy Script**:
   ```bash
   cp .env.production.example .env.production
   chmod +x scripts/deploy.sh
   ./scripts/deploy.sh
   ```
6. **Set up Free SSL (Green Padlock / HTTPS)**:
   Point your domain's DNS A-record to `YOUR_SERVER_IP`, then run:
   ```bash
   sudo apt-get install -y certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```
   Certbot will automatically configure HTTPS in Nginx and renew it forever!

---

## 🛠️ 6. Useful Maintenance & Management Commands

### Stop the Website
- **If running locally in terminals**: Press `Ctrl + C` in both terminal windows.
- **If running in Docker**:
  ```powershell
  docker compose -f docker-compose.prod.yml down
  ```

### View Live Logs (Docker)
```powershell
# View all logs live
docker compose -f docker-compose.prod.yml logs -f

# View only backend errors
docker compose -f docker-compose.prod.yml logs -f backend
```

### Back Up the Database
```powershell
# Local SQLite backup:
copy data\manas.db data\backups\manas_backup_%date%.db

# Docker PostgreSQL automated backup:
docker exec -t manas_db_prod pg_dump -U manas manas > data/backups/pg_backup.sql
```

---

## ❓ Frequently Asked Questions for First Timers

### Q: "It says port 8000 or port 3000 is already in use!"
**Fix**: Another program is using that port. You can find and close it:
```powershell
# Find what's using port 8000
netstat -ano | findstr :8000
# Kill process by PID (replace 12345 with the PID number in the rightmost column)
taskkill /F /PID 12345
```

### Q: "How do I run tests to make sure no code is broken?"
```powershell
python -m pytest tests/ -v
```
All 17 tests will run and report `17 passed (100%)`.

### Q: "Is my data preserved when I shut down the website?"
**Yes!**
- In local mode, everything is safely saved inside `data/manas.db`.
- In Docker mode, PostgreSQL data is safely saved in the persistent Docker volume `manas_pgdata_prod`.

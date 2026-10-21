# MANAS (मनस्) — Production Deployment Guide

This guide details instructions for deploying the **MANAS Computational Brain Disease Mapping Platform** into production environments.

---

## 1. Production Architecture Overview

```mermaid
graph TD
    Client[Web Browser / API Client] -->|Port 80 / 443| Nginx[Nginx Gateway Ingress]
    Nginx -->|/api/*| Backend[FastAPI Backend :8000]
    Nginx -->|/*| Frontend[Next.js 14 Standalone :3000]
    Backend -->|SQLAlchemy Connection Pool| Postgres[(PostgreSQL 16 Database :5432)]
    Backend -->|File System| Storage[Persistent Raw Data & Analysis Reports]
```

### Key Security & Performance Architecture:
- **Unified Ingress**: Nginx serves as the single reverse proxy gateway, eliminating cross-origin resource sharing (CORS) complications in production.
- **Multi-Stage Container Builds**: Both Backend and Frontend use multi-stage Docker builds running under dedicated non-root users (`manas` and `nextjs`).
- **Healthchecks**: Built-in container healthchecks monitor service responsiveness with automated self-healing.
- **Persistent Data Volumes**: Named volumes guarantee safe storage for the PostgreSQL database (`manas_pgdata_prod`) and analysis reports (`manas_data_prod`).

---

## 2. Quick Production Deployment (Docker Compose)

### Prerequisites
- Docker Engine 24.0+
- Docker Compose v2.20+

### Step 1: Configure Environment Variables
Copy the production environment template:
```bash
cp .env.production.example .env
```
Edit `.env` and set a strong database password and secret key:
```env
POSTGRES_USER=manas_admin
POSTGRES_PASSWORD=your_ultra_secure_password_here
POSTGRES_DB=manas_prod
SECRET_KEY=your_random_secret_token_here
```

### Step 2: Execute Automated Deployment
Run the automated deployment script:
```bash
# On Linux / macOS:
chmod +x scripts/deploy.sh
./scripts/deploy.sh

# On Windows PowerShell:
.\scripts\deploy.ps1
```

Or deploy manually with Docker Compose:
```bash
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

### Step 3: Verify Endpoints
- **Frontend Dashboard**: `http://<your-server-ip>/`
- **Backend API Docs**: `http://<your-server-ip>/api/docs`
- **Health Check**: `http://<your-server-ip>/api/health`

---

## 3. Standalone Deployment (Without Docker)

For deployment on bare-metal or Virtual Machines (Ubuntu 22.04 / 24.04 LTS):

### A. Install System Packages
```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv nodejs npm postgresql postgresql-contrib nginx
```

### B. Configure PostgreSQL
```sql
sudo -u postgres psql
CREATE DATABASE manas;
CREATE USER manas WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE manas TO manas;
\q
```

### C. Backend Service Setup (systemd)
Create `/etc/systemd/system/manas-backend.service`:
```ini
[Unit]
Description=MANAS Backend FastAPI Service
After=network.target postgresql.service

[Service]
User=ubuntu
WorkingDirectory=/opt/manas
Environment="PATH=/opt/manas/venv/bin"
Environment="DATABASE_URL=postgresql://manas:secure_password@localhost:5432/manas"
Environment="ENVIRONMENT=production"
ExecStart=/opt/manas/venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start backend:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now manas-backend
```

### D. Frontend Service Setup (PM2 or systemd)
```bash
cd /opt/manas/frontend
npm ci
npm run build
npm install -g pm2
pm2 start server.js --name "manas-frontend"
pm2 save
pm2 startup
```

### E. Configure Nginx Reverse Proxy
Copy [nginx/conf.d/manas.conf](file:///C:/Users/abhinav/.gemini/antigravity-ide/scratch/manas/nginx/conf.d/manas.conf) to `/etc/nginx/sites-available/manas` and link to `/etc/nginx/sites-enabled/`:
```bash
sudo ln -s /etc/nginx/sites-available/manas /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

---

## 4. SSL / TLS Setup with Let's Encrypt (HTTPS)

To enable free automatic HTTPS certificates:
```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.org -d www.yourdomain.org
```
Certbot will automatically configure SSL certificates and renew them via cron.

---

## 5. Automated Backups & Maintenance

### Take an Immediate Database Backup
```bash
# Docker environment:
./scripts/backup_db.sh

# Or manual PostgreSQL dump:
docker exec manas_db_prod pg_dump -U manas manas > ./backups/manas_backup_$(date +%Y%m%d).sql
```

### Setting Up a Daily Backup Cron Job
Add to `crontab -e`:
```bash
0 3 * * * /opt/manas/scripts/backup_db.sh > /dev/null 2>&1
```

---

## 6. Zero-Downtime Updates

To deploy new code changes without interrupting live analyses:
```bash
git pull origin main
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d --no-deps backend frontend
```
Nginx will continue routing requests seamlessly while new containers spin up and pass their health checks.

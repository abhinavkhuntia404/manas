# MANAS Deployment Guide: Vercel + Upstash + Supabase

This guide provides step-by-step instructions to deploy the **MANAS (मनस्)** platform using:
- **GitHub**: Repository hosting under `@abhinavkhuntia404`
- **Vercel**: Next.js frontend deployment with automatic CI/CD
- **Supabase ("superdata")**: Managed cloud PostgreSQL database
- **Upstash**: Serverless Redis caching and rate-limiting queue

---

## Architecture Overview

```
+-----------------------------------------------------------+
|                    CLIENT BROWSER                         |
+-----------------------------+-----------------------------+
                              |
                              v
             +---------------------------------+
             |        VERCEL (Frontend)        |
             |       Next.js 16 App Router     |
             |  URL: https://manas.vercel.app  |
             +----------------+----------------+
                              |
                              v
             +---------------------------------+
             |   FASTAPI BACKEND SERVICE       |
             |    (Render / Railway / VPS)     |
             |  URL: https://api.manas-ad.org  |
             +--------+---------------+--------+
                      |               |
                      v               v
    +--------------------+     +---------------------+
    |     SUPABASE       |     |       UPSTASH       |
    |  Cloud PostgreSQL  |     |  Serverless Redis   |
    |  (Database Engine) |     |  (Cache & Limits)   |
    +--------------------+     +---------------------+
```

---

## Step 1: Push Code to GitHub

Your local repository is already initialized and all 105 project files are committed to the `main` branch.

1. Open your browser and go to: **[https://github.com/new](https://github.com/new)**
2. Set **Repository name**: `manas`
3. Choose **Public** or **Private**
4. **Do NOT check** "Add a README", "Add .gitignore", or "Choose a license" (the project already has all of these).
5. Click **Create repository**.
6. Open your terminal in `scratch/manas` and run:
   ```bash
   git push -u origin main
   ```
   *(Your remote origin is already pre-configured to `https://github.com/abhinavkhuntia404/manas.git`)*

---

## Step 2: Set Up Supabase Database ("superdata")

Supabase provides the managed PostgreSQL database that replaces local SQLite for multi-user production.

1. Sign up / Log in to **[https://supabase.com](https://supabase.com)**.
2. Click **New Project**:
   - **Name**: `manas-db`
   - **Database Password**: Choose a strong password and save it.
   - **Region**: Choose the region closest to your users (e.g., `us-east-1` or `ap-south-1`).
3. Once the database is provisioned, go to **Project Settings** -> **Database**.
4. Under **Connection string**, select **URI**:
   - For direct connections:
     ```text
     postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
     ```
   - For serverless / connection pooler (recommended for cloud):
     ```text
     postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
     ```
5. **Initialize Schema & Seed Data**:
   From your local terminal, run the automated migration and ingestion script pointing to Supabase:
   ```bash
   $env:DATABASE_URL="postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres"
   python scripts/populate_database.py
   ```
   *Alternative*: Go to the **SQL Editor** in the Supabase dashboard, paste the contents of `backend/database/init.sql`, and click **Run**.

---

## Step 3: Set Up Upstash Redis

Upstash provides low-latency caching for brain region hierarchy, ontology lookups, and analysis results.

1. Sign up / Log in to **[https://upstash.com](https://upstash.com)**.
2. Click **Create Database**:
   - **Name**: `manas-cache`
   - **Type**: Regional (select the same region as Supabase / Backend)
   - **Eviction**: Enabled (e.g., `volatile-lru`)
3. On the database details page, copy your credentials:
   - **REST URL**: `UPSTASH_REDIS_REST_URL` (`https://...upstash.io`)
   - **REST Token**: `UPSTASH_REDIS_REST_TOKEN` (`AX...`)
   - **Redis URI**: `REDIS_URL` (`rediss://default:...@...upstash.io:6379`)

---

## Step 4: Deploy the FastAPI Backend

Deploy the FastAPI backend to a service like **Render** or **Railway** (or Fly.io / AWS):

### Using Render:
1. Go to **[https://render.com](https://render.com)** -> **New** -> **Web Service**.
2. Connect your GitHub repository `abhinavkhuntia404/manas`.
3. Configure settings:
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4. Set Environment Variables:
   - `ENVIRONMENT` = `production`
   - `DATABASE_URL` = `postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres`
   - `UPSTASH_REDIS_REST_URL` = `https://[PROJECT-REF].upstash.io`
   - `UPSTASH_REDIS_REST_TOKEN` = `your_upstash_token`
   - `SECRET_KEY` = `your-secure-random-32-char-key`
   - `CORS_ORIGINS` = `https://manas.vercel.app`
5. Click **Create Web Service**. Once deployed, note your backend URL (e.g., `https://manas-api.onrender.com`).

---

## Step 5: Deploy Frontend to Vercel ("varsel")

1. Log in to **[https://vercel.com](https://vercel.com)**.
2. Click **Add New...** -> **Project**.
3. Import the GitHub repository **`abhinavkhuntia404/manas`**.
4. In the project configuration modal:
   - **Framework Preset**: `Next.js`
   - **Root Directory**: Click *Edit* and select **`frontend`**
   - **Build Command**: `next build` (default)
   - **Output Directory**: `.next` (default)
5. Under **Environment Variables**, add:
   - **Key**: `NEXT_PUBLIC_API_URL`
   - **Value**: Your backend URL from Step 4 (e.g., `https://manas-api.onrender.com`)
6. Click **Deploy**.
7. Vercel will build and assign you a production URL (e.g., `https://manas.vercel.app`).

---

## Step 6: Post-Deployment Verification

1. **Verify Health Endpoint**:
   ```bash
   curl -s https://manas-api.onrender.com/api/health
   # Expected response: {"status":"healthy","version":"1.0.0","database":"connected"}
   ```
2. **Verify Frontend UI**:
   - Open `https://manas.vercel.app` in your browser.
   - Navigate to `/datasets`, `/brain-maps`, `/brain-regions`, `/analysis-runs`, and `/evidence`.
   - Confirm all research metrics and atlas plots load dynamically from the cloud database.

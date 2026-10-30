# Deployment Guide

This guide walks you through deploying the Subscription Billing Simulator to **Render** (backend) and **Vercel** (frontend), using your existing **Supabase** PostgreSQL database.

## Prerequisites

- A [Render](https://render.com) account (free tier available)
- A [Vercel](https://vercel.com) account (free tier available)
- Your Supabase PostgreSQL connection string (already configured)
- GitHub account with the repo pushed: `orluprecious55-maker/subscription-billing-simulator`

---

## Step 1: Push your code to GitHub

```bash
cd /home/gamp/PycharmProjects/subscription-billing-simulator
git add .
git commit -m "Prepare for deployment: add Render and Vercel configs"
git push origin main
```

> ⚠️ Make sure `backend/.env` is **not** committed (it's in `.gitignore`).

---

## Step 2: Deploy the Backend on Render

### Option A: Using the render.yaml file (recommended)

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub repository
4. Render will detect the `render.yaml` file automatically
5. Click **"Apply"**

### Option B: Manual setup

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repo — select the `deploy/main` branch
4. Configure:
   - **Name**: `subscription-billing-api`
   - **Region**: Frankfurt (closest to Supabase EU-West)
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Type**: **Free**

> ⚠️ **Important**: Make sure the Root Directory is `backend` — this tells Render to run the build and start commands inside the `backend/` folder. Do NOT include `cd backend` or `backend/` in the commands.

### Environment Variables (required)

After creating the service, add these environment variables in Render dashboard:

| Variable | Value |
|---|---|
| `DATABASE_URL` | Your Supabase connection string |
| `APP_ENV` | `production` |
| `DEMO_MODE` | `true` |
| `RETRY_SCHEDULE` | `3,7,14` |
| `CORS_ORIGINS` | Your Vercel frontend URL (e.g., `https://your-app.vercel.app`) |

> ⚠️ **Important**: After deploying the frontend on Vercel, update `CORS_ORIGINS` on Render with the actual Vercel URL.

Once deployed, Render will give you a URL like `https://subscription-billing-api.onrender.com`. Note this URL — you'll need it for the frontend.

---

## Step 3: Deploy the Frontend on Vercel

### Using the Vercel Dashboard

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **"Add New..."** → **"Project"**
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

### Environment Variables

Add this environment variable in Vercel dashboard:

| Variable | Value |
|---|---|
| `VITE_API_BASE_URL` | Your Render backend URL (e.g., `https://subscription-billing-api.onrender.com`) |

5. Click **"Deploy"**

Vercel will give you a URL like `https://subscription-billing-simulator.vercel.app`.

---

## Step 4: Update CORS on Render

After deploying the frontend:

1. Go to your Render service → **Environment** tab
2. Update `CORS_ORIGINS` to your Vercel URL
3. Wait for Render to redeploy automatically

---

## Step 5: Load Seed Data

After the backend is deployed, you need to seed demo data. Run this from your local machine:

```bash
cd backend
# Temporarily point to the deployed backend's database
export DATABASE_URL="your-supabase-connection-string"
python -m app.seed_data
```

Or use the API directly from the deployed frontend — create a few plans and customers through the UI for your demo.

---

## Accessing Your Deployed App

- **Frontend**: `https://your-app.vercel.app`
- **Backend API**: `https://your-api.onrender.com`
- **API Docs**: `https://your-api.onrender.com/docs`

Your team can now access the app from any device, even when your computer is off!

---

## Free Tier Limitations

- **Render Free Tier**: The backend will **sleep** after 15 minutes of inactivity. The first request after sleeping takes ~30 seconds to wake up. This is fine for demos.
- **Vercel Free Tier**: No sleep issue; the frontend is always fast.
- **Supabase Free Tier**: Database persists indefinitely; no sleep.

### To avoid Render sleeping

For a live presentation, visit the backend URL a few minutes before to wake it up. Alternatively, upgrade to Render's paid tier (~$7/month) to keep it always-on.

---

## Redeployment

Any time you push changes to GitHub:
- **Render**: Automatically rebuilds and deploys the backend
- **Vercel**: Automatically rebuilds and deploys the frontend

No manual intervention needed!

---

## Troubleshooting

### Backend deployment fails on Render

**Check the build logs** in your Render dashboard. Common causes:

1. **Wrong Root Directory**: If set to `backend`, the Build Command should be `pip install -r requirements.txt` (not `pip install -r backend/requirements.txt`). The Start Command should be `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT` (not `cd backend && ...`).

2. **Missing DATABASE_URL**: Ensure you've added the `DATABASE_URL` environment variable in Render's Environment tab with your Supabase connection string.

3. **Database migration fails**: If the database already has tables from a previous deployment, Alembic may fail. Check the logs for the exact error. You may need to reset your Supabase database or check the Alembic version table.

4. **Connection timeout**: Supabase Pooler (port 6543) works with Render. If you see connection errors, try using the direct connection port (5432) from your Supabase dashboard.

### Frontend can't connect to backend

1. **CORS error**: Update `CORS_ORIGINS` on Render to include your Vercel frontend URL.
2. **Wrong API URL**: Verify `VITE_API_BASE_URL` on Vercel matches your Render backend URL exactly (no trailing slash).

### Render free tier sleeping

The backend sleeps after 15 minutes of inactivity. Visit `https://your-api.onrender.com/health` to wake it up before your presentation.

# Evo-AI Deployment Guide

Complete guide for deploying Evo-AI to production.

---

## Architecture Overview

```
Frontend (Vercel)
    ↓
Backend API (Railway/Render/Cloud Run)
    ↓
PostgreSQL Database (Cloud SQL/Neon/Supabase)
    ↓
Redis (Upstash/Redis Cloud)
```

---

## Prerequisites

- GitHub account
- Vercel account (free tier works)
- Railway/Render account (for backend)
- Database provider account (Neon/Supabase)
- LLM API keys (Anthropic/OpenAI)

---

## Step 1: Prepare Repository

### Initialize Git

```bash
cd evo-ai

# Initialize repository
git init
git add .
git commit -m "Initial commit: Evo-AI Platform - Multi-agent evolutionary experimentation system"

# Create GitHub repository (via GitHub CLI or web)
gh repo create evo-ai --public --source=. --remote=origin --push
```

### Create `.gitignore`

Ensure your `.gitignore` includes:

```gitignore
# Environment variables
.env
.env.local
.env.production

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
.venv/

# Node
node_modules/
.next/
out/
build/
*.log

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Database
*.db
*.sqlite

# Docker
.dockerignore

# Secrets
*.pem
*.key
```

---

## Step 2: Deploy Database

### Option A: Neon (Recommended - Free Tier)

1. Go to https://neon.tech
2. Create new project: "evo-ai-production"
3. Copy connection string:
   ```
   postgresql://user:pass@host.neon.tech/evo_ai?sslmode=require
   ```
4. Enable connection pooling

### Option B: Supabase

1. Go to https://supabase.com
2. Create new project
3. Get connection string from Settings > Database
4. Use connection pooler URL

### Option C: Railway PostgreSQL

1. In Railway dashboard
2. Add PostgreSQL plugin
3. Copy `DATABASE_URL`

---

## Step 3: Deploy Redis

### Option A: Upstash (Recommended - Free Tier)

1. Go to https://upstash.com
2. Create Redis database
3. Copy connection URL:
   ```
   redis://default:password@host.upstash.io:6379
   ```

### Option B: Redis Cloud

1. Go to https://redis.com/cloud
2. Create database
3. Get connection string

---

## Step 4: Deploy Backend

### Option A: Railway (Recommended)

1. **Connect Repository**
   ```bash
   # Install Railway CLI
   npm i -g @railway/cli

   # Login
   railway login

   # Link project
   railway init
   ```

2. **Configure Service**
   - Go to Railway dashboard
   - Create new project: "evo-ai"
   - Add service from GitHub repo
   - Select `backend` directory

3. **Set Environment Variables**

   In Railway dashboard, add:

   ```bash
   # Database
   DATABASE_URL=postgresql+asyncpg://user:pass@host.neon.tech/evo_ai?sslmode=require

   # Redis
   REDIS_URL=redis://default:pass@host.upstash.io:6379

   # LLM APIs
   ANTHROPIC_API_KEY=sk-ant-...
   OPENAI_API_KEY=sk-...

   # App Config
   ENVIRONMENT=production
   LOG_LEVEL=INFO
   PORT=8000

   # CORS (update after frontend deploy)
   CORS_ORIGINS=https://your-frontend.vercel.app
   ```

4. **Configure Build**

   Create `railway.json` in backend directory:

   ```json
   {
     "$schema": "https://railway.app/railway.schema.json",
     "build": {
       "builder": "DOCKERFILE",
       "dockerfilePath": "Dockerfile"
     },
     "deploy": {
       "startCommand": "alembic upgrade head && gunicorn evo_ai.api.app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT",
       "restartPolicyType": "ON_FAILURE",
       "restartPolicyMaxRetries": 10
     }
   }
   ```

5. **Deploy**
   ```bash
   railway up
   ```

6. **Get Backend URL**
   - Railway will provide a URL like: `https://evoai-backend.railway.app`
   - Save this for frontend configuration

### Option B: Render

1. Go to https://render.com
2. New Web Service
3. Connect GitHub repository
4. Configure:
   - Name: evo-ai-backend
   - Environment: Docker
   - Dockerfile Path: backend/Dockerfile
   - Plan: Free/Starter

5. Add environment variables (same as Railway above)

6. Deploy

### Option C: Google Cloud Run

```bash
# Build and push image
cd backend
gcloud builds submit --tag gcr.io/PROJECT_ID/evoai-backend

# Deploy
gcloud run deploy evoai-backend \
  --image gcr.io/PROJECT_ID/evoai-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=...,ANTHROPIC_API_KEY=...
```

---

## Step 5: Run Database Migrations

After backend is deployed, run migrations:

```bash
# SSH into Railway/Render
railway run bash  # or Render shell

# Run migrations
alembic upgrade head
```

Or create a one-time job in Railway/Render dashboard.

---

## Step 6: Deploy Frontend

### Vercel Deployment

1. **Install Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **Prepare Frontend**
   ```bash
   cd frontend

   # Create production environment file
   echo "NEXT_PUBLIC_API_URL=https://your-backend.railway.app" > .env.production
   ```

3. **Deploy**
   ```bash
   vercel --prod
   ```

4. **Configure Project Settings**

   In Vercel dashboard:
   - Go to Project Settings
   - Environment Variables:
     ```
     NEXT_PUBLIC_API_URL = https://your-backend.railway.app
     NODE_ENV = production
     ```
   - Build & Development Settings:
     - Framework Preset: Next.js
     - Root Directory: frontend
     - Build Command: `npm run build`
     - Output Directory: `.next`

5. **Enable Auto-Deploy**
   - Settings > Git
   - Enable automatic deployments from `main` branch

6. **Custom Domain (Optional)**
   - Settings > Domains
   - Add your custom domain
   - Configure DNS (Vercel provides instructions)

---

## Step 7: Update CORS Settings

After frontend is deployed:

1. Get Vercel URL: `https://evo-ai.vercel.app`

2. Update backend `CORS_ORIGINS`:
   ```bash
   # In Railway/Render dashboard
   CORS_ORIGINS=https://evo-ai.vercel.app,https://your-custom-domain.com
   ```

3. Redeploy backend

---

## Step 8: Test Deployment

### Health Check

```bash
# Backend health
curl https://your-backend.railway.app/health

# Create test campaign
curl -X POST https://your-backend.railway.app/api/campaigns \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production Test",
    "description": "Testing deployment",
    "config": {"max_rounds": 3, "variants_per_round": 5}
  }'
```

### Frontend Test

1. Visit `https://evo-ai.vercel.app`
2. Create a campaign
3. View campaign details
4. Check that API calls work

---

## Step 9: Set Up Monitoring

### Backend Monitoring

1. **Railway/Render Built-in**
   - View logs in dashboard
   - Set up log drains

2. **Sentry (Error Tracking)**
   ```bash
   pip install sentry-sdk
   ```

   Add to `backend/src/evo_ai/api/app.py`:
   ```python
   import sentry_sdk

   sentry_sdk.init(
       dsn="your-sentry-dsn",
       environment="production"
   )
   ```

3. **Datadog/New Relic (APM)**
   - Install agent
   - Configure via environment variables

### Frontend Monitoring

1. **Vercel Analytics**
   - Automatically enabled in Vercel

2. **Sentry**
   ```bash
   npm install @sentry/nextjs
   ```

   Configure in `next.config.js`

---

## Step 10: Set Up CI/CD

### GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install poetry
          poetry install
      - name: Run tests
        run: |
          cd backend
          poetry run pytest

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      - name: Install and test
        run: |
          cd frontend
          npm ci
          npm test

  deploy-backend:
    needs: [test-backend]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Railway
        run: |
          npm i -g @railway/cli
          railway up
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}

  deploy-frontend:
    needs: [test-frontend]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Vercel
        run: |
          npm i -g vercel
          cd frontend
          vercel --prod --token=${{ secrets.VERCEL_TOKEN }}
        env:
          VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
```

---

## Environment Variables Checklist

### Backend

- [ ] `DATABASE_URL` - PostgreSQL connection string
- [ ] `REDIS_URL` - Redis connection string
- [ ] `ANTHROPIC_API_KEY` - Claude API key
- [ ] `OPENAI_API_KEY` - GPT API key
- [ ] `ENVIRONMENT=production`
- [ ] `LOG_LEVEL=INFO`
- [ ] `CORS_ORIGINS` - Frontend URLs

### Frontend

- [ ] `NEXT_PUBLIC_API_URL` - Backend URL
- [ ] `NODE_ENV=production`

---

## Post-Deployment

### 1. Create First Campaign

Visit your frontend and create a test campaign to ensure everything works.

### 2. Monitor Logs

```bash
# Railway
railway logs

# Render
# View in dashboard

# Vercel
vercel logs
```

### 3. Set Up Alerts

Configure alerts for:
- High error rates
- Slow response times
- Database connection issues
- API rate limits

### 4. Document URLs

Save these URLs:
- Frontend: `https://evo-ai.vercel.app`
- Backend: `https://evoai-backend.railway.app`
- Database: Connection string
- Redis: Connection string

---

## Scaling Considerations

### When to Scale

- **Database**: > 100 concurrent campaigns
  - Upgrade to paid tier
  - Enable read replicas

- **Backend**: > 1000 requests/minute
  - Increase Railway instances
  - Add load balancer

- **Redis**: > 1GB memory usage
  - Upgrade plan
  - Add Redis Cluster

### Cost Optimization

**Free Tier Usage:**
- Vercel: Unlimited frontend hosting
- Railway: $5/month credit (enough for small apps)
- Neon: 0.5GB database (enough for testing)
- Upstash: 10K commands/day

**Expected Costs (Production):**
- Frontend (Vercel): $0/month (free)
- Backend (Railway): $5-20/month
- Database (Neon): $19/month
- Redis (Upstash): $10/month
- **Total**: ~$34-50/month

---

## Troubleshooting

### Backend Won't Start

```bash
# Check logs
railway logs

# Common issues:
# 1. Missing environment variables
# 2. Database connection failed
# 3. Migration errors

# Fix migrations
railway run bash
alembic upgrade head
```

### Frontend API Errors

```bash
# Check CORS settings
# Ensure CORS_ORIGINS includes Vercel URL

# Check API URL
# NEXT_PUBLIC_API_URL must be production backend URL
```

### Database Connection Issues

```bash
# Test connection
railway run bash
python -c "from sqlalchemy import create_engine; engine = create_engine('$DATABASE_URL'); print(engine.connect())"

# Check SSL mode
# Neon requires sslmode=require
```

---

## Security Checklist

- [ ] All API keys in environment variables (not code)
- [ ] CORS properly configured
- [ ] Database uses SSL
- [ ] Redis uses TLS (production)
- [ ] Rate limiting enabled
- [ ] Input validation on all endpoints
- [ ] SQL injection protection (using ORM)
- [ ] XSS protection (React escapes by default)

---

## Backup Strategy

### Database Backups

```bash
# Neon: Automatic backups (7 days retention)
# Supabase: Automatic backups

# Manual backup
pg_dump $DATABASE_URL > backup.sql

# Restore
psql $DATABASE_URL < backup.sql
```

### Code Backups

- Git repository (GitHub)
- Tag releases: `git tag v1.0.0`

---

## Success!

Your Evo-AI platform is now live at:

- **Frontend**: https://evo-ai.vercel.app
- **Backend**: https://evoai-backend.railway.app
- **API Docs**: https://evoai-backend.railway.app/docs

Test it out and start evolving code!

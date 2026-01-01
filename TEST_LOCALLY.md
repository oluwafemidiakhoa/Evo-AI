# 🧪 Test Evo-AI Locally (Fix CORS Error)

## The Problem You're Hitting on Render

```
pydantic_settings.sources.SettingsError: error parsing value for field "cors_origins"
```

**Root Cause**: CORS_ORIGINS environment variable format is wrong in Render.

---

## ✅ Quick Fix for Render (2 minutes)

### Go to Render Dashboard

1. Open: https://dashboard.render.com
2. Select your **evo-ai** backend service
3. Click **Environment** tab
4. Find `CORS_ORIGINS` variable

### Change This Format:

**❌ WRONG (Current):**
```
CORS_ORIGINS = ["https://evo-ai-seven.vercel.app"]
```

**OR:**
```
CORS_ORIGINS = https://evo-ai-seven.vercel.app
```

**✅ CORRECT (Use This):**
```
CORS_ORIGINS = https://evo-ai-seven.vercel.app,http://localhost:3000
```

**Key Points:**
- NO square brackets `[]`
- NO quotes around the whole thing
- Comma-separated for multiple origins
- No spaces after commas

### Save and Redeploy

1. Click **Save Changes**
2. Render will auto-redeploy
3. Wait 2-3 minutes
4. Check logs: `docker-compose logs -f` equivalent on Render

---

## 🐳 Test Locally with Docker (5 minutes)

This tests the EXACT same environment as Render.

### Step 1: Verify Your .env File

Your `.env` file already has API keys. Perfect!

### Step 2: Start Docker Stack

```bash
# Start all services (PostgreSQL, Redis, Backend, Frontend)
docker-compose up -d

# Watch backend logs (to see if it starts without CORS error)
docker-compose logs -f backend
```

**What You Should See:**
```
evoai-backend  | INFO:     Started server process [1]
evoai-backend  | INFO:     Waiting for application startup.
evoai-backend  | INFO:     Application startup complete.
evoai-backend  | INFO:     Uvicorn running on http://0.0.0.0:8000
```

**If you see the CORS error**, it means docker-compose.yml has the wrong format (I just fixed it).

### Step 3: Test the API

```bash
# Health check
curl http://localhost:8002/health

# Should return:
# {"status":"healthy","version":"1.0.0"}
```

### Step 4: Test Frontend

Open browser: http://localhost:3000

### Step 5: Stop Services

```bash
# Stop everything
docker-compose down

# Stop and remove volumes (fresh start)
docker-compose down -v
```

---

## 🔍 Verify the Fix

### Check Config Parsing

The validator in `backend/src/evo_ai/config.py` line 77-83 does this:

```python
@field_validator("cors_origins", mode="before")
@classmethod
def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
    """Parse CORS origins from comma-separated string or list."""
    if isinstance(v, str):
        return [origin.strip() for origin in v.split(",")]  # Split by comma!
    return v
```

**What This Means:**

| Input Format | What `.split(",")` Returns | Result |
|--------------|---------------------------|---------|
| `https://evo-ai-seven.vercel.app,http://localhost:3000` | `['https://evo-ai-seven.vercel.app', 'http://localhost:3000']` | ✅ WORKS |
| `["https://evo-ai-seven.vercel.app"]` | `['["https://evo-ai-seven.vercel.app"]']` | ❌ INVALID URL (has brackets) |
| `https://evo-ai-seven.vercel.app` | `['https://evo-ai-seven.vercel.app']` | ✅ WORKS (single origin) |

---

## 📋 Render Environment Variables Checklist

Make sure these are set correctly in Render:

```bash
# Database (from Neon)
DATABASE_URL=postgresql://username:password@host.neon.tech/dbname?sslmode=require

# Redis (from Upstash)
REDIS_URL=redis://default:password@host.upstash.io:6379

# API Keys
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...

# App Config
SECRET_KEY=your-super-secret-32-character-key
ENVIRONMENT=production
LOG_LEVEL=INFO

# CORS (CRITICAL - Must be comma-separated!)
CORS_ORIGINS=https://evo-ai-seven.vercel.app

# S3 (MinIO or AWS)
S3_ACCESS_KEY=your-minio-access-key
S3_SECRET_KEY=your-minio-secret-key
S3_ENDPOINT=https://your-minio-endpoint.com
S3_BUCKET=evo-ai-reports
```

---

## 🚨 Common Mistakes

### 1. JSON Array Format
```bash
❌ CORS_ORIGINS=["https://evo-ai-seven.vercel.app"]
✅ CORS_ORIGINS=https://evo-ai-seven.vercel.app
```

### 2. Quoted String with JSON Inside
```bash
❌ CORS_ORIGINS='["https://evo-ai-seven.vercel.app"]'
✅ CORS_ORIGINS=https://evo-ai-seven.vercel.app
```

### 3. Spaces After Commas
```bash
❌ CORS_ORIGINS=https://site1.com, https://site2.com
✅ CORS_ORIGINS=https://site1.com,https://site2.com
```

---

## ✅ Success Indicators

### Local Docker Success:
```bash
# Backend starts without errors
docker-compose logs backend | grep "Application startup complete"

# Health endpoint works
curl http://localhost:8002/health
# {"status":"healthy","version":"1.0.0"}

# Frontend loads
open http://localhost:3000
```

### Render Deployment Success:
```bash
# Check Render logs - should see:
INFO:     Application startup complete.

# Test health endpoint:
curl https://evo-ai-nakk.onrender.com/health
# {"status":"healthy","version":"1.0.0"}

# Test CORS by opening frontend:
# https://evo-ai-seven.vercel.app
# Should load without CORS errors in browser console
```

---

## 🎯 Next Steps After Fix

Once backend is running successfully:

1. **Test Campaign Creation**
   - Open: https://evo-ai-seven.vercel.app/campaigns
   - Click "New Campaign"
   - Fill in details
   - If it works → Backend + DB + CORS all working!

2. **Run LeetCode Destroyer**
   - `python leetcode_destroyer.py`
   - Screenshot results
   - Tweet it!

3. **Create GitHub Issue Template**
   - Document this CORS fix
   - Help others who hit the same issue

---

## 📞 Still Stuck?

Check these:

1. **Render Logs**
   - Dashboard → Service → Logs tab
   - Look for the actual CORS_ORIGINS value being parsed

2. **Environment Variables**
   - Dashboard → Service → Environment tab
   - Click "Show" to reveal actual values
   - Copy-paste to verify no hidden characters

3. **Database Connection**
   - If CORS works but DB fails, check DATABASE_URL format
   - Remove `&channel_binding=require` if present (known asyncpg issue)

4. **Redis Connection**
   - Verify REDIS_URL has password if Upstash requires it
   - Format: `redis://default:password@host:6379`

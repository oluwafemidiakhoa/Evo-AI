# Render Deployment Checklist for Evo-AI Backend

## ✅ Step-by-Step Configuration

### **Step 1: Create PostgreSQL Database First**

1. In Render dashboard, click **"New +"** → **"PostgreSQL"**
2. Settings:
   - **Name**: `evo-ai-db`
   - **Database**: `evo_ai`
   - **User**: `evoai`
   - **Region**: **Virginia (US East)**
   - **Plan**: **Free**
3. Click **"Create Database"**
4. Wait for database to be created (~2 minutes)
5. **COPY** the **Internal Database URL** (looks like: `postgresql://evoai:xxx@xxx.oregon-postgres.render.com/evo_ai`)

---

### **Step 2: Get Redis URL**

**Option A: Upstash (Recommended - Free)**
1. Go to https://upstash.com
2. Sign up / Login
3. Click **"Create Database"**
4. Choose **Redis**
5. **Region**: Choose closest to Virginia
6. Click **"Create"**
7. Copy the **connection URL** (format: `rediss://default:xxx@xxx.upstash.io:xxx`)

**Option B: Redis Cloud**
1. Go to https://redis.com/try-free
2. Sign up and create database
3. Copy connection URL

---

### **Step 3: Configure Web Service**

Go to Render → **"New +"** → **"Web Service"**

#### **Basic Settings:**
- **Repository**: `https://github.com/oluwafemidiakhoa/Evo-AI`
- **Name**: `evo-ai-backend`
- **Region**: **Virginia (US East)**
- **Branch**: `main`
- **Instance Type**: **Free**

#### **Build Settings (CRITICAL):**

| Setting | Value |
|---------|-------|
| **Root Directory** | `backend` |
| **Environment** | **Docker** |
| **Dockerfile Path** | `Dockerfile` |
| **Docker Build Context** | `.` |
| **Docker Command** | `sh -c "alembic upgrade head && uvicorn evo_ai.api.app:app --host 0.0.0.0 --port $PORT"` |

#### **Health Check:**
- **Health Check Path**: `/health`

---

### **Step 4: Environment Variables**

Click **"Environment"** tab and add these variables:

| Key | Value | Notes |
|-----|-------|-------|
| `DATABASE_URL` | (Paste from Step 1) | PostgreSQL Internal URL |
| `REDIS_URL` | (Paste from Step 2) | Redis connection URL |
| `ANTHROPIC_API_KEY` | `sk-ant-api03-wocmqHfjv_E_OSYy1JwovQoPA-jSsXiwAA` | Your Anthropic key |
| `OPENAI_API_KEY` | `sk-proj-qFTyuztGSzfHyl5yimukQ87T1DXzA4eZQA` | Your OpenAI key |
| `ENVIRONMENT` | `production` | |
| `LOG_LEVEL` | `INFO` | |
| `CORS_ORIGINS` | `https://evo-ai.vercel.app` | Your Vercel URL |
| `S3_ACCESS_KEY` | `minioadmin` | Default for dev |
| `S3_SECRET_KEY` | `minioadmin` | Default for dev |
| `S3_ENDPOINT` | `http://localhost:9000` | MinIO endpoint |
| `S3_BUCKET` | `evo-ai-reports` | Bucket name |

**Note**: Replace the Vercel URL with your actual frontend URL once deployed.

---

### **Step 5: Deploy**

1. Click **"Create Web Service"** (or "Save Changes" if editing)
2. Wait for build to complete (~5-10 minutes)
3. Check **Logs** tab for any errors
4. Once deployed, your service will be at: `https://evo-ai-backend.onrender.com`

---

## 🔍 Troubleshooting Common Errors

### **Error: "Cannot find Dockerfile"**
- ✅ **Fix**: Set **Root Directory** to `backend`
- ✅ **Fix**: Set **Dockerfile Path** to `Dockerfile` (not `./backend/Dockerfile`)

### **Error: "ModuleNotFoundError: No module named 'evo_ai'"**
- ✅ **Fix**: Make sure **Docker Build Context** is set to `.`
- ✅ **Fix**: Verify Dockerfile has `PYTHONPATH=/app/src`

### **Error: "Connection to database failed"**
- ✅ **Fix**: Use **Internal Database URL** (not External)
- ✅ **Fix**: Ensure PostgreSQL database is in the same region

### **Error: "Health check failed"**
- ✅ **Fix**: Set **Health Check Path** to `/health` (not `/healthz`)
- ✅ **Fix**: Wait longer - first deploy takes 2-3 minutes to start

### **Error: "Port already in use"**
- ✅ **Fix**: Use `$PORT` environment variable in Docker Command
- ✅ **Fix**: Don't hardcode port 8000 - use: `--port $PORT`

---

## 📋 Quick Reference

### Correct Dockerfile Path Configuration:
```
Root Directory: backend
Dockerfile Path: Dockerfile
Docker Context: .
```

### Correct Docker Command:
```bash
sh -c "alembic upgrade head && uvicorn evo_ai.api.app:app --host 0.0.0.0 --port $PORT"
```

### Check Deployment Status:
1. Go to Render dashboard
2. Click on **"evo-ai-backend"**
3. Check **"Logs"** tab
4. Look for: `INFO:     Application startup complete.`

### Test Your Deployment:
```bash
curl https://your-backend-url.onrender.com/health
```

Should return:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "database": "up",
    "redis": "up"
  }
}
```

---

## ⚡ After Successful Deployment

1. **Copy your backend URL**: `https://evo-ai-backend.onrender.com`
2. **Update Vercel**:
   - Go to Vercel project settings
   - Environment Variables
   - Update `NEXT_PUBLIC_API_URL` to your Render URL
   - Redeploy frontend

3. **Update CORS**:
   - Go back to Render
   - Update `CORS_ORIGINS` environment variable
   - Add your Vercel URL: `https://evo-ai.vercel.app`
   - Service will auto-redeploy

---

## 🎉 Success Indicators

✅ Build completes without errors
✅ Service shows "Live" status (green)
✅ Health check returns 200 OK
✅ Logs show "Application startup complete"
✅ Can access `/docs` endpoint
✅ Frontend can make API calls

---

## 📞 Need Help?

If you're still getting errors, check the **Logs** tab in Render and look for the specific error message. Common issues are:

1. Missing environment variables
2. Wrong database URL format
3. Incorrect Docker paths
4. Health check timing out (needs more time)

**Free tier notes:**
- Service may sleep after 15 min of inactivity
- First request after sleep takes ~30 seconds to wake up
- Database has connection limits (95 connections max)

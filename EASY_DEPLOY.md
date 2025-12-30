# EASIEST Way to Deploy Frontend (2 Minutes)

## Why Vercel Instead of Render for Frontend?

**Render frontend deployment is complex:**
- ❌ Requires Docker configuration
- ❌ Memory issues during build
- ❌ Complicated path settings
- ❌ Longer build times

**Vercel is designed for Next.js:**
- ✅ Zero configuration
- ✅ Automatic builds
- ✅ Faster deployments
- ✅ Better performance
- ✅ Free SSL and CDN

---

## Deploy to Vercel (2 Minutes)

### Step 1: Go to Vercel

1. Visit: [vercel.com/new](https://vercel.com/new)
2. Click **"Continue with GitHub"**
3. Select your **Evo-AI** repository

### Step 2: Configure (1 click)

Vercel auto-detects Next.js settings:

**Framework Preset:** Next.js ✅ (auto-detected)

**Root Directory:** Click **"Edit"** → Type `frontend` → Done

**Build Command:** `npm run build` (auto-filled)

**Output Directory:** `.next` (auto-filled)

**Install Command:** `npm install` (auto-filled)

### Step 3: Add Environment Variable

Click **"Environment Variables"** section:

| Name | Value |
|------|-------|
| `NEXT_PUBLIC_API_URL` | `https://evo-ai-nakk.onrender.com` |

### Step 4: Deploy

Click **"Deploy"** button → Wait 2-3 minutes → Done!

You'll get a URL like:
```
https://evo-ai-xxxxx.vercel.app
```

---

## Connect Frontend to Backend

After deployment:

### Update Backend CORS

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click your backend: **evo-ai-nakk**
3. Click **"Environment"** tab
4. Find `CORS_ORIGINS` variable
5. Update to your Vercel URL:
   ```
   https://evo-ai-xxxxx.vercel.app
   ```
6. Click **"Save Changes"**

### Test It

1. Visit your Vercel URL
2. You should see the Evo-AI landing page
3. Click around - it should work!
4. Try creating a campaign

---

## How They Work Together

```
┌─────────────────────────────────┐
│  Frontend (Vercel)              │
│  https://evo-ai-xyz.vercel.app  │
│                                 │
│  - Landing page                 │
│  - Campaign forms               │
│  - Analytics dashboards         │
│  - Real-time monitoring         │
└────────────┬────────────────────┘
             │
             │ When user clicks "Create Campaign":
             │ fetch('https://evo-ai-nakk.onrender.com/api/campaigns')
             │
             ↓
┌─────────────────────────────────┐
│  Backend (Render)               │
│  https://evo-ai-nakk.onrender.com│
│                                 │
│  - API endpoints                │
│  - 5 AI Agents                  │
│  - Campaign processing          │
│  - Variant evolution            │
└────────┬────────────────────────┘
         │
         │ Save/Load data
         ↓
┌──────────────────┐
│  Neon PostgreSQL │
│  (Database)      │
└──────────────────┘
```

---

## What You'll Be Able to Do

### 1. Visit Landing Page
- Go to your Vercel URL
- See beautiful Evo-AI interface
- Navigation works

### 2. Create Campaigns
- Click "Create Campaign"
- Fill in form:
  - Name: "My First Evolution"
  - Max Rounds: 3
  - Variants per Round: 10
- Click "Create"
- Backend processes it
- You see your new campaign!

### 3. Execute Evolution Rounds
- Open a campaign
- Click "Execute Round"
- Watch in real-time:
  - Planner Agent plans strategy
  - Variant Agent creates variants
  - Scorer Agent evaluates them
  - Policy Agent selects best ones
  - Reporter Agent summarizes

### 4. View Analytics
- Charts showing performance
- Lineage trees of variants
- Agent activity logs
- All visual!

---

## Benefits

**Frontend on Vercel:**
- Instant deployments (2-3 min)
- Auto-deploys on git push
- Free SSL
- Global CDN (fast everywhere)
- Always-on (no sleeping)

**Backend on Render:**
- Docker support for Python
- Database connections
- Background workers
- AI agent processing

**Best of both worlds!**

---

## If You Still Want Render for Frontend

If you prefer to keep frontend on Render, fix the settings:

1. **Dockerfile Path:** `Dockerfile` (no "frontend/" prefix, no space)
2. **Docker Build Context Directory:** `.` (just a dot)

The issue was a space: `frontend/ Dockerfile` should be just `Dockerfile`

But honestly, **Vercel is WAY easier** for Next.js!

---

## Complete Deployment Status

After following this guide:

- ✅ Backend: `https://evo-ai-nakk.onrender.com` (already deployed)
- ✅ Frontend: `https://evo-ai-xxxxx.vercel.app` (deploy now)
- ✅ Database: Neon PostgreSQL (already configured)
- ✅ Cache: Upstash Redis (already configured)

**Everything connected and working!**

---

## Next Steps

1. **Deploy to Vercel** (2 minutes) using steps above
2. **Update backend CORS** with your Vercel URL
3. **Visit your frontend** and see it work
4. **Create a campaign** through the UI
5. **Execute rounds** and watch AI agents work
6. **Share with the world!** Tweet your live demo URL

---

## Need Help?

If Vercel deployment has any issues:
- Check that Root Directory = `frontend`
- Check that `NEXT_PUBLIC_API_URL` is set
- Check browser console (F12) for errors
- Make sure backend CORS includes your Vercel URL

**Vercel is 10x easier than Render for Next.js frontend!** 🚀

# Deploy Frontend to Render (All-in-One Render Deployment)

## Why Deploy Frontend to Render?

Keep everything in one place:
- ✅ Backend and Frontend on same platform
- ✅ Both use same free tier credits
- ✅ Easier to manage CORS (internal networking)
- ✅ Simpler environment variable management

---

## Step-by-Step: Deploy Frontend to Render

### 1. Commit Updated Frontend Dockerfile

The frontend Dockerfile has been updated for production. Make sure changes are committed:

```bash
git add frontend/Dockerfile frontend/next.config.js
git commit -m "Update frontend for Render production deployment"
git push origin main
```

### 2. Create Frontend Web Service

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository: **"Evo-AI"**

### 3. Configure Frontend Service

#### **Basic Settings:**

| Setting | Value |
|---------|-------|
| **Name** | `evo-ai-frontend` |
| **Region** | **Virginia (US East)** (same as backend!) |
| **Branch** | `main` |
| **Root Directory** | `frontend` |
| **Environment** | **Docker** |
| **Instance Type** | **Free** |

#### **Build Settings:**

| Setting | Value |
|---------|-------|
| **Dockerfile Path** | `Dockerfile` |
| **Docker Build Context Directory** | `.` |

#### **Environment Variables:**

Click **"Add Environment Variable"** and add:

| Key | Value |
|-----|-------|
| `NEXT_PUBLIC_API_URL` | `https://evo-ai-nakk.onrender.com` |
| `NODE_ENV` | `production` |
| `PORT` | `3000` |

**IMPORTANT:** Replace `evo-ai-nakk.onrender.com` with your actual backend URL!

### 4. Deploy!

1. Click **"Create Web Service"**
2. Wait for build to complete (~5-7 minutes)
3. Watch the logs for:
   ```
   ✓ Compiled successfully
   - info Loaded env from /app/.env
   ready - started server on 0.0.0.0:3000
   ```

### 5. Get Your Frontend URL

Your frontend will be deployed at:
```
https://evo-ai-frontend.onrender.com
```

(or whatever name you chose)

### 6. Update Backend CORS

**CRITICAL:** Update backend to allow frontend requests:

1. Go to backend service: **evo-ai-nakk** (or your backend name)
2. Click **"Environment"** tab
3. Update `CORS_ORIGINS`:
   ```
   https://evo-ai-frontend.onrender.com
   ```
4. Click **"Save Changes"** (backend will auto-redeploy)

---

## Test Your Deployment

### 1. Check Frontend Health

Open your frontend URL in browser:
```
https://evo-ai-frontend.onrender.com
```

You should see the Evo-AI landing page!

### 2. Check Browser Console

Press **F12** → **Console** tab

Should see NO errors. If you see CORS errors:
- Double-check backend `CORS_ORIGINS` is set correctly
- Make sure URLs match exactly (no trailing slashes)

### 3. Create a Campaign

1. Click **"Campaigns"** (or it might redirect automatically)
2. Click **"Create Campaign"**
3. Fill in the form:
   - Name: "My First Evolution"
   - Description: "Testing visual platform"
   - Max Rounds: 3
   - Variants per Round: 10
4. Click **"Create"**

If successful, you'll see the new campaign in the list!

---

## Complete Architecture

You now have:

```
┌─────────────────────────────────────────┐
│  Frontend (Render Web Service)          │
│  https://evo-ai-frontend.onrender.com   │
│  - Next.js 14 UI                        │
│  - Campaign management                  │
│  - Real-time monitoring                 │
│  - Analytics dashboards                 │
└──────────────┬──────────────────────────┘
               │ API calls
               ↓
┌─────────────────────────────────────────┐
│  Backend (Render Web Service)           │
│  https://evo-ai-nakk.onrender.com       │
│  - FastAPI                              │
│  - 5 AI Agents                          │
│  - Campaign execution                   │
│  - Variant evolution                    │
└──────┬──────────────────┬───────────────┘
       │                  │
       ↓                  ↓
  ┌─────────┐      ┌──────────────┐
  │ Neon    │      │ Upstash      │
  │ Postgres│      │ Redis        │
  └─────────┘      └──────────────┘
```

---

## Troubleshooting

### Build Fails: "npm ERR! code ELIFECYCLE"

**Fix:**
- Check that `output: 'standalone'` is set in `next.config.js` ✅ (already done)
- Verify all dependencies are in `package.json`
- Check build logs for specific error

### "Failed to fetch" in Browser

**Cause:** Backend not responding or CORS issue

**Fix:**
1. Check backend health: `https://evo-ai-nakk.onrender.com/health`
2. Wait 30 seconds if backend is sleeping (free tier)
3. Check CORS_ORIGINS in backend environment variables
4. Check browser console for specific error

### Page loads but shows error creating campaign

**Database connection issue** (the `sslmode` error we saw earlier)

**Quick Fix to Try:**
1. Go to Render → Backend → Environment
2. Update `DATABASE_URL` - remove `&channel_binding=require`:
   ```
   From:
   postgresql://neondb_owner:npg_wtYR39DPeNxj@ep-sweet-unit-a4id4r5p-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require

   To:
   postgresql://neondb_owner:npg_wtYR39DPeNxj@ep-sweet-unit-a4id4r5p-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require
   ```
3. Save and wait for redeploy

### Frontend takes 30+ seconds to load

**Cause:** Free tier services sleep after 15 minutes of inactivity

**This is normal!** First request wakes up the service. Subsequent requests are fast.

**To avoid:**
- Upgrade to paid tier ($7/month for always-on)
- Use a uptime monitor to ping every 10 minutes (like UptimeRobot)

---

## Environment Variables Reference

### Frontend Variables:

```bash
NEXT_PUBLIC_API_URL=https://evo-ai-nakk.onrender.com  # Your backend URL
NODE_ENV=production
PORT=3000  # Render sets this automatically
```

### Backend Variables (recap):

```bash
DATABASE_URL=postgresql://neondb_owner:...  # Neon PostgreSQL
REDIS_URL=rediss://default:...  # Upstash Redis
CORS_ORIGINS=https://evo-ai-frontend.onrender.com  # Your frontend URL
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
SECRET_KEY=your-32-char-secret
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_ENDPOINT=http://localhost:9000
S3_BUCKET=evo-ai-reports
ENVIRONMENT=production
LOG_LEVEL=INFO
```

---

## Update README with Live URLs

After successful deployment, update your [README.md](README.md):

```markdown
## 🌐 Live Demo

**Frontend**: https://evo-ai-frontend.onrender.com
**Backend API**: https://evo-ai-nakk.onrender.com

- 📚 **API Docs**: https://evo-ai-nakk.onrender.com/api/docs
- 💚 **Health Check**: https://evo-ai-nakk.onrender.com/health
- 🎨 **Web Interface**: https://evo-ai-frontend.onrender.com
```

---

## Success! What You Can Do Now

### Visual Platform Features:

1. **Campaign Management**
   - Create campaigns with visual forms
   - Configure evolution parameters
   - Set objectives and evaluators

2. **Real-Time Execution**
   - Execute rounds with progress bars
   - Watch variants being created
   - See agent activity in real-time

3. **Lineage Visualization**
   - See variant family trees
   - Track parent-child relationships
   - Visualize evolution over generations

4. **Analytics Dashboards**
   - Performance charts
   - Selection rate graphs
   - Top variant rankings
   - Agent activity timelines

5. **Full Observability**
   - Trace IDs for debugging
   - Agent logs and activity
   - Error tracking
   - Performance metrics

---

## Share Your Platform!

Your multi-agent AI evolution platform is now LIVE! 🚀

**Share it:**
- Tweet the frontend URL
- Add to your portfolio
- Demo to potential employers/investors
- Share on LinkedIn

**Show off these features:**
- 5 AI agents working together
- Visual lineage tracking
- Real-time evolution monitoring
- Production-ready observability
- Clean architecture

---

## Free Tier Limits

Both services on Render free tier:

- **Frontend**: 750 hours/month (enough for 24/7 if only one service)
- **Backend**: 750 hours/month
- **Combined**: You get 750 hours total shared across all free services
- **Bandwidth**: 100GB/month
- **Sleep after**: 15 minutes of inactivity

**Note:** With 2 free services, they'll sleep after inactivity. First request takes ~30s to wake up. Consider upgrading to $7/month for always-on.

---

## Next: Optimize Performance

Once deployed, you can:

1. **Add Caching**: Use Redis for campaign data
2. **Optimize Images**: Add proper image domains to `next.config.js`
3. **Add Analytics**: Integrate Vercel Analytics or Google Analytics
4. **Custom Domain**: Point your domain to Render
5. **CI/CD**: Auto-deploy on git push (already enabled!)

---

## 🎉 Congratulations!

You now have a FULLY DEPLOYED multi-agent AI platform with:
- ✅ Visual user interface
- ✅ Backend API
- ✅ Database (PostgreSQL)
- ✅ Cache (Redis)
- ✅ Full observability
- ✅ Production-ready architecture

**"People can see stuff now!"** 👀

# Deploy Evo-AI Frontend to Vercel

## Quick Deploy (5 minutes)

### Step 1: Push to GitHub (if not already done)

Make sure your latest code is pushed to GitHub:

```bash
git add .
git commit -m "Prepare frontend for Vercel deployment"
git push origin main
```

### Step 2: Deploy to Vercel

1. Go to [vercel.com](https://vercel.com)
2. Click **"Sign Up"** or **"Login"** with GitHub
3. Click **"Add New Project"**
4. Import your GitHub repository: `Evo-AI`
5. Configure project settings:

#### **Framework Preset**: Next.js

#### **Root Directory**: `frontend` (IMPORTANT!)

#### **Build Settings**:
- **Build Command**: `npm run build`
- **Output Directory**: `.next` (default)
- **Install Command**: `npm install`

#### **Environment Variables** (Click "Add" for each):

| Key | Value |
|-----|-------|
| `NEXT_PUBLIC_API_URL` | `https://evo-ai-nakk.onrender.com` |
| `NODE_ENV` | `production` |

6. Click **"Deploy"**

### Step 3: Wait for Build (2-3 minutes)

Vercel will:
- Install dependencies
- Build Next.js application
- Deploy to global CDN
- Provide you with a URL like: `https://evo-ai-xxxxx.vercel.app`

### Step 4: Update Backend CORS

After deployment, update your Render backend environment variables:

1. Go to Render dashboard → `evo-ai-backend`
2. Click **"Environment"** tab
3. Update `CORS_ORIGINS` variable:
   ```
   https://your-vercel-url.vercel.app
   ```
4. Save (backend will auto-redeploy)

---

## Expected Result

Once deployed, you'll have:

- **Frontend**: `https://evo-ai-xxxxx.vercel.app`
- **Backend API**: `https://evo-ai-nakk.onrender.com`
- **API Docs**: `https://evo-ai-nakk.onrender.com/api/docs`

The frontend will connect to your backend and you can:

1. **Create Campaigns** - Visual form to configure AI experiments
2. **Execute Rounds** - Watch agents evolve code in real-time
3. **View Lineage Tree** - See variant evolution visually
4. **Monitor Agents** - Track all 5 AI agents (Planner, Variant, Scorer, Policy, Reporter)
5. **View Analytics** - Charts and graphs of performance metrics

---

## Troubleshooting

### Build fails with TypeScript errors

Already handled! The `next.config.js` has:
```javascript
typescript: {
  ignoreBuildErrors: true,
}
```

### "API request failed" in frontend

**Check**:
1. Backend is running: `https://evo-ai-nakk.onrender.com/health`
2. Environment variable is set correctly in Vercel
3. CORS is configured in Render backend

**Fix**:
- Go to Vercel → Project Settings → Environment Variables
- Verify `NEXT_PUBLIC_API_URL` is set
- Redeploy: Deployments → Click "..." → Redeploy

### Can't access Render backend

**Check**:
1. Render service is "Live" (not sleeping)
2. Health endpoint returns 200: `curl https://evo-ai-nakk.onrender.com/health`

**Note**: Free tier services sleep after 15 min inactivity. First request after sleep takes ~30 seconds.

---

## Alternative: Deploy to Render Static Site

If you prefer to keep everything on Render:

1. In Render dashboard, click **"New +"** → **"Static Site"**
2. Connect your GitHub repo
3. Settings:
   - **Name**: `evo-ai-frontend`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `.next`
   - **Environment Variables**:
     - `NEXT_PUBLIC_API_URL` = `https://evo-ai-nakk.onrender.com`

**Note**: Render static sites don't support Next.js server-side features. Vercel is recommended for Next.js.

---

## After Successful Deployment

### Update README

Add frontend URL to README.md:

```markdown
## Live Demo

- **Frontend**: https://evo-ai-xxxxx.vercel.app
- **Backend API**: https://evo-ai-nakk.onrender.com
- **API Docs**: https://evo-ai-nakk.onrender.com/api/docs
```

### Test the Platform

1. Open your Vercel URL
2. Click **"Create Campaign"**
3. Fill in the form:
   - Name: "My First Evolution"
   - Description: "Testing the platform"
   - Max Rounds: 3
   - Variants per Round: 5
4. Click **"Create"**
5. Click **"Execute Round"** to start evolution
6. Watch the magic happen!

---

## Custom Domain (Optional)

Want a custom domain like `evo-ai.yourdomain.com`?

1. In Vercel, go to Project Settings → Domains
2. Add your domain
3. Update DNS records as instructed
4. Update Render `CORS_ORIGINS` to include your custom domain

---

## Success Indicators

After deployment, you should see:

- [OK] Vercel deployment shows "Ready"
- [OK] Can access frontend at Vercel URL
- [OK] Landing page loads with campaign list
- [OK] Can create new campaigns
- [OK] Backend API responds (check browser console)
- [OK] No CORS errors in browser console

---

## Next Steps

Once deployed:

1. **Create your first campaign** through the UI
2. **Execute rounds** and watch variants evolve
3. **View analytics** - see performance metrics
4. **Check lineage tree** - visualize code evolution
5. **Monitor agents** - track AI agent activity
6. **Share with the world!** - Show off your multi-agent AI platform

---

## Need Help?

If deployment fails, check:

1. **Vercel Deployment Logs** - Click on failed deployment → View logs
2. **Browser Console** - F12 → Console tab for errors
3. **Backend Logs** - Render dashboard → evo-ai-backend → Logs
4. **Network Tab** - F12 → Network tab to see API calls

Common issues:
- Wrong root directory (must be `frontend`)
- Missing environment variable (`NEXT_PUBLIC_API_URL`)
- Backend CORS not configured
- Backend sleeping (free tier)

# Quick Neon PostgreSQL Setup for Evo-AI

## Step-by-Step:

1. **Go to Neon**: https://neon.tech

2. **Sign Up**: Click "Sign up" → Use GitHub (easiest)

3. **Create Project**:
   - Click **"Create a project"**
   - Project name: `evo-ai`
   - Region: **US East (Ohio)** (or closest to your Render region)
   - Compute size: Keep default (0.25 CU)
   - Click **"Create Project"**

4. **Get Connection String**:
   - You'll see a connection string immediately
   - Click **"Connection string"** tab
   - Copy the **Pooled connection** string (recommended)

   Should look like:
   ```
   postgresql://neondb_owner:npg_xxx@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```

5. **Add to Render**:
   - Go to your Render web service
   - Click **"Environment"** tab
   - Add variable:
     - Key: `DATABASE_URL`
     - Value: (paste Neon connection string)
   - Click **"Save Changes"**

6. **Done!** Render will auto-redeploy with the new database

---

## Connection String Format:

Neon provides two types of connection strings:

### **Pooled (Recommended for Render)**:
```
postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
```
✅ Use this one - it has built-in connection pooling

### **Direct**:
```
postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
```

---

## Verify It Works:

After deploying, check Render logs for:
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO:     Application startup complete.
```

---

## Free Tier Limits:

- **Storage**: 0.5 GB (more than enough)
- **Compute**: 0.25 CU always-on
- **Branches**: 10 (for development)
- **No credit card required**
- **No hibernation**

Your Evo-AI database will use ~10-50 MB, so you have plenty of room!

---

## Troubleshooting:

### Error: "SSL required"
✅ Make sure connection string includes `?sslmode=require`

### Error: "Connection refused"
✅ Check you're using the **Pooled** connection string
✅ Verify region matches (US East)

### Error: "Database doesn't exist"
✅ Neon creates default database called `neondb`
✅ Update your Alembic config if needed

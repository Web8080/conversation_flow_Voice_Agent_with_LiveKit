# Vercel Deployment Guide

## Step-by-Step Vercel Setup

### Step 1: Sign Up for Vercel

1. Go to https://vercel.com/
2. Click **"Sign Up"** or **"Log In"**
3. Choose **"Continue with GitHub"** (recommended, easiest way)
4. Authorize Vercel to access your GitHub account

### Step 2: Connect Your GitHub Repository

1. After logging in, you'll see the Vercel dashboard
2. Click **"Add New..."** button (top right)
3. Select **"Project"**
4. You'll see a list of your GitHub repositories
5. Find and select: **`conversation_flow_Voice_Agent_with_LiveKit`**
6. Click **"Import"**

### Step 3: Configure Project Settings

**Framework Preset:**
- Framework: **Next.js** (should auto-detect)
- Root Directory: `frontend` (if asked, otherwise leave as is)
- Build Command: `npm run build` (auto-detected)
- Output Directory: `.next` (auto-detected)
- Install Command: `npm install` (auto-detected)

### Step 4: Add Environment Variables

**This is the critical step!**

1. In the project configuration page, scroll down to **"Environment Variables"**
2. Click **"Add"** or **"Add Environment Variable"**
3. Add the following variables **one by one**:

#### Variable 1: NEXT_PUBLIC_LIVEKIT_URL
- **Key**: `NEXT_PUBLIC_LIVEKIT_URL`
- **Value**: `wss://voiceagent007-fnileh5c.livekit.cloud`
- **Environment**: Select **All** (Production, Preview, Development)
- Click **"Save"**

#### Variable 2: LIVEKIT_API_KEY
- **Key**: `LIVEKIT_API_KEY`
- **Value**: `APIjAbndhXSoyis`
- **Environment**: Select **All** (Production, Preview, Development)
- Click **"Save"**

#### Variable 3: LIVEKIT_API_SECRET
- **Key**: `LIVEKIT_API_SECRET`
- **Value**: `D1pm5XYaXHUJe3iiIjU7Uk5fo7n1ebU2WcBIKDy5sGRA`
- **Environment**: Select **All** (Production, Preview, Development)
- Click **"Save"**

**Important Notes:**
- `NEXT_PUBLIC_*` variables are exposed to the browser (safe for URLs)
- `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET` are server-side only (secure)
- Make sure all three are set to **All environments** (Production, Preview, Development)

### Step 5: Update Build Settings (If Needed)

**If you have a monorepo structure:**

1. Scroll to **"Root Directory"** section
2. Set Root Directory to: `frontend`
3. This tells Vercel where your Next.js app is located

**Build Settings:**
- Build Command: `cd frontend && npm run build`
- Output Directory: `frontend/.next`
- Install Command: `cd frontend && npm install`

### Step 6: Deploy

1. After adding all environment variables, scroll to the bottom
2. Click **"Deploy"** button
3. Vercel will:
   - Clone your repository
   - Install dependencies (`npm install`)
   - Build the Next.js app (`npm run build`)
   - Deploy to a production URL

### Step 7: Monitor Deployment

1. You'll see a deployment log in real-time
2. Watch for any build errors
3. Once complete, you'll see:
   - ✅ **"Ready"** status
   - **Deployment URL** (e.g., `https://your-app-name.vercel.app`)

### Step 8: Test Your Deployment

1. Click on the deployment URL
2. You should see your Voice Agent UI
3. Test the connection:
   - Enter a room name
   - Click "Connect"
   - Test microphone input

---

## Troubleshooting

### Build Fails

**Error: "Cannot find module"**
- Make sure `frontend/package.json` has all dependencies
- Check that `npm install` runs successfully

**Error: "Environment variable not found"**
- Verify all three environment variables are added
- Check they're set for **All environments**
- Redeploy after adding variables

**Error: "Build command failed"**
- Check Root Directory is set to `frontend`
- Verify `frontend/package.json` exists
- Check build logs for specific errors

### Runtime Errors

**"LiveKit credentials not configured"**
- Verify environment variables are set in Vercel
- Check that variables start with correct names
- Redeploy after adding variables

**Connection fails**
- Verify `NEXT_PUBLIC_LIVEKIT_URL` is correct
- Check that `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET` are set
- Test with browser console open to see errors

---

## Updating Environment Variables

**To add or update variables later:**

1. Go to your project in Vercel dashboard
2. Click **"Settings"** tab (top navigation)
3. Click **"Environment Variables"** (left sidebar)
4. Add/Edit/Delete variables as needed
5. **Important**: Click **"Redeploy"** after changing variables
   - Or go to **"Deployments"** tab
   - Click **"..."** menu on latest deployment
   - Select **"Redeploy"**

---

## Quick Reference

**Your LiveKit Credentials:**
```
NEXT_PUBLIC_LIVEKIT_URL=wss://voiceagent007-fnileh5c.livekit.cloud
LIVEKIT_API_KEY=APIjAbndhXSoyis
LIVEKIT_API_SECRET=D1pm5XYaXHUJe3iiIjU7Uk5fo7n1ebU2WcBIKDy5sGRA
```

**Vercel Dashboard:**
- Main Dashboard: https://vercel.com/dashboard
- Project Settings: https://vercel.com/dashboard -> Your Project -> Settings
- Environment Variables: Settings -> Environment Variables

---

## Post-Deployment

After successful deployment:

1. **Save the deployment URL** - This is your production link to share with customers
2. **Test thoroughly** - Make sure all features work
3. **Share with customer** - Give them the Vercel deployment URL
4. **Monitor logs** - Check Vercel logs for any errors

---

## Custom Domain (Optional)

If you want a custom domain:

1. Go to **Settings** -> **Domains**
2. Add your custom domain
3. Follow DNS setup instructions
4. Vercel will automatically configure SSL

---

## Next Steps

Once Vercel is deployed:

1. ✅ Frontend deployed and accessible
2. ⏳ Deploy backend agent to LiveKit Cloud
3. ⏳ Connect frontend to backend agent
4. ⏳ Test end-to-end

---

## Support

- **Vercel Docs**: https://vercel.com/docs
- **Vercel Support**: https://vercel.com/support
- **LiveKit Docs**: https://docs.livekit.io/


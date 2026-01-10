# Deployment Checklist - Stage 1 Voice Agent

## ✅ Completed

1. ✅ **main.py updated** - Stage 1 simple agent (no state machine)
2. ✅ **LiveKit credentials added** to .env files
   - URL: `wss://voiceagent007-fnileh5c.livekit.cloud`
   - API Key: `APIjAbndhXSoyis`
   - API Secret: `D1pm5XYaXHUJe3iiIjU7Uk5fo7n1ebU2WcBIKDy5sGRA`
3. ✅ **OpenAI API Key configured**
4. ✅ **LLM Priority**: OpenAI primary, Ollama fallback
5. ✅ **Git repository initialized** and ready
6. ✅ **.gitignore configured** (excludes .env files)
7. ✅ **111 files ready to commit**

---

## ⏳ Next Steps (In Order)

### Step 1: Push to GitHub

```bash
cd /Users/user/Fortell_AI_Product

# Review what will be committed
git status

# Commit all files
git commit -m "Initial commit: Stage 1 Voice Agent with LiveKit integration"

# Push to GitHub
git push -u origin main
```

**If authentication errors:**
- See `GITHUB_PUSH_GUIDE.md` for help
- Use GitHub Personal Access Token
- Or configure SSH keys

**Verify:**
- Go to: https://github.com/Web8080/conversation_flow_Voice_Agent_with_LiveKit
- Check all files are there
- Verify `.env` files are NOT visible

---

### Step 2: Sign Up for Vercel

1. Go to: https://vercel.com/
2. Click **"Sign Up"** or **"Log In"**
3. Choose **"Continue with GitHub"** (recommended)
4. Authorize Vercel to access your GitHub account

---

### Step 3: Connect GitHub Repository to Vercel

1. In Vercel dashboard, click **"Add New..."** → **"Project"**
2. Find and select: **`conversation_flow_Voice_Agent_with_LiveKit`**
3. Click **"Import"**

---

### Step 4: Configure Project Settings

**Framework Preset:**
- Framework: **Next.js** (auto-detected)
- Root Directory: `frontend` (if monorepo option appears)
- Build Command: `cd frontend && npm run build` (if root directory is set)
- Output Directory: `.next` or `frontend/.next`
- Install Command: `cd frontend && npm install` (if root directory is set)

**Or if you see "Root Directory" option:**
- Set Root Directory to: `frontend`

---

### Step 5: Add Environment Variables in Vercel

**This is the CRITICAL step!**

1. Scroll down to **"Environment Variables"** section
2. Click **"Add"** or **"Add Environment Variable"**

#### Add Variable 1: NEXT_PUBLIC_LIVEKIT_URL

- **Key**: `NEXT_PUBLIC_LIVEKIT_URL`
- **Value**: `wss://voiceagent007-fnileh5c.livekit.cloud`
- **Environment**: Select **All** (Production, Preview, Development) ☑️
- Click **"Save"**

#### Add Variable 2: LIVEKIT_API_KEY

- **Key**: `LIVEKIT_API_KEY`
- **Value**: `APIjAbndhXSoyis`
- **Environment**: Select **All** (Production, Preview, Development) ☑️
- Click **"Save"**

#### Add Variable 3: LIVEKIT_API_SECRET

- **Key**: `LIVEKIT_API_SECRET`
- **Value**: `D1pm5XYaXHUJe3iiIjU7Uk5fo7n1ebU2WcBIKDy5sGRA`
- **Environment**: Select **All** (Production, Preview, Development) ☑️
- Click **"Save"**

**Important Notes:**
- ✅ All three variables must be set for **All environments**
- ✅ `NEXT_PUBLIC_*` is safe for browser (it's exposed)
- ✅ `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET` are server-side only (secure)
- ✅ Verify all three are listed before deploying

---

### Step 6: Deploy

1. After adding all environment variables, scroll to bottom
2. Click **"Deploy"** button
3. Watch the deployment log
4. Wait for deployment to complete (usually 1-3 minutes)

---

### Step 7: Test Deployment

1. Once deployment completes, you'll see:
   - ✅ **"Ready"** status
   - **Deployment URL** (e.g., `https://your-project.vercel.app`)

2. Click on the deployment URL

3. Test the Voice Agent:
   - Enter a room name (e.g., "test-room")
   - Click **"Connect"**
   - Allow microphone permissions
   - Speak something (e.g., "Hello, how are you?")
   - Wait for agent response

4. Check browser console for errors (F12 → Console)

---

## 📋 Quick Reference: Environment Variables

**Copy-paste these into Vercel:**

```
NEXT_PUBLIC_LIVEKIT_URL=wss://voiceagent007-fnileh5c.livekit.cloud
LIVEKIT_API_KEY=APIjAbndhXSoyis
LIVEKIT_API_SECRET=D1pm5XYaXHUJe3iiIjU7Uk5fo7n1ebU2WcBIKDy5sGRA
```

**Set all three to:** All environments (Production, Preview, Development)

---

## 🐛 Troubleshooting

### Build Fails in Vercel

**Error: "Cannot find module"**
- Check Root Directory is set to `frontend`
- Verify `frontend/package.json` exists
- Check build logs for specific errors

**Error: "Environment variable not found"**
- Verify all 3 variables are added
- Check they're set for **All environments**
- Redeploy after adding variables

### Frontend Works But Can't Connect to LiveKit

**Error: "LiveKit credentials not configured"**
- Verify environment variables are set in Vercel
- Check variable names are exact (case-sensitive)
- Redeploy after adding variables

**Error: "Connection failed"**
- Verify `NEXT_PUBLIC_LIVEKIT_URL` is correct
- Check LiveKit dashboard to confirm URL
- Test with browser console open

### Need to Update Environment Variables Later

1. Go to Vercel Dashboard → Your Project → **Settings**
2. Click **"Environment Variables"** (left sidebar)
3. Add/Edit/Delete variables
4. **IMPORTANT:** Go to **"Deployments"** tab
5. Click **"..."** on latest deployment
6. Select **"Redeploy"**

---

## 📚 Documentation

- **Detailed Vercel Guide**: See `VERCEL_DEPLOYMENT_GUIDE.md`
- **GitHub Push Help**: See `GITHUB_PUSH_GUIDE.md`
- **Environment Setup**: See `ENV_SETUP_GUIDE.md`

---

## 🎯 Success Criteria

✅ Frontend deployed and accessible  
✅ Can connect to LiveKit room  
✅ Microphone input works  
✅ Agent responds (after backend is deployed)  

---

## ⏭️ After Vercel Deployment

1. ✅ Frontend is live and accessible
2. ⏳ **Next:** Deploy backend agent to LiveKit Cloud
3. ⏳ **Then:** Test end-to-end voice interaction
4. ⏳ **Finally:** Share deployment URL with customer

---

## 📞 Support Links

- **Vercel Docs**: https://vercel.com/docs
- **LiveKit Docs**: https://docs.livekit.io/
- **GitHub Repo**: https://github.com/Web8080/conversation_flow_Voice_Agent_with_LiveKit

---

## ✅ Final Checklist Before Sharing with Customer

- [ ] Code pushed to GitHub
- [ ] Frontend deployed to Vercel
- [ ] Environment variables configured in Vercel
- [ ] Frontend accessible via URL
- [ ] Can connect to LiveKit room
- [ ] Microphone permissions work
- [ ] Backend agent deployed to LiveKit Cloud (next step)
- [ ] End-to-end voice interaction tested
- [ ] Deployment URL saved and ready to share

---

**Current Status:** Ready for GitHub push and Vercel deployment! 🚀


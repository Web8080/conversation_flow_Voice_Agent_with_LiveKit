# GitHub Push Guide

## Quick Commands

### 1. Review What Will Be Committed
```bash
cd /Users/user/Fortell_AI_Product
git status
```

### 2. Commit All Files
```bash
git commit -m "Initial commit: Stage 1 Voice Agent with LiveKit integration"
```

### 3. Push to GitHub
```bash
git push -u origin main
```

---

## If You Get Authentication Errors

### Option 1: Use GitHub Personal Access Token (Recommended)

1. **Create Personal Access Token:**
 - Go to: https://github.com/settings/tokens
 - Click **"Generate new token"** -> **"Generate new token (classic)"**
 - Name it: "Voice Agent Project"
 - Select scopes: **repo** (full control of private repositories)
 - Click **"Generate token"**
 - **COPY THE TOKEN** (you won't see it again!)

2. **Use Token When Pushing:**
 ```bash
 # When prompted for password, use the token instead
 git push -u origin main
 # Username: Web8080
 # Password: [paste your token here]
 ```

### Option 2: Use SSH Keys

1. **Generate SSH Key (if you don't have one):**
 ```bash
 ssh-keygen -t ed25519 -C "your_email@example.com"
 # Press Enter to accept default location
 # Enter passphrase (optional but recommended)
 ```

2. **Add SSH Key to GitHub:**
 ```bash
 cat ~/.ssh/id_ed25519.pub
 # Copy the output
 ```
 - Go to: https://github.com/settings/keys
 - Click **"New SSH key"**
 - Paste the key
 - Save

3. **Change Remote URL to SSH:**
 ```bash
 git remote set-url origin git@github.com:Web8080/conversation_flow_Voice_Agent_with_LiveKit.git
 git push -u origin main
 ```

### Option 3: Use GitHub CLI

```bash
# Install GitHub CLI (if not installed)
brew install gh # macOS
# or download from: https://cli.github.com/

# Authenticate
gh auth login

# Push
git push -u origin main
```

---

## Verify Push Was Successful

1. Go to: https://github.com/Web8080/conversation_flow_Voice_Agent_with_LiveKit
2. You should see all your files
3. Make sure `.env` files are NOT visible (they should be in .gitignore)

---

## After Successful Push

1. All code is on GitHub
2. Ready to connect to Vercel
3. Follow `VERCEL_DEPLOYMENT_GUIDE.md` for next steps

---

## Troubleshooting

### "Permission denied"
- Check you have access to the repository
- Verify you're pushing to the correct repository
- Try using Personal Access Token

### "Repository not found"
- Verify the repository exists: https://github.com/Web8080/conversation_flow_Voice_Agent_with_LiveKit
- Check repository name is correct
- Make sure repository is not private (or you have access if it is)

### ".env files are being committed"
- Check `.gitignore` includes `.env`
- Remove .env files from git cache:
 ```bash
 git rm --cached backend/.env frontend/.env.local
 git commit -m "Remove .env files from git"
 git push
 ```

---

## Next Steps After Push

1. Connect repository to Vercel (see `VERCEL_DEPLOYMENT_GUIDE.md`)
2. Add environment variables in Vercel dashboard
3. Deploy!
4. Test the deployed link
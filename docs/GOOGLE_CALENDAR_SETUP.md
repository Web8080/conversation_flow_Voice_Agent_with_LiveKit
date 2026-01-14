# Google Calendar API Setup Guide

## Overview

To enable appointment booking to Google Calendar, you need to:
1. Enable Google Calendar API in Google Cloud Console
2. Create a service account
3. Configure credentials in your environment

## Step-by-Step Setup

### 1. Enable Google Calendar API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (or create a new one)
3. Navigate to **APIs & Services** > **Library**
4. Search for "Google Calendar API"
5. Click **Enable**

### 2. Create Service Account

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **Service Account**
3. Fill in:
   - **Service account name**: `voice-agent-calendar` (or your preferred name)
   - **Service account ID**: Auto-generated
   - **Description**: "Service account for voice agent calendar integration"
4. Click **Create and Continue**
5. Skip role assignment (click **Continue**)
6. Click **Done**

### 3. Create and Download Service Account Key

1. Click on the service account you just created
2. Go to **Keys** tab
3. Click **Add Key** > **Create new key**
4. Select **JSON** format
5. Click **Create** (JSON file downloads automatically)
6. Save this file securely (e.g., `google-calendar-credentials.json`)

### 4. Grant Calendar Access

**Option A: Use Service Account's Own Calendar (Recommended for Testing)**

1. Copy the service account email (found in the JSON file under `client_email`)
2. Open Google Calendar in your browser
3. Go to **Settings** > **Settings for my calendars**
4. Click **Add people** next to your calendar
5. Paste the service account email
6. Grant **Make changes to events** permission
7. Click **Send**

**Option B: Create a Shared Calendar**

1. Create a new calendar in Google Calendar
2. Share it with the service account email
3. Grant **Make changes to events** permission
4. Note the calendar ID (found in calendar settings)

### 5. Configure Environment Variables

Add to `backend/.env`:

```bash
# Google Calendar Configuration
GOOGLE_APPLICATION_CREDENTIALS=/path/to/google-calendar-credentials.json
# OR use JSON string directly:
# GOOGLE_APPLICATION_CREDENTIALS_JSON='{"type":"service_account",...}'
```

**For LiveKit Cloud Deployment:**

1. Upload the JSON file content to LiveKit Cloud secrets:
   ```bash
   cd backend
   # Create .env.secrets file with:
   GOOGLE_APPLICATION_CREDENTIALS_JSON='<paste entire JSON content here>'
   
   # Update secrets
   lk agent update-secrets --project voiceagent007 --secrets-file .env.secrets
   ```

### 6. Install Required Packages

The packages are already in `requirements.txt`:
- `google-api-python-client>=2.100.0`
- `google-auth-httplib2>=0.1.1`
- `google-auth-oauthlib>=1.1.0`

If deploying locally, install:
```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### 7. Verify Setup

After deploying, check agent logs:
```bash
cd backend
lk agent logs --project voiceagent007 | grep -i calendar
```

You should see:
```
Google Calendar service initialized calendar_id=primary
```

## Troubleshooting

**Error: "Calendar API not enabled"**
- Ensure Google Calendar API is enabled in Google Cloud Console

**Error: "Insufficient permissions"**
- Verify service account has access to the calendar
- Check that calendar sharing permissions are correct

**Error: "Invalid credentials"**
- Verify JSON file path is correct
- Check that `GOOGLE_APPLICATION_CREDENTIALS` or `GOOGLE_APPLICATION_CREDENTIALS_JSON` is set correctly

**Appointments not appearing**
- Check which calendar the service account is using (default: `primary`)
- Verify the service account email has access to that calendar

## Using a Specific Calendar

To use a specific calendar instead of the primary calendar, modify `backend/agent/services/calendar_service.py`:

```python
# Change this line:
self.calendar_id = 'primary'

# To your calendar ID (found in calendar settings):
self.calendar_id = 'your-calendar-id@group.calendar.google.com'
```


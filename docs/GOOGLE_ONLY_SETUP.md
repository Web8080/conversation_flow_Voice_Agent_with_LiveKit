# Google Services Only - Setup Guide

This guide ensures the system works perfectly with Google services only, keeping OpenAI as a silent fallback (even if it doesn't work).

## Current Configuration

The system is already configured to use Google as primary for all services:
- **LLM**: Google Gemini (`gemini-1.5-flash` primary)
- **STT**: Google Cloud Speech-to-Text
- **TTS**: Google Cloud Text-to-Speech

OpenAI is kept as fallback but won't break the system if it fails.

## Required Google Credentials

You need two types of Google credentials:

### 1. Google API Key (for Gemini LLM)
- **Purpose**: Used for Google Gemini API
- **Where to get**: https://console.cloud.google.com/apis/credentials
- **Environment Variable**: `GOOGLE_API_KEY`

### 2. Google Service Account (for STT and TTS)
- **Purpose**: Used for Google Cloud Speech-to-Text and Text-to-Speech
- **Where to get**: https://console.cloud.google.com/iam-admin/serviceaccounts
- **Environment Variable**: `GOOGLE_APPLICATION_CREDENTIALS_JSON` (JSON content as string)

## Setup Steps

### Step 1: Get Google API Key for Gemini

1. Go to https://console.cloud.google.com/
2. Create a project (or use existing)
3. Enable **Generative AI API**:
   - Go to https://console.cloud.google.com/apis/library
   - Search for "Generative AI API"
   - Click "Enable"
4. Create API Key:
   - Go to https://console.cloud.google.com/apis/credentials
   - Click "Create Credentials" → "API Key"
   - Copy the API key
   - (Optional) Restrict to "Generative AI API" for security

### Step 2: Get Service Account for STT/TTS

1. Go to https://console.cloud.google.com/iam-admin/serviceaccounts
2. Click "Create Service Account"
3. Name: `voice-agent-services`
4. Grant role: **Editor** (or more specific: "Cloud Speech-to-Text API User" + "Cloud Text-to-Speech API User")
5. Enable APIs:
   - Go to https://console.cloud.google.com/apis/library
   - Enable "Cloud Speech-to-Text API"
   - Enable "Cloud Text-to-Speech API"
6. Create and download JSON key:
   - In service account, go to "Keys" tab
   - Click "Add Key" → "Create new key" → Choose "JSON"
   - Download the JSON file

### Step 3: Configure LiveKit Cloud Secrets

1. Go to your LiveKit Cloud dashboard
2. Navigate to your agent → **Secrets** section
3. Add/Update these secrets:

```
GOOGLE_API_KEY=your-gemini-api-key-here
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account","project_id":"...","private_key_id":"...","private_key":"...","client_email":"...","client_id":"...","auth_uri":"...","token_uri":"...","auth_provider_x509_cert_url":"...","client_x509_cert_url":"..."}
```

**Important**: For `GOOGLE_APPLICATION_CREDENTIALS_JSON`, paste the entire JSON content from the downloaded service account file as a single-line string.

### Step 4: Verify Configuration

After updating secrets, redeploy the agent:

```bash
cd backend
lk agent deploy --project voiceagent007
```

Check logs to verify:

```bash
lk agent logs --project voiceagent007 | grep -i google
```

You should see:
- `Initialized Google Gemini LLM service model=gemini-1.5-flash`
- `Initialized Google STT service`
- `Initialized Google TTS service`

## How the System Works

### LLM Flow
1. **Primary**: Google Gemini (`gemini-1.5-flash`)
   - If fails → tries `gemini-1.5-pro`
   - If fails → tries `gemini-pro`
2. **Fallback**: OpenAI (silent, won't break if fails)
3. **Fallback**: Ollama (if configured)
4. **Fallback**: Groq (if configured)

### STT Flow
1. **Primary**: Google Cloud Speech-to-Text
   - Returns `None` for silence/unclear audio (this is normal)
   - System skips processing when `None` is returned
2. **Fallback**: OpenAI Whisper (only if Google throws exception, not for "no results")

### TTS Flow
1. **Primary**: Google Cloud Text-to-Speech
2. **Fallback**: OpenAI TTS (only if Google fails)

## Expected Behavior

### Normal Operation
- User speaks → Google STT transcribes → Google Gemini generates response → Google TTS speaks
- If user is silent → Google STT returns `None` → System skips processing (no error)

### When Google Services Fail
- **STT failure**: Falls back to OpenAI (silent, won't break)
- **LLM failure**: Falls back to OpenAI → Ollama → Groq (silent, won't break)
- **TTS failure**: Falls back to OpenAI (silent, won't break)

### Error Messages
- If all LLM providers fail: "I'm sorry, I didn't understand. Could you repeat that?"
- If STT fails: System skips that audio chunk (no error message)
- If TTS fails: Error logged but system continues

## Testing

1. Connect to the voice agent
2. Say "Hello" clearly
3. Check logs for:
   - `DEBUG: Google STT transcription successful` (should see this)
   - `DEBUG: Trying primary LLM provider=GoogleLLMService` (should succeed)
   - `Google TTS synthesis completed` (should see this)

## Troubleshooting

### Google Gemini 404 Errors
- **Fixed**: System now tries `gemini-1.5-flash` first
- If still fails: Check API key is correct and Generative AI API is enabled

### Google STT Returns No Results
- **Normal**: This happens for silence or unclear audio
- **Not an error**: System correctly skips processing
- **Solution**: Speak more clearly or wait for user to speak

### Google TTS Fails
- Check service account has "Cloud Text-to-Speech API User" role
- Verify `GOOGLE_APPLICATION_CREDENTIALS_JSON` is correctly formatted
- Check API is enabled in Google Cloud Console

### All Services Fail
- Verify all credentials are correct
- Check Google Cloud Console for API quotas/limits
- Review agent logs for specific error messages

## Cost Considerations

Google Cloud offers generous free tiers:
- **Speech-to-Text**: 60 minutes/month free
- **Text-to-Speech**: 4M characters/month free (Standard voices)
- **Gemini**: Free tier available

After free tier:
- Speech-to-Text: ~$0.006 per 15 seconds
- Text-to-Speech: ~$4 per 1M characters (Standard)
- Gemini: ~$0.075 per 1M input tokens (Flash model)

## Summary

The system is optimized for Google services:
- ✅ Google is primary for all services
- ✅ OpenAI is silent fallback (won't break if fails)
- ✅ Handles "no results" gracefully
- ✅ Comprehensive error handling
- ✅ Detailed logging for debugging

Just ensure your Google credentials are properly configured and the system will work perfectly!


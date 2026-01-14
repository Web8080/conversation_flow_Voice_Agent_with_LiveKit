# OpenAI API Quota Fix Guide

## Problem
The agent is receiving `429` errors from OpenAI API:
```
Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details.'}}
```

## Solution Steps

### Step 1: Check Your OpenAI Account Status

1. Go to https://platform.openai.com/
2. Log in to your account
3. Navigate to **Settings** → **Billing**
4. Check:
   - **Account Status**: Should be "Active"
   - **Usage Limits**: Check your current usage vs limits
   - **Payment Method**: Ensure a valid payment method is added

### Step 2: Add Payment Method (If Missing)

1. In OpenAI dashboard, go to **Settings** → **Billing**
2. Click **Add Payment Method**
3. Enter your credit card details
4. OpenAI will verify the payment method (may take a few minutes)

### Step 3: Check Usage Limits

1. Go to **Settings** → **Usage Limits**
2. Verify:
   - **Rate Limits**: Should allow sufficient requests per minute
   - **Spending Limits**: Ensure limits are set appropriately
   - **Current Usage**: Check if you've hit any limits

### Step 4: Verify API Key

1. Go to **API Keys** section: https://platform.openai.com/api-keys
2. Verify your API key is active and has proper permissions
3. If needed, create a new API key:
   - Click **Create new secret key**
   - Copy the key immediately (you won't see it again)
   - Update your `.env` file with the new key

### Step 5: Update Environment Variables

Update your `.env` file or LiveKit Cloud secrets:

```bash
OPENAI_API_KEY=sk-proj-...your-new-key-here...
```

For LiveKit Cloud:
1. Go to your agent dashboard
2. Navigate to **Secrets** section
3. Update `OPENAI_API_KEY` with your new/verified key
4. Redeploy the agent

### Step 6: Test API Key

You can test your API key using curl:

```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

If successful, you should see a list of available models.

### Step 7: Wait for Quota Reset (If Applicable)

If you've hit a rate limit:
- **Per-minute limits**: Wait 1 minute
- **Per-day limits**: Wait until the next day (UTC)
- **Per-month limits**: Wait until the next billing cycle

### Alternative: Use Google Gemini (Already Configured)

The system is already configured to use Google Gemini as primary LLM. If OpenAI quota is an issue, you can:

1. **Rely on Google Gemini**: The system will automatically use Google Gemini first
2. **Fix Google Gemini**: Ensure `GOOGLE_API_KEY` is properly configured
3. **Remove OpenAI dependency**: The system will work with just Google services

## Verification

After fixing the quota issue, test the agent:

1. Connect to the voice agent
2. Say "Hello"
3. Check agent logs for:
   - `DEBUG: Trying primary LLM provider=GoogleLLMService` (should succeed)
   - If Google fails: `DEBUG: Trying fallback LLM provider=OpenAILLMService` (should now succeed)

## Current System Status

The system has **runtime fallback** configured:
1. **Primary**: Google Gemini (`gemini-1.5-flash`)
2. **Fallback 1**: OpenAI GPT (requires quota fix)
3. **Fallback 2**: Ollama (requires local setup)
4. **Fallback 3**: Groq (requires valid API key)

Once OpenAI quota is fixed, the system will automatically use it as fallback when Google Gemini fails.

## Support

If issues persist:
- Check OpenAI status: https://status.openai.com/
- Review OpenAI documentation: https://platform.openai.com/docs/guides/rate-limits
- Contact OpenAI support: https://help.openai.com/


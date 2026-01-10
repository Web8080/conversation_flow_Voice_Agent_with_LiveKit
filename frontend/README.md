# Voice Agent Frontend

Next.js frontend for the LiveKit voice agent.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Copy `.env.example` to `.env.local`:
```bash
cp .env.example .env.local
```

3. Configure environment variables in `.env.local`:
```
NEXT_PUBLIC_LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
```

4. Run development server:
```bash
npm run dev
```

5. Open http://localhost:3000

## Production Build

```bash
npm run build
npm start
```

# Learnora — AI Math Tutor

A GoStudent-style tutoring platform where students book and take live video
lessons with an AI Math tutor instead of a human. Two services:

- **`apps/web`** — Next.js 16 app: signup/login, booking, calendar, and the
  live lesson call screen.
- **`apps/agent`** — Python FastAPI service hosting a Google ADK agent (the
  tutor's "brain", powered by Gemini) that decides what the tutor says.

The tutor's live video/voice in the call comes from HeyGen's LiveAvatar
streaming API (the tutor's "face and voice") — a **paid, pay-as-you-go**
service (~$0.20/min). Gemini's free tier powers the reasoning.

## Prerequisites

- Node.js 20.19+ / 22.12+ / 24+ (Prisma's floor). If your system Node is
  older, install [nvm](https://github.com/nvm-sh/nvm) and run `nvm install 22`
  inside `apps/web` before any `npm` command.
- Python 3.11+
- A [Gemini API key](https://aistudio.google.com/apikey) (free tier — Flash
  models).
- A [HeyGen API key](https://app.heygen.com/settings?nav=API) with a funded
  pay-as-you-go wallet, for the LiveAvatar streaming API.

## 1. Set up `apps/web`

```bash
cd apps/web
npm install
npx prisma migrate dev   # creates dev.db (SQLite)
```

Fill in `apps/web/.env`:

| Variable | Where to get it |
|---|---|
| `DATABASE_URL` | Already set to `file:./dev.db` |
| `SESSION_SECRET` | Already generated |
| `GEMINI_API_KEY` | https://aistudio.google.com/apikey (only needed by `apps/agent`, not this app — leave as-is here) |
| `HEYGEN_API_KEY` | https://app.heygen.com/settings?nav=API |
| `HEYGEN_AVATAR_ID` | Pick a public avatar at https://labs.heygen.com/interactive-avatar → "Select Avatar", or create your own |
| `AGENT_SERVICE_URL` | Already set to `http://localhost:8000` |
| `NEXT_PUBLIC_APP_URL` | Already set to `http://localhost:3000` |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Optional — Google Calendar sync. Create an OAuth client at https://console.cloud.google.com/apis/credentials (Web application), enable the Google Calendar API, add `http://localhost:3000/api/google-calendar/callback` as an authorized redirect URI. Leave blank to disable the feature (it degrades silently, no button shown) |
| `RESEND_API_KEY` | Optional — sends a "your lesson starts in 1 hour" email. Get a key at https://resend.com/api-keys. Leave blank to disable (silently skipped) |

Run it:

```bash
npm run dev
```

Visit http://localhost:3000, sign up, and book a lesson.

## 2. Set up `apps/agent`

```bash
cd apps/agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Fill in `apps/agent/.env`:

| Variable | Where to get it |
|---|---|
| `GEMINI_API_KEY` | https://aistudio.google.com/apikey |
| `WEB_ORIGIN` | Already set to `http://localhost:3000` |

Run it:

```bash
uvicorn app.main:app --reload --port 8000
```

Check it's alive: `curl http://localhost:8000/health` → `{"status":"ok"}`.

## Taking a lesson

1. Sign up / log in at http://localhost:3000.
2. Book a lesson (slots are generated on the fly — the AI tutor has no real
   capacity limit, so anything in the next two weeks works). You can start a
   lesson up to 10 minutes before its scheduled time.
3. Open the lesson — the app connects to HeyGen for the tutor's live video
   and to your webcam. Speak (Chrome's built-in speech recognition transcribes
   you); the FastAPI agent generates the tutor's reply via Gemini, and the
   HeyGen avatar speaks it back.

## Known caveats / things to verify with your own keys

- **HeyGen token endpoint**: `apps/web/src/app/api/heygen/token/route.ts`
  calls `POST https://api.liveavatar.com/v1/sessions/token` with an
  `X-API-KEY` header to mint a session token. This was confirmed against the
  installed `@heygen/liveavatar-web-sdk`'s own base URL and REST path
  conventions (`/v1/sessions/start`, `/stop`, `/keep-alive`), but the token
  endpoint itself couldn't be hit live without a funded key. If it 404s or
  errors once you add your key, check https://docs.liveavatar.com for the
  current path/shape and update that one route — everything downstream (the
  `@heygen/liveavatar-web-sdk` client usage in `CallScreen.tsx`) is verified
  against the SDK's actual type definitions.
- **Speech capture** requires Chrome (or another `SpeechRecognition`-capable
  browser) and mic/camera permissions.
- **`InMemoryRunner`** in `apps/agent` keeps ADK sessions in-process; fine for
  a single dev server, not for multiple workers or production scale.

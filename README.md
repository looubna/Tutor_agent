# Zanoba — an AI tutor that actually teaches a lesson

Zanoba is a **live tutoring agent**. A student books an hour, joins a call, and
is taught — out loud, on a worksheet, by a tutor with a face.

It is not a chat window. The agent plans the hour before the student arrives,
speaks and listens in real time, turns the pages of a worksheet, writes on it
while it explains, and adapts when the student gets something wrong.

**Category:** Collaborative Partner — the agent leads the session, asks
questions, guides step by step, and records what it learns about the student.

🎬 **[Watch the demo](https://www.youtube.com/watch?v=VhYs4kiZe0k)**

|  | |
|---|---|
| 🧠 **Model** | `gemini-3.5-flash` (lesson preparation) · `gemini-3.1-flash-live-preview` (live class) |
| 🧩 **Agent framework** | Google ADK (`google-adk`) — a 12-node graph, plus a 22-tool live agent |
| ☁️ **Google Cloud** | Cloud Run (agent service) · Firestore (curriculum, lesson cache, profiles, history) |
| 🖥️ **Front end** | Next.js 16 · React 19 · Prisma |
| 🙂 **Face & voice** | Gemini Live audio, streamed into a Simli avatar for lip sync |

---

## What it does

| Step | What happens |
|---|---|
| 1. Book | Student picks a subject, level and slot. |
| 2. Prepare | An ADK graph plans the lesson and writes the worksheet **before** the class. |
| 3. Teach | The student joins a call. The tutor greets them and starts. |
| 4. Work | The tutor turns pages, writes on the paper, circles answers, fills gaps. |
| 5. Adapt | Wrong answers are marked, observed and remembered for next time. |

Two subjects are wired end to end: **French mathematics** (Sixième, 299
curriculum items) and **German A1**.

---

## Architecture

```
                        ┌──────────────────────────────────────────┐
   BEFORE THE LESSON    │  ADK preparation graph  (gemini-3.5)     │
                        │                                          │
                        │  curriculum → diagnostic → objectives     │
                        │                    │                     │
                        │             route_by_domain              │
                        │              ╱            ╲              │
                        │      language          stem              │
                        │      planner           planner           │
                        │              ╲            ╱              │
                        │            material_planner              │
                        │              ╱            ╲              │
                        │      language          stem              │
                        │      material          material          │
                        │              ╲            ╱              │
                        │          quality_checker → gate          │
                        └───────────────────┬──────────────────────┘
                                            │ lesson plan + worksheet
                                            ▼
                                      ☁️ Firestore
                                            │
   ─────────────────────────────────────────┼───────────────────────────────
                                            │
   DURING THE LESSON                        ▼
   ┌────────────┐   PCM 16kHz    ┌────────────────────────┐
   │            │ ─────────────► │  Cloud Run: agent      │
   │  Browser   │                │  ADK live tutor        │
   │  Next.js   │ ◄───────────── │  gemini-3.1-flash-live │
   │            │  PCM 24kHz +   │  22 tools              │
   │            │  JSON events   └───────────┬────────────┘
   └─────┬──────┘                            │ writes marks
         │                                   ▼
         │ 24k→16k                    worksheet API
         ▼                            (Next.js + Prisma)
   ┌────────────┐
   │   Simli    │  lip-synced video of the tutor
   └────────────┘
```

The authoritative diagram is `apps/agent/architecture.excalidraw.json`.

### How the pieces talk

| Link | Transport | Why |
|---|---|---|
| Browser → agent | WebSocket, raw PCM | A lesson is speech. HTTP turns would add a hop to every 20 ms of sound. |
| Agent → browser | Same socket: audio frames + JSON events | One framing for the voice, the page turns, the marks and the board. |
| Browser → Simli | WebRTC (LiveKit) | The tutor's own Gemini voice drives the mouth — no second text-to-speech. |
| Agent → worksheet | HTTPS, shared secret | The agent has no user session; the web app signs a short-lived ticket instead. |

### State

- **Per lesson** — `LiveLesson` holds the plan, paper, board and state machine,
  keyed by booking id. Cloud Run runs with `--session-affinity` so a student's
  turns keep reaching the instance holding their hour.
- **Across lessons** — Firestore keeps the student profile, the lesson history
  and the prepared-material cache.
- **In the browser** — nothing that matters. Refreshing mid-lesson reloads the
  transcript from the database and rejoins.

---

## Spin-up

### Prerequisites

- Node.js **22+** (Prisma's floor)
- Python **3.11+** and [`uv`](https://docs.astral.sh/uv/)
- A Gemini API key with Live API access
- A [Simli](https://app.simli.com) API key (free tier) for the tutor's face

### 1. The agent

```bash
cd apps/agent
cp .env.example .env          # set GOOGLE_API_KEY, AGENT_TOKEN, ZANOBA_WEB_URL
uv sync
uv run pytest -q              # 393 tests, no network, no cost
uv run --env-file .env uvicorn server:app --port 8080
```

`GET localhost:8080/health` reports the model, the graph's nodes, and
`paper_reachable` — whether the agent can actually reach a student's worksheet.

### 2. The web app

```bash
cd apps/web
cp .env.example .env          # set AGENT_URL + the same AGENT_TOKEN, and SIMLI_API_KEY
npm install
npx prisma migrate deploy
npm run dev
```

### 3. A lesson you can actually open

The lesson page only admits you from ten minutes before a booking until it
ends, so anything booked through the UI is in the future. Put one on the clock:

```bash
cd apps/web
npm run lesson:now                       # defaults to German A1
npm run lesson:now you@example.com nombres-entiers-et-decimaux l1 mathematics fr.sixieme
```

It prints the URL. Open it, press **Join audio**, and the tutor greets you.

> ⚠️ `lesson:now` cancels any booking that overlaps the slot it takes.
> Use a test account if you care about the data.

### Deploying the agent to Cloud Run

```bash
cd apps/agent
set -a; . ./.env; set +a
gcloud run deploy zanoba-agent --source . --project ai-tutor-zanoba \
  --region europe-west1 --allow-unauthenticated --memory 1Gi --timeout 900 \
  --session-affinity \
  --set-env-vars "GOOGLE_API_KEY=${GOOGLE_API_KEY},GOOGLE_GENAI_USE_VERTEXAI=FALSE,GOOGLE_CLOUD_PROJECT=ai-tutor-zanoba,ZANOBA_WEB_URL=${ZANOBA_WEB_URL},AGENT_TOKEN=${AGENT_TOKEN}"
```

`--session-affinity` is not optional: a class lives in one instance's memory.

The service is private by default. To let a browser (or a judge) reach it:

```bash
gcloud run services add-iam-policy-binding zanoba-agent \
  --region europe-west1 --project ai-tutor-zanoba \
  --member=allUsers --role=roles/run.invoker
```

A deployed agent also needs `ZANOBA_WEB_URL` pointing at the deployed web app,
not `localhost` — otherwise it teaches but cannot reach the worksheet, and
`/health` reports `paper_reachable: false`.

---

## Layout

```
apps/agent/          Python. The tutor.
  server.py          FastAPI: /prepare, /lesson/turn, ws /lesson/live
  src/zanoba_agent/
    agents/          ADK agents — the graph, and the live tutor's 22 tools
    live/            audio config, paper, session registry
    workflows/       the preparation pipeline
    store/           Firestore profiles and history
  tests/             393 tests

apps/web/            TypeScript. Everything the student sees.
  src/app/           routes: booking, calendar, the lesson screen
  src/components/    CallScreen, LessonPaper, Whiteboard
  src/lib/           liveLesson (audio socket), tutorFace (avatar), curriculum
```

---

## Data sources

| Source | Used for |
|---|---|
| French *Sixième* mathematics programme | 299 curriculum items, hand-encoded |
| German A1 word list (`data/words.de.json`) | Exercise generation, hand-checked |
| Pexels | Illustrations in generated material |

---

## Known limitations

Written down rather than discovered by a judge.

| Limitation | Detail |
|---|---|
| **One lesson per instance** | `bind_session` points the live tutor's tools at a lesson through module-level globals, so two concurrent classes on one instance would collide. Cloud Run's `--session-affinity` plus low traffic hides it today; the fix is a per-session context object, not a bigger machine. |
| **Avatar realism** | The tutor's face is built from a single photograph on a free tier, so she lip-syncs but does not gesture. A filmed avatar or a paid generator fixes it; nothing in the code changes. |
| **Two subjects** | French *Sixième* maths and German A1 are wired end to end. The graph is subject-agnostic; the curricula are the work. |
| **SQLite** | The web app uses Prisma on SQLite for the hackathon. Cloud SQL is a connection-string change. |

---

## What we learned

**A live model does not speak first.** The socket opened, the queue sat empty,
and the tutor waited for a student who was waiting for the tutor. Twenty
seconds later a watchdog called it a failed connection. A spoken lesson that
worked perfectly never once made a sound. Live sessions need an opening turn.

**Never race a watchdog against the work it watches.** The same watchdog was one
of three tasks in a `FIRST_COMPLETED` wait. The moment the tutor *did* speak,
the watchdog finished — and cancelled the two tasks doing the teaching. The
lesson ended 1.6 seconds in. It hid for as long as the model stayed silent.

**Send the avatar audio, not text.** Handing a transcript to an avatar service
means waiting for the turn to finish, paying for a second text-to-speech, and
getting a different voice. Gemini Live emits PCM; the avatar accepts PCM. Piping
one into the other removed a whole stage and made the tutor answer instantly.

**Sample rates are not a detail.** Gemini speaks at 24 kHz, Simli listens at
16 kHz. Getting it wrong does not error — it plays a third fast and a fifth
high, and the lips agree with it perfectly.

**Green tests are not a working feature.** Every bug above passed `tsc`, eslint
and the full suite. They were only ever found by opening a browser and
measuring what actually came down the socket.

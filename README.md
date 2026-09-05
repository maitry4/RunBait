# RunBait

**Your PR changed the code. Did it break the product?**

[RunBait](https://run-bait.vercel.app/) is AI QA for pull requests. It reads the diff, figures out which user journeys are at risk, boots the real app, drives a real browser, and tells you what actually broke — with screenshots, severity, and a confidence score.

No test files to write. No selectors to maintain. Sign in with GitHub and run an analysis.

**Live product:** [https://run-bait.vercel.app/](https://run-bait.vercel.app/)

---

## Why it exists

Unit tests catch logic. CI catches builds. Neither answers the question that ships (or sinks) a PR:

> Would a real user still be able to complete this flow?

Manual QA does not scale with every pull request. Full end-to-end suites rot as the UI changes. RunBait sits in the gap: **targeted, PR-aware journeys on the real application**, judged by a multimodal model that can see the screen.

---

## Use it in under a minute

The frontend and backend are live and talk to each other end to end. You do not need to clone this repo to try the product.

1. Open **[run-bait.vercel.app](https://run-bait.vercel.app/)**
2. Click **Connect GitHub** and sign in
3. On **Overview**, pick a pull request
4. Click **Run analysis**
5. Watch status move through discovery → browser run → judgment
6. Open **Analyses** for the report: issues, flows tested, evidence, confidence

That is the whole loop.

### Demo path (zero setup)

The dashboard includes a demo against `maitry4/opensource.razorpay.com`. Choose a PR number and run. RunBait maps the change, starts the app in GitHub Actions, executes Playwright flows, and returns a verdict in the UI.

### Your own repo

Switch to a custom repository, paste `owner/repo` and the PR number, optionally override install / start commands (`npm install`, `npm run dev` by default), and run the same pipeline.

```
Connect GitHub  →  Pick a PR  →  Run  →  Real browser  →  Report
```

---

## What you get

| | |
| --- | --- |
| **GitHub-native auth** | OAuth sign-in. Your session is an HttpOnly JWT. The dashboard never handles the token in JavaScript. |
| **Journey discovery** | Gemini reads a distilled repo summary and writes testable flows (search, filters, checkout, …). |
| **PR-aware selection** | Only journeys tied to the diff run — not a kitchen-sink suite. |
| **Real browser execution** | Playwright against the PR head, not mocks. Screenshots at checkpoints and on failure. |
| **Visual + behavioral judge** | Gemini scores screenshots and step logs: regression or clean, with severity and confidence. |
| **Live dashboard** | Overview to launch, Repositories you have touched, Analyses with history and filters. |

Analyses run in the background. The dashboard polls every few seconds. You can leave and come back.

---

## Product architecture

RunBait is two services that stay in sync: a Next.js app on Vercel, and a FastAPI orchestrator that owns the pipeline.

```
                         https://run-bait.vercel.app
                         ┌─────────────────────────┐
                         │  Next.js 16  ·  React 19 │
                         │  Landing  ·  Dashboard   │
                         │  /api/*  auth + run proxy│
                         └────────────┬────────────┘
                                      │ Bearer JWT (server-side)
                                      ▼
                         ┌─────────────────────────┐
                         │  FastAPI  ·  Orchestrator│
                         │  OAuth, runs, webhooks   │
                         └──────┬──────┬──────┬────┘
                                │      │      │
                    ┌───────────┘      │      └───────────┐
                    ▼                  ▼                  ▼
              GitHub API         Google Gemini      GitHub Actions
           PR diff, tree,      flow discovery,      checkout PR head,
           OAuth profile       impact ranking,      start app, Playwright,
                               regression judge     screenshot artifacts
                    │
                    ▼
              Supabase (Postgres)
           users, runs, JSON results
```

**The dashboard is the product surface.** It never talks to FastAPI from the browser. Next.js API routes read the HttpOnly cookie and forward requests so CORS stays simple and tokens stay off the client.

**FastAPI is the brain.** `POST /api/runs` returns immediately with a `run_id`. Phases 1–3 run as a background task. When flows are selected, the orchestrator dispatches `.github/workflows/runbait_worker.yml`. The worker posts results to `/api/runs/{id}/webhook`, which kicks off the judge. Status is written to Supabase the whole way: `pending` → `phase1-3` → `github-actions` → `phase6` → `completed` | `failed`.

**GitHub Actions is the execution environment.** It checks out *this* repo (the Playwright agent) and the *target* PR head, installs the app, waits on `http://localhost:3000`, runs flows, uploads `output/` as an artifact, and always notifies the backend — including on failure, so a run never sits forever.

**Gemini is scoped, not open-ended.** Discovery and impact use **Gemini 2.5 Flash** with Pydantic structured outputs. The judge uses **Gemini 3.1 Flash-Lite** with screenshots inlined as images. Every AI step returns JSON the pipeline can parse, not free-form prose.

---

## Pipeline (what happens after you click Run)

Five phases. AI only where judgment is required. Everything else is deterministic.

```
Phase 1          Phase 2           Phase 3            Phase 4              Phase 6
Repo context  →  Flow discovery →  PR impact      →  Playwright runner →  Regression judge
GitHub API       Gemini 2.5 Flash  Gemini 2.5 Flash   GitHub Actions       Gemini 3.1 Flash-Lite
no clone         FlowFile JSON     selected flows     real Chromium        verdicts + report
```

### 1. Repo context (deterministic)

The GitHub REST API yields a lean summary: README, filtered file tree, `package.json`, framework (Next, Vite, Nuxt, …), detected routes, snippets of config and page files. No full clone. That distilled context is cheaper and more useful than dumping the repo into a prompt.

### 2. Flow discovery (Gemini 2.5 Flash)

Gemini acts as a QA engineer and emits a `FlowFile`: a short list of realistic journeys with Playwright-friendly steps (`navigate`, `click`, `fill`, `wait`) and checkpoint flags for screenshots.

```json
{
  "flows": [
    {
      "name": "search-filters",
      "description": "User searches and narrows results with filter tags",
      "entry_url": "/",
      "steps": [
        { "action": "navigate", "target": "/", "checkpoint": true },
        { "action": "fill", "target": "Search", "value": "S", "checkpoint": true },
        { "action": "click", "target": "SDKs", "checkpoint": true }
      ]
    }
  ]
}
```

### 3. PR impact (Gemini 2.5 Flash)

Changed files are keyword-mapped to candidate flows first. Gemini then ranks which journeys the diff actually threatens (`high` / `medium` / `low`) and explains why, citing filenames.

```json
{
  "summary": "Search filter state and result rendering changed.",
  "selected_flows": [
    {
      "flow": "search-filters",
      "reason": "Filter tags and search query composition were modified.",
      "priority": "high"
    }
  ]
}
```

If nothing is at risk, the run completes with no browser work.

### 4. Playwright runner (GitHub Actions)

The worker:

1. Checks out RunBait’s agent and the target PR (`refs/pull/{n}/head`)
2. Runs your install and start commands
3. Fetches selected flows from `GET /api/runs/{id}/runner-data`
4. Executes them headlessly against `http://localhost:3000`
5. Uses layered locators (role → visible text → CSS) so generated steps stay resilient
6. Captures screenshots on checkpoints and failures, plus console errors
7. POSTs execution JSON to the orchestrator webhook

### 5. Regression judge (Gemini 3.1 Flash-Lite)

For each flow, the judge sees the intended steps, the execution log, checkpoint screenshots, and PR context. It returns a structured verdict, then those verdicts roll up into one report.

```json
{
  "bug_found": true,
  "severity": "high",
  "bug_type": "behavioral",
  "description": "SDK filter does not update results while a search query is active.",
  "evidence_step": 7,
  "confidence": 0.94,
  "details": "After filling search with 'S' and clicking SDKs, the screenshot still shows mixed non-SDK results."
}
```

The dashboard shows overall status, per-flow verdicts, and the evidence trail.

---

## How the frontend and backend stay in sync

| Concern | How it works |
| --- | --- |
| **Auth** | Browser hits FastAPI `GET /api/auth/github/login` → GitHub → callback upserts the user in Supabase → JWT issued → redirect to Next.js `/api/auth/set-token` which sets an HttpOnly cookie → `/dashboard`. |
| **API** | Dashboard calls same-origin `/api/runs`. Next.js reads the cookie and proxies to FastAPI with `Authorization: Bearer`. |
| **Launch** | `POST /api/runs` creates a row (`pending`) and schedules phases 1–3. Client stores `run_id`. |
| **Progress** | Client polls `GET /api/runs/{id}` every 5s while status is in-flight. |
| **Worker** | Actions POSTs `/api/runs/{id}/webhook`. Success starts phase 6; failure marks the run failed. |
| **History** | `GET /api/runs` lists the user’s analyses. Repositories is the unique `owner/repo` set from that list. |

CORS on FastAPI allows only `FRONTEND_URL`. Session middleware holds OAuth state between login and callback.

---

## Repository layout

```
RunBait/
├── runbait_frontend/              # Next.js app (Vercel)
│   ├── src/app/                   # Landing, sign-in, dashboard
│   ├── src/app/api/               # Cookie-aware proxies (auth, runs)
│   └── src/components/            # Marketing + DashboardClient
├── runbait_backend/               # FastAPI orchestrator
│   ├── main.py                    # App, CORS, routers
│   ├── routers/                   # auth, users, runs (+ worker webhook)
│   ├── services/orchestrator.py   # Phases 1–3, Actions dispatch, phase 6
│   ├── phase1_repo_context.py
│   ├── phase2_flow_discovery.py
│   ├── phase3_pr_impact.py
│   ├── phase4_playwright_runner.py
│   ├── phase6_regression_judge.py
│   ├── github_actions_runner.py   # Invoked inside the Actions job
│   ├── runbait_agent.py           # Optional local CLI
│   ├── schemas.py                 # Structured AI + execution models
│   └── migrations/                # Supabase SQL (users, runs)
└── .github/workflows/
    └── runbait_worker.yml         # Playwright worker (workflow_dispatch)
```

---

## Tech stack

| Layer | Choice |
| --- | --- |
| Product UI | [Next.js 16](https://nextjs.org/), React 19, Tailwind CSS 4 |
| Hosting (frontend) | [Vercel](https://run-bait.vercel.app/) |
| API | FastAPI, Uvicorn, Authlib (GitHub OAuth), python-jose (JWT) |
| Data | Supabase (Postgres) — `users`, `runs` |
| AI | Google Gemini (`gemini-2.5-flash`, `gemini-3.1-flash-lite`), structured outputs |
| Browser | Playwright (Chromium), smart locators |
| Execution | GitHub Actions (`ubuntu-latest`) |
| Auth | GitHub OAuth → JWT in HttpOnly cookie |

---

## Local development

Use this if you are changing the product itself. Day-to-day QA does not require it — use the [live app](https://run-bait.vercel.app/).

### Prerequisites

- Node.js 20+
- Python 3.11+
- A [GitHub OAuth App](https://github.com/settings/developers) with callback `http://localhost:8000/api/auth/github/callback`
- [Gemini API key](https://aistudio.google.com/apikey)
- Supabase project (run `runbait_backend/migrations/`)

### Frontend

```bash
cd runbait_frontend
npm install
```

Set `BACKEND_URL` and `NEXT_PUBLIC_BACKEND_URL` to your FastAPI origin (default `http://localhost:8000`).

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### Backend

```bash
cd runbait_backend
pip install -r requirements.txt
playwright install chromium
```

Copy `.env.example` to `.env` and fill `SUPABASE_*`, `GITHUB_CLIENT_*`, `JWT_SECRET`, `GEMINI_API_KEY`, `GITHUB_TOKEN`, `FRONTEND_URL`, `BACKEND_URL`.

```bash
uvicorn main:app --reload --port 8000
```

API docs: [http://localhost:8000/docs](http://localhost:8000/docs).

### Standalone pipeline (no dashboard)

Phases 1–3 only, or full Playwright if the app is already running:

```bash
cd runbait_backend
python runbait_agent.py
python runbait_agent.py --app-url http://localhost:3000 --pr 42
```

---

## License

TBD

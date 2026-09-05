# RunBait

**Your PR changed the code. Did it break the product?**

[RunBait](https://run-bait.vercel.app/) is an AI QA agent for pull requests. It looks at what changed, figures out which user journeys could be affected, boots the actual application, drives a real browser with Playwright, and checks whether those flows still work.

Instead of writing another test file for every UI change, RunBait tries to answer a simpler question:

> **If a real user used this product after this PR, would something break?**

It returns the flows it tested, what happened during execution, screenshots as evidence, severity, and a confidence score.

**Live product:** https://run-bait.vercel.app/

---

## The idea

A pull request can be perfectly valid from a code perspective and still break the product.

Unit tests are great for logic. CI catches builds and existing automated tests. But neither necessarily tells you that a change to a component, route, state, or API has quietly broken an important user journey.

Full end-to-end test suites help, but maintaining a large suite for every possible flow is expensive — especially when the UI keeps changing.

RunBait takes a different approach:

**PR → understand the change → identify affected journeys → run those journeys → inspect the result**

It is **targeted QA instead of running everything.**

---

## Proof: I tested it on a real open-source PR

I didn't want RunBait to only work on a toy repository.

As a real-world test, I forked **Razorpay's open-source `opensource.razorpay.com` repository**, made a feature change, and raised a pull request against the fork.

RunBait analyzed the PR, identified the affected flow, started the application through GitHub Actions, and ran the generated Playwright journey against the PR head.

The important part: **the changed feature introduced a runtime issue, and RunBait was able to detect it during browser execution.**

That was the test I wanted to see — not just whether the pipeline could produce a report, but whether it could actually catch something that went wrong when the application was running.

---

## Try it

The frontend and backend are live and connected end to end. You don't need to clone this repository to try the product.

1. Open **[run-bait.vercel.app](https://run-bait.vercel.app/)**
2. Click **Connect GitHub** and sign in
3. From **Overview**, choose a pull request
4. Click **Run analysis**
5. Watch the run move through discovery → browser execution → judgment
6. Open **Analyses** to see the report, flows, evidence, severity, and confidence

That's the complete loop.

### Demo path

The dashboard includes a demo path using `maitry4/opensource.razorpay.com`.

Choose a PR and run an analysis. RunBait maps the change, starts the application in GitHub Actions, executes the selected Playwright flows, and sends the execution back to the backend for analysis.

### Test your own repository

You can also switch to a custom repository and provide:

* `owner/repo`
* PR number
* install command
* start command

The default commands are:

```bash
npm install
npm run dev
```

Then RunBait runs the same pipeline against that PR.

```text
Connect GitHub → Pick a PR → Run → Real browser → Report
```

---

## What RunBait does

| Feature                      | What it does                                                         |
| ----------------------------- | ---------------------------------------------------------------------|
| **GitHub authentication**    | OAuth sign-in with an HttpOnly JWT session                           |
| **Repository understanding** | Builds a compact view of the repository using GitHub's API           |
| **Journey discovery**        | Gemini identifies realistic user flows from the application          |
| **PR-aware testing**         | Selects flows that are actually relevant to the changes              |
| **Real browser execution**   | Runs Playwright against the PR's code, not mocks                     |
| **Visual evidence**          | Captures screenshots at checkpoints and when things fail             |
| **Runtime signals**          | Collects execution information including browser/console errors     |
| **AI regression judgment**   | Gemini evaluates the execution and screenshots                       |
| **Analysis history**         | Stores completed runs and their results in the dashboard             |
| **Live progress**            | The dashboard polls the running analysis and shows its current phase |

Analyses run in the background, so starting a run doesn't block the dashboard.

---

## How it works

RunBait is built as two services:

* **Next.js frontend** — dashboard, authentication flow, and API proxy
* **FastAPI backend** — orchestration, AI pipeline, GitHub integration, and run state

GitHub Actions acts as the execution environment for the actual application and Playwright agent.

```text
                         RunBait
                            │
             ┌──────────────┴──────────────┐
             │                             │
             ▼                             ▼
       Next.js / Vercel              FastAPI
          Frontend                 Orchestrator
             │                             │
             │                       ┌─────┼─────┐
             │                       │     │     │
             │                       ▼     ▼     ▼
             │                    GitHub Gemini Supabase
             │                      API     │    Postgres
             │                              │
             │                              ▼
             │                       GitHub Actions
             │                              │
             │                              ▼
             │                         Playwright
             │                              │
             │                              ▼
             │                          Screenshots
             │                          + execution
             │                              │
             └──────────────────────────────┘
```

The dashboard is the product surface. The browser doesn't directly talk to FastAPI with the user's JWT.

Instead:

```text
Browser
   ↓
Next.js API route
   ↓
HttpOnly session cookie
   ↓
FastAPI
```

This keeps the authentication token away from client-side JavaScript while still allowing the dashboard to communicate with the backend.

---

## The pipeline

RunBait breaks an analysis into five logical stages.

```text
┌─────────────────┐
│ 1. Repo Context │
└────────┬────────┘
         ↓
┌────────────────────┐
│ 2. Flow Discovery  │
└────────┬───────────┘
         ↓
┌────────────────────┐
│ 3. PR Impact       │
└────────┬───────────┘
         ↓
┌────────────────────┐
│ 4. Browser Run     │
└────────┬───────────┘
         ↓
┌────────────────────┐
│ 5. Regression Judge│
└────────────────────┘
```

AI is used where reasoning is useful. The rest of the pipeline is deterministic.

### 1. Repository context

RunBait starts with the GitHub API rather than cloning the entire repository into the model.

It builds a compact representation containing things such as:

* README
* filtered file tree
* `package.json`
* detected framework
* routes
* relevant configuration
* selected page/component snippets

The goal is to give the model enough context to understand the application without dumping an entire repository into a prompt.

### 2. Flow discovery

**Gemini 2.5 Flash** acts as the QA engineer.

From the repository context it generates realistic user journeys and turns them into structured Playwright-friendly steps.

For example:

```json
{
  "flows": [
    {
      "name": "search-filters",
      "description": "User searches and narrows results with filter tags",
      "entry_url": "/",
      "steps": [
        {
          "action": "navigate",
          "target": "/",
          "checkpoint": true
        },
        {
          "action": "fill",
          "target": "Search",
          "value": "S",
          "checkpoint": true
        },
        {
          "action": "click",
          "target": "SDKs",
          "checkpoint": true
        }
      ]
    }
  ]
}
```

The output is validated as structured data rather than treated as free-form model text.

### 3. PR impact analysis

The next question is not:

> "What can I test?"

It is:

> **"What should I test because of this PR?"**

RunBait first maps changed files to potentially related flows and then uses **Gemini 2.5 Flash** to rank their relevance.

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

If the change doesn't appear to affect any known journey, RunBait can finish without unnecessarily starting a browser run.

### 4. Real browser execution

This is where the analysis leaves the AI prompt and touches the actual application.

GitHub Actions:

1. Checks out the RunBait agent
2. Checks out the target PR head
3. Installs the target application
4. Starts the application
5. Waits for it to become available
6. Retrieves the selected flows
7. Runs them using Playwright and Chromium
8. Captures screenshots at checkpoints
9. Captures screenshots when a flow fails
10. Collects browser/console execution signals
11. Sends the execution results back to FastAPI

The worker uses layered locators such as:

```text
role → visible text → CSS
```

so generated flows don't depend on one fragile selector wherever possible.

Most importantly, the browser runs against **the actual PR code**.

### 5. Regression judgment

The final stage is where Gemini looks at what actually happened.

**Gemini 3.1 Flash-Lite** receives the relevant PR context, intended flow, execution information, and screenshots.

It produces a structured verdict such as:

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

The dashboard then turns these individual flow verdicts into the final analysis report.

---

## Why the execution layer matters

A big part of RunBait is that it doesn't stop at:

```text
PR diff → LLM → "looks risky"
```

The model's reasoning determines **what to test**, but the application itself is still executed before the final verdict.

That creates a useful separation:

```text
AI decides what is worth testing
              ↓
Deterministic runner executes it
              ↓
AI judges the observed behavior
```

The AI doesn't get to simply declare that a regression exists because a diff looks suspicious. It has execution evidence to work with.

---

## Keeping everything in sync

The main services communicate through a small set of explicit states.

```text
pending
   ↓
phase1-3
   ↓
github-actions
   ↓
phase6
   ↓
completed
```

A run is created immediately when the user clicks **Run analysis**.

The frontend receives a `run_id` and polls the backend while the analysis is running.

GitHub Actions sends its execution results to:

```text
POST /api/runs/{id}/webhook
```

The backend stores the run state and results in Supabase throughout the process.

If the worker fails, it still notifies the backend so that a run does not remain stuck indefinitely.

---

## Repository structure

```text
RunBait/
├── runbait_frontend/              # Next.js application
│   ├── src/app/                   # Landing, sign-in, dashboard
│   ├── src/app/api/               # Cookie-aware API proxies
│   └── src/components/            # UI + dashboard components
│
├── runbait_backend/               # FastAPI orchestrator
│   ├── main.py
│   ├── routers/
│   │   ├── auth
│   │   ├── users
│   │   └── runs
│   ├── services/
│   │   └── orchestrator.py
│   ├── phase1_repo_context.py
│   ├── phase2_flow_discovery.py
│   ├── phase3_pr_impact.py
│   ├── phase4_playwright_runner.py
│   ├── phase6_regression_judge.py
│   ├── github_actions_runner.py
│   ├── runbait_agent.py
│   ├── schemas.py
│   └── migrations/
│
└── .github/
    └── workflows/
        └── runbait_worker.yml
```

---

## Tech stack

| Layer                 | Technology                            |
| ---------------------- | -------------------------------------- |
| Frontend              | Next.js 16, React 19, Tailwind CSS 4  |
| Frontend hosting      | Vercel                                 |
| Backend               | FastAPI, Uvicorn                       |
| Authentication        | GitHub OAuth, Authlib, JWT             |
| Database              | Supabase / PostgreSQL                  |
| AI                    | Google Gemini                          |
| Browser automation    | Playwright + Chromium                  |
| Execution             | GitHub Actions                         |
| Structured AI output  | Pydantic                               |

### Models

* **Gemini 2.5 Flash** — repository understanding, flow discovery, and PR impact analysis
* **Gemini 3.1 Flash-Lite** — screenshot + execution based regression judgment

---

## Local development

You can use the live application without setting up the project locally.

If you want to work on RunBait itself, you'll need:

* Node.js 20+
* Python 3.11+
* GitHub OAuth App
* Gemini API key
* Supabase project
* GitHub token for Actions integration

### Frontend

```bash
cd runbait_frontend
npm install
npm run dev
```

Set your backend URL in the environment variables.

The frontend will be available at:

```text
http://localhost:3000
```

### Backend

```bash
cd runbait_backend

pip install -r requirements.txt
playwright install chromium

uvicorn main:app --reload --port 8000
```

API documentation:

```text
http://localhost:8000/docs
```

### Standalone agent

The pipeline can also be run outside the dashboard for development:

```bash
cd runbait_backend

python runbait_agent.py

python runbait_agent.py \
  --app-url http://localhost:3000 \
  --pr 42
```

---

## What's next

RunBait is currently focused on the core loop:

**understand the PR → select affected journeys → run the real application → find regressions**

There are plenty of directions I'd like to take it further — better repository understanding, more reliable generated journeys, deeper browser interaction, richer evidence, and eventually making the agent capable of adapting its own exploration when a flow doesn't behave as expected.

For now, the goal was simpler:

> **Give a PR to an AI QA agent and see if it can actually catch something that breaks.**

And after testing it against a real open-source Razorpay codebase and catching a runtime issue, I think the core idea is worth pursuing.

---

## License

TBD
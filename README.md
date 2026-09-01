# RunBait

**Your PR changed the code. Did it break the product?**

RunBait automatically tests the user journeys affected by your pull request — using the real application, real browser interactions, and AI-powered visual and behavioral analysis.

---

## The problem

Pull requests change code every day. Unit tests catch syntax and logic, but they rarely answer the question that actually matters: **did this change break something a real user would notice?**

Manual QA is slow. Full end-to-end suites are brittle and expensive to maintain. Developers ship PRs hoping nothing regressed — and users find out when they do.

## The solution

RunBait connects to your GitHub repository, reads your PR diff, discovers which user journeys are affected, launches your app in a real browser, runs targeted Playwright workflows, and uses multimodal AI to judge whether anything regressed — then posts the result directly on the PR.


---

## How it works

```
PR opened
    ↓
AI understands the change
    ↓
Affected journeys identified
    ↓
Real app launched
    ↓
Browser tests executed
    ↓
Screenshots analyzed
    ↓
Regression reported
```

### Example output

After analysis completes, a developer sees this on their PR:

```
🤖 RunBait QA Report

RunBait analyzed this PR against the real application.

Flows tested:
✓ Checkout
✓ Cart

🚨 1 regression detected

HIGH — Checkout
The payment button remains disabled after
the payment form is completed.

Evidence: Step 7
Confidence: 94%

View detailed analysis → RunBait
```

No dashboard required. The result appears where developers already work: **GitHub**.

---

## Features

| Feature | Description |
| --- | --- |
| **GitHub-native** | OAuth login, repo selection, PR selection — minimal UI, maximum signal |
| **Journey discovery** | AI analyzes your codebase to identify testable user flows (login, checkout, search, etc.) |
| **PR-aware testing** | Only journeys potentially affected by the diff are selected — not your entire test suite |
| **Real browser execution** | Playwright runs against the actual application via GitHub Actions |
| **Multimodal regression judge** | Gemini analyzes screenshots + step metadata to detect visual and behavioral regressions |
| **PR comments** | Structured QA reports posted directly on the pull request |

---

## Architecture

```
┌─────────────┐     POST /analysis      ┌─────────────┐
│   Next.js   │ ──────────────────────► │   FastAPI   │
│  Dashboard  │ ◄── analysis_id ─────── │ Orchestrator│
└─────────────┘                         └──────┬──────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    ▼                          ▼                          ▼
             GitHub API                  Gemini (AI)              GitHub Actions
          PR diff, metadata         journey discovery,          app startup,
          repo structure            PR impact analysis,         Playwright runner,
                                    regression judging           artifact upload
```

**FastAPI** is the brain — it orchestrates analysis, never blocks on long-running work.

**GitHub Actions** is the execution environment — it checks out the repo, starts the app, and runs the RunBait browser runner.

**Gemini 2.5 Flash-Lite** is the judge — a cost-efficient multimodal model with structured outputs, deliberately scoped to specific QA decisions rather than open-ended reasoning.

---

## AI pipeline

RunBait uses three constrained AI steps, each with structured JSON output:

### 1. Repository analyzer

Extracts structured context from the repo (routes, pages, components, tests, API endpoints) and asks Gemini to discover testable user journeys:

```json
{
  "flows": [
    {
      "name": "checkout",
      "description": "User adds items and completes payment",
      "steps": []
    }
  ]
}
```

### 2. PR impact analyzer

Combines repository workflows with the PR diff. Deterministic signals (changed files → component mapping → candidate flows) are ranked by Gemini:

```json
{
  "selected_flows": [
    {
      "flow": "checkout",
      "reason": "PaymentButton and checkout state management changed."
    }
  ]
}
```

### 3. Regression judge

Given the PR diff, affected flow, step sequence, and screenshots, Gemini decides whether a regression occurred:

```json
{
  "bug_found": true,
  "severity": "high",
  "type": "behavioral",
  "description": "Checkout payment button remains disabled after payment info is entered.",
  "evidence_step": 6,
  "confidence": 0.94
}
```

---

## Workflow format

Generated browser workflows are stored as JSON — and executed directly by the Playwright runner:

```json
{
  "flow": "checkout",
  "steps": [
    { "action": "navigate", "target": "/products" },
    { "action": "click", "target": "Add to cart", "checkpoint": true },
    { "action": "click", "target": "Checkout", "checkpoint": true }
  ]
}
```

Screenshot capture is decided by the workflow generator at each checkpoint. No manual configuration required.

---

## Tech stack

| Layer | Technology |
| --- | --- |
| Frontend | Next.js, React, Tailwind CSS |
| Backend | FastAPI (Python) |
| Auth | GitHub OAuth |
| Browser testing | Playwright |
| Execution | GitHub Actions |
| AI | Google Gemini 2.5 Flash-Lite (structured outputs) |
| Artifacts | Screenshots, traces, step metadata, console/network errors |

---

<!-- ## Project structure

```
RunBait/
├── runbait_frontend/     # Next.js dashboard & landing page
│   └── src/app/
└── README.md
```

Backend (`FastAPI`), GitHub Action runner, and Playwright executor are planned — see roadmap below.

---

## Roadmap

| Step | Component | Status |
| --- | --- | --- |
| 1 | Landing page (hero, flow diagram, sample report) | 🚧 In progress |
| 2 | GitHub OAuth (`/login`) | Planned |
| 3 | Repository selection dashboard | Planned |
| 4 | PR selection & "Run Analysis" | Planned |
| 5 | FastAPI orchestrator (`POST /analysis`) | Planned |
| 6 | GitHub API integration (PR diff, metadata) | Planned |
| 7 | AI repository analyzer (journey discovery) | Planned |
| 8 | Workflow generation (JSON → Playwright) | Planned |
| 9 | PR impact analysis (affected flows) | Planned |
| 10 | GitHub Actions dispatch | Planned |
| 11 | Playwright runner execution | Planned |
| 12 | Artifact upload (screenshots, traces) | Planned |
| 13 | Gemini regression judge | Planned |
| 14 | Dashboard analysis report | Planned |
| 15 | GitHub PR comment | Planned | -->

---

## Getting started

### Prerequisites

- Node.js 20+
- npm

### Frontend

```bash
cd runbait_frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### Backend

Coming soon. The FastAPI orchestrator will live in a separate service directory.

---

## License

TBD

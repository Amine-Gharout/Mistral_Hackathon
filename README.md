# GreenRights — AI-Powered French Green Transition Advisor

An agentic AI application that helps French citizens discover and calculate their entitlements to green transition subsidies, powered by **Mistral AI** with deterministic tool-calling and real-time SSE streaming.

---

## Why GreenRights?

### The Problem

France offers **dozens of financial aids** to help citizens renovate their homes and switch to clean mobility — MaPrimeRénov', CEE Coup de pouce, Éco-PTZ, prime à la conversion, bonus vélo, ZFE top-ups, and more. But navigating these programs is a nightmare:

- **Fragmented information** — rules are spread across ANAH guides, Service-Public.gouv.fr, ADEME resources, and local government websites
- **Complex eligibility** — amounts depend on income brackets (4 tiers), geography (Île-de-France vs. rest), DPE energy class, type of work, and stacking rules between programs
- **Constantly changing** — MaPrimeRénov' was suspended and reopened in February 2026; the Bonus Écologique was replaced by Prime Coup de Pouce VE in July 2025; ZFE timelines shift regularly
- **Intimidating process** — many eligible citizens never apply because they don't know what they qualify for or how much they could receive

> **Result:** Billions of euros in available subsidies go unclaimed every year.

### The Solution

GreenRights is a **conversational AI advisor** that acts like a knowledgeable friend at the town hall. Through a natural chat interface, it:

1. **Asks targeted questions** — progressively, one or two at a time (not a 20-field form)
2. **Calculates exact amounts** — using the official 2026 barème data from ANAH, with deterministic tools that the LLM calls but never replaces
3. **Checks all programs simultaneously** — renovation AND mobility aids, including stacking compatibility
4. **Generates a personal action plan** — downloadable as a PDF with amounts, conditions, required documents, and next steps

### The Key Principle

> **The AI never invents a single euro.**

Every financial amount shown to the user comes from a **deterministic calculator** that reads official barème JSON data. The LLM's role is to understand the citizen's situation, decide which tools to call, and present the results in a clear, personalized narrative. This hybrid approach combines the natural language understanding of Mistral Large with the reliability of rule-based computation.

---

## What It Does — Functionalities

### 🏠 Home Energy Renovation

| Aid Program | What GreenRights Calculates |
|---|---|
| **MaPrimeRénov' par geste** | Exact subsidy per renovation action (heat pumps, insulation, windows, VMC, solar…) based on income bracket |
| **MaPrimeRénov' Ampleur** | Accompanied renovation pathway — percentage of costs covered based on DPE improvement (e.g., F→B) |
| **CEE Coup de Pouce** | Energy savings certificate estimates for eligible actions |
| **Éco-PTZ** | Zero-interest loan — eligible amount (**up to €50,000**) and duration based on work scope |
| **Aid Stacking** | Verifies whether aids can be combined, applies global caps, and warns about incompatibilities |

### 🚗 Clean Mobility

| Aid Program | What GreenRights Calculates |
|---|---|
| **Prime Coup de Pouce VE** | CEE-funded EV purchase bonus (replaced Bonus Écologique since July 2025) |
| **Prime à la Conversion** | Scrapping bonus for replacing a Crit'Air 3+ vehicle |
| **Surprime ZFE** | Additional €1,000–€3,000 for residents/workers in Low Emission Zones |
| **Bonus Vélo** | E-bike and e-cargo bike subsidies based on income |
| **ZFE Compliance Check** | Verifies if a vehicle is banned in a given city's Low Emission Zone (18 zones tracked) |

### 🤖 Intelligent Conversation

- **Progressive profiling** — the AI collects information naturally through dialogue, adapting its questions to the user's context (renovation vs. mobility vs. both)
- **Bilingual** — full system prompts and responses in French (default) and English
- **Context-aware** — remembers all previous messages and calculations within a session (24h TTL)
- **Demo profiles** — 3 pre-built personas (Marie, Pierre, Fatima) to demo the system instantly without entering personal data

### 📊 RAG Knowledge Base

- **FAISS vector search** over the ANAH 2026 guide (PDF chunked into ~1,200-character segments)
- **Mistral Embed** for semantic similarity — the AI can answer qualitative questions ("What conditions for MaPrimeRénov'?") by retrieving relevant excerpts from official documentation
- **Automatic index building** — the FAISS index is built on first startup if not present, and persisted for subsequent runs

### 📄 PDF Report

- **Auto-generated entitlement report** summarizing all calculated aids, eligibility conditions, required documents, and recommended next steps
- **Downloadable** directly from the chat interface
- **Shareable** via a unique link

---

## How It Works — The Agentic Loop

GreenRights uses **Mistral Large** in an agentic tool-calling loop. Here's what happens when a user sends a message:

```
┌─────────────┐
│  User sends  │
│  a message   │
└──────┬──────┘
       ▼
┌──────────────────────┐
│   Mistral Large      │──── Decides: reply directly, or call a tool?
│   (with 8 tools)     │
└──────┬──────┬────────┘
       │      │
  [no tool]  [tool_call]
       │      │
       ▼      ▼
┌──────────┐ ┌───────────────────────┐
│  Stream   │ │  Deterministic calc   │ ← reads JSON barème data
│  response │ │  (Python function)    │
│  via SSE  │ └───────────┬───────────┘
└──────────┘              │
                          ▼
                 ┌─────────────────┐
                 │  Result returned │ → model receives tool output
                 │  to Mistral      │ → may call more tools or respond
                 └─────────────────┘
```

The loop runs up to **10 iterations** per turn, allowing the agent to chain multiple tool calls (e.g., determine income bracket → calculate MPR → check stacking → respond with summary).

### The 8 Tools

| # | Tool | Purpose |
|---|---|---|
| 1 | `determine_income_bracket` | Classify household into bleu/jaune/violet/rose based on RFR, household size, and geography |
| 2 | `calculate_mpr_par_geste` | Compute MaPrimeRénov' amount for a specific renovation action |
| 3 | `calculate_mpr_ampleur` | Compute MaPrimeRénov' for accompanied full-renovation pathway |
| 4 | `calculate_mobility_aid` | Compute all applicable mobility subsidies |
| 5 | `check_zfe_vehicle` | Check if a vehicle is allowed in a city's Low Emission Zone |
| 6 | `check_stacking` | Verify aid compatibility and apply cumulation caps |
| 7 | `calculate_eco_ptz` | Compute Éco-PTZ eligible loan amount and duration |
| 8 | `search_anah_guide` | RAG search over the ANAH 2026 guide for qualitative information |

---

## Features

- 🏠 **Home Energy Renovation** — MaPrimeRénov' (par geste + ampleur), CEE Coup de pouce, Éco-PTZ
- 🚗 **Clean Mobility** — Prime à la conversion, Prime coup de pouce VE, bonus vélo, ZFE surprime
- 🤖 **Agentic AI** — Mistral Large with 8 deterministic tools — the LLM never invents amounts
- ⚡ **Real-time Streaming** — SSE token-by-token streaming with live markdown rendering
- 📊 **RAG Pipeline** — FAISS vector search over ANAH 2026 guide for qualitative queries
- 📄 **PDF Export** — Downloadable report with all calculated aids and action steps
- 🌓 **Dark / Light Mode** — Full theme support with system auto-detection
- 🎭 **Demo Profiles** — 3 pre-built profiles to test immediately

---

## Architecture

```
┌──────────────────────────────┐        ┌──────────────────────────────┐
│    Next.js 14 Frontend       │        │    FastAPI Backend            │
│                              │  SSE   │                              │
│  • Chat UI (streaming)       │───────▶│  • Mistral AI Agent          │
│  • Profile Sidebar           │◀───────│  • 8 Deterministic Tools     │
│  • PDF Download              │        │  • FAISS RAG Pipeline        │
│  • Dark / Light Theme        │        │  • PDF Generator (fpdf2)     │
└──────────────────────────────┘        └──────────────────────────────┘
         Netlify                            Hugging Face Spaces
```

### Tool-Calling Flow

```
User message → Mistral Large → [Tool Call] → Deterministic Calculator → [Result]
                    ↓                                                        ↓
              Final Response ←───────── Formatted with real amounts ────────←
```

> **The LLM NEVER computes amounts.** Every euro comes from verified barème data via tool calls.

---

## Tech Stack

| Component  | Technology                             |
| ---------- | -------------------------------------- |
| Frontend   | Next.js 14, TypeScript, Tailwind CSS   |
| Backend    | FastAPI, Python 3.12, Pydantic v2      |
| AI Model   | Mistral Large (`mistral-large-latest`) |
| Streaming  | Server-Sent Events (SSE)               |
| RAG        | FAISS IndexFlatIP + Mistral Embed      |
| Markdown   | react-markdown + remark-gfm           |
| PDF        | fpdf2                                  |
| Sessions   | In-memory with 24 h TTL                |

---

## Quick Start (Local)

### Prerequisites

- Python 3.12+
- Node.js 18+
- A [Mistral AI API key](https://console.mistral.ai/)

### 1. Clone & set up environment

```bash
git clone <your-repo-url>
cd mistral

python3.12 -m venv env
source env/bin/activate
pip install -r backend/requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
MISTRAL_API_KEY=your_mistral_api_key_here
MISTRAL_MODEL=mistral-large-latest
MISTRAL_EMBED_MODEL=mistral-embed
FRONTEND_URL=http://localhost:3000
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
```

### 3. Start the backend

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Start the frontend (new terminal)

```bash
cd frontend
npm install
npm run dev
```

### 5. Open

Visit **[http://localhost:3000](http://localhost:3000)**

---

## Docker (Local)

```bash
docker-compose up --build
```

This starts both backend (`:8000`) and frontend (`:3000`).

---

## Deployment

### Overview

| Service  | Platform            | What it runs               |
| -------- | ------------------- | -------------------------- |
| Backend  | Hugging Face Spaces | FastAPI + Mistral AI Agent |
| Frontend | Netlify             | Next.js static + SSR       |
| Source   | GitHub              | Full monorepo              |

---

### Step 0 — Push to GitHub

```bash
cd mistral
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/greenrights.git
git branch -M main
git push -u origin main
```

> The `.gitignore` already excludes `env/`, `node_modules/`, `.next/`, `__pycache__/`, `.env`, and FAISS binaries.

---

### Step 1 — Deploy the Backend on Hugging Face Spaces

Hugging Face Spaces supports Docker-based apps for free (with CPU).

#### 1.1 Create a new Space

1. Go to **[huggingface.co/new-space](https://huggingface.co/new-space)**
2. Fill in:
   - **Space name**: `greenrights-api`
   - **SDK**: **Docker**
   - **Visibility**: Public (or Private)
3. Click **Create Space**

#### 1.2 Push the backend

The `backend/` directory already contains a ready-to-use `Dockerfile` and `README.md` with HF metadata. Push it as the Space repo:

```bash
cd backend
git init
git remote add space https://huggingface.co/spaces/YOUR_USERNAME/greenrights-api
git add .
git commit -m "Initial deploy"
git push space main
```

> The Dockerfile listens on port **7860** as required by HF Spaces.

#### 1.3 Set secrets

In the Space **Settings → Secrets**, add:

| Secret Name           | Value                                 |
| --------------------- | ------------------------------------- |
| `MISTRAL_API_KEY`     | Your Mistral API key                  |
| `MISTRAL_MODEL`       | `mistral-large-latest`                |
| `MISTRAL_EMBED_MODEL` | `mistral-embed`                       |
| `FRONTEND_URL`        | `https://your-app.netlify.app`        |
| `EXTRA_CORS_ORIGINS`  | `https://your-app.netlify.app`        |

#### 1.4 Verify

HF auto-builds the Docker image. Once ready, your API is live at:

```
https://YOUR_USERNAME-greenrights-api.hf.space
```

```bash
curl https://YOUR_USERNAME-greenrights-api.hf.space/health
```

---

### Step 2 — Deploy the Frontend on Netlify

The frontend is pre-configured with `netlify.toml` and `@netlify/plugin-nextjs`.

#### 2.1 Set the backend URL

In Netlify dashboard (or via `frontend/.env.local` for CLI deploys):

```env
NEXT_PUBLIC_API_URL=https://YOUR_USERNAME-greenrights-api.hf.space
```

#### 2.2 Deploy to Netlify

**Option A — Netlify CLI:**

```bash
npm install -g netlify-cli
cd frontend
netlify login
netlify init
netlify deploy --build --prod
```

**Option B — GitHub integration (recommended):**

1. Push your repo to GitHub (Step 0)
2. Go to **[app.netlify.com](https://app.netlify.com)** → **"Add new site"** → **"Import an existing project"**
3. Select your repo
4. Configure:
   - **Base directory**: `frontend`
   - **Build command**: `npm run build`
   - **Publish directory**: `frontend/.next`
5. Add environment variable in **Site settings → Environment variables**:
   - `NEXT_PUBLIC_API_URL` = `https://YOUR_USERNAME-greenrights-api.hf.space`
6. Click **Deploy site**

#### 2.3 Verify

Visit your Netlify URL (`https://your-app.netlify.app`):

1. Click **"Commencer"** → creates a session
2. Type a message → tokens stream in real-time
3. Provide income data → AI calls tools and shows exact amounts

---

### Deployment Checklist

- [ ] Code pushed to **GitHub** (`.gitignore` excludes secrets & build artifacts)
- [ ] Backend `Dockerfile` uses port `7860` for HF Spaces
- [ ] `MISTRAL_API_KEY` set in HF Space **Secrets**
- [ ] `EXTRA_CORS_ORIGINS` set in HF Space **Secrets** → your Netlify domain
- [ ] `NEXT_PUBLIC_API_URL` set in Netlify **Environment variables** → HF Space URL
- [ ] `@netlify/plugin-nextjs` installed and `netlify.toml` present
- [ ] Test `/health` endpoint on HF Space
- [ ] Test chat streaming on Netlify site

---

## API Endpoints

| Method | Endpoint                        | Description                    |
| ------ | ------------------------------- | ------------------------------ |
| POST   | `/api/session`                  | Create a new chat session      |
| POST   | `/api/chat`                     | Send a message (non-streaming) |
| POST   | `/api/chat/stream`              | Send a message (SSE streaming) |
| GET    | `/api/session/{id}/history`     | Get conversation history       |
| POST   | `/api/calculate/income-bracket` | Determine income bracket       |
| POST   | `/api/calculate/mpr-par-geste`  | Calculate MPR per action       |
| POST   | `/api/calculate/mpr-ampleur`    | Calculate MPR ampleur          |
| POST   | `/api/calculate/mobility`       | Calculate mobility aids        |
| POST   | `/api/calculate/zfe-check`      | Check ZFE vehicle compliance   |
| POST   | `/api/calculate/stacking`       | Check aid compatibility        |
| POST   | `/api/calculate/eco-ptz`        | Calculate Éco-PTZ              |
| GET    | `/api/calculate/gestes`         | List renovation actions        |
| POST   | `/api/report/generate`          | Generate entitlement report    |
| GET    | `/api/report/{id}/pdf`          | Download PDF report            |
| GET    | `/api/report/{id}/share`        | Get shareable link             |
| GET    | `/api/demo-profiles`            | List demo profiles             |
| GET    | `/health`                       | Health check                   |

---

## Data Sources

All financial data is **hardcoded in JSON files** derived from official government publications. The AI never scrapes or guesses — it reads structured barème data.

| Source | File | Description |
|---|---|---|
| ANAH 2026 Barème | `subsidies.json` | Official MaPrimeRénov' amounts per geste & bracket (Arrêté du 14 janvier 2020, version 01/01/2026) |
| Income Thresholds | `income_thresholds.json` | Île-de-France and hors-IDF brackets for 2026 (based on 2025 tax notice, 2024 income) |
| Mobility Aids | `mobility_aids.json` | Prime coup de pouce VE (post-July 2025), prime à la conversion, bonus vélo, ZFE surprime |
| ZFE Zones | `zfe_zones.json` | 18 active Low Emission Zones with Crit'Air restrictions, enforcement status, and fine amounts |
| Stacking Rules | `stacking_rules.json` | Aid compatibility matrix — which aids can be combined, global caps (e.g., 100% of cost HT) |
| Regional Aids | `regional_aids.json` | Supplementary local aids (Île-de-France, Grand Lyon, etc.) |
| Demo Profiles | `demo_profiles.json` | 3 pre-built test personas with complete household data |

> **Last updated:** February 23, 2026 — reflects the reopening of MaPrimeRénov' and current ZFE enforcement status.

---

## Project Structure

```
mistral/
├── backend/
│   ├── Dockerfile               # HF Spaces Docker build (port 7860)
│   ├── README.md                # HF Spaces metadata (emoji, sdk, port)
│   ├── requirements.txt
│   └── app/
│       ├── agents/              # AI orchestrator, prompts & tool definitions
│       ├── calculators/         # Deterministic calculators (income, MPR, mobility…)
│       ├── data/                # JSON barème data (7 files)
│       ├── models/              # Pydantic schemas (session, citizen, property…)
│       ├── rag/                 # FAISS vector search pipeline
│       ├── routers/             # FastAPI endpoints (chat, calculate, report)
│       ├── services/            # Session store, PDF generator
│       ├── scripts/             # PDF download utility
│       ├── config.py            # Pydantic Settings
│       └── main.py              # App entry point + lifespan
├── frontend/
│   ├── netlify.toml             # Netlify build config + Next.js plugin
│   ├── package.json
│   ├── next.config.js           # Standalone (Docker) or default (Netlify)
│   └── src/
│       ├── app/
│       │   ├── page.tsx             # Landing page
│       │   ├── chat/page.tsx        # Chat UI (streaming)
│       │   ├── api/chat/stream/     # SSE Route Handler (proxy)
│       │   └── globals.css          # Tailwind + prose-chat styles
│       └── components/              # ThemeToggle, ProfileSidebar
├── docker-compose.yml           # Local full-stack dev
├── Dockerfile.backend           # Docker-compose backend (port 8000)
├── Dockerfile.frontend          # Docker-compose frontend
├── .env.example                 # Backend env template
├── .gitignore
└── README.md
```

---

## Environment Variables

### Backend (`.env`)

| Variable              | Required | Default                 | Description                            |
| --------------------- | -------- | ----------------------- | -------------------------------------- |
| `MISTRAL_API_KEY`     | Yes      | —                       | Mistral AI API key                     |
| `MISTRAL_MODEL`       | No       | `mistral-large-latest`  | Chat model                             |
| `MISTRAL_EMBED_MODEL` | No       | `mistral-embed`         | Embedding model (RAG)                  |
| `FRONTEND_URL`        | No       | `http://localhost:3000`  | Primary CORS allowed origin            |
| `EXTRA_CORS_ORIGINS`  | No       | —                       | Additional CORS origins (comma-sep)    |
| `BACKEND_HOST`        | No       | `0.0.0.0`              | Server bind host                       |
| `BACKEND_PORT`        | No       | `8000`                  | Server bind port                       |

### Frontend (`frontend/.env.local`)

| Variable              | Required | Default                 | Description            |
| --------------------- | -------- | ----------------------- | ---------------------- |
| `NEXT_PUBLIC_API_URL` | No       | `http://localhost:8000`  | Backend API base URL   |

---

## Who Is This For?

| Audience | How They Use GreenRights |
|---|---|
| **French homeowners** | Discover renovation subsidies they qualify for, get exact amounts before contacting contractors |
| **Tenants & landlords** | Check which aids apply to rental properties (some MPR gestes are landlord-eligible) |
| **Car owners in ZFE cities** | Find out if their vehicle is banned, and what financial help exists to switch |
| **France Rénov' advisors** | Use as a quick pre-screening tool before in-depth consultations |
| **Developers & AI builders** | Study a production-quality example of agentic tool-calling with Mistral AI |

---

## Design Decisions

| Decision | Rationale |
|---|---|
| **LLM never computes amounts** | Eliminates hallucinated financial figures — every euro is traceable to a JSON barème entry |
| **SSE streaming** | Users see tokens appear in real-time, reducing perceived latency during tool-calling loops |
| **In-memory sessions** | Simple, no database needed — appropriate for a demo; sessions auto-expire after 24h |
| **JSON barème files** | Easy to update when government publishes new rates — no database migrations needed |
| **FAISS (not a vector DB)** | Lightweight, no external service — the index is small enough (~500 chunks) to fit in memory |
| **Next.js rewrites** | Frontend proxies `/api/*` to the backend — avoids CORS issues during local development |

---

## License

MIT — Educational / demonstration project. Not affiliated with the French government.

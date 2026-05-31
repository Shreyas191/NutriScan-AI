<div align="center">

# 🧬 NutriScan AI

### *From Bloodwork to Basket — Automatically.*

An AI-powered health assistant that transforms uploaded bloodwork PDFs into actionable nutrition decisions. Upload a lab report, detect deficiencies, get plain-English explanations, and have an Instacart cart automatically filled — all in under 60 seconds.

[![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)](https://python.org/)
[![Groq](https://img.shields.io/badge/LLM-Groq%20Llama%203.3-F55036?logo=meta)](https://groq.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Agentic Pipeline](#-agentic-pipeline)
- [Cart Automation](#-cart-automation)
- [Getting Started](#-getting-started)
- [Environment Variables](#-environment-variables)
- [Project Structure](#-project-structure)
- [API Reference](#-api-reference)
- [Roadmap](#-roadmap)
- [Disclaimer](#-disclaimer)

---

## 🔍 Overview

Most people receive lab reports and don't know what to do with them. **NutriScan AI** bridges the gap between clinical data and real-world action — it reads your bloodwork, identifies what's low, explains it simply, and builds a grocery cart with the foods and supplements to fix it.

**The full pipeline:**

```
📄 PDF Upload  →  🔬 OCR Extraction  →  🧠 AI Agent Analysis
→  🍎 Food Recommendations  →  🛒 Instacart Cart Auto-filled
```

---

## ✨ Features

### 📄 Smart PDF Ingestion
- Accepts both digital and scanned bloodwork PDFs
- Dual OCR: **pdfplumber** for digital PDFs, **Tesseract** for scanned images
- Confidence scoring to detect low-quality extractions

### 🧠 Autonomous AI Agent
- An agentic reasoning loop (powered by **Groq + Llama 3.3 70B**) autonomously calls tools step-by-step
- Streams live reasoning steps to the frontend via Server-Sent Events (SSE)
- Falls back gracefully through a model chain if rate limits are hit

### 🔬 Deficiency Detection
- Rule-based clinical threshold engine — no LLM hallucination risk for classification
- Severity levels: **Normal / Insufficient / Severe**
- Covers common biomarkers: Vitamin D, B12, Iron, Ferritin, Folate, Calcium, TSH, and more

### 💬 Plain-English Explanations
- LLM-generated explanations per deficiency — clear, non-alarmist, and actionable
- Explains what the biomarker does, what being low means, and how food can help

### 🥗 Personalised Nutrition Recommendations
- Evidence-based food and supplement mapping per deficiency
- Dietary preference filters: Vegan, Vegetarian, Lactose-Free, Gluten-Free, Nut-Free
- Severity-adjusted quantity guidance

### 🛒 Automated Instacart Cart
- Playwright-based browser automation fills your Instacart cart automatically
- Uses cookie-exported sessions from your real Chrome — no bot detection issues
- Streams live progress logs to the frontend via SSE

### 🔐 Authentication
- **Clerk** for sign-up / sign-in flows
- JWT verification on all backend endpoints
- Protected routes on both frontend and backend

---

## 🏗 Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     Frontend  (Next.js 16)                       │
│          Neumorphic UI · TypeScript · Clerk Auth · SSE           │
│                                                                  │
│  /upload ──────────────────── streams live agent reasoning       │
│  /results ─────────────────── biomarkers, deficiencies, foods    │
│  /cart ────────────────────── marketplace selector + auto-shop   │
└───────────────────────────┬──────────────────────────────────────┘
                            │  REST + SSE  (localhost:8000)
┌───────────────────────────▼──────────────────────────────────────┐
│                      Backend  (FastAPI)                          │
│                                                                  │
│  POST /api/upload/stream                                         │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                  AI Agent Loop  (agent.py)                 │  │
│  │                                                            │  │
│  │  ① extract_text_from_pdf  →  pdfplumber / Tesseract       │  │
│  │  ② extract_biomarkers     →  Groq Llama 3.3 70B           │  │
│  │  ③ detect_deficiencies    →  rule-based threshold engine   │  │
│  │  ④ generate_explanations  →  Groq Llama 3.3 70B           │  │
│  │  ⑤ recommend_foods        →  Groq Llama 3.3 70B           │  │
│  │  ⑥ build_shopping_carts   →  Instacart API + link builder │  │
│  │                                                            │  │
│  │  Each step streamed as SSE  ──────────────────────────►   │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  POST /api/cart/auto-shop                                        │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │             Playwright Cart Automation                     │  │
│  │   instacart_cart.py  →  Chrome + cookie session           │  │
│  │   Searches each item → clicks Add → streams log via SSE   │  │
│  └────────────────────────────────────────────────────────────┘  │
└───────────────────────────┬──────────────────────────────────────┘
                            │
           ┌────────────────┼────────────────┐
           ▼                ▼                ▼
    ┌────────────┐  ┌──────────────┐  ┌───────────┐
    │  Supabase  │  │   Supabase   │  │  Sentry   │
    │ PostgreSQL │  │   Storage    │  │ Monitoring│
    └────────────┘  └──────────────┘  └───────────┘
```

---

## 🛠 Tech Stack

### Frontend

| Technology | Role |
|-----------|------|
| **Next.js 16** (App Router) | Framework, SSR, routing |
| **TypeScript** | Type safety |
| **Tailwind CSS 4** | Utility styling |
| **Neumorphism Design System** | Custom soft-UI design tokens (CSS variables + dual-shadow system) |
| **Plus Jakarta Sans / DM Sans** | Typography |
| **Clerk** | Authentication (sign-up, sign-in, JWT) |
| **Lucide React** | Icons |
| **Server-Sent Events (SSE)** | Live streaming of agent reasoning steps and cart logs |

### Backend

| Technology | Role |
|-----------|------|
| **FastAPI** | API framework |
| **Python 3.11** | Runtime |
| **Groq API** (Llama 3.3 70B) | Primary LLM — biomarker extraction, explanations, recommendations |
| **Groq model fallback chain** | Auto-rotates on 429/413 errors through 5 models |
| **pdfplumber** | OCR for digital PDFs |
| **Tesseract** | OCR for scanned PDFs |
| **Playwright** | Browser automation for Instacart cart filling |
| **SQLAlchemy** (async) | ORM |
| **Alembic** | Database migrations |
| **Supabase** | PostgreSQL + file storage |
| **Clerk JWT** | Backend auth verification |
| **Sentry** | Error tracking |

---

## 🤖 Agentic Pipeline

The core of NutriScan AI is an **autonomous tool-calling loop** in `agent.py`. Rather than a fixed sequential pipeline, the LLM decides which tool to call next based on the current state:

```
System prompt → [tool loop, max 15 iterations]
    ↓
  model output has tool_calls?
    ├── YES → execute tool, add result to context, loop
    └── NO  → return final text response
```

**Tools available to the agent:**

| Tool | What it does |
|------|-------------|
| `extract_text_from_pdf` | Runs pdfplumber or Tesseract on the uploaded PDF bytes |
| `extract_biomarkers` | Sends OCR text to Groq → returns structured JSON of biomarker values |
| `detect_deficiencies` | Compares biomarkers against clinical thresholds (rule-based, no LLM) |
| `generate_explanations` | Sends deficiencies to Groq → plain-English explanation per deficiency |
| `recommend_foods` | Sends deficiencies + dietary prefs to Groq → food/supplement list |
| `build_shopping_carts` | Builds Instacart shopping links from recommendations |

**Model fallback chain** (auto-rotates on rate limits):
```
llama-3.3-70b-versatile → openai/gpt-oss-20b → openai/gpt-oss-120b
→ meta-llama/llama-4-scout-17b-16e-instruct → llama-3.1-8b-instant
```

Each step is streamed to the frontend in real-time via SSE so users watch the agent think.

---

## 🛒 Cart Automation

Cart filling uses **Playwright** with a real Chrome browser session — not headless, to avoid bot detection.

### How it works

1. Export cookies from your logged-in Chrome browser using `browser_cookie3`
2. Save them to `backend/playwright_data/instacart_auth.json`
3. Playwright loads the session, navigates to `instacart.com/store`, searches each item, and clicks Add

### Refreshing the session (when cookies expire)

```bash
cd backend
python3 -c "
import browser_cookie3, json, os
cookies = []
for domain in ['instacart.com', '.instacart.com', 'www.instacart.com']:
    for c in browser_cookie3.chrome(domain_name=domain.lstrip('.')):
        cookies.append({'name':c.name,'value':c.value,'domain':c.domain,
            'path':c.path,'expires':c.expires or -1,'httpOnly':False,
            'secure':bool(c.secure),'sameSite':'Lax'})
os.makedirs('playwright_data', exist_ok=True)
with open('playwright_data/instacart_auth.json','w') as f:
    json.dump({'cookies':cookies,'origins':[]},f)
print(f'Saved {len(cookies)} cookies')
"
```

> **Note on Walmart:** Walmart's PerimeterX bot-detection blocks all Playwright automation (headless, headed, and stealth). Instacart is the primary supported retailer.

---

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- Tesseract OCR — `brew install tesseract` (macOS)
- Poppler — `brew install poppler` (macOS)
- A [Groq](https://console.groq.com) account (free tier)
- A [Clerk](https://clerk.com) project
- A [Supabase](https://supabase.com) project (optional for MVP — data stored in-memory without it)

### 1. Clone

```bash
git clone https://github.com/Shreyas191/NutriScan-AI.git
cd NutriScan-AI
```

### 2. Backend

```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Fill in GROQ_API_KEY, CLERK_SECRET_KEY, CLERK_JWKS_URL, CLERK_ISSUER
# DATABASE_URL and SUPABASE_* are optional for local development

# Start the server
uvicorn app.main:app --reload --port 8000
```

API docs available at `http://localhost:8000/docs`

### 3. Frontend

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local
echo "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_key" > .env.local
echo "CLERK_SECRET_KEY=your_secret" >> .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" >> .env.local

# Start the dev server
npm run dev
```

Frontend available at `http://localhost:3000`

### 4. Instacart Cart (optional)

To use the auto-shop feature, export your Instacart session cookies (see [Cart Automation](#-cart-automation) above) before triggering a cart fill.

---

## 🔑 Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | ✅ | Primary LLM — get free key at [console.groq.com](https://console.groq.com) |
| `CLERK_SECRET_KEY` | ✅ | Clerk backend secret |
| `CLERK_JWKS_URL` | ✅ | e.g. `https://your-app.clerk.accounts.dev/.well-known/jwks.json` |
| `CLERK_ISSUER` | ✅ | e.g. `https://your-app.clerk.accounts.dev` |
| `DATABASE_URL` | ⚠️ optional | PostgreSQL connection string (in-memory fallback for MVP) |
| `SUPABASE_URL` | ⚠️ optional | Supabase project URL |
| `SUPABASE_KEY` | ⚠️ optional | Supabase anon key |
| `SENTRY_DSN` | ⚠️ optional | Error tracking |
| `CEREBRAS_API_KEY` | ⚠️ optional | Fallback LLM for cart automation |
| `OPENROUTER_API_KEY` | ⚠️ optional | Fallback LLM for cart automation |

### Frontend (`frontend/.env.local`)

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk public key |
| `CLERK_SECRET_KEY` | Clerk secret key |
| `NEXT_PUBLIC_API_URL` | Backend URL (default: `http://localhost:8000`) |

---

## 📁 Project Structure

```
NutriScan-AI/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── instacart_cart.py      # Playwright Instacart automation (primary)
│   │   │   └── playwright_cart.py     # Playwright Walmart (blocked — fallback only)
│   │   ├── models/
│   │   │   ├── biomarker.py           # Pydantic response models
│   │   │   └── db_models.py           # SQLAlchemy ORM (users, reports, biomarkers…)
│   │   ├── routes/
│   │   │   ├── reports.py             # POST /api/upload, GET /api/reports/{id}
│   │   │   └── cart.py                # POST /api/cart/auto-shop
│   │   ├── services/
│   │   │   ├── agent.py               # Autonomous tool-calling loop (main pipeline)
│   │   │   ├── analysis_pipeline.py   # Orchestration wrapper + deterministic fallbacks
│   │   │   ├── gemini_client.py       # Groq LLM wrapper (legacy name — wraps Groq, not Gemini)
│   │   │   ├── ocr_service.py         # pdfplumber + Tesseract OCR
│   │   │   ├── biomarker_extractor.py # LLM → structured biomarker JSON
│   │   │   ├── deficiency_engine.py   # Rule-based clinical threshold classification
│   │   │   ├── explanation_generator.py # LLM → plain-English explanations
│   │   │   ├── food_recommender.py    # LLM → food + supplement recommendations
│   │   │   ├── shopping.py            # Cart link builder (Instacart + Amazon)
│   │   │   ├── instacart.py           # Instacart Developer Platform API
│   │   │   └── storage.py             # Supabase file storage
│   │   ├── auth.py                    # Clerk JWT verification dependency
│   │   ├── config.py                  # pydantic-settings config
│   │   ├── database.py                # SQLAlchemy async engine + session
│   │   └── main.py                    # FastAPI app entry point
│   ├── alembic/                       # Database migrations
│   ├── scripts/
│   │   └── verify_shopping.py         # Local script to test cart automation
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── page.tsx               # Landing page
│       │   ├── upload/page.tsx        # PDF upload + live agent reasoning
│       │   ├── results/page.tsx       # Analysis results
│       │   ├── cart/page.tsx          # Grocery cart + auto-shop
│       │   ├── dashboard/page.tsx     # Report history
│       │   ├── sign-in/               # Clerk sign-in
│       │   └── sign-up/               # Clerk sign-up
│       ├── components/
│       │   ├── Navbar.tsx
│       │   ├── Footer.tsx
│       │   ├── CartItem.tsx
│       │   ├── DeficiencyCard.tsx
│       │   ├── DietaryPreferenceSelector.tsx
│       │   ├── ExplanationPanel.tsx
│       │   ├── FoodRecommendation.tsx
│       │   └── MedicalDisclaimer.tsx
│       └── lib/
│           └── api.ts                 # Typed API client (fetch + SSE)
├── CLAUDE.md                          # Codebase context for AI assistants
├── .gitignore
└── README.md
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `POST` | `/api/upload` | Upload PDF, run agent, return full JSON result |
| `POST` | `/api/upload/stream` | Upload PDF, stream agent reasoning steps via SSE |
| `GET` | `/api/reports/{id}` | Fetch saved analysis result by report ID |
| `POST` | `/api/cart/auto-shop` | Add items to Instacart cart via Playwright (SSE) |

**SSE event types (`/api/upload/stream`):**

| Event | Payload |
|-------|---------|
| `step` | `{ step_number, action, tool_name, reasoning, result_summary }` |
| `done` | `{ report_id, biomarker_count, deficiency_count, recommendation_count }` |
| `error` | `{ error: string }` |

**SSE events (`/api/cart/auto-shop`):**

| Field | Description |
|-------|-------------|
| `log` | Progress line (browser opened, item searched, item added, etc.) |
| `status: "done"` | All items processed |
| `error` | Something went wrong |

> Interactive Swagger docs at `http://localhost:8000/docs`

---

## 🗺 Roadmap

- [x] PDF upload with dual OCR (pdfplumber + Tesseract)
- [x] Autonomous AI agent with live reasoning stream
- [x] Rule-based deficiency classification engine
- [x] LLM-generated plain-English explanations
- [x] Personalised food & supplement recommendations
- [x] Dietary preference filters
- [x] Instacart cart automation (Playwright + cookie session)
- [x] Neumorphic UI design system
- [x] Clerk authentication
- [ ] Supabase persistence (schema ready, routes use in-memory for now)
- [ ] Dashboard with report history
- [ ] Multi-deficiency cross-analysis
- [ ] Personalised weekly meal plans
- [ ] Supplement subscription automation
- [ ] Predictive deficiency trend modeling

---

## ⚠️ Disclaimer

**NutriScan AI is not a medical device and does not provide medical advice, diagnosis, or treatment.** All information is for educational and informational purposes only. AI-generated explanations and recommendations are not a substitute for advice from a qualified healthcare provider. Always consult your doctor before making changes to your diet or supplement regimen based on lab results.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

**Built by [Shreyas Kaldate](https://github.com/Shreyas191)**

</div>

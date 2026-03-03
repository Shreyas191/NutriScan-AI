<div align="center">

# 🧬 NutriScan AI

### *From Bloodwork to Basket — Automatically.*

An AI-powered health assistant that transforms uploaded bloodwork reports into actionable nutrition decisions. Upload a lab report, detect deficiencies, and get a personalized grocery cart — all in under 60 seconds.

[![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)](https://python.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-4-06B6D4?logo=tailwindcss)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
- [Environment Variables](#-environment-variables)
- [Project Structure](#-project-structure)
- [API Endpoints](#-api-endpoints)
- [Roadmap](#-roadmap)
- [Disclaimer](#-disclaimer)
- [License](#-license)

---

## 🔍 Overview

Patients frequently receive lab reports but struggle to understand medical terminology, ignore mild deficiencies, and lack clear next steps. **NutriScan AI** bridges the gap between clinical diagnostics and real-world behavior change by converting lab results into immediate nutritional action.

**The Pipeline:**

```
📄 PDF Upload → 🔬 OCR Extraction → 🧠 AI Analysis → 🍎 Food Recommendations → 🛒 Grocery Cart
```

---

## ✨ Features

### 🔬 Smart Lab Report Analysis
- Upload bloodwork PDFs (scanned or digital)
- OCR-powered extraction via **Tesseract** with confidence scoring
- AI-driven biomarker extraction into structured JSON

### 🧠 AI-Powered Deficiency Detection
- Threshold-based classification engine (Severe / Insufficient / Normal)
- Plain-English explanations — clear, actionable, and non-alarmist
- Powered by **Google Gemini** and **Anthropic Claude**

### 🥗 Personalized Nutrition Recommendations
- Evidence-based food and supplement mapping per deficiency
- Dietary preference support (vegan, lactose-free, gluten-free, etc.)
- Severity-adjusted intake guidance

### 🛒 Automated Grocery Integration
- Auto-generated grocery cart from recommendations
- **Instacart** and **Walmart** integration via browser automation
- Cart preview with edit, remove, and substitute controls
- One-click checkout redirect

### 🔐 Secure Authentication
- **Clerk** integration with sign-up/sign-in flows
- JWT-based backend validation
- Protected routes and session management

### 📊 Interactive Dashboard
- Deficiency overview with severity indicators
- Detailed explanation cards per biomarker
- Recommended foods & supplements sections
- Report history tracking

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js 16)                     │
│           Tailwind CSS · Clerk Auth · TypeScript             │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST API
┌──────────────────────────▼──────────────────────────────────┐
│                    Backend (FastAPI)                         │
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │  OCR Service │  │  AI Analysis │  │ Deficiency Engine │  │
│  │  (Tesseract) │  │ (Gemini/     │  │ (Rule-based       │  │
│  │              │  │  Claude)     │  │  Classification)  │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬──────────┘  │
│         │                 │                    │             │
│  ┌──────▼─────────────────▼────────────────────▼──────────┐ │
│  │              Analysis Pipeline                         │ │
│  │  PDF → OCR → Extraction → Detection → Recommendations │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐  │
│  │          Shopping Agents (Browser Automation)          │  │
│  │          Instacart · Walmart · Extensible              │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
     ┌──────────┐   ┌───────────┐   ┌───────────┐
     │ Supabase │   │ Supabase  │   │  Sentry   │
     │ Postgres │   │ Storage   │   │ Monitoring│
     └──────────┘   └───────────┘   └───────────┘
```

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 16, React 19, TypeScript, Tailwind CSS 4 |
| **Backend** | FastAPI, Uvicorn, Python 3.11 |
| **Authentication** | Clerk (JWT validation) |
| **Database** | Supabase PostgreSQL, SQLAlchemy, Alembic |
| **File Storage** | Supabase Storage |
| **OCR** | Tesseract, pdf2image, pdfplumber |
| **AI / LLM** | Google Gemini, Anthropic Claude |
| **Shopping Agents** | Browser-Use, Playwright |
| **Monitoring** | Sentry |
| **CI/CD** | GitHub Actions |
| **Containerization** | Docker |

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** 18+ and **npm**
- **Python** 3.11+
- **Tesseract OCR** (`brew install tesseract` on macOS)
- **Poppler** (`brew install poppler` on macOS)

### 1. Clone the Repository

```bash
git clone https://github.com/Shreyas191/NutriScan-AI.git
cd NutriScan-AI
```

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and database URL

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.local.example .env.local
# Edit .env.local with your Clerk keys and API URL

# Start the dev server
npm run dev
```

The frontend will be available at `http://localhost:3000` and the backend API docs at `http://localhost:8000/docs`.

### 4. Docker (Backend Only)

```bash
cd backend
docker build -t nutriscan-backend .
docker run -p 8000:8000 --env-file .env nutriscan-backend
```

---

## 🔑 Environment Variables

### Backend (`backend/.env`)

| Variable | Description |
|----------|------------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase anonymous key |
| `DATABASE_URL` | PostgreSQL connection string |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key |
| `CLERK_SECRET_KEY` | Clerk backend secret key |
| `CLERK_JWKS_URL` | Clerk JWKS endpoint URL |
| `CLERK_ISSUER` | Clerk token issuer URL |
| `SENTRY_DSN` | Sentry error tracking DSN |

### Frontend (`frontend/.env.local`)

| Variable | Description |
|----------|------------|
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk public key |
| `CLERK_SECRET_KEY` | Clerk secret key |
| `NEXT_PUBLIC_API_URL` | Backend API URL |

---

## 📁 Project Structure

```
NutriScan-AI/
├── backend/
│   ├── app/
│   │   ├── agents/              # AI agent configurations
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── routes/              # FastAPI route handlers
│   │   ├── services/
│   │   │   ├── ocr_service.py           # Tesseract OCR processing
│   │   │   ├── biomarker_extractor.py   # AI biomarker extraction
│   │   │   ├── deficiency_engine.py     # Rule-based deficiency detection
│   │   │   ├── explanation_generator.py # AI plain-English explanations
│   │   │   ├── food_recommender.py      # Nutrition recommendations
│   │   │   ├── analysis_pipeline.py     # End-to-end analysis orchestrator
│   │   │   ├── instacart.py             # Instacart integration
│   │   │   ├── walmart_agent.py         # Walmart browser agent
│   │   │   ├── shopping_agent.py        # Generic shopping orchestrator
│   │   │   └── storage.py              # Supabase file storage
│   │   ├── auth.py              # JWT authentication
│   │   ├── config.py            # App configuration
│   │   ├── database.py          # Database connection
│   │   └── main.py              # FastAPI app entry point
│   ├── alembic/                 # Database migrations
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── page.tsx         # Landing page
│       │   ├── dashboard/       # User dashboard
│       │   ├── upload/          # PDF upload page
│       │   ├── results/         # Analysis results page
│       │   ├── cart/            # Grocery cart page
│       │   ├── sign-in/         # Authentication
│       │   └── sign-up/         # Registration
│       ├── components/
│       │   ├── DeficiencyCard.tsx
│       │   ├── ExplanationPanel.tsx
│       │   ├── FoodRecommendation.tsx
│       │   ├── CartItem.tsx
│       │   ├── DietaryPreferenceSelector.tsx
│       │   ├── MedicalDisclaimer.tsx
│       │   ├── Navbar.tsx
│       │   └── Footer.tsx
│       └── lib/
│           └── api.ts           # Backend API client
├── .github/workflows/           # CI/CD pipelines
└── .gitignore
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/upload` | Upload a bloodwork PDF |
| `GET` | `/reports` | List user's lab reports |
| `GET` | `/reports/{id}` | Get report details & analysis |
| `POST` | `/analyze` | Trigger OCR + AI analysis pipeline |
| `GET` | `/recommendations/{report_id}` | Get food & supplement recommendations |
| `GET` | `/cart/{report_id}` | Get generated cart items |

> 📖 Full interactive API docs available at `http://localhost:8000/docs` when running the backend.

---

## 🗺 Roadmap

- [x] PDF upload & OCR processing
- [x] AI-powered biomarker extraction
- [x] Deficiency detection engine
- [x] Plain-English explanation generation
- [x] Food & supplement recommendations
- [x] Instacart grocery integration
- [x] Walmart shopping agent
- [x] Clerk authentication
- [x] Interactive dashboard
- [x] Dietary preference support
- [ ] Multi-deficiency cross-analysis
- [ ] Personalized meal plans
- [ ] Supplement subscription automation
- [ ] Wearable device integrations
- [ ] Predictive deficiency modeling
- [ ] Telehealth integration

---

## ⚠️ Disclaimer

> **NutriScan AI is not a medical device and does not provide medical advice, diagnosis, or treatment.** All information is for educational and informational purposes only. The AI-generated explanations and recommendations are not a substitute for professional medical advice. Always consult with a qualified healthcare provider before making changes to your diet or supplement regimen based on lab results.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

**Built with ❤️ by [Shreyas Kaldate](https://github.com/Shreyas191)**

</div>

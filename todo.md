# NutriScan AI — Development Todo List

Derived from [prd.txt](file:///Users/shreyaskaldate/Desktop/NutriScan%20AI/prd.txt) and [techstack.txt](file:///Users/shreyaskaldate/Desktop/NutriScan%20AI/techstack.txt).

---

## 1. Project Setup & Infrastructure

- [x] Initialize **Next.js 14** (App Router) project with TypeScript & Tailwind CSS
- [x] Initialize **FastAPI** backend project with Uvicorn
- [ ] Set up **Supabase** project (PostgreSQL + Storage) *(requires account setup)*
- [ ] Set up **GitHub** repository with branching strategy *(requires `git init` + remote)*
- [x] Configure **GitHub Actions** CI/CD pipeline
- [x] Create **Docker** configuration for the FastAPI backend
- [ ] Configure **Vercel** deployment for frontend *(requires account setup)*
- [ ] Configure **Render / Railway** deployment for backend *(requires account setup)*

---

## 2. Authentication

- [x] Integrate **Clerk** (Free Tier) into Next.js frontend
- [x] Implement sign-up / sign-in flows
- [x] Configure **JWT** token validation in FastAPI backend
- [x] Implement role-based access control (RBAC)
- [x] Add session management and protected routes

---

## 3. Database & Storage

- [x] Design PostgreSQL schema (users, lab reports, biomarkers, deficiency history, analytics)
- [x] Set up **SQLAlchemy** ORM models
- [x] Configure **Alembic** for database migrations
- [x] Create initial migration scripts
- [x] Configure **Supabase Storage** bucket for PDF uploads
- [x] Implement secure file upload flow (Frontend → Supabase Storage)

---

## 4. Frontend (Next.js)

- [x] Design and implement **landing page** with product value proposition
- [x] Build **user dashboard** layout
  - [x] Identified deficiencies display
  - [x] Plain-language explanation cards
  - [x] Recommended foods & supplements section
- [x] Build **PDF upload** component (drag-and-drop / file picker)
- [x] Build **results/analysis** page showing parsed lab data
- [x] Build **grocery cart preview** page
  - [x] Edit / remove items
  - [x] Substitute products
  - [x] "Shop on Instacart" redirect button
- [x] Implement **dietary preference** selector (vegan, lactose-free, etc.)
- [x] Add loading states and progress indicators (< 60s target)
- [x] Implement responsive design for mobile & desktop
- [x] Add medical disclaimer banner/modal

---

## 5. Backend — API Layer (FastAPI)

- [ ] Define API routes:
  - [ ] `POST /upload` — receive and store PDF
  - [ ] `GET /reports` — list user's lab reports
  - [ ] `GET /reports/{id}` — get report details & analysis
  - [ ] `POST /analyze` — trigger OCR + AI pipeline
  - [ ] `GET /recommendations/{report_id}` — get food/supplement recs
  - [ ] `GET /cart/{report_id}` — get generated cart items & Instacart URLs
- [ ] Implement request validation with **Pydantic** models
- [ ] Add error handling and structured error responses
- [ ] Implement audit logging for all sensitive operations

---

## 6. OCR Layer

- [ ] Integrate **Tesseract** OCR into the backend container
- [ ] Implement PDF-to-image conversion pipeline
- [ ] Extract raw text from uploaded lab report PDFs
- [ ] Implement **confidence scoring** for OCR output
- [ ] Add validation checks to flag low-confidence extractions
- [ ] Support both scanned and digital PDF formats

---

## 7. AI & Extraction Layer (OpenAI)

- [ ] Integrate **OpenAI API** client in backend
- [ ] Build prompt pipeline: `Raw OCR Text → OpenAI → Structured JSON`
  - [ ] Extract test name, result value, units, and reference range
  - [ ] Output validated biomarker JSON
- [ ] Build **AI explanation generator**
  - [ ] Plain-English summary of each deficiency
  - [ ] Tone: clear, actionable, non-alarmist, non-diagnostic
  - [ ] Include encouragement to consult a healthcare provider
- [ ] Build **food recommendation generator**
  - [ ] Evidence-based nutrient-to-food mapping
  - [ ] Respect dietary preferences
  - [ ] Avoid medical dosing claims

---

## 8. Deficiency Detection Engine

- [ ] Implement **threshold-based classification** rules in pure Python
  - [ ] MVP: Vitamin D only (Severe / Insufficient / Normal)
- [ ] Define Pydantic validation models for biomarker data
- [ ] Map severity → health implications → suggested daily intake
- [ ] Add clinically verified threshold rules
- [ ] Design engine to be extensible for future multi-marker support

---

## 9. Grocery Integration (Instacart Redirect)

- [ ] Build **query builder** that converts food list → Instacart search URL
- [ ] Generate dynamic redirect links per deficiency
- [ ] Implement "Shop for [Nutrient] Foods" CTA on frontend
- [ ] Add fallback substitutions if primary items unavailable
- [ ] Support manual cart editing before redirect

---

## 10. Monitoring & Error Tracking

- [ ] Integrate **Sentry** (Free Tier) into FastAPI backend
- [ ] Integrate **Sentry** into Next.js frontend
- [ ] Configure crash and performance monitoring
- [ ] Set up alert rules for critical errors

---

## 11. Non-Functional Requirements

- [ ] Ensure PDF analysis completes within **60 seconds**
- [ ] Target system uptime **> 99%**
- [ ] Implement **TLS 1.2+** for all data in transit
- [ ] Implement **encrypted file storage** for PDFs
- [ ] Build **HIPAA-ready** architecture foundations
- [ ] Add clear **medical disclaimer** ("not medical advice")
- [ ] Ensure no resale/sharing of health data

---

## 12. Testing & Quality

- [ ] Write unit tests for deficiency detection engine
- [ ] Write unit tests for OCR confidence scoring
- [ ] Write integration tests for the full upload → analysis pipeline
- [ ] Test with multiple lab report formats
- [ ] End-to-end test: PDF upload → dashboard → Instacart redirect
- [ ] Performance test: verify < 60s end-to-end latency

---

## 13. Documentation & Legal

- [ ] Write API documentation (auto-generated via FastAPI `/docs`)
- [ ] Write user-facing FAQ / How It Works page
- [ ] Draft Terms of Service & Privacy Policy
- [ ] Add medical disclaimer copy (non-diagnostic positioning)
- [ ] Document upgrade path (Instacart API, AWS HIPAA infra)

---

> **MVP Scope (8–10 Weeks):** PDF upload, Vitamin D detection only, AI explanation, basic nutrition mapping, Instacart cart redirect, manual cart review.
>
> **Excluded from MVP:** Multi-marker optimization, subscription automation, wearable integrations, predictive analytics.

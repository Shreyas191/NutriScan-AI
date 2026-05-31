# NutriScan AI — Codebase Context

## What This App Does
"From Bloodwork to Basket" — user uploads a blood test PDF → AI extracts biomarkers → detects deficiencies → recommends foods/supplements → builds a Walmart/Amazon shopping cart.

## Stack

### Backend (`/backend`)
- **Framework:** FastAPI (Python)
- **Database:** PostgreSQL via SQLAlchemy async + Supabase
- **Auth:** Clerk (JWT verification)
- **Error tracking:** Sentry
- **OCR:** pdfplumber (digital PDFs) + Tesseract (scanned PDFs)

### Frontend (`/frontend`)
- **Framework:** Next.js 14 (App Router)
- **Auth:** Clerk
- **Pages:** `/`, `/upload`, `/results`, `/dashboard`, `/cart`, `/sign-in`, `/sign-up`

---

## AI / LLM Provider

**Active provider: Groq** (free tier, Llama 3.3 70B + fallbacks)

> `gemini_client.py` is **misleadingly named** — it actually wraps the Groq API via `AsyncGroq`. There is NO active Gemini usage. `GEMINI_API_KEY` in config is marked "legacy, unused".

### LLM clients
| File | Purpose | Actual Provider |
|------|---------|----------------|
| `app/services/gemini_client.py` | Core LLM wrapper | **Groq** (`AsyncGroq`) |
| `app/services/claude_client.py` | Exists but unused in main pipeline | Anthropic Claude |

### Model fallback chain (`gemini_client.py`)
**Tool-calling:** `llama-3.3-70b-versatile` → `openai/gpt-oss-20b` → `openai/gpt-oss-120b` → `meta-llama/llama-4-scout-17b-16e-instruct` → `llama-3.1-8b-instant`

**Text/JSON:** Same chain + `qwen/qwen3-32b`

Auto-rotates on 429 (rate limit), 413 (too large), or decommissioned model errors.

---

## Agent Architecture (`app/services/agent.py`)

Autonomous agentic loop powered by Groq tool-calling:

1. **System prompt** instructs the model to reason step-by-step
2. **Tool loop** (max 15 iterations):
   - `extract_text_from_pdf` — OCR the PDF
   - `extract_biomarkers` — parse biomarkers from OCR text
   - `detect_deficiencies` — classify against clinical thresholds
   - `generate_explanations` — plain-English explanations
   - `recommend_foods` — evidence-based food/supplement recs
   - `build_shopping_carts` — Walmart + Amazon links
3. **AgentState** accumulates all results across iterations
4. Loop ends when model returns text with no tool calls

---

## Key Services

| File | Role |
|------|------|
| `services/ocr_service.py` | pdfplumber + Tesseract OCR |
| `services/biomarker_extractor.py` | Groq → structured biomarker JSON |
| `services/deficiency_engine.py` | Clinical threshold rules (no LLM) |
| `services/explanation_generator.py` | Groq → plain-English deficiency summaries |
| `services/food_recommender.py` | Groq → food + supplement recommendations |
| `services/shopping.py` | Builds Walmart/Amazon cart links |
| `services/agent.py` | Main agentic loop |
| `services/analysis_pipeline.py` | Legacy fixed pipeline (non-agentic) |

---

## API Routes

| Route | File | Purpose |
|-------|------|---------|
| `POST /reports/upload` | `routes/reports.py` | Upload PDF, run agent, return full analysis |
| `GET /reports/{id}` | `routes/reports.py` | Fetch saved report |
| `POST /cart/...` | `routes/cart.py` | Cart management |

---

## Environment Variables (`app/config.py`)

```
GROQ_API_KEY          # Active — main LLM provider
SUPABASE_URL/KEY      # Database
DATABASE_URL          # PostgreSQL
ANTHROPIC_API_KEY     # Exists but pipeline uses Groq
GEMINI_API_KEY        # Legacy, unused
CLERK_SECRET_KEY      # Auth
CLERK_JWKS_URL
CLERK_ISSUER
WALMART_EMAIL/PASSWORD # Browser automation for cart
CEREBRAS_API_KEY      # For browser automation fallback
OPENROUTER_API_KEY    # For browser automation fallback
BROWSER_USE_API_KEY   # Paid browser automation
SENTRY_DSN            # Error tracking
```

---

## Cart Automation — Instacart (Primary)

### How it works
`app/agents/instacart_cart.py` uses Playwright with cookies exported from the user's real Chrome browser. Runs headed Chrome (less bot-detection risk). Navigates to `instacart.com/store`, searches each item, clicks Add.

**Session file:** `playwright_data/instacart_auth.json` (Playwright storageState format)

**To refresh session when cookies expire:**
```bash
cd backend
.venv/bin/python3.12 -c "
import browser_cookie3, json, os
cookies = []
for domain in ['instacart.com', 'www.instacart.com']:
    for c in browser_cookie3.chrome(domain_name=domain):
        cookies.append({'name':c.name,'value':c.value,'domain':c.domain,
            'path':c.path,'expires':c.expires or -1,'httpOnly':False,
            'secure':bool(c.secure),'sameSite':'Lax'})
os.makedirs('playwright_data', exist_ok=True)
with open('playwright_data/instacart_auth.json','w') as f:
    json.dump({'cookies':cookies,'origins':[]},f)
print(f'Saved {len(cookies)} cookies')
"
```

### Cart endpoint
`POST /api/cart/auto-shop` — defaults to `retailer: "instacart"`. Also supports `"walmart"` (but Walmart's PerimeterX blocks Playwright — avoid).

```bash
curl -X POST http://localhost:8000/api/cart/auto-shop \
  -H "Content-Type: application/json" \
  -d '{"items": ["Spinach", "Wild Salmon", "Vitamin D3"], "retailer": "instacart"}'
```

### Key files
- `playwright_data/instacart_auth.json` — exported Chrome cookies
- `app/agents/instacart_cart.py` — Playwright automation
- `app/agents/playwright_cart.py` — Walmart automation (blocked by PerimeterX, kept as fallback)
- `app/routes/cart.py` — SSE streaming endpoint

### Why not Walmart
Walmart uses PerimeterX which blocks all Playwright automation (headless AND headed, even with stealth patches). Instacart works reliably with cookie-based sessions.

---

## Known Issues / Notes

- `gemini_client.py` should be renamed to `groq_client.py` — the name is a leftover from an earlier Gemini implementation
- `agent.py` still imports from `gemini_client` by the old name
- `analysis_pipeline.py` is the legacy non-agentic pipeline, superseded by `agent.py`
- `claude_client.py` exists but is not wired into the main analysis flow
- Shopping agent has both `shopping.py` (active) and `shopping_agent.py` / `instacart_mcp.py` / `walmart.py` (experimental/browser-based)

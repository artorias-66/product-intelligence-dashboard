# Product Intelligence Dashboard

**An end-to-end web application for Flipkart sellers to extract product data from video, validate listing quality, compare competitor prices, and receive actionable alerts.**

Built as a complete intern assignment submission: deployed frontend + backend, persistent database, async job processing, and a reviewer-friendly demo flow.

---

## Submission at a Glance

| Deliverable | Link |
|---|---|
| **Live Frontend** | [https://product-intelligence-dashboard-aw9mqc63r-artorias-66s-projects.vercel.app](https://product-intelligence-dashboard-aw9mqc63r-artorias-66s-projects.vercel.app/) |
| **Live Backend API** | [https://product-intelligence-api-dkuo.onrender.com](https://product-intelligence-api-dkuo.onrender.com) |
| **Interactive API Docs (Swagger)** | [https://product-intelligence-api-dkuo.onrender.com/api/docs](https://product-intelligence-api-dkuo.onrender.com/api/docs) |
| **GitHub Repository** | [https://github.com/artorias-66/product-intelligence-dashboard](https://github.com/artorias-66/product-intelligence-dashboard) |
| **Health Check** | [https://product-intelligence-api-dkuo.onrender.com/api/health](https://product-intelligence-api-dkuo.onrender.com/api/health) |

**No login required.** Open the frontend and follow the [5-minute reviewer demo](#5-minute-reviewer-demo) below.

> **Note on Render free tier:** The backend may take 30–60 seconds to wake up on first request after idle time. A GitHub Actions cron job pings `/api/health` every 5 minutes to reduce cold starts during review.

---

## 5-Minute Reviewer Demo

This path exercises the full assignment flow without local setup.

1. **Open the dashboard** → [Live Frontend](https://product-intelligence-dashboard-aw9mqc63r-artorias-66s-projects.vercel.app/)
2. **Seed sample data** (if the catalog is empty) → Click **Seed Sample Data** on the Dashboard. This loads 25 Flipkart-style products with issues, competitor prices, alerts, and price history.
3. **Explore quality analytics** → Dashboard shows total products, average quality score, severity breakdown, and quality distribution charts.
4. **Upload a product video** → Go to **Upload** → use `backend/sample/sample_product_video.mp4` from this repo → enable **Enhance product title** → submit.
5. **Track the job** → You are redirected to the job detail page. Status progresses through extraction → **Review Needed** (manual edit of AI-extracted fields) → **Processing** → **Completed**.
6. **Approve extracted data** → Edit any fields in the review form, then click **Approve & Process**. Validation, title enhancement, competitor prices, and alerts run automatically.
7. **Inspect a product** → Open **Products** → click any SKU → see listing issues, enhanced title (original vs suggested), competitor price comparison, price gap %, recommended action, and price history chart.
8. **Refresh competitor prices** → On a product detail page or **Competitor Prices** page, click **Refresh Prices**. New simulated prices are generated; significant drops trigger MEDIUM alerts.
9. **Review alerts** → **Alerts** page shows in-app notification history filtered by severity (HIGH / MEDIUM / LOW).

**Alternative quick path:** Upload `backend/sample/sample_products.csv` (includes intentionally bad rows to trigger validation issues) instead of a video.

---

## Assignment Requirements Coverage

All 12 minimum requirements from the assignment brief are implemented.

| # | Requirement | Status | Where to see it |
|---|---|---|---|
| 1 | Upload product video | Done | Upload page → Product Video tab |
| 2 | Extract/simulate product info from video | Done | OpenCV frame extraction + Tesseract OCR + Groq/Gemini vision; review step on job detail |
| 3 | CSV fallback + manual edit | Done | Upload → CSV tab or Manual Entry tab; job review form for video extraction |
| 4 | Validate product data & detect issues | Done | 11 validation rules; issues on product detail page |
| 5 | Product quality dashboard | Done | Dashboard page with summary metrics and charts |
| 6 | Title enhancement flag | Done | Toggle on upload form |
| 7 | Enhanced title suggestions | Done | Product detail → Enhanced Title section |
| 8 | Competitor prices (mock/CSV/manual) | Done | Auto-generated on ingest; CSV upload on Competitor Prices page |
| 9 | Price comparison (Flipkart vs competitors) | Done | Product detail → price gap, %, recommended action |
| 10 | Alerts for listing/pricing issues | Done | Alerts page + dashboard widget |
| 11 | Job status tracking | Done | Jobs list + job detail with progress 0–100% |
| 12 | Deploy frontend + backend | Done | Vercel + Render links above |

### Bonus features implemented

| Bonus | Status |
|---|---|
| Real OCR from video frames (Tesseract) | Yes |
| Real AI-based product extraction (Groq Vision + Gemini fallback) | Yes |
| External notifications (Telegram) | Yes (optional, env-configured) |
| Scheduled background price refresh (APScheduler, every 12h) | Yes |
| Price history chart (Recharts) | Yes |
| Downloadable product quality report (CSV) | Yes — `GET /api/dashboard/quality-report-csv` |
| Retry failed jobs | Yes — `POST /api/jobs/{job_id}/retry` |
| Product recommendation engine | Yes — category/brand similarity on product detail |
| OpenAPI / Swagger documentation | Yes |
| Dockerized deployment | Yes — `docker-compose.yml` + Dockerfiles |

---

## Architecture

```mermaid
flowchart TB
    subgraph Client["Frontend (React + Vite)"]
        UI[Dashboard / Upload / Jobs / Products / Alerts]
    end

    subgraph API["Backend (FastAPI)"]
        R1[Upload Router]
        R2[Jobs Router]
        R3[Products Router]
        R4[Dashboard Router]
        R5[Competitor Prices Router]
        R6[Alerts Router]
        S1[Video Extraction Pipeline]
        S2[Validation Engine]
        S3[Title Enhancement]
        S4[Alert Rules Engine]
        S5[Competitor Pricing Service]
        SCH[APScheduler - 12h price refresh]
    end

    subgraph External["External Services"]
        GROQ[Groq Vision + LLM]
        GEM[Gemini 2.5 Flash]
        TG[Telegram Bot API]
    end

    subgraph Data["PostgreSQL (Neon / Docker)"]
        DB[(Jobs · Products · Issues · Alerts · CompetitorPrices · PriceHistory · EnhancedTitles)]
    end

    UI -->|REST + polling| API
    R1 --> S1
    S1 --> GROQ
    S1 --> GEM
    R1 --> S2
    R3 --> S3
    S3 --> GROQ
    S3 --> GEM
    S2 --> S4
    S4 --> TG
    S5 --> DB
    SCH --> S5
    API --> DB
```

### End-to-end data flow

```
Video/CSV Upload
    → Create Job (PENDING → RUNNING)
    → [Video] OpenCV middle-frame → Tesseract OCR → Groq Vision → Gemini fallback
    → [Video] PENDING_REVIEW (user-approve extracted fields)
    → Validate (11 rules) → Quality Score
    → [Optional] Title Enhancement (Groq → Gemini → rule-based fallback)
    → Generate Competitor Prices (mock simulation)
    → Generate Alerts (listing + pricing rules)
    → Job COMPLETED / PARTIALLY_COMPLETED / FAILED
    → Dashboard + Product Detail + Alerts UI
```

### Project structure

```
product-intelligence-dashboard/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, routers, lifespan
│   │   ├── models.py            # 7 SQLAlchemy tables
│   │   ├── schemas.py           # Pydantic request/response models
│   │   ├── routers/             # upload, jobs, products, dashboard, alerts, pricing
│   │   └── services/            # video extraction, validation, alerts, AI, pricing
│   ├── sample/                  # Sample video, product CSV, competitor CSV
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/pages/               # Dashboard, Upload, Jobs, Products, Alerts, Pricing
│   ├── src/api/client.js        # Axios API client
│   └── Dockerfile
├── docker-compose.yml
├── .github/workflows/keep-alive.yml
└── README.md
```

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **Frontend** | React 18, Vite, React Router, Recharts, Axios | Fast SPA with routing and charting for quality/pricing analytics |
| **Backend** | FastAPI, Pydantic, SQLAlchemy 2 | Typed async API with auto-generated OpenAPI docs |
| **Database** | PostgreSQL (Neon serverless in prod; Postgres 15 in Docker locally) | Persistent relational storage for products, jobs, alerts, price history |
| **Video / OCR** | OpenCV, Tesseract, Pillow | Real frame extraction and local OCR before AI reasoning |
| **AI** | Groq (Llama 4 Scout vision + Llama 3.3 70B), Gemini 2.5 Flash | Primary + fallback for extraction and title enhancement |
| **Jobs** | Python `threading` (daemon workers) | Async processing without Redis/Celery overhead for demo scale |
| **Scheduler** | APScheduler | Automated competitor price refresh every 12 hours |
| **Notifications** | Telegram Bot API | Optional external alerts for HIGH-severity issues |
| **Deployment** | Vercel (frontend), Render (backend), Docker Compose (local) | Full cloud deployment + reproducible local environment |

---

## Application Walkthrough

Screenshots are in `frontend/public/` on the repository.

| Screen | Description |
|---|---|
| Dashboard | Quality summary, severity charts, recent alerts, seed button |
| Upload | Video / CSV / manual entry + title enhancement toggle |
| Job Detail | Progress bar, extraction review form, approve/retry actions |
| Products | Filterable catalog by category, score, search |
| Product Detail | Issues, enhanced title, competitor comparison, price history chart |
| Competitor Prices | Bulk refresh + CSV upload |
| Alerts | Severity-filtered notification history with mark-as-read |

---

## Using the Deployed App

### First visit

1. Open the [live frontend](https://product-intelligence-dashboard-aw9mqc63r-artorias-66s-projects.vercel.app/).
2. If the product list is empty, click **Seed Sample Data** on the Dashboard (calls `POST /api/seed`).
3. Browse seeded products, alerts, and pricing data immediately.

### Upload workflow

**Video (primary path)**

1. Upload → **Product Video** tab.
2. Select a short `.mp4` product video (sample: `backend/sample/sample_product_video.mp4`).
3. Optionally add a **video hint** (e.g., "Nike blue running shoes") to improve extraction accuracy.
4. Toggle **Enhance product title** on/off.
5. After upload, review AI-extracted fields on the job page → edit if needed → **Approve & Process**.

**CSV fallback**

1. Upload → **Product CSV** tab → use `backend/sample/sample_products.csv`.
2. Processing runs in the background; track progress on the Jobs page.

**Manual entry**

1. Upload → **Manual Entry** tab → fill product fields → submits as a one-row CSV internally.

### Competitor pricing

- Prices are **auto-generated** when products are processed (mock data across Amazon, Myntra, Ajio, Nykaa Fashion, Tata Cliq, Meesho).
- Upload real/mock competitor data via **Competitor Prices** → CSV upload using `backend/sample/sample_competitor_prices.csv`.
- **Refresh Prices** (per product or bulk) simulates market movement and logs price history; drops >5% create MEDIUM alerts.

---

## Running Locally

### Option A — Docker Compose (recommended)

**Prerequisites:** Docker and Docker Compose.

```bash
git clone https://github.com/artorias-66/product-intelligence-dashboard.git
cd product-intelligence-dashboard
```

Create `backend/.env`:

```env
# Required for AI video extraction and title enhancement
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key

# Optional — Telegram alerts
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Docker Compose sets DATABASE_URL automatically to local Postgres
# For Neon/cloud Postgres instead, set:
# DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
```

Start all services:

```bash
docker-compose up -d --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost |
| Backend API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/api/docs |
| Postgres | localhost:5433 |

### Option B — Run services individually

**Backend**

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Install system deps: tesseract-ocr, ffmpeg, libgl1 (for OpenCV)
export DATABASE_URL=postgresql://postgres:password@localhost:5433/product_intel
uvicorn app.main:app --reload --port 8000
```

**Frontend**

```bash
cd frontend
npm install
VITE_API_URL=http://localhost:8000 npm run dev
# → http://localhost:5173
```

---

## API Documentation

Full interactive docs: **[Swagger UI](https://product-intelligence-api-dkuo.onrender.com/api/docs)**

### Core endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/health` | Health check + DB connectivity |
| `POST` | `/api/upload-video` | Upload video; returns `job_id` |
| `POST` | `/api/upload-products-csv` | Upload product feed CSV; returns `job_id` |
| `GET` | `/api/jobs` | List jobs (filter by status, type) |
| `GET` | `/api/jobs/{job_id}` | Job status, progress, draft data, products |
| `POST` | `/api/jobs/{job_id}/approve` | Approve video extraction → resume processing |
| `POST` | `/api/jobs/{job_id}/retry` | Retry a FAILED job with saved draft data |
| `GET` | `/api/products` | List products (pagination, filters, search) |
| `GET` | `/api/products/{sku_id}` | Product detail + issues + enhanced titles + competitor prices |
| `PUT` | `/api/products/{sku_id}` | Update product; re-runs validation and alerts |
| `GET` | `/api/products/{sku_id}/recommendations` | Similar products by category/brand |
| `POST` | `/api/products/{sku_id}/enhance-title` | Generate/regenerate enhanced title |
| `GET` | `/api/dashboard/quality-summary` | Dashboard aggregate metrics |
| `GET` | `/api/dashboard/quality-report-csv` | Download full quality report |
| `POST` | `/api/competitor-prices/upload-csv` | Upload competitor price CSV |
| `POST` | `/api/competitor-prices/refresh` | Bulk refresh all product prices |
| `POST` | `/api/competitor-prices/product/{sku_id}/refresh` | Refresh prices for one SKU |
| `GET` | `/api/competitor-prices/product/{sku_id}` | Current competitor prices |
| `GET` | `/api/competitor-prices/product/{sku_id}/history` | Price history for charts |
| `GET` | `/api/alerts` | List alerts (filter by severity, read status) |
| `PUT` | `/api/alerts/{alert_id}/read` | Mark alert as read |
| `POST` | `/api/alerts/rules` | Create manual alert |
| `POST` | `/api/seed` | Seed demo data |
| `POST` | `/api/reset` | Reset database (admin) |

### Example: upload video

```bash
curl -X POST "https://product-intelligence-api-dkuo.onrender.com/api/upload-video" \
  -F "file=@backend/sample/sample_product_video.mp4" \
  -F "enhance_titles=true" \
  -F "video_hint=Nike blue running shoes"
```

Response:

```json
{
  "job_id": "uuid-here",
  "message": "Analyzing video ...",
  "status": "PROCESSING"
}
```

Poll `GET /api/jobs/{job_id}` until status is `PENDING_REVIEW`, then approve via UI or API.

---

## Data Model

PostgreSQL schema with 7 tables:

| Table | Purpose | Key fields |
|---|---|---|
| `jobs` | Async ingestion tracking | `status`, `progress`, `type`, `draft_data`, `enhance_titles`, timestamps |
| `products` | Flipkart seller listings | `sku_id`, `product_title`, `brand`, `category`, `price`, `mrp`, attributes, `quality_score` |
| `product_issues` | Validation findings | `issue_type`, `severity`, `message`, `suggested_fix` |
| `enhanced_titles` | AI-generated title variants | `original_title`, `extracted_attributes`, `suggested_keywords`, `enhanced_title`, `reason` |
| `competitor_prices` | Latest competitor snapshots | `platform`, `competitor_price`, `competitor_url`, `last_checked_at` |
| `price_history` | Historical price points | `platform`, `price`, `checked_at` |
| `alerts` | In-app (+ optional Telegram) notifications | `type`, `severity`, `title`, `message`, `is_read` |

**Job statuses:** `PENDING` → `RUNNING` → `PENDING_REVIEW` (video only) → `PROCESSING` → `COMPLETED` | `PARTIALLY_COMPLETED` | `FAILED`

---

## Validation Rules (11 rules)

| Issue | Severity | Trigger |
|---|---|---|
| Missing title | HIGH | Empty or whitespace title |
| Very short title | MEDIUM | Title &lt; 20 characters |
| Missing brand | MEDIUM | No brand provided |
| Invalid price | HIGH | Missing, non-numeric, or ≤ 0 |
| MRP &lt; selling price | HIGH | MRP lower than price |
| Missing image | HIGH | No `image_url` |
| Broken image URL | MEDIUM | URL doesn't start with `http://` or `https://` |
| Duplicate SKU | HIGH | Same `sku_id` exists on another product |
| Weak description | LOW | Missing or &lt; 50 characters |
| Missing attributes | MEDIUM | Color, size, and material all missing |
| Out of stock | LOW | Availability is out_of_stock / unavailable |

**Quality score:** Starts at 100; deductions by severity (HIGH −15, MEDIUM −8, LOW −3). Clamped to 0–100.

---

## Alert Rules

| Condition | Severity | Alert type |
|---|---|---|
| Missing title, invalid price, missing image, duplicate SKU, MRP error | HIGH | Critical listing issue |
| Short title, missing brand/attributes, broken image URL | MEDIUM | Listing improvement needed |
| Weak description, out of stock | LOW | Minor listing issue |
| Flipkart price &gt; 10% above lowest competitor | HIGH | Price not competitive |
| Competitor price drops &gt; 5% on refresh | MEDIUM | Competitor price drop detected |

Telegram notifications fire for HIGH-severity listing and pricing alerts when `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are configured.

---

## Sample Files

| File | Purpose |
|---|---|
| [`backend/sample/sample_product_video.mp4`](backend/sample/sample_product_video.mp4) | Primary input — short product showcase video |
| [`backend/sample/sample_products.csv`](backend/sample/sample_products.csv) | Product feed with good + intentionally bad rows (invalid price, duplicate SKU, missing fields) |
| [`backend/sample/sample_competitor_prices.csv`](backend/sample/sample_competitor_prices.csv) | Competitor prices across Amazon, Myntra, Ajio, etc. |

The seeded dataset (`POST /api/seed`) creates **25 products** (15 healthy, 5 medium-issue, 5 critical-issue) with competitor prices, price history, alerts, and enhanced titles — useful for immediate dashboard exploration.

---

## What Is Real vs Mocked

### Real / fully functional

| Component | Details |
|---|---|
| **Video pipeline** | OpenCV extracts the middle frame; Tesseract runs local OCR; Groq Vision (primary) and Gemini 2.5 Flash (fallback) interpret the frame + OCR text |
| **Title enhancement** | Groq LLM → Gemini → deterministic rule-based fallback |
| **Validation & scoring** | All 11 rules execute server-side against PostgreSQL data |
| **Job processing** | Background threads with real status/progress tracking and polling UI |
| **Database** | Persistent PostgreSQL (Neon in production) |
| **Price history** | Stored and charted on every refresh |
| **Scheduled refresh** | APScheduler runs every 12 hours on backend startup |
| **API documentation** | Auto-generated OpenAPI/Swagger |
| **Keep-alive** | GitHub Action pings Render every 5 minutes |

### Mocked / simulated (by design)

| Component | Details |
|---|---|
| **Competitor prices** | Generated with realistic ±15–20% variation from our Flipkart price; no live scraping (assignment explicitly allows mocks; avoids legal/ToS issues) |
| **Authentication** | Omitted so reviewers can test immediately without credentials |

---

## Assumptions

1. **Seller context:** We are a Flipkart seller; our price is stored in `products.price`; competitors are Amazon, Myntra, Ajio, Nykaa Fashion, Tata Cliq, Meesho.
2. **Video input:** Short (&lt;60s) `.mp4` product videos where the product is visible in the middle frame.
3. **Scale:** Internal B2B dashboard for catalog quality review — not high-concurrency consumer traffic.
4. **AI availability:** Groq/Gemini free tiers may rate-limit; fallbacks (Gemini retry with backoff, rule-based title, honest extraction placeholder + manual review) keep the flow unblocked.

---

## Trade-offs and Limitations

| Trade-off | Rationale |
|---|---|
| **Single middle frame** | Reduces API cost and latency vs multi-frame analysis; may miss products only shown at start/end of video |
| **Polling vs WebSockets** | Simpler on serverless/free-tier hosts (Vercel + Render); frontend polls jobs every 1.5s |
| **Threading vs Celery/Redis** | Sufficient for demo scale; avoids extra infrastructure on free tier |
| **Mock competitor data** | Reliable, legal, and assignment-compliant vs fragile live scraping |
| **Render cold starts** | Free tier sleeps after inactivity; mitigated by keep-alive cron but first request may still lag |

---

## What I Would Improve With More Time

1. **Multi-frame video analysis** — sample frames across the timeline for better extraction on fast-moving product shots.
2. **Inline product editing in the UI** — edit listing fields directly from the product detail page (API `PUT /products/{sku_id}` already exists).
3. **Celery + Redis job queue** — durable background workers with retry policies and horizontal scaling.
4. **Live competitor price feeds** — official marketplace APIs or licensed data providers instead of simulation.
5. **Authentication & multi-tenant support** — JWT/OAuth so each seller sees only their catalog.
6. **WebSocket job updates** — eliminate polling overhead for real-time progress.
7. **Bulk export & reporting** — PDF quality reports and scheduled email digests for operations teams.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes (prod) | PostgreSQL connection string |
| `GROQ_API_KEY` | Recommended | Primary AI for vision extraction and title enhancement |
| `GEMINI_API_KEY` | Recommended | Fallback AI when Groq is unavailable |
| `TELEGRAM_BOT_TOKEN` | Optional | Telegram bot token for external alerts |
| `TELEGRAM_CHAT_ID` | Optional | Target chat ID for Telegram notifications |
| `CORS_ORIGINS` | Optional | Comma-separated allowed origins (default: `*`) |

---

## Implementation Summary (for reviewers)

**Fully implemented:** Complete upload-to-dashboard pipeline, 11 validation rules, quality scoring, AI video extraction with human review step, title enhancement toggle, competitor price comparison with refresh + history, alert engine with severity tiers, job tracking with retry, Docker + cloud deployment, Swagger docs, sample inputs, and seed data.

**Mocked by choice:** Competitor price fetching (simulated data + CSV upload); no authentication.

**Differentiators:** Real OCR + vision AI pipeline (not pure mock extraction), hybrid Groq/Gemini with fallbacks, manual review gate after video extraction, Telegram integration, scheduled price refresh, downloadable quality CSV, and a one-click seed for instant demo.

---

Built by [artorias-66](https://github.com/artorias-66) · Product Intelligence Dashboard · Intern Assignment Submission

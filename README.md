# ProductIQ

**Product Intelligence Dashboard for e-commerce sellers**

A full-stack platform that turns product videos and catalog feeds into actionable listing intelligence — validation scores, AI-enhanced titles, competitor price comparisons, and real-time alerts.

Built and maintained by [Anubhav Verma](https://www.linkedin.com/in/anubhav-verma-b83787338/).

![Dashboard Overview](frontend/public/screenshot.png)

---

## Live Demo

| | Link |
|---|---|
| **App** | [https://product-intelligence-dashboard-nine.vercel.app](https://product-intelligence-dashboard-nine.vercel.app/) |
| **API** | [https://product-intelligence-api-dkuo.onrender.com](https://product-intelligence-api-dkuo.onrender.com) |
| **Swagger** | [https://product-intelligence-api-dkuo.onrender.com/api/docs](https://product-intelligence-api-dkuo.onrender.com/api/docs) |
| **Source** | [https://github.com/artorias-66/product-intelligence-dashboard](https://github.com/artorias-66/product-intelligence-dashboard) |

Sign in with Clerk to access the dashboard. On first visit, use **Seed Sample Data** on the Dashboard to populate your account with demo products, alerts, and pricing data.

> **Note:** The backend runs on Render's free tier and may take 30–60 seconds to wake up after idle time. A GitHub Actions cron pings `/api/health` every 5 minutes to reduce cold starts.

---

## The Problem

Marketplace sellers on platforms like Flipkart often have product videos, CSV feeds, competitor price signals, and listing data spread across tools — but no single place to answer three questions:

1. **Is my listing good enough?** (title, images, attributes, pricing errors)
2. **Am I priced competitively?** (vs Amazon, Myntra, Ajio, and others)
3. **What should I fix first?** (prioritized alerts by severity)

ProductIQ combines ingestion, validation, AI enhancement, and pricing intelligence into one dashboard.

---

## Features

### Ingestion & Processing
- **Video upload** — extract product details from short showcase videos
- **CSV upload** — bulk import product feeds
- **Manual entry** — add a single product without a file
- **Async job pipeline** — background processing with live status, progress (0–100%), and error reporting
- **Human-in-the-loop review** — edit AI-extracted fields before final processing

### AI Pipeline
- **OpenCV** middle-frame extraction + **Tesseract OCR** for packaging text
- **Groq Vision** (primary) + **Gemini 2.5 Flash** (fallback) for product identification
- **Title enhancement** — SEO-optimized titles with extracted attributes, trend keywords, and reasoning
- **Rule-based fallbacks** when AI APIs are unavailable or rate-limited

### Listing Quality
- **11 validation rules** with HIGH / MEDIUM / LOW severity classification
- **Quality score** (0–100) computed from issue severity weights
- **Dashboard analytics** — issue breakdown, quality distribution charts, downloadable CSV report

### Competitor Pricing
- Simulated competitor prices across Amazon, Myntra, Ajio, Nykaa Fashion, Tata Cliq, Meesho
- **Price comparison** — lowest, highest, average, gap %, recommended action
- **CSV upload** and manual entry for competitor data
- **Price refresh** (manual + scheduled every 12h) with history tracking and drop alerts

### Alerts & Notifications
- In-app alert history with severity filters and mark-as-read
- Rules for critical listing issues, pricing gaps (>10% above lowest competitor), and competitor price drops (>5%)
- Optional **Telegram** notifications for HIGH-severity events

### Platform
- **Clerk authentication** — secure sign-in on frontend; JWT verification on every API route
- **Multi-tenant data isolation** — all products, jobs, and alerts scoped per user
- **Product recommendations** — similar products by category and brand
- **Job retry** — recover failed video/CSV jobs from saved draft data
- **Docker Compose** for local development
- **OpenAPI / Swagger** auto-generated docs

---

## Screenshots

### Dashboard & Quality Analytics

![Dashboard Overview](frontend/public/1.png)
![Quality Metrics & Charts](frontend/public/2.png)

### Upload (Video / CSV / Manual)

![Video Upload Form](frontend/public/product_video.png)

### AI Extraction Review

![Extraction Review](frontend/public/4.png)

### Job Tracking

![Jobs List](frontend/public/10.png)
![Job Processing Progress](frontend/public/3.png)

### Enhanced Titles & Product Detail

![AI Title Enhancement](frontend/public/5.png)
![Product Detail](frontend/public/6.png)

### Product Catalog

![Product List](frontend/public/7.png)

### Competitor Pricing

![Competitor Price Analysis](frontend/public/8.png)
![Competitor Price CSV Upload](frontend/public/9.png)

### Alerts

![Alerts](frontend/public/alert.png)

---

## Architecture

```mermaid
flowchart TB
    subgraph Client["Frontend — React + Vite (ProductIQ UI)"]
        AUTH[Clerk Auth]
        UI[Dashboard · Upload · Jobs · Products · Alerts · Pricing]
    end

    subgraph API["Backend — FastAPI"]
        JWT[JWT Verification]
        R1[Upload]
        R2[Jobs]
        R3[Products]
        R4[Dashboard]
        R5[Competitor Prices]
        R6[Alerts]
        S1[Video Extraction]
        S2[Validation Engine]
        S3[Title Enhancement]
        S4[Alert Rules]
        S5[Competitor Pricing]
        SCH[APScheduler — 12h refresh]
    end

    subgraph External["External Services"]
        CLERK[Clerk]
        GROQ[Groq Vision + LLM]
        GEM[Gemini 2.5 Flash]
        TG[Telegram Bot API]
    end

    subgraph Data["PostgreSQL"]
        DB[(Jobs · Products · Issues · Alerts · Prices · History · Titles)]
    end

    AUTH --> CLERK
    UI -->|Bearer JWT| JWT
    JWT --> API
    S1 --> GROQ
    S1 --> GEM
    S3 --> GROQ
    S3 --> GEM
    S4 --> TG
    API --> DB
    SCH --> S5
```

### Data flow

```
Sign in (Clerk) → Upload video/CSV
    → Job created (scoped to user_id)
    → [Video] OpenCV frame → Tesseract OCR → Groq Vision → Gemini fallback
    → PENDING_REVIEW → user edits & approves
    → Validate (11 rules) → Quality score
    → [Optional] Title enhancement
    → Competitor prices generated → Alerts created
    → Dashboard · Product detail · Alerts UI
```

### Project structure

```
product-intelligence-dashboard/
├── backend/
│   ├── app/
│   │   ├── auth.py              # Clerk JWT verification
│   │   ├── main.py              # FastAPI app + router mounting
│   │   ├── models.py            # SQLAlchemy models (user-scoped)
│   │   ├── routers/             # upload, jobs, products, dashboard, alerts, pricing
│   │   └── services/            # extraction, validation, alerts, AI, pricing
│   ├── sample/                  # Demo video + CSV files
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/auth/     # Axios JWT interceptor
│   │   ├── pages/               # Dashboard, Upload, Jobs, Products, Alerts, Pricing
│   │   └── index.css            # ProductIQ design system
│   └── Dockerfile
├── docker-compose.yml
└── .github/workflows/keep-alive.yml
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18, Vite, React Router, Recharts, Axios, Lucide icons |
| **UI** | Custom ProductIQ design system (glassmorphism, Inter typography) |
| **Auth** | Clerk (React SDK + FastAPI JWT verification via JWKS) |
| **Backend** | FastAPI, Pydantic, SQLAlchemy 2 |
| **Database** | PostgreSQL (Neon in production; Postgres 15 via Docker locally) |
| **Video / OCR** | OpenCV, Tesseract, Pillow |
| **AI** | Groq (Llama 4 Scout vision + Llama 3.3 70B), Gemini 2.5 Flash |
| **Jobs** | Python daemon threads with polling UI |
| **Scheduler** | APScheduler (12-hour competitor price refresh) |
| **Notifications** | Telegram Bot API (optional) |
| **Deployment** | Vercel (frontend), Render (backend), Docker Compose (local) |

---

## Quick Start (Live App)

1. Open the [live app](https://product-intelligence-dashboard-nine.vercel.app/) and sign in with Clerk.
2. If your catalog is empty, click **Seed Sample Data** on the Dashboard.
3. Explore products, alerts, and pricing analytics.
4. Go to **Upload** → upload `backend/sample/sample_product_video.mp4` with **Enhance product title** enabled.
5. On the job detail page, review extracted fields → **Approve & Process**.
6. Open the product from **Products** to see validation issues, enhanced title, and competitor comparison.
7. Click **Refresh Prices** to simulate market updates and trigger new alerts.

**Alternative:** Upload `backend/sample/sample_products.csv` for a faster CSV-only flow.

---

## Running Locally

### Prerequisites

- Docker & Docker Compose, **or** Node 18+ and Python 3.11
- [Clerk](https://clerk.com) application (publishable + secret keys)
- Groq and/or Gemini API keys (for AI features)
- System packages for backend: `tesseract-ocr`, `ffmpeg`, `libgl1`

### Docker Compose (recommended)

```bash
git clone https://github.com/artorias-66/product-intelligence-dashboard.git
cd product-intelligence-dashboard
```

Create `backend/.env`:

```env
CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
GROQ_API_KEY=your_groq_key
GEMINI_API_KEY=your_gemini_key

# Optional
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

Create `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
VITE_CLERK_PUBLISHABLE_KEY=pk_test_...
```

```bash
docker-compose up -d --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost |
| Backend | http://localhost:8000 |
| Swagger | http://localhost:8000/api/docs |
| Postgres | localhost:5433 |

### Manual setup

**Backend**

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
export DATABASE_URL=postgresql://postgres:password@localhost:5433/product_intel
uvicorn app.main:app --reload --port 8000
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

---

## API Reference

Interactive docs: **[Swagger UI](https://product-intelligence-api-dkuo.onrender.com/api/docs)**

All routes under `/api` (except `/api/health`) require a Clerk JWT:

```
Authorization: Bearer <clerk_session_token>
```

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check (no auth) |
| `POST` | `/api/upload-video` | Upload video → returns `job_id` |
| `POST` | `/api/upload-products-csv` | Upload product CSV |
| `GET` | `/api/jobs` | List user's jobs |
| `GET` | `/api/jobs/{job_id}` | Job status, progress, draft data |
| `POST` | `/api/jobs/{job_id}/approve` | Approve video extraction |
| `POST` | `/api/jobs/{job_id}/retry` | Retry a failed job |
| `GET` | `/api/products` | List products (paginated, filterable) |
| `GET` | `/api/products/{sku_id}` | Product detail + issues + prices |
| `PUT` | `/api/products/{sku_id}` | Update product (re-validates) |
| `POST` | `/api/products/{sku_id}/enhance-title` | Generate enhanced title |
| `GET` | `/api/dashboard/quality-summary` | Dashboard metrics |
| `GET` | `/api/dashboard/quality-report-csv` | Download quality report |
| `POST` | `/api/competitor-prices/upload-csv` | Upload competitor prices |
| `POST` | `/api/competitor-prices/refresh` | Bulk price refresh |
| `POST` | `/api/competitor-prices/product/{sku_id}/refresh` | Refresh one SKU |
| `GET` | `/api/alerts` | List alerts |
| `POST` | `/api/seed` | Seed demo data for current user |

---

## Data Model

PostgreSQL with 7 tables. Jobs, products, and alerts are scoped by `user_id` for multi-tenant isolation.

| Table | Purpose |
|---|---|
| `jobs` | Async ingestion — status, progress, draft data, timestamps |
| `products` | Seller listings — SKU, title, brand, price, attributes, quality score |
| `product_issues` | Validation findings — type, severity, suggested fix |
| `enhanced_titles` | AI-generated titles — attributes, keywords, reason |
| `competitor_prices` | Latest competitor snapshots per platform |
| `price_history` | Historical price points for charts |
| `alerts` | Notifications — severity, type, read status |

**Job statuses:** `PENDING` → `RUNNING` → `PENDING_REVIEW` (video) → `PROCESSING` → `COMPLETED` | `PARTIALLY_COMPLETED` | `FAILED`

---

## Business Logic

### Validation rules (11)

| Issue | Severity |
|---|---|
| Missing title | HIGH |
| Very short title (<20 chars) | MEDIUM |
| Missing brand | MEDIUM |
| Invalid price | HIGH |
| MRP < selling price | HIGH |
| Missing image | HIGH |
| Broken image URL | MEDIUM |
| Duplicate SKU | HIGH |
| Weak description | LOW |
| Missing attributes (color, size, material) | MEDIUM |
| Out of stock | LOW |

Quality score starts at 100; deductions: HIGH −15, MEDIUM −8, LOW −3.

### Alert rules

| Trigger | Severity |
|---|---|
| Critical listing issues (missing title, invalid price, etc.) | HIGH |
| Flipkart price >10% above lowest competitor | HIGH |
| Weak title, missing attributes, broken image | MEDIUM |
| Competitor price drop >5% on refresh | MEDIUM |
| Weak description, out of stock | LOW |

---

## Sample Data

| File | Description |
|---|---|
| [`backend/sample/sample_product_video.mp4`](backend/sample/sample_product_video.mp4) | Short product showcase video |
| [`backend/sample/sample_products.csv`](backend/sample/sample_products.csv) | Product feed with good and intentionally bad rows |
| [`backend/sample/sample_competitor_prices.csv`](backend/sample/sample_competitor_prices.csv) | Competitor prices across platforms |

The **Seed Sample Data** button creates 25 demo products (healthy, medium-issue, and critical-issue) scoped to your account.

---

## What's Real vs Simulated

| Real | Simulated |
|---|---|
| Video frame extraction + OCR | Competitor prices (mock ±15–20% variation; no live scraping) |
| Groq / Gemini AI extraction & titles | |
| Validation, scoring, alerts | |
| Clerk auth + per-user data isolation | |
| Job processing with progress tracking | |
| Price history on refresh | |
| Scheduled 12h price refresh | |
| Telegram notifications (when configured) | |

Competitor pricing uses simulated data by design — reliable, legal, and avoids fragile marketplace scraping.

---

## Environment Variables

### Backend

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes (prod) | PostgreSQL connection string |
| `CLERK_PUBLISHABLE_KEY` | Yes | Clerk publishable key (JWKS URL derivation) |
| `CLERK_SECRET_KEY` | Yes | Clerk secret key |
| `GROQ_API_KEY` | Recommended | Primary AI for vision + titles |
| `GEMINI_API_KEY` | Recommended | Fallback AI |
| `TELEGRAM_BOT_TOKEN` | Optional | Telegram alerts |
| `TELEGRAM_CHAT_ID` | Optional | Telegram chat ID |
| `CORS_ORIGINS` | Optional | Allowed origins (comma-separated) |

### Frontend

| Variable | Required | Description |
|---|---|---|
| `VITE_CLERK_PUBLISHABLE_KEY` | Yes | Clerk publishable key |
| `VITE_API_URL` | Yes | Backend API base URL |

### Deployment

**Vercel (frontend):** `VITE_API_URL`, `VITE_CLERK_PUBLISHABLE_KEY`

**Render / Railway (backend):** `DATABASE_URL`, `CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`, `GROQ_API_KEY`, `GEMINI_API_KEY`, `CORS_ORIGINS`

---

## Roadmap

- [ ] Multi-frame video analysis for better extraction accuracy
- [ ] Inline product editing on the product detail page
- [ ] Celery + Redis for durable background job queues
- [ ] Live competitor price feeds via official marketplace APIs
- [ ] WebSocket-based job progress (replace polling)
- [ ] PDF quality reports and scheduled email digests
- [ ] Row-level security policies at the database layer

---

## Author

**Anubhav Verma**

[LinkedIn](https://www.linkedin.com/in/anubhav-verma-b83787338/) · [GitHub](https://github.com/artorias-66)

---

## License

This project is open source for portfolio and learning purposes. Feel free to explore the code and architecture.

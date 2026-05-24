# Product Intelligence Dashboard

A comprehensive end-to-end dashboard designed to intelligently extract product details from videos/images, validate e-commerce listing quality, analyze competitor pricing, and automatically alert users of listing issues.

## 🔗 Deployment Links
- **Frontend App**: *(To be deployed — e.g. Vercel/Netlify URL)*
- **Backend API**: *(To be deployed — e.g. Render/Heroku URL)*
- **GitHub Repository**: [https://github.com/artorias-66/product-intelligence-dashboard](https://github.com/artorias-66/product-intelligence-dashboard)

*(Note: If running locally, Frontend is `http://localhost:5173` or `http://localhost` via Docker, Backend is `http://localhost:8000`)*

---

## 🛠️ Tech Stack
- **Frontend**: React (Vite), TailwindCSS, React Router, Lucide Icons, Recharts (for price history).
- **Backend**: Python, FastAPI, SQLAlchemy (ORM), Uvicorn.
- **Database**: PostgreSQL (Neon Serverless for prod, local Docker Postgres for dev).
- **AI/ML Integration**: 
  - Google Cloud Vision API (Robust OCR extraction from video frames).
  - Google Gemini 2.5 Flash / Gemini Vision (Contextual product extraction & title enhancement).
- **Background Jobs**: APScheduler (Scheduled competitor price scraping & real-time Telegram alerts).
- **Deployment**: Docker & Docker Compose (Containerization).

---

## 🚀 How to Run Locally

### 1. Using Docker Compose (Recommended)
This is the easiest way to spin up the entire application (Database, Backend API, and Frontend) simultaneously.
1. Clone the repository: `git clone https://github.com/artorias-66/product-intelligence-dashboard.git`
2. Create a `backend/.env` file with your API keys (see Environment Variables section below).
3. Run the following command in the root directory:
   ```bash
   docker-compose up --build -d
   ```
4. Access the **Frontend** at `http://localhost`
5. Access the **Backend API Docs** at `http://localhost:8000/docs`

### 2. Manual Setup (Without Docker)
**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # (or venv\Scripts\activate on Windows)
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```
**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Environment Variables (`backend/.env`)
```env
DATABASE_URL=postgresql://user:password@localhost:5432/db_name
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key
GOOGLE_APPLICATION_CREDENTIALS=gcp-vision-key.json
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

---

## 📖 How to Use the App

1. **Upload Video / Job Creation**: Navigate to the "Upload" tab and drag-and-drop an MP4 video of a product. The backend extracts frames using `ffmpeg`, runs it through Google Cloud Vision OCR, and feeds the context to Google Gemini to extract accurate JSON listings.
2. **Review & Approve**: Go to the "Jobs" page. Review the AI-extracted product. You can manually edit the title/brand/price before approving.
3. **Dashboard & Alerts**: Once approved, the product flows into the master inventory. The background scheduler evaluates the listing quality, checks competitor prices, and flags any issues (e.g., "Missing Title", "Price 10% higher than Amazon").
4. **AI Enhancement**: On the Product Details page, click "AI Enhance" to automatically generate SEO-optimized titles.
5. **Real-time Notifications**: Critical alerts are automatically pushed to Telegram via a background bot.

---

## 🗄️ Data Model & Schema Explanation

The Postgres database utilizes SQLAlchemy ORM with the following core entities:
- **VideoJob**: Tracks the upload and asynchronous AI extraction status (`PENDING`, `ACTIVE`, `COMPLETED`, `FAILED`).
- **Product**: The canonical master listing. Contains SEO details, Flipkart pricing, and a calculated `quality_score`.
- **CompetitorPrice**: A One-to-Many relationship with `Product`. Tracks historical price fluctuations across Amazon, Myntra, etc.
- **Alert**: A One-to-Many relationship with `Product`. Flags business logic violations (e.g., `CRITICAL`, `WARNING`).

---

## 🔌 API Documentation

The backend heavily utilizes FastAPI, which automatically generates Swagger/OpenAPI documentation. 
When the backend is running, visit **`http://localhost:8000/docs`** for interactive, clean API documentation.

### Core Endpoints:
- `POST /api/jobs/upload`: Accepts `multipart/form-data` video files.
- `GET /api/jobs/{job_id}`: Polls extraction status and returns AI-identified draft products.
- `POST /api/jobs/{job_id}/approve`: Commits draft products to the master `Product` catalog.
- `GET /api/products`: Lists all approved inventory.
- `GET /api/alerts`: Fetches unread quality & pricing alerts.
- `POST /api/products/{sku_id}/recommendations`: Triggers LLM to enhance product titles.

---

## 🤔 Assumptions Made
- A single video can contain multiple items, but generally represents one primary item.
- Competitor prices fluctuate dynamically. For the sake of this assignment, background workers occasionally simulate competitor price scraping since live E-commerce scraping requires heavy proxies.
- Not all videos are perfectly readable; fallback OCR and prompt engineering is relied upon for "best effort" extraction.

---

## 🎭 What is Real vs. Mocked

**Real Implementation:**
- **AI Extraction**: Real Google Gemini 2.5 Flash / Vision integration.
- **OCR Engine**: Real Google Cloud Vision API integration.
- **Database**: Real PostgreSQL persistence.
- **Notifications**: Real Telegram Bot API integration delivering live push notifications.
- **File Handling**: Real MP4 byte extraction and background processing.
- **Containerization**: Fully Dockerized environments.

**Mocked Implementation:**
- **Competitor Price Scraping**: Live Amazon/Myntra scraping is mocked using scheduled background randomized volatility functions to simulate a live market without getting IP-banned.
- **Cloud Storage**: Videos are processed fully in-memory or via temporary file systems rather than permanent S3 buckets to reduce architectural overhead for the assignment.

---

## ⚖️ Trade-offs and Limitations
- **Processing Time**: Relying on external AI APIs (Gemini/GCP) means job extraction takes ~5-15 seconds. In a heavily scaled production system, this would be decoupled into a Redis/Celery queue rather than native FastAPI background tasks.
- **Video Size Limits**: Hardcoded to accept reasonable video sizes since FastAPI loads the upload into memory/tempfiles. A signed S3 direct-upload would be better for multi-GB videos.

---

## 🔮 What I Would Improve With More Time
1. **Message Broker Integration**: Implement Celery + Redis or RabbitMQ for truly robust, distributed job processing and retries.
2. **WebSocket Real-time Updates**: Replace frontend polling (`setInterval`) with WebSockets/Server-Sent Events for instant Job and Alert updates.
3. **Advanced RAG**: Connect the AI extraction to an internal product vector database (e.g., Pinecone/Milvus) to match extracted video items against an existing internal catalog perfectly.
4. **Authentication**: Implement OAuth2 / JWT to isolate dashboards by User/Organization.

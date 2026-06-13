"""Upload router — handles CSV product upload and video upload with async background processing."""

import csv
import io
import uuid
import threading
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.models import Product
from app.schemas import UploadResponse
from app.auth import verify_clerk_token
from app.services.job_processor import create_job, start_job, update_job_progress, complete_job, fail_job
from app.services.validation import validate_and_save_issues
from app.services.title_enhancement import enhance_product_title
from app.services.video_extraction import extract_products_from_video
from app.services.alerts import generate_alerts_for_product
from app.services.competitor_pricing import generate_competitor_prices

router = APIRouter(tags=["Upload"])


# ─── Background processing functions ──────────────────────────────────────────

def _process_csv_rows(job_id: str, rows: list, enhance_titles: bool, filename: str, user_id: str):
    """Process CSV rows in background thread with its own DB session."""
    db = SessionLocal()
    try:
        job = db.query(__import__('app.models', fromlist=['Job']).Job).filter_by(id=job_id).first()
        if not job:
            return

        errors = []
        processed = 0

        for idx, row in enumerate(rows):
            try:
                sku = row.get("sku_id", row.get("SKU", row.get("sku", f"SKU-{uuid.uuid4().hex[:8]}")))
                product = Product(
                    user_id=user_id,
                    job_id=job.id,
                    sku_id=sku,
                    product_title=row.get("product_title", row.get("title", row.get("name", None))) or None,
                    description=row.get("description", row.get("desc", None)) or None,
                    brand=row.get("brand", None) or None,
                    category=row.get("category", None) or None,
                    price=_safe_float(row.get("price", row.get("selling_price", None))),
                    mrp=_safe_float(row.get("mrp", row.get("MRP", None))),
                    image_url=row.get("image_url", row.get("image", None)) or None,
                    product_url=row.get("product_url", row.get("url", None)) or None,
                    availability=row.get("availability", row.get("stock_status", "in_stock")) or "in_stock",
                    color=row.get("color", None) or None,
                    size=row.get("size", None) or None,
                    material=row.get("material", None) or None,
                )
                db.add(product)
                db.flush()

                # Validate and score
                validate_and_save_issues(product, db)

                # Generate alerts
                generate_alerts_for_product(product, db)

                # AI title enhancement (optional)
                if enhance_titles:
                    try:
                        enhance_product_title(product, db)
                    except Exception:
                        pass  # Never fail a product over AI enhancement

                # Generate mock competitor prices
                try:
                    generate_competitor_prices(product, db)
                except Exception:
                    pass

                processed += 1
                update_job_progress(job, db, processed)
                db.commit()

            except Exception as e:
                db.rollback()
                errors.append(f"Row {idx + 1}: {str(e)[:100]}")

        error_msg = "; ".join(errors[:5]) if errors else None  # Cap at 5 errors
        complete_job(job, db, error_message=error_msg)
        db.commit()

    except Exception as e:
        db.rollback()
        try:
            job = db.query(__import__('app.models', fromlist=['Job']).Job).filter_by(id=job_id).first()
            if job:
                fail_job(job, db, str(e)[:200])
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


def _process_video(job_id: str, filename: str, enhance_titles: bool, video_bytes: bytes = None, video_hint: str = None):
    """Process video in background thread with its own DB session."""
    db = SessionLocal()
    try:
        job = db.query(__import__('app.models', fromlist=['Job']).Job).filter_by(id=job_id).first()
        if not job:
            return

        # Pass actual video bytes + user hint so Gemini can analyze the real content
        extracted = extract_products_from_video(filename, video_bytes=video_bytes, video_hint=video_hint)
        
        # Save to draft_data and set status to PENDING_REVIEW
        job.draft_data = [
            {
                "sku_id": item.sku_id,
                "product_title": item.product_title,
                "description": item.description,
                "brand": item.brand,
                "category": item.category,
                "price": item.price,
                "mrp": item.mrp,
                "image_url": item.image_url,
                "color": item.color,
                "size": item.size,
                "material": item.material,
            }
            for item in extracted
        ]
        job.total_products = len(extracted)
        job.status = "PENDING_REVIEW"
        db.commit()

    except Exception as e:
        db.rollback()
        try:
            job = db.query(__import__('app.models', fromlist=['Job']).Job).filter_by(id=job_id).first()
            if job:
                fail_job(job, db, str(e)[:200])
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


# ─── Routes ────────────────────────────────────────────────────────────────────

@router.post("/upload-products-csv", response_model=UploadResponse)
def upload_products_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    enhance_titles: bool = Form(False),
    db: Session = Depends(get_db),
    current_user_id: str = Depends(verify_clerk_token),
):
    """Upload a CSV file. Returns job_id immediately; processing happens in background."""
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    try:
        contents = file.file.read().decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read file: {str(e)}")

    reader = csv.DictReader(io.StringIO(contents))
    rows = list(reader)

    if not rows:
        raise HTTPException(status_code=400, detail="CSV file is empty or has no data rows.")

    # Create job and return IMMEDIATELY — processing happens in background
    job = create_job(
        db,
        job_type="csv_upload",
        user_id=current_user_id,
        file_name=file.filename,
        enhance_titles=enhance_titles,
        total_products=len(rows),
    )
    job = start_job(job, db)
    db.commit()

    job_id = str(job.id)

    # Run processing in a daemon background thread (works without celery/redis)
    t = threading.Thread(
        target=_process_csv_rows,
        args=(job_id, rows, enhance_titles, file.filename, current_user_id),
        daemon=True,
    )
    t.start()

    return UploadResponse(
        job_id=job.id,
        message=f"Processing {len(rows)} products from '{file.filename}' in background. Track progress on the Jobs page.",
        status="PROCESSING",
    )


@router.post("/upload-video", response_model=UploadResponse)
def upload_video(
    file: UploadFile = File(...),
    enhance_titles: bool = Form(False),
    video_hint: str = Form("", description="Optional: describe what products are in the video"),
    db: Session = Depends(get_db),
    current_user_id: str = Depends(verify_clerk_token),
):
    """Upload a video file for product extraction. Returns job_id immediately."""
    allowed = (".mp4", ".avi", ".mov", ".mkv", ".webm")
    if not file.filename or not any(file.filename.lower().endswith(ext) for ext in allowed):
        raise HTTPException(status_code=400, detail=f"Only video files ({', '.join(allowed)}) are accepted.")

    # Read video bytes NOW (before background thread — UploadFile closes after request)
    try:
        video_bytes = file.file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read video file: {str(e)}")

    if not video_bytes:
        raise HTTPException(status_code=400, detail="Uploaded video file is empty.")

    job = create_job(
        db,
        job_type="video_upload",
        user_id=current_user_id,
        file_name=file.filename,
        enhance_titles=enhance_titles,
    )
    job = start_job(job, db)
    db.commit()

    job_id = str(job.id)
    filename = file.filename
    hint = video_hint.strip() if video_hint else None

    t = threading.Thread(
        target=_process_video,
        args=(job_id, filename, enhance_titles, video_bytes, hint),
        daemon=True,
    )
    t.start()

    return UploadResponse(
        job_id=job.id,
        message=f"Analyzing video '{filename}' with Gemini AI. Track progress on the Jobs page.",
        status="PROCESSING",
    )


def _safe_float(value) -> Optional[float]:
    """Safely convert a value to float, return None if not possible."""
    if value is None or str(value).strip() in ("", "-", "N/A", "na", "null", "none"):
        return None
    try:
        return float(str(value).strip().replace(",", "").replace("₹", "").replace("$", ""))
    except (ValueError, TypeError):
        return None

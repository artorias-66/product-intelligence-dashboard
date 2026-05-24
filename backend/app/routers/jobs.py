"""Jobs router — list all jobs and get job details with products."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models import Job, Product
from app.schemas import JobResponse, JobListResponse

router = APIRouter(prefix="/jobs", tags=["Jobs"])

# Background task logic for processing approved products
def _process_approved_products(job_id: str, products_data: list):
    import threading
    from app.database import SessionLocal
    from app.models import Job, Product
    from app.services.job_processor import update_job_progress, complete_job, fail_job
    from app.services.validation import validate_and_save_issues
    from app.services.title_enhancement import enhance_product_title
    from app.services.alerts import generate_alerts_for_product
    from app.services.competitor_pricing import generate_competitor_prices

    def _run():
        db = SessionLocal()
        try:
            job = db.query(Job).filter_by(id=job_id).first()
            if not job:
                return

            # Change status from PENDING_REVIEW to PROCESSING
            job.status = "PROCESSING"
            job.total_products = len(products_data)
            update_job_progress(job, db, 0)
            db.commit()

            processed = 0
            for item in products_data:
                product = Product(
                    job_id=job.id,
                    sku_id=item.get("sku_id"),
                    product_title=item.get("product_title"),
                    description=item.get("description"),
                    brand=item.get("brand"),
                    category=item.get("category"),
                    price=item.get("price"),
                    mrp=item.get("mrp"),
                    image_url=item.get("image_url"),
                    color=item.get("color"),
                    size=item.get("size"),
                    material=item.get("material"),
                    availability="in_stock",
                )
                db.add(product)
                db.flush()

                validate_and_save_issues(product, db)
                generate_alerts_for_product(product, db)

                if job.enhance_titles:
                    try:
                        enhance_product_title(product, db)
                    except Exception:
                        pass

                # Generate mock competitor prices
                try:
                    generate_competitor_prices(product, db)
                except Exception:
                    pass

                processed += 1
                update_job_progress(job, db, processed)
                db.commit()

            complete_job(job, db)
            db.commit()
        except Exception as e:
            db.rollback()
            try:
                job = db.query(Job).filter_by(id=job_id).first()
                if job:
                    fail_job(job, db, str(e)[:200])
                    db.commit()
            except Exception:
                pass
        finally:
            db.close()

    t = threading.Thread(target=_run, daemon=True)
    t.start()


@router.get("", response_model=JobListResponse)
def list_jobs(
    status: Optional[str] = Query(None, description="Filter by status"),
    job_type: Optional[str] = Query(None, description="Filter by type"),
    # Support both limit/offset AND page/page_size
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List all jobs with optional filtering."""
    query = db.query(Job)

    if status:
        query = query.filter(Job.status == status.upper())
    if job_type:
        query = query.filter(Job.type == job_type)

    total = query.count()

    # Honour both pagination styles
    effective_limit = limit
    effective_offset = offset
    if page > 1 or page_size != 50:
        effective_limit = page_size
        effective_offset = (page - 1) * page_size

    jobs = query.order_by(desc(Job.created_at)).offset(effective_offset).limit(effective_limit).all()

    return JobListResponse(
        jobs=[JobResponse.model_validate(j) for j in jobs],
        total=total,
    )


@router.get("/{job_id}")
def get_job(job_id: UUID, db: Session = Depends(get_db)):
    """Get details of a specific job including its processed products."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    # Load products associated with this job
    products = (
        db.query(Product)
        .filter(Product.job_id == job.id)
        .order_by(Product.created_at.desc())
        .all()
    )

    job_data = JobResponse.model_validate(job).model_dump()
    job_data["products"] = [
        {
            "sku_id": p.sku_id,
            "product_title": p.product_title,
            "quality_score": p.quality_score,
            "availability": p.availability,
            "brand": p.brand,
            "category": p.category,
        }
        for p in products
    ]

    return job_data


@router.post("/{job_id}/approve")
def approve_job(job_id: UUID, products_data: list[dict], db: Session = Depends(get_db)):
    """Approve extracted products and resume processing."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    if job.status != "PENDING_REVIEW":
        raise HTTPException(status_code=400, detail=f"Job is in status '{job.status}', expected 'PENDING_REVIEW'.")

    # Start the background processing thread
    _process_approved_products(str(job_id), products_data)

    return {"message": "Job approved and processing resumed."}


@router.post("/{job_id}/retry")
def retry_failed_job(job_id: UUID, db: Session = Depends(get_db)):
    """Retry a failed job. Resets it to PENDING_REVIEW if draft data is available."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    if job.status != "FAILED":
        raise HTTPException(status_code=400, detail="Only FAILED jobs can be retried.")

    if not job.draft_data:
        raise HTTPException(status_code=400, detail="Cannot retry this job because original draft data is missing. Please re-upload.")

    # Reset job to PENDING_REVIEW so user can fix data and re-approve
    job.status = "PENDING_REVIEW"
    job.error_message = None
    job.progress = 50
    db.commit()

    return {"message": "Job reset to PENDING_REVIEW. You may now review and approve it again."}

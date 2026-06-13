"""Job state machine and processing logic."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Job


class JobStatus:
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED"


def create_job(
    db: Session,
    job_type: str,
    user_id: str,
    file_name: Optional[str] = None,
    enhance_titles: bool = False,
    total_products: int = 0,
) -> Job:
    """Create a new job in PENDING state."""
    job = Job(
        user_id=user_id,
        type=job_type,
        status=JobStatus.PENDING,
        file_name=file_name,
        enhance_titles=enhance_titles,
        total_products=total_products,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def start_job(job: Job, db: Session) -> Job:
    """Transition job from PENDING → RUNNING."""
    job.status = JobStatus.RUNNING
    job.started_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(job)
    return job


def update_job_progress(
    job: Job, db: Session, processed: int, total: Optional[int] = None
) -> Job:
    """Update progress counters on a running job."""
    job.processed_products = processed
    if total is not None:
        job.total_products = total
    if job.total_products > 0:
        job.progress = min(100, int((processed / job.total_products) * 100))
    db.commit()
    db.refresh(job)
    return job


def complete_job(job: Job, db: Session, error_message: Optional[str] = None) -> Job:
    """Transition job to COMPLETED or PARTIALLY_COMPLETED."""
    job.completed_at = datetime.now(timezone.utc)
    job.progress = 100

    if error_message:
        job.error_message = error_message
        if job.processed_products < job.total_products:
            job.status = JobStatus.PARTIALLY_COMPLETED
        else:
            job.status = JobStatus.COMPLETED
    else:
        job.status = JobStatus.COMPLETED

    db.commit()
    db.refresh(job)
    return job


def fail_job(job: Job, db: Session, error_message: str) -> Job:
    """Transition job to FAILED."""
    job.status = JobStatus.FAILED
    job.error_message = error_message
    job.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(job)
    return job

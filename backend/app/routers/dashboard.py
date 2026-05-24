"""Dashboard router — quality summary analytics."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import Product, ProductIssue
from app.schemas import (
    QualitySummaryResponse,
    IssueSeverityCount,
    IssueTypeCount,
    QualityDistribution,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/quality-summary", response_model=QualitySummaryResponse)
def get_quality_summary(db: Session = Depends(get_db)):
    """Get aggregated quality summary for the dashboard."""

    total_products = db.query(func.count(Product.id)).scalar() or 0
    avg_score = db.query(func.avg(Product.quality_score)).scalar() or 0.0

    # Products with at least one issue
    products_with_issues = (
        db.query(func.count(func.distinct(ProductIssue.product_id))).scalar() or 0
    )

    total_issues = db.query(func.count(ProductIssue.id)).scalar() or 0

    # Issues by severity
    severity_rows = (
        db.query(ProductIssue.severity, func.count(ProductIssue.id))
        .group_by(ProductIssue.severity)
        .all()
    )
    issues_by_severity = [
        IssueSeverityCount(severity=sev, count=cnt) for sev, cnt in severity_rows
    ]

    severity_map = {s.severity: s.count for s in issues_by_severity}
    high_count = severity_map.get("HIGH", 0)
    medium_count = severity_map.get("MEDIUM", 0)
    low_count = severity_map.get("LOW", 0)

    # Issues by type
    type_rows = (
        db.query(ProductIssue.issue_type, func.count(ProductIssue.id))
        .group_by(ProductIssue.issue_type)
        .order_by(func.count(ProductIssue.id).desc())
        .all()
    )
    issues_by_type = [
        IssueTypeCount(issue_type=it, count=cnt) for it, cnt in type_rows
    ]

    # Quality distribution buckets
    ranges = [
        ("0-20 (Critical)", 0, 20),
        ("21-40 (Poor)", 21, 40),
        ("41-60 (Fair)", 41, 60),
        ("61-80 (Good)", 61, 80),
        ("81-100 (Excellent)", 81, 100),
    ]
    quality_distribution = []
    for label, low, high in ranges:
        cnt = (
            db.query(func.count(Product.id))
            .filter(Product.quality_score >= low, Product.quality_score <= high)
            .scalar()
            or 0
        )
        quality_distribution.append(QualityDistribution(range_label=label, count=cnt))

    return QualitySummaryResponse(
        total_products=total_products,
        average_quality_score=round(float(avg_score), 2),
        products_with_issues=products_with_issues,
        total_issues=total_issues,
        issues_by_severity=issues_by_severity,
        issues_by_type=issues_by_type,
        quality_distribution=quality_distribution,
        high_severity_count=high_count,
        medium_severity_count=medium_count,
        low_severity_count=low_count,
    )


import csv
import io
from fastapi import Response

@router.get("/quality-report-csv")
def download_quality_report_csv(db: Session = Depends(get_db)):
    """Generate a downloadable CSV report of all products and their quality scores."""
    products = db.query(Product).order_by(Product.quality_score.asc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "SKU ID", 
        "Product Title", 
        "Brand", 
        "Category", 
        "Quality Score", 
        "Availability", 
        "Issues Count",
        "Last Updated"
    ])

    for p in products:
        writer.writerow([
            p.sku_id,
            p.product_title or "N/A",
            p.brand or "N/A",
            p.category or "N/A",
            round(p.quality_score, 2) if p.quality_score is not None else "N/A",
            p.availability or "N/A",
            len(p.issues),
            p.updated_at.strftime("%Y-%m-%d %H:%M:%S") if p.updated_at else "N/A"
        ])

    response = Response(content=output.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=product_quality_report.csv"
    return response

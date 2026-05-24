"""Competitor prices router — upload, refresh, and query competitor pricing data."""

import csv
import io
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product, CompetitorPrice, PriceHistory
from app.schemas import (
    CompetitorPriceResponse,
    CompetitorPriceUploadResponse,
    PriceHistoryResponse,
    MessageResponse,
)
from app.services.competitor_pricing import (
    generate_competitor_prices,
    refresh_competitor_prices,
)
from app.services.alerts import generate_alerts_for_product, generate_price_drop_alert

router = APIRouter(prefix="/competitor-prices", tags=["Competitor Prices"])


@router.post("/refresh")
def refresh_all_competitor_prices(db: Session = Depends(get_db)):
    """Refresh competitor prices for ALL products in the database (runs in background)."""
    import threading
    from app.models import Product as Prod
    from app.database import SessionLocal

    def _do_refresh():
        bdb = SessionLocal()
        try:
            products = bdb.query(Prod).filter(Prod.price.isnot(None)).limit(100).all()
            for product in products:
                try:
                    old_prices = {
                        cp.platform: cp.competitor_price
                        for cp in bdb.query(CompetitorPrice)
                        .filter(CompetitorPrice.product_id == product.id)
                        .all()
                    }
                    refreshed = refresh_competitor_prices(product, bdb)
                    for cp in refreshed:
                        old = old_prices.get(cp.platform)
                        if old:
                            generate_price_drop_alert(product, cp.platform, old, cp.competitor_price, bdb)
                except Exception as e:
                    print(f"Refresh failed for {product.sku_id}: {e}")
            print(f"Bulk refresh complete for {len(products)} products")
        finally:
            bdb.close()

    t = threading.Thread(target=_do_refresh, daemon=True)
    t.start()
    return {"message": "Competitor price refresh started in the background. Prices will be updated shortly.", "status": "started"}


@router.get("/product/{sku_id}", response_model=list[CompetitorPriceResponse])
def get_competitor_prices_by_product(sku_id: str, db: Session = Depends(get_db)):
    """Get all competitor prices for a product by SKU ID."""
    product = db.query(Product).filter(Product.sku_id == sku_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product with SKU '{sku_id}' not found.")

    prices = (
        db.query(CompetitorPrice)
        .filter(CompetitorPrice.product_id == product.id)
        .order_by(CompetitorPrice.competitor_price.asc())
        .all()
    )
    return [CompetitorPriceResponse.model_validate(p) for p in prices]


@router.get("/product/{sku_id}/history", response_model=list[PriceHistoryResponse])
def get_price_history(
    sku_id: str,
    platform: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Get price history for a product, optionally filtered by platform."""
    product = db.query(Product).filter(Product.sku_id == sku_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product with SKU '{sku_id}' not found.")

    query = db.query(PriceHistory).filter(PriceHistory.product_id == product.id)
    if platform:
        query = query.filter(PriceHistory.platform == platform)

    history = query.order_by(PriceHistory.checked_at.desc()).limit(limit).all()
    return [PriceHistoryResponse.model_validate(h) for h in history]


@router.post("/product/{sku_id}/generate", response_model=list[CompetitorPriceResponse])
def generate_prices_for_product(sku_id: str, db: Session = Depends(get_db)):
    """Generate mock competitor prices for a product."""
    product = db.query(Product).filter(Product.sku_id == sku_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product with SKU '{sku_id}' not found.")

    prices = generate_competitor_prices(product, db)
    return [CompetitorPriceResponse.model_validate(p) for p in prices]


@router.post("/product/{sku_id}/refresh", response_model=list[CompetitorPriceResponse])
def refresh_prices_for_product(sku_id: str, db: Session = Depends(get_db)):
    """Refresh competitor prices for a product and check for price drops."""
    product = db.query(Product).filter(Product.sku_id == sku_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product with SKU '{sku_id}' not found.")

    # Get old prices before refresh
    old_prices = {
        cp.platform: cp.competitor_price
        for cp in db.query(CompetitorPrice)
        .filter(CompetitorPrice.product_id == product.id)
        .all()
    }

    refreshed = refresh_competitor_prices(product, db)

    # Check for price drops > 5% and generate alerts
    for cp in refreshed:
        old = old_prices.get(cp.platform)
        if old:
            generate_price_drop_alert(product, cp.platform, old, cp.competitor_price, db)

    return [CompetitorPriceResponse.model_validate(p) for p in refreshed]


@router.post("/upload-csv", response_model=CompetitorPriceUploadResponse)
def upload_competitor_prices_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload competitor prices from a CSV file."""
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    try:
        contents = file.file.read().decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read file: {str(e)}")

    reader = csv.DictReader(io.StringIO(contents))
    rows = list(reader)

    if not rows:
        raise HTTPException(status_code=400, detail="CSV file is empty.")

    uploaded = 0
    product_id = None

    for row in rows:
        sku = row.get("sku_id", row.get("SKU", ""))
        product = db.query(Product).filter(Product.sku_id == sku).first()
        if not product:
            continue

        product_id = product.id

        try:
            price = float(row.get("competitor_price", row.get("price", "0")))
        except (ValueError, TypeError):
            continue

        cp = CompetitorPrice(
            product_id=product.id,
            sku_id=sku,
            platform=row.get("platform", "Unknown"),
            product_name=row.get("product_name", product.product_title),
            competitor_url=row.get("competitor_url", row.get("url", None)),
            competitor_price=price,
            currency=row.get("currency", "INR"),
        )
        db.add(cp)
        uploaded += 1

    db.commit()

    if product_id is None:
        raise HTTPException(status_code=404, detail="No matching products found for the uploaded SKUs.")

    return CompetitorPriceUploadResponse(
        message=f"Uploaded {uploaded} competitor prices.",
        total_uploaded=uploaded,
        product_id=product_id,
    )

"""Products router — list, get, update products."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from app.database import get_db
from app.models import Product
from app.schemas import (
    ProductResponse,
    ProductDetailResponse,
    ProductListResponse,
    ProductUpdate,
    ProductIssueResponse,
    EnhancedTitleResponse,
    CompetitorPriceResponse,
)
from app.services.validation import validate_and_save_issues
from app.services.alerts import generate_alerts_for_product, clear_alerts_for_product
from app.auth import verify_clerk_token

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=ProductListResponse)
def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None, ge=0, le=100),
    max_score: Optional[float] = Query(None, ge=0, le=100),
    search: Optional[str] = Query(None, description="Search in title or SKU"),
    sort_by: Optional[str] = Query("created_at", description="Sort field"),
    sort_order: Optional[str] = Query("desc", description="asc or desc"),
    job_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user_id: str = Depends(verify_clerk_token),
):
    """List products with pagination, filtering, and search."""
    query = db.query(Product).filter(Product.user_id == current_user_id)

    if job_id:
        query = query.filter(Product.job_id == job_id)
    if category:
        query = query.filter(Product.category.ilike(f"%{category}%"))
    if brand:
        query = query.filter(Product.brand.ilike(f"%{brand}%"))
    if min_score is not None:
        query = query.filter(Product.quality_score >= min_score)
    if max_score is not None:
        query = query.filter(Product.quality_score <= max_score)
    if search:
        query = query.filter(
            (Product.product_title.ilike(f"%{search}%"))
            | (Product.sku_id.ilike(f"%{search}%"))
        )

    total = query.count()

    # Sorting
    sort_column = getattr(Product, sort_by, Product.created_at)
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    offset = (page - 1) * page_size
    products = query.offset(offset).limit(page_size).all()

    return ProductListResponse(
        products=[ProductResponse.model_validate(p) for p in products],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{sku_id}", response_model=ProductDetailResponse)
def get_product(sku_id: str, db: Session = Depends(get_db), current_user_id: str = Depends(verify_clerk_token)):
    """Get detailed product info by SKU ID, including issues, titles, and competitor prices."""
    product = (
        db.query(Product)
        .options(
            joinedload(Product.issues),
            joinedload(Product.enhanced_titles),
            joinedload(Product.competitor_prices),
        )
        .filter(Product.sku_id == sku_id, Product.user_id == current_user_id)
        .order_by(Product.created_at.desc())
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail=f"Product with SKU '{sku_id}' not found.")

    return ProductDetailResponse(
        **ProductResponse.model_validate(product).model_dump(),
        issues=[ProductIssueResponse.model_validate(i) for i in product.issues],
        enhanced_titles=[EnhancedTitleResponse.model_validate(t) for t in product.enhanced_titles],
        competitor_prices=[CompetitorPriceResponse.model_validate(c) for c in product.competitor_prices],
    )


@router.put("/{sku_id}", response_model=ProductResponse)
def update_product(
    sku_id: str, update: ProductUpdate, db: Session = Depends(get_db), current_user_id: str = Depends(verify_clerk_token)
):
    """Update a product by SKU ID. Re-runs validation and alert generation."""
    product = db.query(Product).filter(Product.sku_id == sku_id, Product.user_id == current_user_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product with SKU '{sku_id}' not found.")

    # Apply updates
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)

    # Re-validate
    validate_and_save_issues(product, db)

    # Re-generate alerts
    clear_alerts_for_product(product.id, db)
    generate_alerts_for_product(product, db)

    db.refresh(product)
    return ProductResponse.model_validate(product)


@router.get("/{sku_id}/recommendations", response_model=list[ProductResponse])
def get_recommendations(sku_id: str, limit: int = 4, db: Session = Depends(get_db), current_user_id: str = Depends(verify_clerk_token)):
    """Get similar product recommendations based on category and brand matching."""
    product = db.query(Product).filter(Product.sku_id == sku_id, Product.user_id == current_user_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product with SKU '{sku_id}' not found.")

    # 1. Try to find products in the exact same category, excluding the current product
    query = db.query(Product).filter(Product.id != product.id, Product.user_id == current_user_id)
    
    if product.category:
        query = query.filter(Product.category == product.category)
    elif product.brand:
        query = query.filter(Product.brand == product.brand)

    # Order by highest quality score and return top N
    recommendations = query.order_by(Product.quality_score.desc()).limit(limit).all()

    # If we didn't get enough, fall back to any high quality products
    if len(recommendations) < limit:
        ids_to_exclude = [r.id for r in recommendations] + [product.id]
        more = (
            db.query(Product)
            .filter(Product.id.notin_(ids_to_exclude), Product.user_id == current_user_id)
            .order_by(Product.quality_score.desc())
            .limit(limit - len(recommendations))
            .all()
        )
        recommendations.extend(more)

    return [ProductResponse.model_validate(r) for r in recommendations]

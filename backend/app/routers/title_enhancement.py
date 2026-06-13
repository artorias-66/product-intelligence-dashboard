"""Title enhancement router — enhance product titles using Gemini AI."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product
from app.schemas import EnhancedTitleResponse, EnhanceTitleRequest
from app.services.title_enhancement import enhance_product_title
from app.auth import verify_clerk_token

router = APIRouter(tags=["Title Enhancement"])


@router.post("/products/{sku_id}/enhance-title", response_model=EnhancedTitleResponse)
def enhance_title(
    sku_id: str,
    request: EnhanceTitleRequest = None,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(verify_clerk_token),
):
    """Enhance a product title using Gemini AI with fallback."""
    product = db.query(Product).filter(Product.sku_id == sku_id, Product.user_id == current_user_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product with SKU '{sku_id}' not found.")

    category = None
    brand = None
    if request:
        category = request.category
        brand = request.brand

    enhanced = enhance_product_title(product, db, category=category, brand=brand)
    return EnhancedTitleResponse.model_validate(enhanced)

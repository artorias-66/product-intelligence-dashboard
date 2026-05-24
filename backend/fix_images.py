"""One-time script to update image URLs in the database from fake Flipkart URLs to real Unsplash URLs."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import Product

IMAGE_MAP = {
    "FLK-SHOE-001": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&q=80",
    "FLK-TSHIRT-002": "https://images.unsplash.com/photo-1586790170083-2f9ceadc732d?w=400&q=80",
    "FLK-PHONE-003": "https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=400&q=80",
    "FLK-WATCH-004": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&q=80",
    "FLK-LAPTOP-005": "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=400&q=80",
    "FLK-HDPHN-006": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&q=80",
    "FLK-KURTA-007": "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=400&q=80",
    "FLK-BACKPK-008": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&q=80",
    "FLK-MIXER-009": "https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=400&q=80",
    "FLK-SAREE-010": "https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=400&q=80",
    "FLK-FRIDGE-011": "https://images.unsplash.com/photo-1571175443880-49e1d25b2bc5?w=400&q=80",
    "FLK-PERFM-012": "https://images.unsplash.com/photo-1541643600914-78b084683702?w=400&q=80",
    "FLK-JEANS-013": "https://images.unsplash.com/photo-1542272604-787c3835535d?w=400&q=80",
    "FLK-TABLET-014": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=400&q=80",
    "FLK-BEDSH-015": "https://images.unsplash.com/photo-1631016800696-5ea8801b3c2a?w=400&q=80",
    "FLK-SHOE-016": "https://images.unsplash.com/photo-1614252235316-8c857d38b5f4?w=400&q=80",
    "FLK-CABLE-018": "https://images.unsplash.com/photo-1588348460-edd8c2b0cfe6?w=400&q=80",
    "FLK-PILLOW-019": "https://images.unsplash.com/photo-1584100936595-c0654b55a2e2?w=400&q=80",
    "FLK-BOTTLE-020": "https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=400&q=80",
}

db = SessionLocal()
updated = 0
try:
    for sku_id, new_url in IMAGE_MAP.items():
        product = db.query(Product).filter(Product.sku_id == sku_id).first()
        if product:
            product.image_url = new_url
            updated += 1
            print(f"  Updated {sku_id}")
    db.commit()
    print(f"\n✅ Updated {updated} product image URLs in database.")
except Exception as e:
    db.rollback()
    print(f"❌ Error: {e}")
finally:
    db.close()

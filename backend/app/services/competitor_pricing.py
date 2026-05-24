"""Competitor pricing service — generates mock competitor price data."""

import random
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Product, CompetitorPrice, PriceHistory

PLATFORMS = ["Amazon", "Myntra", "Ajio", "Nykaa Fashion", "Tata Cliq", "Meesho"]

def generate_competitor_prices(
    product: Product, db: Session, platforms: Optional[list[str]] = None
) -> list[CompetitorPrice]:
    """
    Generate mock competitor prices for a product across platforms.
    Returns list of created CompetitorPrice records.
    """
    target_platforms = platforms or PLATFORMS
    created = []

    for platform in target_platforms:
        if not product.price or product.price <= 0:
            base_price = random.uniform(500, 5000)
        else:
            # Vary competitor price by -15% to +20% from our price
            variation = random.uniform(-0.15, 0.20)
            base_price = product.price * (1 + variation)

        base_price = round(base_price, 2)

        cp = CompetitorPrice(
            product_id=product.id,
            sku_id=product.sku_id,
            platform=platform,
            product_name=product.product_title or f"{product.sku_id} on {platform}",
            competitor_url=f"https://www.{platform.lower().replace(' ', '')}.com/dp/{product.sku_id}",
            competitor_price=base_price,
            currency="INR",
            last_checked_at=datetime.now(timezone.utc),
        )
        db.add(cp)
        created.append(cp)

    db.commit()
    for c in created:
        db.refresh(c)
    return created


def refresh_competitor_prices(product: Product, db: Session) -> list[CompetitorPrice]:
    """
    Refresh competitor prices for a product by updating existing or generating new ones.
    Also logs price history for tracking drops.
    """
    existing = (
        db.query(CompetitorPrice)
        .filter(CompetitorPrice.product_id == product.id)
        .all()
    )

    if not existing:
        return generate_competitor_prices(product, db)

    refreshed = []
    for cp in existing:
        old_price = cp.competitor_price

        # Log old price to history
        history = PriceHistory(
            product_id=product.id,
            platform=cp.platform,
            price=old_price,
            checked_at=cp.last_checked_at,
        )
        db.add(history)

        # Update with slight variation (-8% to +5%)
        variation = random.uniform(-0.08, 0.05)
        new_price = round(old_price * (1 + variation), 2)
        cp.competitor_price = new_price
        cp.last_checked_at = datetime.now(timezone.utc)
        refreshed.append(cp)

    db.commit()
    for r in refreshed:
        db.refresh(r)
    return refreshed


def generate_price_history(
    product: Product, db: Session, days: int = 30, points_per_platform: int = 5
) -> list[PriceHistory]:
    """Generate mock historical price data for a product across all platforms."""
    created = []
    base_price = product.price or random.uniform(500, 5000)

    for platform in PLATFORMS:
        platform_variation = random.uniform(-0.10, 0.15)
        platform_base = base_price * (1 + platform_variation)

        # Generate data points spread over the last N days
        for i in range(points_per_platform):
            days_ago = random.randint(1, days)
            price_drift = random.uniform(-0.08, 0.08)
            price = round(platform_base * (1 + price_drift), 2)

            ph = PriceHistory(
                product_id=product.id,
                platform=platform,
                price=price,
                checked_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
            )
            db.add(ph)
            created.append(ph)

    db.commit()
    return created

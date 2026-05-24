"""Automated background scheduler for periodic tasks."""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.database import SessionLocal
from app.models import Product
from app.services.competitor_pricing import refresh_competitor_prices

logger = logging.getLogger(__name__)

# Initialize the scheduler
scheduler = BackgroundScheduler()

def scheduled_price_refresh():
    """Refresh competitor prices for all products."""
    logger.info("Starting automated competitor price refresh...")
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        refreshed_count = 0
        for p in products:
            try:
                refresh_competitor_prices(p, db)
                refreshed_count += 1
            except Exception as e:
                logger.error(f"Failed to refresh prices for SKU {p.sku_id}: {e}")
        logger.info(f"Automated price refresh completed for {refreshed_count} products.")
    except Exception as e:
        logger.error(f"Error during scheduled price refresh: {e}")
    finally:
        db.close()

def start_scheduler():
    """Start the background scheduler."""
    if not scheduler.running:
        # Run every 12 hours
        scheduler.add_job(
            scheduled_price_refresh,
            trigger=IntervalTrigger(hours=12),
            id="price_refresh_job",
            name="Refresh Competitor Prices",
            replace_existing=True,
        )
        scheduler.start()
        logger.info("Background scheduler started. Next price refresh scheduled in 12 hours.")

def stop_scheduler():
    """Stop the background scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Background scheduler stopped.")

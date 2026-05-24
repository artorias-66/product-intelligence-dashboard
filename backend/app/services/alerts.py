"""Alert rules engine — generates and evaluates alerts based on product and pricing data."""

from typing import Optional

from sqlalchemy.orm import Session

from app.models import Product, ProductIssue, CompetitorPrice, Alert
from app.services.notifications import send_telegram_notification


def generate_alerts_for_product(product: Product, db: Session) -> list[Alert]:
    """
    Evaluate alert rules for a single product based on its issues and competitor prices.
    Returns newly created Alert records.
    """
    created_alerts: list[Alert] = []

    # ─── Listing Issue Alerts ──────────────────────────────────────
    issues = (
        db.query(ProductIssue).filter(ProductIssue.product_id == product.id).all()
    )

    high_issues = [i for i in issues if i.severity == "HIGH"]
    medium_issues = [i for i in issues if i.severity == "MEDIUM"]
    low_issues = [i for i in issues if i.severity == "LOW"]

    # HIGH: No title / price / invalid price → "Critical listing issue"
    critical_types = {"missing_title", "invalid_price", "missing_image", "duplicate_sku", "mrp_less_than_price"}
    critical_issues = [i for i in high_issues if i.issue_type in critical_types]
    if critical_issues:
        issue_list = ", ".join(set(i.issue_type for i in critical_issues))
        alert = Alert(
            product_id=product.id,
            type="listing_issue",
            severity="HIGH",
            title="Critical listing issue",
            message=f"Product '{product.sku_id}' has critical issues: {issue_list}. These must be fixed for the listing to be effective.",
        )
        db.add(alert)
        created_alerts.append(alert)
        
        # Send Telegram notification for critical issues
        send_telegram_notification(
            f"🚨 *CRITICAL LISTING ISSUE*\n\n"
            f"Product: `{product.sku_id}`\n"
            f"Issues: {issue_list}\n"
            f"Action Required: Immediate fix needed."
        )

    # MEDIUM: Weak title / missing attributes → "Listing improvement needed"
    improvement_types = {"short_title", "missing_brand", "missing_attributes", "broken_image_url"}
    improvement_issues = [i for i in medium_issues if i.issue_type in improvement_types]
    if improvement_issues:
        issue_list = ", ".join(set(i.issue_type for i in improvement_issues))
        alert = Alert(
            product_id=product.id,
            type="listing_improvement",
            severity="MEDIUM",
            title="Listing improvement needed",
            message=f"Product '{product.sku_id}' can be improved: {issue_list}. Fixing these will boost discoverability.",
        )
        db.add(alert)
        created_alerts.append(alert)

    # LOW: Weak description / out of stock → "Minor listing issue"
    minor_types = {"weak_description", "out_of_stock"}
    minor_issues = [i for i in low_issues if i.issue_type in minor_types]
    if minor_issues:
        issue_list = ", ".join(set(i.issue_type for i in minor_issues))
        alert = Alert(
            product_id=product.id,
            type="minor_issue",
            severity="LOW",
            title="Minor listing issue",
            message=f"Product '{product.sku_id}' has minor issues: {issue_list}.",
        )
        db.add(alert)
        created_alerts.append(alert)

    # ─── Competitor Price Alerts ──────────────────────────────────
    if product.price and product.price > 0:
        competitor_prices = (
            db.query(CompetitorPrice)
            .filter(CompetitorPrice.product_id == product.id)
            .all()
        )

        if competitor_prices:
            lowest = min(cp.competitor_price for cp in competitor_prices)
            lowest_platform = next(
                cp.platform for cp in competitor_prices if cp.competitor_price == lowest
            )

            # HIGH: Our price >10% above lowest competitor
            if product.price > lowest * 1.10:
                pct = round(((product.price - lowest) / lowest) * 100, 1)
                alert = Alert(
                    product_id=product.id,
                    type="price_competitive",
                    severity="HIGH",
                    title="Price not competitive",
                    message=(
                        f"Product '{product.sku_id}' is priced at ₹{product.price} — "
                        f"{pct}% above the lowest competitor price of ₹{lowest} on {lowest_platform}."
                    ),
                )
                db.add(alert)
                created_alerts.append(alert)

                # Send Telegram notification for severe pricing disadvantage
                send_telegram_notification(
                    f"⚠️ *PRICE COMPETITIVENESS ALERT*\n\n"
                    f"Product: `{product.sku_id}`\n"
                    f"Our Price: ₹{product.price}\n"
                    f"Competitor: {lowest_platform} @ ₹{lowest}\n"
                    f"Gap: +{pct}%\n"
                    f"Action Required: Adjust pricing strategy."
                )

    db.commit()
    for a in created_alerts:
        db.refresh(a)
    return created_alerts


def generate_price_drop_alert(
    product: Product, platform: str, old_price: float, new_price: float, db: Session
) -> Optional[Alert]:
    """
    MEDIUM: Competitor price dropped >5% on refresh → "Competitor price drop detected"
    """
    if old_price <= 0:
        return None

    drop_pct = ((old_price - new_price) / old_price) * 100
    if drop_pct > 5:
        alert = Alert(
            product_id=product.id,
            type="competitor_price_drop",
            severity="MEDIUM",
            title="Competitor price drop detected",
            message=(
                f"Price on {platform} dropped {round(drop_pct, 1)}% from "
                f"₹{old_price} to ₹{new_price} for product '{product.sku_id}'. "
                f"Consider adjusting your pricing strategy."
            ),
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

        send_telegram_notification(
            f"📉 *COMPETITOR PRICE DROP*\n\n"
            f"Product: `{product.sku_id}`\n"
            f"Platform: {platform}\n"
            f"Drop: {round(drop_pct, 1)}% (₹{old_price} -> ₹{new_price})\n"
            f"Action Required: Review pricing."
        )
        
        return alert
    return None


def clear_alerts_for_product(product_id, db: Session) -> int:
    """Clear all alerts for a product. Returns count of deleted alerts."""
    count = db.query(Alert).filter(Alert.product_id == product_id).delete()
    db.commit()
    return count

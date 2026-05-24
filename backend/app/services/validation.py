"""Product validation engine with 11 quality rules.

Each rule returns a list of issues found for a given product.
The validate_product function runs all rules and computes a quality score.
"""

from typing import Optional
from sqlalchemy.orm import Session

from app.models import Product, ProductIssue


def _check_missing_title(product: Product) -> Optional[dict]:
    """Rule 1: Missing title → HIGH severity."""
    if not product.product_title or not product.product_title.strip():
        return {
            "issue_type": "missing_title",
            "severity": "HIGH",
            "message": "Product title is missing.",
            "suggested_fix": "Add a clear product title with brand, type, and key attributes.",
        }
    return None


def _check_short_title(product: Product) -> Optional[dict]:
    """Rule 2: Very short title (<20 chars) → MEDIUM severity."""
    if product.product_title and 0 < len(product.product_title.strip()) < 20:
        return {
            "issue_type": "short_title",
            "severity": "MEDIUM",
            "message": f"Product title is too short ({len(product.product_title.strip())} chars).",
            "suggested_fix": "Add brand, product type, color, gender, or material to the title.",
        }
    return None


def _check_missing_brand(product: Product) -> Optional[dict]:
    """Rule 3: Missing brand → MEDIUM severity."""
    if not product.brand or not product.brand.strip():
        return {
            "issue_type": "missing_brand",
            "severity": "MEDIUM",
            "message": "Brand information is missing.",
            "suggested_fix": "Add brand if known, or mark as unbranded.",
        }
    return None


def _check_invalid_price(product: Product) -> Optional[dict]:
    """Rule 4: Invalid price (non-numeric, <=0, None) → HIGH severity."""
    if product.price is None or product.price <= 0:
        return {
            "issue_type": "invalid_price",
            "severity": "HIGH",
            "message": "Price is missing or invalid.",
            "suggested_fix": "Price should be positive and numeric.",
        }
    return None


def _check_mrp_vs_price(product: Product) -> Optional[dict]:
    """Rule 5: MRP < selling price → HIGH severity."""
    if (
        product.mrp is not None
        and product.price is not None
        and product.mrp > 0
        and product.price > 0
        and product.mrp < product.price
    ):
        return {
            "issue_type": "mrp_less_than_price",
            "severity": "HIGH",
            "message": f"MRP (₹{product.mrp}) is less than selling price (₹{product.price}).",
            "suggested_fix": "Correct MRP or selling price. MRP should be >= selling price.",
        }
    return None


def _check_missing_image(product: Product) -> Optional[dict]:
    """Rule 6: Missing image → HIGH severity."""
    if not product.image_url or not product.image_url.strip():
        return {
            "issue_type": "missing_image",
            "severity": "HIGH",
            "message": "Product image is missing.",
            "suggested_fix": "Add at least one product image URL.",
        }
    return None


def _check_broken_image_url(product: Product) -> Optional[dict]:
    """Rule 7: Broken image URL (no http/https) → MEDIUM severity."""
    if product.image_url and product.image_url.strip():
        url = product.image_url.strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            return {
                "issue_type": "broken_image_url",
                "severity": "MEDIUM",
                "message": "Image URL does not start with http:// or https://.",
                "suggested_fix": "Replace with an accessible image URL starting with http:// or https://.",
            }
    return None


def _check_duplicate_sku(product: Product, db: Session) -> Optional[dict]:
    """Rule 8: Duplicate SKU → HIGH severity."""
    duplicate_count = (
        db.query(Product)
        .filter(Product.sku_id == product.sku_id, Product.id != product.id)
        .count()
    )
    if duplicate_count > 0:
        return {
            "issue_type": "duplicate_sku",
            "severity": "HIGH",
            "message": f"SKU '{product.sku_id}' is used by {duplicate_count} other product(s).",
            "suggested_fix": "Keep SKU IDs unique across all products.",
        }
    return None


def _check_weak_description(product: Product) -> Optional[dict]:
    """Rule 9: Weak description (<50 chars or None) → LOW severity."""
    if not product.description or len(product.description.strip()) < 50:
        return {
            "issue_type": "weak_description",
            "severity": "LOW",
            "message": "Product description is missing or too short.",
            "suggested_fix": "Add more product details and attributes (at least 50 characters).",
        }
    return None


def _check_missing_attributes(product: Product) -> Optional[dict]:
    """Rule 10: Missing attributes (color+size+material all None) → MEDIUM severity."""
    has_color = product.color and product.color.strip()
    has_size = product.size and product.size.strip()
    has_material = product.material and product.material.strip()
    if not has_color and not has_size and not has_material:
        return {
            "issue_type": "missing_attributes",
            "severity": "MEDIUM",
            "message": "Product attributes (color, size, material) are all missing.",
            "suggested_fix": "Add color, size, material, gender, or category-specific attributes.",
        }
    return None


def _check_out_of_stock(product: Product) -> Optional[dict]:
    """Rule 11: Out of stock → LOW severity."""
    if product.availability and product.availability.strip().lower() in (
        "out of stock",
        "out_of_stock",
        "unavailable",
    ):
        return {
            "issue_type": "out_of_stock",
            "severity": "LOW",
            "message": "Product is currently out of stock.",
            "suggested_fix": "Mark separately or notify operations team to restock.",
        }
    return None


# Severity weight for score calculation
SEVERITY_WEIGHTS = {
    "HIGH": 15,
    "MEDIUM": 8,
    "LOW": 3,
}


def validate_product(product: Product, db: Session) -> tuple[list[dict], float]:
    """
    Run all 11 validation rules on a product.

    Returns:
        Tuple of (list of issue dicts, quality_score 0-100).
    """
    issues: list[dict] = []

    # Rules that don't need DB
    simple_rules = [
        _check_missing_title,
        _check_short_title,
        _check_missing_brand,
        _check_invalid_price,
        _check_mrp_vs_price,
        _check_missing_image,
        _check_broken_image_url,
        _check_weak_description,
        _check_missing_attributes,
        _check_out_of_stock,
    ]

    for rule in simple_rules:
        result = rule(product)
        if result:
            issues.append(result)

    # Rule needing DB (duplicate SKU)
    dup_result = _check_duplicate_sku(product, db)
    if dup_result:
        issues.append(dup_result)

    # Calculate quality score (100 = perfect, deducted by severity weight)
    total_deduction = sum(SEVERITY_WEIGHTS.get(i["severity"], 5) for i in issues)
    quality_score = max(0.0, min(100.0, 100.0 - total_deduction))

    return issues, quality_score


def validate_and_save_issues(product: Product, db: Session) -> float:
    """
    Validate a product, clear old issues, save new ones, update quality score.
    Returns the computed quality score.
    """
    # Clear existing issues for this product
    db.query(ProductIssue).filter(ProductIssue.product_id == product.id).delete()

    issues, quality_score = validate_product(product, db)

    for issue_data in issues:
        issue = ProductIssue(
            product_id=product.id,
            issue_type=issue_data["issue_type"],
            severity=issue_data["severity"],
            message=issue_data["message"],
            suggested_fix=issue_data.get("suggested_fix"),
        )
        db.add(issue)

    product.quality_score = quality_score
    db.commit()

    return quality_score

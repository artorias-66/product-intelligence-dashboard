"""Title enhancement service — Groq → Gemini → rule-based fallback."""

import json
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Product, EnhancedTitle


def _build_prompt(product: Product, category: Optional[str] = None, brand: Optional[str] = None) -> str:
    cat = category or product.category or "General"
    br = brand or product.brand or "Unknown"
    return f"""You are an e-commerce SEO expert for Indian marketplaces like Flipkart and Amazon India.

Analyze the following product and generate an enhanced title.

Current Title: {product.product_title or 'N/A'}
Brand: {br}
Category: {cat}
Description: {product.description or 'N/A'}
Color: {product.color or 'N/A'}
Size: {product.size or 'N/A'}
Material: {product.material or 'N/A'}
Price: ₹{product.price or 'N/A'}

Please respond ONLY with a valid JSON object (no markdown, no code fences) with these keys:
- "enhanced_title": A concise, SEO-optimized title (max 200 chars) including brand, product type, key features, color, and material where relevant.
- "extracted_attributes": An object with keys like "brand", "type", "color", "material", "size", "gender", "pattern", "occasion" extracted from the current title and description.
- "suggested_keywords": A list of 5-8 relevant search keywords for this product. Format each keyword as an object: {{"keyword": "the keyword", "trend_score": 85}}. The trend_score should be a realistic estimation from 1-100 of the search volume/popularity for this keyword in India.
- "reason": A brief explanation of why this title is better.

Respond with pure JSON only."""



def _enhance_with_groq(product: Product, category: Optional[str] = None, brand: Optional[str] = None) -> Optional[dict]:
    """Use Groq LPU to generate an enhanced title. Free tier: 30 RPM, 14400 RPD."""
    if not settings.GROQ_API_KEY:
        return None
    try:
        import time
        from groq import Groq
        client = Groq(api_key=settings.GROQ_API_KEY)
        prompt = _build_prompt(product, category, brand)

        for attempt in range(3):
            try:
                completion = client.chat.completions.create(
                    model=settings.GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a JSON-only API. Only output valid JSON without markdown formatting."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    response_format={"type": "json_object"}
                )
                text = completion.choices[0].message.content.strip()
                result = json.loads(text)
                return {
                    "enhanced_title": result.get("enhanced_title", ""),
                    "extracted_attributes": result.get("extracted_attributes", {}),
                    "suggested_keywords": result.get("suggested_keywords", []),
                    "reason": result.get("reason", "Enhanced by Groq AI") + " [Groq LPU]",
                }
            except Exception as e:
                err_str = str(e)
                if ("429" in err_str or "rate" in err_str.lower()) and attempt < 2:
                    time.sleep(2 ** (attempt + 1))
                    continue
                raise

    except Exception as e:
        print(f"Groq title enhancement failed for SKU {product.sku_id}: {type(e).__name__}: {str(e)[:100]}")
        return None


def _enhance_with_gemini(product: Product, category: Optional[str] = None, brand: Optional[str] = None) -> Optional[dict]:
    """Use Gemini as a last-resort AI fallback, with retry logic for rate limits."""
    import time
    
    max_retries = 3
    base_delay = 5  # Start with a 5 second delay for 429s

    for attempt in range(max_retries):
        try:
            from google import genai
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            prompt = _build_prompt(product, category, brand)
            response = client.models.generate_content(model=settings.GEMINI_MODEL, contents=prompt)
            text = response.text.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                lines = [l for l in lines if not l.strip().startswith("```")]
                text = "\n".join(lines).strip()
            result = json.loads(text)
            return {
                "enhanced_title": result.get("enhanced_title", ""),
                "extracted_attributes": result.get("extracted_attributes", {}),
                "suggested_keywords": result.get("suggested_keywords", []),
                "reason": result.get("reason", "Enhanced by Gemini AI") + " [Gemini]",
            }
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
                if attempt < max_retries - 1:
                    sleep_time = base_delay * (2 ** attempt)
                    print(f"Gemini rate limit hit for SKU {product.sku_id}. Retrying in {sleep_time}s... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(sleep_time)
                    continue
                else:
                    print(f"Gemini quota exceeded for SKU {product.sku_id} after {max_retries} attempts.")
            else:
                print(f"Gemini title enhancement failed for SKU {product.sku_id}: {type(e).__name__}: {str(e)[:100]}")
            
            return None


def _rule_based_fallback(product: Product) -> dict:
    """Generate a structured title using simple rules when all AI APIs fail."""
    parts = []
    if product.brand:
        parts.append(product.brand)
    if product.product_title:
        parts.append(product.product_title)
    if product.color:
        parts.append(f"- {product.color}")
    if product.material:
        parts.append(f"- {product.material}")
    if product.size:
        parts.append(f"- Size {product.size}")
    if product.category:
        parts.append(f"for {product.category}")

    enhanced = " ".join(parts) if parts else "Product Title Needs Enhancement"
    attributes = {}
    for key, val in [("brand", product.brand), ("color", product.color), ("material", product.material), ("size", product.size), ("type", product.category)]:
        if val:
            attributes[key] = val
    keywords = [{"keyword": attr.lower(), "trend_score": 70} for attr in [product.brand, product.category, product.color, product.material] if attr]
    keywords += [{"keyword": "buy online", "trend_score": 90}, {"keyword": "best price india", "trend_score": 85}]

    return {
        "enhanced_title": enhanced[:200],
        "extracted_attributes": attributes,
        "suggested_keywords": keywords[:8],
        "reason": "Enhanced using rule-based fallback (all AI APIs unavailable). [Fallback Engine]",
    }


def enhance_product_title(
    product: Product, db: Session, category: Optional[str] = None, brand: Optional[str] = None
) -> EnhancedTitle:
    """
    Enhance a product title using:
    Groq → Gemini → Rule-based fallback
    """
    result = (
        _enhance_with_groq(product, category, brand)
        or _enhance_with_gemini(product, category, brand)
        or _rule_based_fallback(product)
    )

    db.query(EnhancedTitle).filter(EnhancedTitle.product_id == product.id).delete()

    enhanced = EnhancedTitle(
        product_id=product.id,
        original_title=product.product_title,
        extracted_attributes=result["extracted_attributes"],
        suggested_keywords=result["suggested_keywords"],
        enhanced_title=result["enhanced_title"],
        reason=result["reason"],
    )
    db.add(enhanced)
    db.commit()
    db.refresh(enhanced)
    return enhanced

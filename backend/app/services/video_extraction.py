"""
Video extraction service — Hybrid Pipeline: OpenCV (Frames) → Tesseract (OCR) → Gemini 1.5 Flash (AI)
"""

import base64
import json
import os
import tempfile
import cv2
import pytesseract
from PIL import Image
from typing import Optional

from app.config import settings
from app.schemas import VideoExtractionResult

# Use the modern 2.5-flash model as 1.5 is deprecated
GEMINI_MODEL = "gemini-2.5-flash"


# ── Shared JSON parser ────────────────────────────────────────────────────────

def _parse_products(text: str) -> list[VideoExtractionResult]:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}. Snippet: {text[:200]}")
        return []

    if isinstance(data, dict):
        data = data.get("products", data.get("items", [data]))
    if not isinstance(data, list):
        return []

    results = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            continue
        try:
            results.append(VideoExtractionResult(
                sku_id=item.get("sku_id", f"VID-P{i+1:03d}"),
                product_title=str(item.get("product_title", item.get("title", "Unknown Product")))[:200],
                description=str(item.get("description", "Product extracted from video."))[:1000],
                brand=item.get("brand") or None,
                category=item.get("category") or "General",
                price=float(item["price"]) if item.get("price") else None,
                mrp=float(item["mrp"]) if item.get("mrp") else None,
                image_url=None,
                color=item.get("color") or None,
                size=item.get("size") or None,
                material=item.get("material") or None,
            ))
        except Exception as e:
            print(f"Skipping product item {i}: {e}")
    return results


# ── Local Processing (Free) ───────────────────────────────────────────────────

def _extract_best_frame(video_bytes: bytes) -> Optional[bytes]:
    """Extract a representative frame from the video using OpenCV."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as vin:
            vin.write(video_bytes)
            vin_path = vin.name

        cap = cv2.VideoCapture(vin_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if total_frames == 0:
            return None

        # Grab a frame from the middle of the video (often the clearest)
        middle_frame = int(total_frames / 2)
        cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame)
        ret, frame = cap.read()
        cap.release()
        os.unlink(vin_path)

        if ret:
            # Encode frame to jpeg in memory
            _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            frame_bytes = buffer.tobytes()
            print(f"OpenCV extracted middle frame ({len(frame_bytes)} bytes)")
            return frame_bytes
        return None
    except Exception as e:
        print(f"OpenCV frame extraction failed: {e}")
        return None

def _run_tesseract_ocr(frame_bytes: bytes) -> Optional[str]:
    """Run Tesseract OCR locally on the extracted frame."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as img_file:
            img_file.write(frame_bytes)
            img_path = img_file.name

        text = pytesseract.image_to_string(Image.open(img_path))
        os.unlink(img_path)
        
        text = text.strip()
        if text:
            print(f"Tesseract OCR extracted {len(text)} characters: {text[:50]}...")
            return text
        return None
    except Exception as e:
        print(f"Tesseract OCR failed: {e}")
        return None


# ── Gemini API (AI Merging) ───────────────────────────────────────────────────

VISION_PROMPT = """You are a product identification expert for Indian e-commerce.

Analyze the provided product image AND the OCR text extracted from the packaging.
Merge this information to identify the exact product.

Return a JSON array with one object for the primary product:
- sku_id: "VID-P001"
- product_title: Full title with Brand + Model + Type + Key Features + Color (min 60 chars)
- description: Detailed description of what you see (min 80 chars)
- brand: The brand name
- category: Specific category
- price: Realistic INR price
- mrp: INR MRP (slightly higher)
- color: Primary color
- material: Primary material

Return ONLY a valid JSON array. No markdown."""

def _call_gemini_vision(frame_bytes: bytes, ocr_text: str, file_name: str, video_hint: str) -> Optional[list[VideoExtractionResult]]:
    """Send frame + OCR text to Gemini 1.5 Flash."""
    try:
        from google import genai
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        b64 = base64.b64encode(frame_bytes).decode("utf-8")
        
        prompt = VISION_PROMPT
        prompt += f"\n\nFilename: {file_name}"
        if ocr_text:
            prompt += f"\n\nCRITICAL - Local OCR extracted the following text from the image:\n{ocr_text}"
        if video_hint:
            prompt += f"\n\nUser described the product as: {video_hint}"

        print(f"Sending frame + OCR to {GEMINI_MODEL}...")
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                {"inline_data": {"mime_type": "image/jpeg", "data": b64}},
                prompt
            ]
        )
        
        text = response.text
        if text:
            results = _parse_products(text)
            if results:
                print(f"Gemini {GEMINI_MODEL} extracted {len(results)} product(s)")
                return results[:1]
        return None
    except Exception as e:
        print(f"Gemini Vision failed: {e}")
        return None


# ── Honest Fallback ───────────────────────────────────────────────────────────

def _honest_fallback(file_name: str) -> list[VideoExtractionResult]:
    print(f"All extraction methods failed. Returning placeholder for '{file_name}'")
    return [
        VideoExtractionResult(
            sku_id="VID-P001",
            product_title="Please Edit: Product Title Not Extracted",
            description="The AI could not analyse this video (OpenCV/OCR/API failed). Please manually edit this listing with the correct product name, brand, price, and description.",
            brand=None, category="General", price=None, mrp=None,
            image_url=None, color=None, size=None, material=None,
        )
    ]

# ── Main Entry ────────────────────────────────────────────────────────────────

def extract_products_from_video(
    file_name: str,
    video_bytes: bytes = None,
    video_hint: str = None,
) -> list[VideoExtractionResult]:
    
    # 1. OpenCV Frame Extraction
    frame_bytes = None
    if video_bytes:
        frame_bytes = _extract_best_frame(video_bytes)
        
    if frame_bytes:
        # 2. Local Tesseract OCR
        ocr_text = _run_tesseract_ocr(frame_bytes)
        
        # 3. Gemini 1.5 Flash Merge
        results = _call_gemini_vision(frame_bytes, ocr_text, file_name, video_hint)
        if results:
            return results
            
    # 4. Fallback
    return _honest_fallback(file_name)

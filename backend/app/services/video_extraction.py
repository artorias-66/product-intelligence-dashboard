"""
Video extraction service — Hybrid Pipeline: OpenCV (Frames) → Tesseract (OCR) → Groq Vision (Primary) → Gemini (Fallback)
"""

import base64
import json
import os
import tempfile
import time
import cv2
import pytesseract
from PIL import Image
from typing import Optional

from app.config import settings
from app.schemas import VideoExtractionResult

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
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if total_frames == 0:
            cap.release()
            os.unlink(vin_path)
            return None

        middle_frame = int(total_frames / 2)
        cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame)
        ret, frame = cap.read()
        cap.release()
        os.unlink(vin_path)

        if ret:
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


# ── Vision Prompt ────────────────────────────────────────────────────────────

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


def _build_vision_prompt(file_name: str, ocr_text: str, video_hint: str) -> str:
    prompt = VISION_PROMPT
    prompt += f"\n\nFilename: {file_name}"
    if ocr_text:
        prompt += f"\n\nCRITICAL - Local OCR extracted the following text from the image:\n{ocr_text}"
    if video_hint:
        prompt += f"\n\nUser described the product as: {video_hint}"
    return prompt


# ── Groq Vision (Primary — Free, generous quota) ────────────────────────────

def _call_groq_vision(frame_bytes: bytes, ocr_text: str, file_name: str, video_hint: str, max_retries: int = 2) -> Optional[list[VideoExtractionResult]]:
    """Send frame + OCR text to Groq Vision (Llama 4 Scout). Free tier: 30 RPM, 14400 RPD."""
    if not settings.GROQ_API_KEY:
        return None

    try:
        from groq import Groq
        client = Groq(api_key=settings.GROQ_API_KEY)

        b64 = base64.b64encode(frame_bytes).decode("utf-8")
        prompt = _build_vision_prompt(file_name, ocr_text, video_hint)

        for attempt in range(max_retries + 1):
            try:
                print(f"Sending frame + OCR to Groq {settings.GROQ_VISION_MODEL} (attempt {attempt + 1})...")
                response = client.chat.completions.create(
                    model=settings.GROQ_VISION_MODEL,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                            {"type": "text", "text": prompt},
                        ]
                    }],
                    temperature=0.2,
                    max_tokens=1024,
                )

                text = response.choices[0].message.content.strip()
                if text:
                    results = _parse_products(text)
                    if results:
                        print(f"Groq Vision extracted {len(results)} product(s)")
                        return results[:1]
                return None

            except Exception as e:
                err_str = str(e)
                if ("429" in err_str or "rate" in err_str.lower()) and attempt < max_retries:
                    wait = 2 ** (attempt + 1)
                    print(f"Groq rate limited, retrying in {wait}s...")
                    time.sleep(wait)
                    continue
                raise

    except Exception as e:
        print(f"Groq Vision failed: {e}")
        return None


# ── Gemini Vision (Fallback) ─────────────────────────────────────────────────

def _call_gemini_vision(frame_bytes: bytes, ocr_text: str, file_name: str, video_hint: str) -> Optional[list[VideoExtractionResult]]:
    """Send frame + OCR text to Gemini. Used as fallback when Groq is unavailable."""
    if not settings.GEMINI_API_KEY:
        return None

    try:
        from google import genai
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        b64 = base64.b64encode(frame_bytes).decode("utf-8")
        prompt = _build_vision_prompt(file_name, ocr_text, video_hint)

        print(f"Sending frame + OCR to Gemini {GEMINI_MODEL} (fallback)...")
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

        # 3. Groq Vision (primary — free, 30 RPM / 14400 RPD)
        results = _call_groq_vision(frame_bytes, ocr_text, file_name, video_hint)
        if results:
            return results

        # 4. Gemini Vision (fallback — limited free quota)
        results = _call_gemini_vision(frame_bytes, ocr_text, file_name, video_hint)
        if results:
            return results

    # 5. Honest fallback
    return _honest_fallback(file_name)

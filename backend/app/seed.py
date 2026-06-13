"""Comprehensive seed data for Product Intelligence Dashboard.

Creates 25 products (15 good, 5 medium issues, 5 critical),
competitor prices, price history, alerts, enhanced titles, and jobs.
Uses realistic Indian e-commerce data (Flipkart seller context).
"""

import uuid
import random
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session

from app.models import (
    Job,
    Product,
    ProductIssue,
    EnhancedTitle,
    CompetitorPrice,
    PriceHistory,
    Alert,
)


def utcnow():
    return datetime.now(timezone.utc)


PLATFORMS = ["Amazon India", "Flipkart", "Myntra", "Snapdeal", "Meesho"]


# ─── 15 Good Products ──────────────────────────────────────────────────────────

GOOD_PRODUCTS = [
    {
        "sku_id": "FLK-SHOE-001",
        "product_title": "Nike Air Max 270 React Men's Running Shoes - Black/White Mesh Breathable Sports Shoe",
        "description": "Nike Air Max 270 React running shoes combine lightweight comfort with bold style. Features a breathable mesh upper, responsive React foam midsole, and Max Air unit for all-day comfort. Perfect for running, gym, and casual wear.",
        "brand": "Nike",
        "category": "Footwear",
        "price": 8999.0,
        "mrp": 12999.0,
        "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&q=80",
        "product_url": "https://www.flipkart.com/nike-air-max-270/p/itm123",
        "availability": "in_stock",
        "color": "Black/White",
        "size": "UK 9",
        "material": "Mesh",
    },
    {
        "sku_id": "FLK-TSHIRT-002",
        "product_title": "U.S. Polo Assn. Men's Classic Fit Cotton Polo T-Shirt - Navy Blue Solid Collared Tee",
        "description": "Premium cotton polo t-shirt from U.S. Polo Assn. with classic fit design. Features a ribbed collar, button placket, and the iconic USPA logo. Machine washable, comfortable for office and casual outings.",
        "brand": "U.S. Polo Assn.",
        "category": "Clothing",
        "price": 999.0,
        "mrp": 1799.0,
        "image_url": "https://images.unsplash.com/photo-1586790170083-2f9ceadc732d?w=400&q=80",
        "product_url": "https://www.flipkart.com/uspa-polo/p/itm124",
        "availability": "in_stock",
        "color": "Navy Blue",
        "size": "L",
        "material": "Cotton",
    },
    {
        "sku_id": "FLK-PHONE-003",
        "product_title": "Samsung Galaxy S24 Ultra 5G (Titanium Black, 256 GB, 12 GB RAM) - AI Smartphone",
        "description": "Samsung Galaxy S24 Ultra with 200MP camera, Snapdragon 8 Gen 3 processor, 6.8-inch QHD+ Dynamic AMOLED display. Built-in S Pen, AI-powered features including Circle to Search and Live Translate. 5000mAh battery.",
        "brand": "Samsung",
        "category": "Electronics",
        "price": 129999.0,
        "mrp": 144999.0,
        "image_url": "https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=400&q=80",
        "product_url": "https://www.flipkart.com/samsung-s24-ultra/p/itm125",
        "availability": "in_stock",
        "color": "Titanium Black",
        "size": "256 GB",
        "material": "Titanium Frame",
    },
    {
        "sku_id": "FLK-WATCH-004",
        "product_title": "Fossil Gen 6 Hybrid Smartwatch for Men - Brown Leather Strap with Heart Rate Monitor",
        "description": "Fossil Gen 6 Hybrid smartwatch featuring heart rate monitoring, SpO2 tracking, and Alexa built-in. Classic analog watch design with smart notifications. Brown leather strap, 44mm case, water resistant up to 3 ATM.",
        "brand": "Fossil",
        "category": "Watches",
        "price": 14999.0,
        "mrp": 21995.0,
        "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&q=80",
        "product_url": "https://www.flipkart.com/fossil-gen6/p/itm126",
        "availability": "in_stock",
        "color": "Brown",
        "size": "44mm",
        "material": "Leather Strap, Stainless Steel Case",
    },
    {
        "sku_id": "FLK-LAPTOP-005",
        "product_title": "ASUS ROG Strix G16 2024 Gaming Laptop - Intel i9-14900HX, RTX 4060, 16GB DDR5, 1TB SSD",
        "description": "ASUS ROG Strix G16 gaming laptop with Intel Core i9-14900HX processor, NVIDIA GeForce RTX 4060 8GB graphics, 16-inch 2.5K 240Hz display. 16GB DDR5 RAM, 1TB NVMe SSD, per-key RGB keyboard.",
        "brand": "ASUS",
        "category": "Laptops",
        "price": 134999.0,
        "mrp": 169999.0,
        "image_url": "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=400&q=80",
        "product_url": "https://www.flipkart.com/asus-rog-strix/p/itm127",
        "availability": "in_stock",
        "color": "Eclipse Gray",
        "size": "16 inch",
        "material": "Aluminum Chassis",
    },
    {
        "sku_id": "FLK-HDPHN-006",
        "product_title": "Sony WH-1000XM5 Wireless Noise Cancelling Headphones - Black Over-Ear Bluetooth",
        "description": "Industry-leading noise cancellation with Auto NC Optimizer. 30-hour battery life, multipoint connection, Speak-to-Chat, and LDAC for Hi-Res Audio. Ultra-comfortable lightweight design at 250g.",
        "brand": "Sony",
        "category": "Audio",
        "price": 26999.0,
        "mrp": 34990.0,
        "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&q=80",
        "product_url": "https://www.flipkart.com/sony-wh1000xm5/p/itm128",
        "availability": "in_stock",
        "color": "Black",
        "size": "Over-Ear",
        "material": "Soft-fit Leather, Plastic",
    },
    {
        "sku_id": "FLK-KURTA-007",
        "product_title": "Manyavar Men's Silk Blend Embroidered Kurta Set - Maroon Festive Ethnic Wear with Pajama",
        "description": "Premium silk blend kurta set from Manyavar with intricate embroidery work. Includes matching pajama. Ideal for weddings, festivals, and celebrations. Dry clean recommended.",
        "brand": "Manyavar",
        "category": "Ethnic Wear",
        "price": 4999.0,
        "mrp": 7999.0,
        "image_url": "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=400&q=80",
        "product_url": "https://www.flipkart.com/manyavar-kurta/p/itm129",
        "availability": "in_stock",
        "color": "Maroon",
        "size": "40",
        "material": "Silk Blend",
    },
    {
        "sku_id": "FLK-BACKPK-008",
        "product_title": "American Tourister Casual Backpack 32L - Blue Polyester Laptop Bag with Rain Cover",
        "description": "American Tourister 32-litre casual backpack with dedicated 15.6-inch laptop compartment. Includes rain cover, padded shoulder straps, and multiple organizer pockets. Water-resistant polyester material.",
        "brand": "American Tourister",
        "category": "Bags",
        "price": 1499.0,
        "mrp": 2800.0,
        "image_url": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&q=80",
        "product_url": "https://www.flipkart.com/at-backpack/p/itm130",
        "availability": "in_stock",
        "color": "Blue",
        "size": "32L",
        "material": "Polyester",
    },
    {
        "sku_id": "FLK-MIXER-009",
        "product_title": "Bajaj Rex 500W Mixer Grinder - 3 Jars Stainless Steel Multi-Purpose Kitchen Appliance",
        "description": "Bajaj Rex 500 watt mixer grinder with 3 stainless steel jars for dry grinding, wet grinding, and chutney making. Motor overload protection, anti-skid feet, and 2-year warranty.",
        "brand": "Bajaj",
        "category": "Kitchen Appliances",
        "price": 2199.0,
        "mrp": 3195.0,
        "image_url": "https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=400&q=80",
        "product_url": "https://www.flipkart.com/bajaj-rex-mixer/p/itm131",
        "availability": "in_stock",
        "color": "White",
        "size": "500W",
        "material": "Stainless Steel Jars, ABS Body",
    },
    {
        "sku_id": "FLK-SAREE-010",
        "product_title": "Mimosa Women's Kanjivaram Art Silk Saree - Red with Golden Zari Border Traditional Wear",
        "description": "Exquisite Kanjivaram art silk saree with rich golden zari border and pallu. Comes with matching blouse piece. Perfect for weddings, pujas, and festive occasions. Saree length: 5.5m + blouse: 0.8m.",
        "brand": "Mimosa",
        "category": "Sarees",
        "price": 1299.0,
        "mrp": 4999.0,
        "image_url": "https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=400&q=80",
        "product_url": "https://www.flipkart.com/mimosa-saree/p/itm132",
        "availability": "in_stock",
        "color": "Red",
        "size": "Free Size",
        "material": "Art Silk",
    },
    {
        "sku_id": "FLK-FRIDGE-011",
        "product_title": "LG 260L 3-Star Frost Free Double Door Refrigerator - Shiny Steel Smart Inverter Compressor",
        "description": "LG 260 litre frost free double door refrigerator with Smart Inverter Compressor for energy efficiency. Features Smart Diagnosis, Multi Air Flow cooling, and moist balance crisper. BEE 3-star rated.",
        "brand": "LG",
        "category": "Home Appliances",
        "price": 27999.0,
        "mrp": 33990.0,
        "image_url": "https://images.unsplash.com/photo-1571175443880-49e1d25b2bc5?w=400&q=80",
        "product_url": "https://www.flipkart.com/lg-fridge-260/p/itm133",
        "availability": "in_stock",
        "color": "Shiny Steel",
        "size": "260L",
        "material": "Steel",
    },
    {
        "sku_id": "FLK-PERFM-012",
        "product_title": "Denver Hamilton Eau de Parfum for Men - 100ml Long Lasting Premium Fragrance",
        "description": "Denver Hamilton eau de parfum with long-lasting woody and aromatic fragrance. Top notes of bergamot and cardamom, heart of lavender, base of sandalwood and musk. Ideal for office and evening wear.",
        "brand": "Denver",
        "category": "Fragrances",
        "price": 499.0,
        "mrp": 799.0,
        "image_url": "https://images.unsplash.com/photo-1541643600914-78b084683702?w=400&q=80",
        "product_url": "https://www.flipkart.com/denver-hamilton/p/itm134",
        "availability": "in_stock",
        "color": "N/A",
        "size": "100ml",
        "material": "Glass Bottle",
    },
    {
        "sku_id": "FLK-JEANS-013",
        "product_title": "Levi's 511 Slim Fit Men's Stretch Denim Jeans - Dark Indigo Wash Casual Wear",
        "description": "Levi's 511 slim fit jeans in dark indigo wash. Made with stretch denim for comfortable movement. Classic 5-pocket styling, zip fly with button closure. Sits below waist, slim through thigh.",
        "brand": "Levi's",
        "category": "Clothing",
        "price": 2499.0,
        "mrp": 4299.0,
        "image_url": "https://images.unsplash.com/photo-1542272604-787c3835535d?w=400&q=80",
        "product_url": "https://www.flipkart.com/levis-511/p/itm135",
        "availability": "in_stock",
        "color": "Dark Indigo",
        "size": "32",
        "material": "Stretch Denim",
    },
    {
        "sku_id": "FLK-TABLET-014",
        "product_title": "Apple iPad Air M2 11-inch 2024 (Wi-Fi, 128GB) - Starlight Tablet with Liquid Retina Display",
        "description": "Apple iPad Air with M2 chip for next-level performance. 11-inch Liquid Retina display with True Tone. 12MP wide camera, landscape front camera, Touch ID, USB-C. Supports Apple Pencil Pro and Magic Keyboard.",
        "brand": "Apple",
        "category": "Tablets",
        "price": 59999.0,
        "mrp": 69900.0,
        "image_url": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=400&q=80",
        "product_url": "https://www.flipkart.com/ipad-air-m2/p/itm136",
        "availability": "in_stock",
        "color": "Starlight",
        "size": "11 inch",
        "material": "Aluminum",
    },
    {
        "sku_id": "FLK-BEDSH-015",
        "product_title": "Bombay Dyeing Cotton King Size Bedsheet Set - Floral Print with 2 Pillow Covers 280 TC",
        "description": "Bombay Dyeing 280 TC cotton bedsheet in king size (274x274 cm) with 2 matching pillow covers (46x69 cm each). Vibrant floral print, colorfast, machine washable. 100% cotton for a comfortable sleep experience.",
        "brand": "Bombay Dyeing",
        "category": "Home Furnishing",
        "price": 899.0,
        "mrp": 1999.0,
        "image_url": "https://images.unsplash.com/photo-1631016800696-5ea8801b3c2a?w=400&q=80",
        "product_url": "https://www.flipkart.com/bd-bedsheet/p/itm137",
        "availability": "in_stock",
        "color": "Multicolor Floral",
        "size": "King (274x274 cm)",
        "material": "Cotton 280 TC",
    },
]

# ─── 5 Medium Issue Products ──────────────────────────────────────────────────

MEDIUM_PRODUCTS = [
    {
        "sku_id": "FLK-SHOE-016",
        "product_title": "Bata Shoes",  # Short title (<20 chars)
        "description": "Comfortable formal shoes for men. Suitable for office and daily wear. Genuine leather upper with cushioned insole.",
        "brand": None,  # Missing brand
        "category": "Footwear",
        "price": 1999.0,
        "mrp": 2999.0,
        "image_url": "https://images.unsplash.com/photo-1614252235316-8c857d38b5f4?w=400&q=80",
        "product_url": "https://www.flipkart.com/bata-formal/p/itm138",
        "availability": "in_stock",
        "color": None,  # Missing attributes
        "size": None,
        "material": None,
    },
    {
        "sku_id": "FLK-CREAM-017",
        "product_title": "Pond's Face Cream",  # Short title
        "description": "Moisturizing face cream for daily use.",  # Weak description (< 50 chars)
        "brand": "Pond's",
        "category": "Beauty",
        "price": 199.0,
        "mrp": 250.0,
        "image_url": "ftp://images.flipkart.com/ponds-cream.jpg",  # Broken URL (ftp)
        "product_url": "https://www.flipkart.com/ponds-cream/p/itm139",
        "availability": "in_stock",
        "color": None,
        "size": "100g",
        "material": None,
    },
    {
        "sku_id": "FLK-CABLE-018",
        "product_title": "USB Cable Type C",  # Short title
        "description": "Fast charging USB Type-C cable, 1 meter length. Compatible with most Android smartphones.",
        "brand": None,  # Missing brand
        "category": "Accessories",
        "price": 149.0,
        "mrp": 499.0,
        "image_url": "https://images.unsplash.com/photo-1588348460-edd8c2b0cfe6?w=400&q=80",
        "product_url": "https://www.flipkart.com/usb-cable/p/itm140",
        "availability": "in_stock",
        "color": "Black",
        "size": "1m",
        "material": None,  # Partially missing attributes
    },
    {
        "sku_id": "FLK-PILLOW-019",
        "product_title": "Recron Pillow Set",  # Short title
        "description": "Soft and comfortable fiber pillow set of 2. Hypoallergenic filling, suitable for all sleeping positions.",
        "brand": "Recron",
        "category": "Home Furnishing",
        "price": 599.0,
        "mrp": 999.0,
        "image_url": "https://images.unsplash.com/photo-1584100936595-c0654b55a2e2?w=400&q=80",
        "product_url": "https://www.flipkart.com/recron-pillow/p/itm141",
        "availability": "out_of_stock",  # Out of stock
        "color": "White",
        "size": "Standard",
        "material": None,
    },
    {
        "sku_id": "FLK-BOTTLE-020",
        "product_title": "Milton Water Bottle",  # Short title
        "description": "Stainless steel insulated water bottle.",  # Weak description
        "brand": None,  # Missing brand
        "category": "Kitchen",
        "price": 599.0,
        "mrp": 899.0,
        "image_url": "https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=400&q=80",
        "product_url": "https://www.flipkart.com/milton-bottle/p/itm142",
        "availability": "in_stock",
        "color": None,
        "size": None,
        "material": None,  # All attributes missing
    },
]

# ─── 5 Critical Issue Products ─────────────────────────────────────────────────

CRITICAL_PRODUCTS = [
    {
        "sku_id": "FLK-CRIT-021",
        "product_title": None,  # Missing title
        "description": None,  # Missing description
        "brand": None,
        "category": "Unknown",
        "price": None,  # Missing price
        "mrp": None,
        "image_url": None,  # Missing image
        "product_url": None,
        "availability": "in_stock",
        "color": None,
        "size": None,
        "material": None,
    },
    {
        "sku_id": "FLK-CRIT-022",
        "product_title": "",  # Empty title
        "description": "Just a thing",  # Very weak
        "brand": None,
        "category": None,
        "price": -500.0,  # Invalid (negative) price
        "mrp": 999.0,
        "image_url": "not-a-valid-url",  # Broken image URL
        "product_url": None,
        "availability": "out_of_stock",
        "color": None,
        "size": None,
        "material": None,
    },
    {
        "sku_id": "FLK-CRIT-023",
        "product_title": "Random Product Without Details or Proper Pricing",
        "description": "Cheap product for testing purposes only, please ignore this listing.",
        "brand": None,
        "category": "Miscellaneous",
        "price": 5999.0,
        "mrp": 3999.0,  # MRP < selling price
        "image_url": None,  # Missing image
        "product_url": None,
        "availability": "in_stock",
        "color": None,
        "size": None,
        "material": None,
    },
    {
        "sku_id": "FLK-CRIT-024",
        "product_title": "Test",  # Very short title
        "description": None,
        "brand": None,
        "category": None,
        "price": 0,  # Zero price (invalid)
        "mrp": 0,
        "image_url": "file:///local/image.jpg",  # Broken URL
        "product_url": None,
        "availability": "unavailable",
        "color": None,
        "size": None,
        "material": None,
    },
    {
        "sku_id": "FLK-CRIT-021",  # Duplicate SKU (same as first critical)
        "product_title": "Duplicate Product Entry for Testing",
        "description": None,
        "brand": None,
        "category": "Unknown",
        "price": None,
        "mrp": None,
        "image_url": None,
        "product_url": None,
        "availability": "out_of_stock",
        "color": None,
        "size": None,
        "material": None,
    },
]


# ─── Enhanced Title Seeds ──────────────────────────────────────────────────────

ENHANCED_TITLES_DATA = [
    {
        "sku_id": "FLK-SHOE-001",
        "original_title": "Nike Air Max 270 React Men's Running Shoes - Black/White Mesh Breathable Sports Shoe",
        "enhanced_title": "Nike Air Max 270 React Men's Running Shoes | Black White Mesh | Breathable Lightweight Sports Shoe for Gym & Running | Size UK 9",
        "extracted_attributes": {"brand": "Nike", "type": "Running Shoes", "color": "Black/White", "material": "Mesh", "gender": "Men", "size": "UK 9"},
        "suggested_keywords": ["nike running shoes", "air max 270", "men sports shoes", "black running shoes", "breathable shoes", "gym shoes"],
        "reason": "Added size, use case, and pipe-separated attributes for better search visibility.",
    },
    {
        "sku_id": "FLK-TSHIRT-002",
        "original_title": "U.S. Polo Assn. Men's Classic Fit Cotton Polo T-Shirt - Navy Blue Solid Collared Tee",
        "enhanced_title": "U.S. Polo Assn. Men's Classic Fit Cotton Polo T-Shirt | Navy Blue Solid | Collared Half Sleeve Tee | Size L",
        "extracted_attributes": {"brand": "U.S. Polo Assn.", "type": "Polo T-Shirt", "color": "Navy Blue", "material": "Cotton", "gender": "Men", "fit": "Classic"},
        "suggested_keywords": ["uspa polo", "men polo tshirt", "cotton tshirt", "navy blue tshirt", "branded tshirt", "casual tshirt"],
        "reason": "Added sleeve type and structured format with pipes for marketplace SEO.",
    },
    {
        "sku_id": "FLK-PHONE-003",
        "original_title": "Samsung Galaxy S24 Ultra 5G (Titanium Black, 256 GB, 12 GB RAM) - AI Smartphone",
        "enhanced_title": "Samsung Galaxy S24 Ultra 5G Smartphone | Titanium Black | 256GB Storage 12GB RAM | 200MP Camera | S Pen | AI Features",
        "extracted_attributes": {"brand": "Samsung", "type": "Smartphone", "color": "Titanium Black", "storage": "256GB", "ram": "12GB", "camera": "200MP"},
        "suggested_keywords": ["samsung s24 ultra", "galaxy s24", "5g phone", "ai smartphone", "200mp camera phone", "samsung flagship"],
        "reason": "Highlighted key specs (camera, AI) and storage prominently for search relevance.",
    },
    {
        "sku_id": "FLK-WATCH-004",
        "original_title": "Fossil Gen 6 Hybrid Smartwatch for Men - Brown Leather Strap with Heart Rate Monitor",
        "enhanced_title": "Fossil Gen 6 Hybrid Smartwatch for Men | Brown Leather Strap | Heart Rate & SpO2 Monitor | Alexa Built-in | 44mm",
        "extracted_attributes": {"brand": "Fossil", "type": "Hybrid Smartwatch", "color": "Brown", "material": "Leather", "gender": "Men", "size": "44mm"},
        "suggested_keywords": ["fossil smartwatch", "hybrid watch men", "leather smartwatch", "heart rate watch", "alexa watch", "fossil gen 6"],
        "reason": "Added SpO2 and Alexa features which are key selling points for smartwatch searches.",
    },
    {
        "sku_id": "FLK-KURTA-007",
        "original_title": "Manyavar Men's Silk Blend Embroidered Kurta Set - Maroon Festive Ethnic Wear with Pajama",
        "enhanced_title": "Manyavar Men's Silk Blend Embroidered Kurta Pajama Set | Maroon | Wedding & Festive Ethnic Wear | Size 40",
        "extracted_attributes": {"brand": "Manyavar", "type": "Kurta Set", "color": "Maroon", "material": "Silk Blend", "occasion": "Wedding, Festive", "gender": "Men"},
        "suggested_keywords": ["manyavar kurta", "silk kurta set", "men ethnic wear", "wedding kurta", "maroon kurta", "festive wear men"],
        "reason": "Added wedding context and size for better targeted search results.",
    },
    {
        "sku_id": "FLK-SAREE-010",
        "original_title": "Mimosa Women's Kanjivaram Art Silk Saree - Red with Golden Zari Border Traditional Wear",
        "enhanced_title": "Mimosa Kanjivaram Art Silk Saree for Women | Red with Golden Zari Border | Traditional Wedding Saree | Free Size with Blouse Piece",
        "extracted_attributes": {"brand": "Mimosa", "type": "Kanjivaram Saree", "color": "Red", "material": "Art Silk", "occasion": "Wedding, Traditional", "gender": "Women"},
        "suggested_keywords": ["kanjivaram saree", "silk saree", "red saree", "wedding saree", "zari border saree", "south indian saree"],
        "reason": "Added blouse piece inclusion and wedding context which are top search filters.",
    },
    {
        "sku_id": "FLK-HDPHN-006",
        "original_title": "Sony WH-1000XM5 Wireless Noise Cancelling Headphones - Black Over-Ear Bluetooth",
        "enhanced_title": "Sony WH-1000XM5 Wireless Active Noise Cancelling Headphones | Black | Over-Ear Bluetooth | 30Hr Battery | Hi-Res Audio",
        "extracted_attributes": {"brand": "Sony", "type": "Wireless Headphones", "color": "Black", "feature": "Active Noise Cancelling", "battery": "30 hours"},
        "suggested_keywords": ["sony headphones", "noise cancelling headphones", "wireless headphones", "wh1000xm5", "bluetooth headphones", "over ear headphones"],
        "reason": "Added battery life and Hi-Res Audio specs which are key differentiators.",
    },
    {
        "sku_id": "FLK-JEANS-013",
        "original_title": "Levi's 511 Slim Fit Men's Stretch Denim Jeans - Dark Indigo Wash Casual Wear",
        "enhanced_title": "Levi's 511 Slim Fit Men's Jeans | Dark Indigo Wash | Stretch Denim | Casual & Office Wear | Size 32",
        "extracted_attributes": {"brand": "Levi's", "type": "Slim Fit Jeans", "color": "Dark Indigo", "material": "Stretch Denim", "gender": "Men", "fit": "511 Slim"},
        "suggested_keywords": ["levis jeans", "511 slim fit", "men denim jeans", "dark indigo jeans", "stretch jeans", "branded jeans"],
        "reason": "Added size and dual-use context (casual & office) for broader search appeal.",
    },
]


def run_seed(db: Session, user_id: str) -> str:
    """Run the complete seed process. Returns a status message."""

    # Check if data already exists
    existing = db.query(Product).filter(Product.user_id == user_id).count()
    if existing > 0:
        return f"Database already has {existing} products for this user. Clear data if you want a fresh seed."

    # ─── Create Jobs ────────────────────────────────────────────
    job1 = Job(
        user_id=user_id,
        type="csv_upload",
        status="COMPLETED",
        progress=100,
        file_name="flipkart_products_batch1.csv",
        enhance_titles=True,
        total_products=15,
        processed_products=15,
        started_at=utcnow() - timedelta(days=7),
        completed_at=utcnow() - timedelta(days=7) + timedelta(minutes=2),
        created_at=utcnow() - timedelta(days=7),
    )

    job2 = Job(
        user_id=user_id,
        type="csv_upload",
        status="COMPLETED",
        progress=100,
        file_name="flipkart_products_batch2.csv",
        enhance_titles=False,
        total_products=5,
        processed_products=5,
        started_at=utcnow() - timedelta(days=3),
        completed_at=utcnow() - timedelta(days=3) + timedelta(minutes=1),
        created_at=utcnow() - timedelta(days=3),
    )

    job3 = Job(
        user_id=user_id,
        type="csv_upload",
        status="PARTIALLY_COMPLETED",
        progress=100,
        file_name="flipkart_products_problematic.csv",
        enhance_titles=False,
        total_products=5,
        processed_products=5,
        error_message="2 products had critical data issues: missing title, invalid price. Processed with warnings.",
        started_at=utcnow() - timedelta(days=1),
        completed_at=utcnow() - timedelta(days=1) + timedelta(minutes=1),
        created_at=utcnow() - timedelta(days=1),
    )

    db.add_all([job1, job2, job3])
    db.flush()

    # ─── Create Products ────────────────────────────────────────
    all_products = []

    for product_data in GOOD_PRODUCTS:
        p = Product(user_id=user_id, job_id=job1.id, **product_data)
        db.add(p)
        db.flush()
        all_products.append(p)

    for product_data in MEDIUM_PRODUCTS:
        p = Product(user_id=user_id, job_id=job2.id, **product_data)
        db.add(p)
        db.flush()
        all_products.append(p)

    for product_data in CRITICAL_PRODUCTS:
        p = Product(user_id=user_id, job_id=job3.id, **product_data)
        db.add(p)
        db.flush()
        all_products.append(p)

    # ─── Run Validation on All Products ─────────────────────────
    from app.services.validation import validate_product

    for p in all_products:
        issues, quality_score = validate_product(p, db)
        p.quality_score = quality_score
        for issue_data in issues:
            issue = ProductIssue(
                product_id=p.id,
                issue_type=issue_data["issue_type"],
                severity=issue_data["severity"],
                message=issue_data["message"],
                suggested_fix=issue_data.get("suggested_fix"),
            )
            db.add(issue)

    db.flush()

    # ─── Create Enhanced Titles ─────────────────────────────────
    sku_to_product = {p.sku_id: p for p in all_products}

    for et_data in ENHANCED_TITLES_DATA:
        product = sku_to_product.get(et_data["sku_id"])
        if product:
            et = EnhancedTitle(
                product_id=product.id,
                original_title=et_data["original_title"],
                enhanced_title=et_data["enhanced_title"],
                extracted_attributes=et_data["extracted_attributes"],
                suggested_keywords=et_data["suggested_keywords"],
                reason=et_data["reason"],
            )
            db.add(et)

    db.flush()

    # ─── Create Competitor Prices ───────────────────────────────
    for p in all_products:
        if p.price and p.price > 0:
            for platform in PLATFORMS:
                variation = random.uniform(-0.15, 0.20)
                comp_price = round(p.price * (1 + variation), 2)

                cp = CompetitorPrice(
                    product_id=p.id,
                    sku_id=p.sku_id,
                    platform=platform,
                    product_name=p.product_title or f"{p.sku_id} on {platform}",
                    competitor_url=f"https://www.{platform.lower().replace(' ', '')}.com/dp/{p.sku_id}",
                    competitor_price=comp_price,
                    currency="INR",
                    last_checked_at=utcnow() - timedelta(hours=random.randint(1, 48)),
                )
                db.add(cp)

    db.flush()

    # ─── Create Price History ───────────────────────────────────
    for p in all_products:
        base = p.price or random.uniform(500, 5000)
        for platform in PLATFORMS:
            platform_var = random.uniform(-0.10, 0.15)
            platform_base = base * (1 + platform_var)

            num_points = random.randint(4, 6)
            for _ in range(num_points):
                days_ago = random.randint(1, 30)
                drift = random.uniform(-0.08, 0.08)
                price = round(platform_base * (1 + drift), 2)

                ph = PriceHistory(
                    product_id=p.id,
                    platform=platform,
                    price=price,
                    checked_at=utcnow() - timedelta(days=days_ago, hours=random.randint(0, 23)),
                )
                db.add(ph)

    db.flush()

    # ─── Create Alerts ──────────────────────────────────────────
    alert_count = 0

    for p in all_products:
        issues = db.query(ProductIssue).filter(ProductIssue.product_id == p.id).all()

        high_issues = [i for i in issues if i.severity == "HIGH"]
        medium_issues = [i for i in issues if i.severity == "MEDIUM"]
        low_issues = [i for i in issues if i.severity == "LOW"]

        critical_types = {"missing_title", "invalid_price", "missing_image", "duplicate_sku", "mrp_less_than_price"}
        if any(i.issue_type in critical_types for i in high_issues):
            alert = Alert(
                user_id=user_id,
                product_id=p.id,
                type="listing_issue",
                severity="HIGH",
                title="Critical listing issue",
                message=f"Product '{p.sku_id}' has critical issues: {', '.join(set(i.issue_type for i in high_issues if i.issue_type in critical_types))}.",
                is_read=random.choice([True, False]),
                created_at=utcnow() - timedelta(hours=random.randint(1, 72)),
            )
            db.add(alert)
            alert_count += 1

        improvement_types = {"short_title", "missing_brand", "missing_attributes", "broken_image_url"}
        if any(i.issue_type in improvement_types for i in medium_issues):
            alert = Alert(
                user_id=user_id,
                product_id=p.id,
                type="listing_improvement",
                severity="MEDIUM",
                title="Listing improvement needed",
                message=f"Product '{p.sku_id}' needs improvements: {', '.join(set(i.issue_type for i in medium_issues if i.issue_type in improvement_types))}.",
                is_read=random.choice([True, False]),
                created_at=utcnow() - timedelta(hours=random.randint(1, 72)),
            )
            db.add(alert)
            alert_count += 1

        minor_types = {"weak_description", "out_of_stock"}
        if any(i.issue_type in minor_types for i in low_issues):
            alert = Alert(
                user_id=user_id,
                product_id=p.id,
                type="minor_issue",
                severity="LOW",
                title="Minor listing issue",
                message=f"Product '{p.sku_id}' has minor issues: {', '.join(set(i.issue_type for i in low_issues if i.issue_type in minor_types))}.",
                is_read=random.choice([True, False]),
                created_at=utcnow() - timedelta(hours=random.randint(1, 72)),
            )
            db.add(alert)
            alert_count += 1

        # Price competitiveness alerts
        if p.price and p.price > 0:
            comp_prices = db.query(CompetitorPrice).filter(CompetitorPrice.product_id == p.id).all()
            if comp_prices:
                lowest = min(cp.competitor_price for cp in comp_prices)
                lowest_platform = next(cp.platform for cp in comp_prices if cp.competitor_price == lowest)
                if p.price > lowest * 1.10:
                    pct = round(((p.price - lowest) / lowest) * 100, 1)
                    alert = Alert(
                        user_id=user_id,
                        product_id=p.id,
                        type="price_competitive",
                        severity="HIGH",
                        title="Price not competitive",
                        message=f"'{p.sku_id}' is ₹{p.price}, {pct}% above ₹{lowest} on {lowest_platform}.",
                        is_read=False,
                        created_at=utcnow() - timedelta(hours=random.randint(1, 48)),
                    )
                    db.add(alert)
                    alert_count += 1

    db.commit()

    product_count = db.query(Product).count()
    issue_count = db.query(ProductIssue).count()
    cp_count = db.query(CompetitorPrice).count()
    ph_count = db.query(PriceHistory).count()
    et_count = db.query(EnhancedTitle).count()
    final_alert_count = db.query(Alert).count()

    return (
        f"Seed complete! Created: {product_count} products, {issue_count} issues, "
        f"{cp_count} competitor prices, {ph_count} price history records, "
        f"{et_count} enhanced titles, {final_alert_count} alerts, 3 jobs."
    )

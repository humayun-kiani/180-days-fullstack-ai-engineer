# ============================================================
# src/models.py
# Document templates for the product catalog
#
# MongoDB is schema-less, but having Python templates helps
# ensure consistency and serves as documentation.
# ============================================================

from datetime import datetime
from typing import Optional


def create_product_base(
    sku: str,
    name: str,
    brand: str,
    category: str,
    price: float,
    description: str = "",
    tags: list = None,
    images: list = None
) -> dict:
    """
    Base product document structure.

    All product types share these fields.
    Category-specific fields are added separately.
    """
    return {
        "sku": sku,
        "name": name,
        "brand": brand,
        "category": category,
        "price": float(price),
        "description": description,
        "tags": tags or [],
        "images": images or [],
        "is_active": True,
        "is_featured": False,
        "rating": {
            "average": 0.0,
            "count": 0,
            "distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        },
        "inventory": {
            "total_stock": 0,
            "reserved": 0,
            "available": 0
        },
        "pricing": {
            "original_price": float(price),
            "current_price": float(price),
            "discount_pct": 0,
            "currency": "PKR"
        },
        "seo": {
            "slug": name.lower().replace(" ", "-"),
            "meta_title": name,
            "meta_description": description[:160]
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "views": 0,
        "purchases": 0
    }


def create_laptop_product(
    sku: str, name: str, brand: str, price: float,
    ram: int, storage: int, processor: str,
    screen_size: float, gpu: str = None,
    battery_hours: int = None, weight_kg: float = None,
    os: str = "Windows 11"
) -> dict:
    """Laptop-specific product document."""
    product = create_product_base(
        sku=sku, name=name, brand=brand,
        category="Laptops", price=price,
        tags=["laptop", brand.lower(), "computer"]
    )
    product["specs"] = {
        "ram_gb": ram,
        "storage_gb": storage,
        "processor": processor,
        "screen_size_inches": screen_size,
        "operating_system": os,
        "gpu": gpu,
        "battery_hours": battery_hours,
        "weight_kg": weight_kg
    }
    product["connectivity"] = {
        "wifi": "WiFi 6",
        "bluetooth": "5.0",
        "usb_ports": 3,
        "hdmi": True
    }
    return product


def create_phone_product(
    sku: str, name: str, brand: str, price: float,
    ram: int, storage: int, battery_mah: int,
    screen_size: float, camera_mp: int,
    has_5g: bool = True, os: str = "Android"
) -> dict:
    """Smartphone-specific product document."""
    product = create_product_base(
        sku=sku, name=name, brand=brand,
        category="Smartphones", price=price,
        tags=["smartphone", "mobile", brand.lower()]
    )
    product["specs"] = {
        "ram_gb": ram,
        "storage_gb": storage,
        "battery_mah": battery_mah,
        "screen_size_inches": screen_size,
        "main_camera_mp": camera_mp,
        "operating_system": os,
        "has_5g": has_5g,
        "charging_watts": 65
    }
    # Phones have color/storage variants
    product["variants"] = []
    return product


def create_clothing_product(
    sku: str, name: str, brand: str, price: float,
    gender: str, material: str, clothing_type: str,
    sizes: list, colors: list
) -> dict:
    """Clothing-specific product document."""
    product = create_product_base(
        sku=sku, name=name, brand=brand,
        category="Clothing", price=price,
        tags=["clothing", gender.lower(), clothing_type.lower(), brand.lower()]
    )
    product["attributes"] = {
        "gender": gender,
        "material": material,
        "type": clothing_type,
        "care_instructions": ["Machine washable", "Do not bleach"]
    }
    # Clothing has size/color variants with individual stock
    product["variants"] = [
        {
            "size": size,
            "color": color,
            "sku_variant": f"{sku}-{size}-{color[:3].upper()}",
            "price_adjustment": 0,
            "stock": 0
        }
        for size in sizes
        for color in colors
    ]
    return product


def create_book_product(
    sku: str, name: str, author: str, publisher: str,
    price: float, isbn: str, pages: int, genre: str,
    language: str = "English", edition: int = 1
) -> dict:
    """Book-specific product document."""
    product = create_product_base(
        sku=sku, name=name, brand=publisher,
        category="Books", price=price,
        tags=["book", genre.lower(), author.split()[-1].lower()]
    )
    product["publication_details"] = {
        "author": author,
        "publisher": publisher,
        "isbn": isbn,
        "pages": pages,
        "genre": genre,
        "language": language,
        "edition": edition,
        "format": "Paperback"
    }
    return product


def create_review(
    product_id,
    user_id: str,
    username: str,
    rating: int,
    title: str,
    comment: str,
    verified_purchase: bool = True
) -> dict:
    """Review document structure."""
    return {
        "product_id": product_id,
        "user_id": user_id,
        "username": username,
        "rating": rating,
        "title": title,
        "comment": comment,
        "verified_purchase": verified_purchase,
        "helpful_votes": 0,
        "created_at": datetime.utcnow(),
        "is_approved": True
    }
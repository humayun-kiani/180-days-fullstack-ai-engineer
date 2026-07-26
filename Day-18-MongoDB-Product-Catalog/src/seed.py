# ============================================================
# src/seed.py
# Seed the product catalog with diverse realistic data
# ============================================================

import random
from datetime import datetime, timedelta
from faker import Faker

from src.models import (
    create_laptop_product, create_phone_product,
    create_clothing_product, create_book_product,
    create_review
)

fake = Faker()
random.seed(42)

# Product data
LAPTOP_DATA = [
    ("LAP-001", "Dell XPS 15", "Dell", 185000, 16, 512, "Intel i7-13th Gen", 15.6, "NVIDIA RTX 4060", 8, 1.8),
    ("LAP-002", "MacBook Pro 14", "Apple", 350000, 16, 512, "Apple M3 Pro", 14.2, None, 18, 1.6),
    ("LAP-003", "ASUS ROG Strix", "ASUS", 220000, 32, 1000, "Intel i9-13th Gen", 15.6, "NVIDIA RTX 4070", 6, 2.3),
    ("LAP-004", "Lenovo ThinkPad X1", "Lenovo", 175000, 16, 512, "Intel i7-12th Gen", 14.0, None, 12, 1.1),
    ("LAP-005", "HP Spectre x360", "HP", 155000, 16, 512, "Intel i7-13th Gen", 13.5, None, 10, 1.3),
    ("LAP-006", "Acer Predator Helios", "Acer", 195000, 32, 1000, "Intel i9-13th Gen", 16.0, "NVIDIA RTX 4080", 5, 2.6),
]

PHONE_DATA = [
    ("PHN-001", "Samsung Galaxy S24 Ultra", "Samsung", 245000, 12, 512, 5000, 6.8, 200, True, "Android"),
    ("PHN-002", "iPhone 15 Pro Max", "Apple", 285000, 8, 256, 4422, 6.7, 48, True, "iOS"),
    ("PHN-003", "OnePlus 12", "OnePlus", 135000, 12, 256, 5400, 6.82, 50, True, "Android"),
    ("PHN-004", "Google Pixel 8 Pro", "Google", 175000, 12, 128, 5050, 6.7, 50, True, "Android"),
    ("PHN-005", "Xiaomi 14 Pro", "Xiaomi", 125000, 12, 512, 4880, 6.73, 50, True, "Android"),
    ("PHN-006", "Vivo X100 Pro", "Vivo", 115000, 16, 512, 5400, 6.78, 50, True, "Android"),
]

BOOK_DATA = [
    ("BOK-001", "Clean Code", "Robert C. Martin", "Prentice Hall", 2800, "978-0132350884", 464, "Programming", "English", 1),
    ("BOK-002", "Designing Data-Intensive Applications", "Martin Kleppmann", "O'Reilly", 4200, "978-1449373320", 616, "Technology", "English", 1),
    ("BOK-003", "The Pragmatic Programmer", "Andrew Hunt", "Addison-Wesley", 3500, "978-0201616224", 352, "Programming", "English", 20),
    ("BOK-004", "Python Crash Course", "Eric Matthes", "No Starch Press", 2200, "978-1593279288", 544, "Programming", "English", 3),
    ("BOK-005", "Atomic Habits", "James Clear", "Avery Publishing", 1800, "978-0735211292", 320, "Self-Help", "English", 1),
    ("BOK-006", "Deep Learning", "Ian Goodfellow", "MIT Press", 5500, "978-0262035613", 800, "AI/ML", "English", 1),
]

CLOTHING_DATA = [
    ("CLO-001", "Kurta Shalwar", "Gul Ahmed", 3500, "Male", "Cotton", "Kurta", ["S", "M", "L", "XL", "XXL"], ["White", "Blue", "Green"]),
    ("CLO-002", "Women's Formal Shirt", "Khaadi", 2800, "Female", "Lawn", "Shirt", ["XS", "S", "M", "L", "XL"], ["Pink", "White", "Yellow"]),
    ("CLO-003", "Jeans", "Levis", 4500, "Male", "Denim", "Jeans", ["30", "32", "34", "36"], ["Blue", "Black"]),
    ("CLO-004", "Casual T-Shirt", "Bonanza", 1200, "Male", "Cotton", "T-Shirt", ["S", "M", "L", "XL"], ["White", "Black", "Red", "Navy"]),
    ("CLO-005", "Abaya", "Junaid Jamshed", 6500, "Female", "Chiffon", "Abaya", ["S", "M", "L", "XL"], ["Black", "Navy", "Brown"]),
]

REVIEW_TEXTS = {
    5: [
        "Absolutely amazing product! Exceeded all my expectations.",
        "Best purchase I've made this year. Highly recommended!",
        "Perfect quality and fast delivery. Will buy again.",
        "Outstanding performance and value for money.",
    ],
    4: [
        "Very good product. Minor issues but overall satisfied.",
        "Great quality for the price. Would recommend.",
        "Good product, delivery was fast. Happy with purchase.",
        "Works as advertised. One small complaint but overall good.",
    ],
    3: [
        "Average product. Does the job but nothing special.",
        "Decent quality for the price. Some improvements needed.",
        "OK product. Expected better based on description.",
    ],
    2: [
        "Below expectations. Quality could be better.",
        "Not worth the price. Has some issues.",
    ],
    1: [
        "Disappointing product. Does not match description.",
        "Poor quality. Would not buy again.",
    ]
}

USERNAMES = ["humayun_k", "ali_hassan", "sara_ahmed", "omar_f",
             "fatima_m", "bilal_q", "zara_s", "ahmed_r",
             "nadia_b", "imran_ch", "ayesha_n", "hassan_r"]


def generate_reviews(product_id, num_reviews: int) -> list:
    """Generate realistic reviews for a product."""
    reviews = []
    # Weight toward higher ratings
    rating_weights = [1, 2, 3, 5, 8]  # 1→2→3→4→5 star weights
    ratings = random.choices([1, 2, 3, 4, 5], weights=rating_weights, k=num_reviews)

    for rating in ratings:
        username = random.choice(USERNAMES)
        text = random.choice(REVIEW_TEXTS[rating])
        reviews.append(create_review(
            product_id=product_id,
            user_id=f"user_{username}",
            username=username,
            rating=rating,
            title=text[:30] + "...",
            comment=text,
            verified_purchase=random.random() > 0.2
        ))
    return reviews


def seed_catalog(db) -> dict:
    """Seed the entire product catalog."""
    products_col = db["products"]
    reviews_col = db["reviews"]

    print("\n  Seeding product catalog...")

    all_products = []

    # Laptops
    for data in LAPTOP_DATA:
        product = create_laptop_product(*data)
        product["inventory"] = {
            "total_stock": random.randint(5, 50),
            "reserved": random.randint(0, 5),
            "available": random.randint(3, 45)
        }
        product["views"] = random.randint(100, 5000)
        product["purchases"] = random.randint(5, 200)
        product["is_featured"] = random.random() > 0.5
        all_products.append(product)

    # Phones
    for data in PHONE_DATA:
        product = create_phone_product(*data)
        product["variants"] = [
            {"color": c, "storage": s, "stock": random.randint(0, 30)}
            for c in ["Black", "White", "Gold"]
            for s in [128, 256, 512]
        ]
        product["inventory"] = {
            "total_stock": random.randint(20, 100),
            "reserved": random.randint(0, 10),
            "available": random.randint(15, 90)
        }
        product["views"] = random.randint(500, 10000)
        product["purchases"] = random.randint(20, 500)
        product["is_featured"] = random.random() > 0.4
        all_products.append(product)

    # Books
    for data in BOOK_DATA:
        product = create_book_product(*data)
        product["inventory"] = {
            "total_stock": random.randint(10, 200),
            "reserved": 0,
            "available": random.randint(8, 200)
        }
        product["views"] = random.randint(50, 2000)
        product["purchases"] = random.randint(3, 100)
        product["is_featured"] = random.random() > 0.7
        all_products.append(product)

    # Clothing
    for data in CLOTHING_DATA:
        product = create_clothing_product(*data)
        # Set random stock for each variant
        for variant in product["variants"]:
            variant["stock"] = random.randint(0, 25)
        total_stock = sum(v["stock"] for v in product["variants"])
        product["inventory"] = {
            "total_stock": total_stock,
            "reserved": 0,
            "available": total_stock
        }
        product["views"] = random.randint(200, 8000)
        product["purchases"] = random.randint(10, 300)
        all_products.append(product)

    # Insert all products
    insert_result = products_col.insert_many(all_products)
    inserted_ids = insert_result.inserted_ids
    print(f"  ✅ Inserted {len(inserted_ids)} products.")

    # Generate and insert reviews
    all_reviews = []
    for i, product_id in enumerate(inserted_ids):
        num_reviews = random.randint(2, 12)
        reviews = generate_reviews(product_id, num_reviews)
        all_reviews.extend(reviews)

    if all_reviews:
        reviews_col.insert_many(all_reviews)
        print(f"  ✅ Inserted {len(all_reviews)} reviews.")

    # Update product ratings from reviews
    print("  Calculating product ratings...")
    for product_id in inserted_ids:
        pipeline = [
            {"$match": {"product_id": product_id, "is_approved": True}},
            {"$group": {
                "_id": None,
                "avg": {"$avg": "$rating"},
                "count": {"$sum": 1},
                "d1": {"$sum": {"$cond": [{"$eq": ["$rating", 1]}, 1, 0]}},
                "d2": {"$sum": {"$cond": [{"$eq": ["$rating", 2]}, 1, 0]}},
                "d3": {"$sum": {"$cond": [{"$eq": ["$rating", 3]}, 1, 0]}},
                "d4": {"$sum": {"$cond": [{"$eq": ["$rating", 4]}, 1, 0]}},
                "d5": {"$sum": {"$cond": [{"$eq": ["$rating", 5]}, 1, 0]}}
            }}
        ]
        result = list(reviews_col.aggregate(pipeline))
        if result:
            s = result[0]
            products_col.update_one(
                {"_id": product_id},
                {"$set": {
                    "rating.average": round(s["avg"], 2),
                    "rating.count": s["count"],
                    "rating.distribution": {
                        "1": s["d1"], "2": s["d2"], "3": s["d3"],
                        "4": s["d4"], "5": s["d5"]
                    }
                }}
            )

    print("  ✅ Product ratings updated.")
    print(f"\n  🎉 Catalog seeded!")

    return {
        "products": len(inserted_ids),
        "reviews": len(all_reviews),
        "categories": len(set(p["category"] for p in all_products))
    }
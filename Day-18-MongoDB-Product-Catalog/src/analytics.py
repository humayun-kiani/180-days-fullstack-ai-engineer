# ============================================================
# src/analytics.py
# Aggregation pipeline analytics for the product catalog
# ============================================================

from pymongo import DESCENDING
from pymongo.database import Database


class CatalogAnalytics:
    """
    Advanced analytics using MongoDB aggregation pipelines.

    Demonstrates the power of MongoDB's aggregation framework
    for real e-commerce analytics.
    """

    def __init__(self, db: Database):
        self.db = db
        self.products = db["products"]
        self.reviews = db["reviews"]

    def category_performance(self) -> list:
        """
        Category-wise performance analysis.

        Shows: product count, price range, avg rating,
        total inventory, brand diversity.
        """
        pipeline = [
            {"$match": {"is_active": True}},
            {"$group": {
                "_id": "$category",
                "product_count": {"$sum": 1},
                "avg_price": {"$avg": "$price"},
                "min_price": {"$min": "$price"},
                "max_price": {"$max": "$price"},
                "total_stock": {"$sum": "$inventory.total_stock"},
                "avg_rating": {"$avg": "$rating.average"},
                "total_reviews": {"$sum": "$rating.count"},
                "brands": {"$addToSet": "$brand"},
                "featured_count": {
                    "$sum": {"$cond": ["$is_featured", 1, 0]}
                }
            }},
            {"$project": {
                "category": "$_id",
                "product_count": 1,
                "avg_price": {"$round": ["$avg_price", 0]},
                "price_range": {
                    "$concat": [
                        "Rs.",
                        {"$toString": {"$round": ["$min_price", 0]}},
                        " - Rs.",
                        {"$toString": {"$round": ["$max_price", 0]}}
                    ]
                },
                "total_stock": 1,
                "avg_rating": {"$round": ["$avg_rating", 2]},
                "total_reviews": 1,
                "brand_count": {"$size": "$brands"},
                "featured_count": 1,
                "_id": 0
            }},
            {"$sort": {"product_count": DESCENDING}}
        ]
        return list(self.products.aggregate(pipeline))

    def brand_analysis(self, category: str = None) -> list:
        """
        Brand market share analysis within a category or all categories.

        Uses $bucket to create price tiers per brand.
        """
        match_stage = {"$match": {"is_active": True}}
        if category:
            match_stage["$match"]["category"] = category

        pipeline = [
            match_stage,
            {"$group": {
                "_id": "$brand",
                "product_count": {"$sum": 1},
                "avg_price": {"$avg": "$price"},
                "avg_rating": {"$avg": "$rating.average"},
                "categories": {"$addToSet": "$category"},
                "total_views": {"$sum": "$views"},
                "total_purchases": {"$sum": "$purchases"}
            }},
            {"$project": {
                "brand": "$_id",
                "product_count": 1,
                "avg_price": {"$round": ["$avg_price", 0]},
                "avg_rating": {"$round": ["$avg_rating", 2]},
                "category_count": {"$size": "$categories"},
                "total_views": 1,
                "total_purchases": 1,
                "conversion_rate": {
                    "$cond": [
                        {"$gt": ["$total_views", 0]},
                        {"$round": [
                            {"$multiply": [
                                {"$divide": ["$total_purchases", "$total_views"]},
                                100
                            ]},
                            2
                        ]},
                        0
                    ]
                },
                "_id": 0
            }},
            {"$sort": {"product_count": DESCENDING}}
        ]
        return list(self.products.aggregate(pipeline))

    def price_distribution(self) -> list:
        """
        Product count in different price buckets.

        Uses $bucket for price range analysis.
        """
        pipeline = [
            {"$match": {"is_active": True}},
            {"$bucket": {
                "groupBy": "$price",
                "boundaries": [0, 1000, 5000, 15000, 50000, 100000, 300000],
                "default": "300000+",
                "output": {
                    "count": {"$sum": 1},
                    "avg_price": {"$avg": "$price"},
                    "avg_rating": {"$avg": "$rating.average"},
                    "products": {
                        "$push": {
                            "name": "$name",
                            "price": "$price"
                        }
                    }
                }
            }},
            {"$project": {
                "price_range": {
                    "$switch": {
                        "branches": [
                            {"case": {"$eq": ["$_id", 0]}, "then": "Under Rs.1,000"},
                            {"case": {"$eq": ["$_id", 1000]}, "then": "Rs.1,000 - 5,000"},
                            {"case": {"$eq": ["$_id", 5000]}, "then": "Rs.5,000 - 15,000"},
                            {"case": {"$eq": ["$_id", 15000]}, "then": "Rs.15,000 - 50,000"},
                            {"case": {"$eq": ["$_id", 50000]}, "then": "Rs.50,000 - 1,00,000"},
                            {"case": {"$eq": ["$_id", 100000]}, "then": "Rs.1,00,000 - 3,00,000"},
                        ],
                        "default": "Above Rs.3,00,000"
                    }
                },
                "count": 1,
                "avg_price": {"$round": ["$avg_price", 0]},
                "avg_rating": {"$round": ["$avg_rating", 2]},
                "sample_product": {"$first": "$products.name"},
                "_id": 0
            }}
        ]
        return list(self.products.aggregate(pipeline))

    def rating_analysis(self) -> dict:
        """
        Rating distribution analysis using $facet for multiple
        sub-pipelines on the same input.
        """
        pipeline = [
            {"$match": {"is_active": True, "rating.count": {"$gt": 0}}},
            {"$facet": {
                "overall_stats": [
                    {"$group": {
                        "_id": None,
                        "avg_rating": {"$avg": "$rating.average"},
                        "total_products": {"$sum": 1},
                        "total_reviews": {"$sum": "$rating.count"},
                        "five_star_products": {
                            "$sum": {"$cond": [
                                {"$gte": ["$rating.average", 4.5]}, 1, 0
                            ]}
                        }
                    }}
                ],
                "by_category": [
                    {"$group": {
                        "_id": "$category",
                        "avg_rating": {"$avg": "$rating.average"},
                        "count": {"$sum": 1}
                    }},
                    {"$project": {
                        "category": "$_id",
                        "avg_rating": {"$round": ["$avg_rating", 2]},
                        "count": 1,
                        "_id": 0
                    }},
                    {"$sort": {"avg_rating": DESCENDING}}
                ],
                "top_rated": [
                    {"$sort": {"rating.average": DESCENDING}},
                    {"$limit": 5},
                    {"$project": {
                        "name": 1,
                        "brand": 1,
                        "category": 1,
                        "rating": "$rating.average",
                        "reviews": "$rating.count",
                        "_id": 0
                    }}
                ]
            }}
        ]
        result = list(self.products.aggregate(pipeline))
        if result:
            return result[0]
        return {}

    def tag_cloud(self, top_n: int = 20) -> list:
        """
        Tag frequency analysis — what are the most common tags?

        Uses $unwind to expand tag arrays into individual documents.
        """
        pipeline = [
            {"$match": {"is_active": True}},
            {"$unwind": "$tags"},    # expand array → one doc per tag
            {"$group": {
                "_id": "$tags",
                "count": {"$sum": 1},
                "categories": {"$addToSet": "$category"},
                "avg_price": {"$avg": "$price"}
            }},
            {"$project": {
                "tag": "$_id",
                "count": 1,
                "category_count": {"$size": "$categories"},
                "avg_price": {"$round": ["$avg_price", 0]},
                "_id": 0
            }},
            {"$sort": {"count": DESCENDING}},
            {"$limit": top_n}
        ]
        return list(self.products.aggregate(pipeline))

    def inventory_health(self) -> dict:
        """
        Inventory status analysis.

        Identifies out-of-stock, low-stock, and overstocked products.
        """
        pipeline = [
            {"$match": {"is_active": True}},
            {"$facet": {
                "stock_levels": [
                    {"$group": {
                        "_id": {
                            "$switch": {
                                "branches": [
                                    {"case": {"$eq": ["$inventory.available", 0]}, "then": "Out of Stock"},
                                    {"case": {"$lte": ["$inventory.available", 5]}, "then": "Low Stock"},
                                    {"case": {"$lte": ["$inventory.available", 20]}, "then": "Medium Stock"},
                                ],
                                "default": "Well Stocked"
                            }
                        },
                        "count": {"$sum": 1},
                        "products": {"$push": "$name"}
                    }}
                ],
                "category_stock": [
                    {"$group": {
                        "_id": "$category",
                        "total_units": {"$sum": "$inventory.total_stock"},
                        "available": {"$sum": "$inventory.available"},
                        "products": {"$sum": 1}
                    }},
                    {"$project": {
                        "category": "$_id",
                        "total_units": 1,
                        "available": 1,
                        "products": 1,
                        "utilization_pct": {
                            "$cond": [
                                {"$gt": ["$total_units", 0]},
                                {"$round": [
                                    {"$multiply": [
                                        {"$divide": [
                                            {"$subtract": ["$total_units", "$available"]},
                                            "$total_units"
                                        ]},
                                        100
                                    ]},
                                    1
                                ]},
                                0
                            ]
                        },
                        "_id": 0
                    }},
                    {"$sort": {"available": 1}}  # lowest stock first
                ]
            }}
        ]
        result = list(self.products.aggregate(pipeline))
        return result[0] if result else {}

    def review_sentiment(self) -> list:
        """
        Review analysis — ratings over time.
        Groups reviews by month to show rating trends.
        """
        pipeline = [
            {"$match": {"is_approved": True}},
            {"$group": {
                "_id": {
                    "year": {"$year": "$created_at"},
                    "month": {"$month": "$created_at"}
                },
                "review_count": {"$sum": 1},
                "avg_rating": {"$avg": "$rating"},
                "five_stars": {"$sum": {"$cond": [{"$eq": ["$rating", 5]}, 1, 0]}},
                "one_stars": {"$sum": {"$cond": [{"$eq": ["$rating", 1]}, 1, 0]}}
            }},
            {"$project": {
                "period": {
                    "$concat": [
                        {"$toString": "$_id.year"},
                        "-",
                        {"$toString": "$_id.month"}
                    ]
                },
                "review_count": 1,
                "avg_rating": {"$round": ["$avg_rating", 2]},
                "five_stars": 1,
                "one_stars": 1,
                "_id": 0
            }},
            {"$sort": {"period": DESCENDING}},
            {"$limit": 6}
        ]
        return list(self.reviews.aggregate(pipeline))

    def search_analytics(self, search_term: str) -> list:
        """Search products using text index with relevance scoring."""
        return list(
            self.products.find(
                {
                    "$text": {"$search": search_term},
                    "is_active": True
                },
                {"score": {"$meta": "textScore"},
                 "name": 1, "brand": 1, "category": 1,
                 "price": 1, "rating": 1}
            )
            .sort([("score", {"$meta": "textScore"})])
            .limit(8)
        )
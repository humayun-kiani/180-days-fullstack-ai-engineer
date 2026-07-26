# ============================================================
# src/repository.py
# MongoDB operations — CRUD and queries for product catalog
# ============================================================

from datetime import datetime
from typing import Optional
from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ASCENDING, DESCENDING, ReturnDocument
from pymongo.collection import Collection
from pymongo.database import Database


class ProductRepository:
    """
    Repository for product catalog operations.

    All MongoDB operations are centralized here.
    """

    def __init__(self, db: Database):
        self.db = db
        self.products: Collection = db["products"]
        self.reviews: Collection = db["reviews"]

    # ─────────────────────────────────────────
    # CREATE
    # ─────────────────────────────────────────

    def insert_product(self, product_doc: dict) -> ObjectId:
        """
        Insert a new product document.

        Args:
            product_doc (dict): Product document to insert.

        Returns:
            ObjectId: The inserted document's ID.
        """
        result = self.products.insert_one(product_doc)
        return result.inserted_id

    def insert_many_products(self, product_docs: list) -> list:
        """
        Insert multiple products at once.

        Args:
            product_docs (list): List of product documents.

        Returns:
            list: List of inserted ObjectIds.
        """
        result = self.products.insert_many(product_docs)
        return result.inserted_ids

    def add_review(self, review_doc: dict) -> ObjectId:
        """
        Add a review and update product rating.

        Args:
            review_doc (dict): Review document.

        Returns:
            ObjectId: Inserted review ID.
        """
        result = self.reviews.insert_one(review_doc)

        # Recalculate product rating from all reviews
        self._update_product_rating(review_doc["product_id"])

        return result.inserted_id

    def _update_product_rating(self, product_id: ObjectId) -> None:
        """Recalculate and update product rating from all reviews."""
        pipeline = [
            {"$match": {"product_id": product_id, "is_approved": True}},
            {"$group": {
                "_id": None,
                "average": {"$avg": "$rating"},
                "count": {"$sum": 1},
                "dist_1": {"$sum": {"$cond": [{"$eq": ["$rating", 1]}, 1, 0]}},
                "dist_2": {"$sum": {"$cond": [{"$eq": ["$rating", 2]}, 1, 0]}},
                "dist_3": {"$sum": {"$cond": [{"$eq": ["$rating", 3]}, 1, 0]}},
                "dist_4": {"$sum": {"$cond": [{"$eq": ["$rating", 4]}, 1, 0]}},
                "dist_5": {"$sum": {"$cond": [{"$eq": ["$rating", 5]}, 1, 0]}}
            }}
        ]
        result = list(self.reviews.aggregate(pipeline))

        if result:
            stats = result[0]
            self.products.update_one(
                {"_id": product_id},
                {"$set": {
                    "rating.average": round(stats["average"], 2),
                    "rating.count": stats["count"],
                    "rating.distribution": {
                        "1": stats["dist_1"],
                        "2": stats["dist_2"],
                        "3": stats["dist_3"],
                        "4": stats["dist_4"],
                        "5": stats["dist_5"]
                    }
                }}
            )

    # ─────────────────────────────────────────
    # READ
    # ─────────────────────────────────────────

    def get_by_id(self, product_id: str) -> Optional[dict]:
        """Get product by string ID."""
        try:
            return self.products.find_one({"_id": ObjectId(product_id)})
        except InvalidId:
            return None

    def get_by_sku(self, sku: str) -> Optional[dict]:
        """Get product by SKU."""
        return self.products.find_one({"sku": sku})

    def get_all(
        self,
        page: int = 1,
        per_page: int = 20,
        category: str = None,
        min_price: float = None,
        max_price: float = None,
        brand: str = None,
        in_stock_only: bool = False,
        sort_by: str = "created_at",
        sort_order: int = DESCENDING
    ) -> tuple[list, int]:
        """
        Get products with filtering, sorting, and pagination.

        Returns:
            tuple: (list of products, total count)
        """
        # Build filter
        query = {"is_active": True}

        if category:
            query["category"] = category
        if brand:
            query["brand"] = {"$regex": brand, "$options": "i"}
        if min_price is not None or max_price is not None:
            query["price"] = {}
            if min_price is not None:
                query["price"]["$gte"] = min_price
            if max_price is not None:
                query["price"]["$lte"] = max_price
        if in_stock_only:
            query["inventory.available"] = {"$gt": 0}

        total = self.products.count_documents(query)
        products = list(
            self.products.find(query)
            .sort(sort_by, sort_order)
            .skip((page - 1) * per_page)
            .limit(per_page)
        )
        return products, total

    def search(self, query: str, limit: int = 20) -> list:
        """Full-text search across name, description, brand, tags."""
        return list(
            self.products.find(
                {
                    "$text": {"$search": query},
                    "is_active": True
                },
                {"score": {"$meta": "textScore"}}
            )
            .sort([("score", {"$meta": "textScore"})])
            .limit(limit)
        )

    def get_featured(self, limit: int = 6) -> list:
        """Get featured products."""
        return list(
            self.products.find(
                {"is_featured": True, "is_active": True}
            )
            .sort("rating.average", DESCENDING)
            .limit(limit)
        )

    def get_top_rated(self, category: str = None, limit: int = 10) -> list:
        """Get top rated products."""
        query = {"is_active": True, "rating.count": {"$gte": 1}}
        if category:
            query["category"] = category
        return list(
            self.products.find(query)
            .sort("rating.average", DESCENDING)
            .limit(limit)
        )

    def get_reviews(self, product_id: str, limit: int = 10) -> list:
        """Get approved reviews for a product."""
        try:
            return list(
                self.reviews.find(
                    {
                        "product_id": ObjectId(product_id),
                        "is_approved": True
                    }
                )
                .sort("created_at", DESCENDING)
                .limit(limit)
            )
        except InvalidId:
            return []

    def get_categories(self) -> list:
        """Get all distinct categories with product counts."""
        pipeline = [
            {"$match": {"is_active": True}},
            {"$group": {
                "_id": "$category",
                "count": {"$sum": 1},
                "avg_price": {"$avg": "$price"},
                "brands": {"$addToSet": "$brand"}
            }},
            {"$project": {
                "category": "$_id",
                "count": 1,
                "avg_price": {"$round": ["$avg_price", 0]},
                "brand_count": {"$size": "$brands"},
                "_id": 0
            }},
            {"$sort": {"count": DESCENDING}}
        ]
        return list(self.products.aggregate(pipeline))

    # ─────────────────────────────────────────
    # UPDATE
    # ─────────────────────────────────────────

    def update_price(self, product_id: str, new_price: float, discount_pct: float = 0) -> bool:
        """Update product price with optional discount."""
        original = new_price / (1 - discount_pct / 100) if discount_pct > 0 else new_price
        result = self.products.update_one(
            {"_id": ObjectId(product_id)},
            {
                "$set": {
                    "price": new_price,
                    "pricing.current_price": new_price,
                    "pricing.original_price": original,
                    "pricing.discount_pct": discount_pct,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0

    def update_inventory(self, sku: str, quantity: int) -> bool:
        """Update inventory stock level."""
        result = self.products.update_one(
            {"sku": sku},
            {
                "$set": {
                    "inventory.total_stock": quantity,
                    "inventory.available": quantity,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0

    def update_variant_stock(self, sku: str, size: str, color: str, stock: int) -> bool:
        """Update stock for a specific clothing variant."""
        result = self.products.update_one(
            {
                "sku": sku,
                "variants.size": size,
                "variants.color": color
            },
            {
                "$set": {"variants.$.stock": stock},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        return result.modified_count > 0

    def increment_views(self, product_id: str) -> None:
        """Increment view counter atomically."""
        self.products.update_one(
            {"_id": ObjectId(product_id)},
            {"$inc": {"views": 1}}
        )

    def mark_as_featured(self, product_ids: list, featured: bool = True) -> int:
        """Bulk mark products as featured or not."""
        object_ids = [ObjectId(pid) for pid in product_ids]
        result = self.products.update_many(
            {"_id": {"$in": object_ids}},
            {"$set": {"is_featured": featured, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count

    def add_tag(self, product_id: str, tag: str) -> bool:
        """Add a tag to a product (addToSet prevents duplicates)."""
        result = self.products.update_one(
            {"_id": ObjectId(product_id)},
            {"$addToSet": {"tags": tag.lower()}}
        )
        return result.modified_count > 0

    # ─────────────────────────────────────────
    # DELETE
    # ─────────────────────────────────────────

    def deactivate_product(self, product_id: str) -> bool:
        """Soft delete — mark as inactive instead of deleting."""
        result = self.products.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    def hard_delete(self, product_id: str) -> bool:
        """Permanently delete a product and its reviews."""
        obj_id = ObjectId(product_id)
        self.reviews.delete_many({"product_id": obj_id})
        result = self.products.delete_one({"_id": obj_id})
        return result.deleted_count > 0

    # ─────────────────────────────────────────
    # COUNTS
    # ─────────────────────────────────────────

    def count(self, active_only: bool = True) -> int:
        query = {"is_active": True} if active_only else {}
        return self.products.count_documents(query)

    def count_reviews(self) -> int:
        return self.reviews.count_documents({"is_approved": True})
# Day 18 — MongoDB: Documents, Collections, CRUD & Aggregation Pipeline

> **Phase 1 — Foundations** | Week 3 | Day 18 of 180

---

## 📌 What I Learned Today

- What NoSQL means and when to use MongoDB vs PostgreSQL
- Documents — JSON-like objects with flexible schema
- Collections — groups of documents (like tables)
- MongoDB vs PostgreSQL tradeoffs in real scenarios
- CRUD operations: insertOne, insertMany, find, findOne,
  updateOne, updateMany, deleteOne, deleteMany
- Query operators: $eq, $ne, $gt, $gte, $lt, $lte,
  $in, $nin, $exists, $regex, $type
- Logical operators: $and, $or, $not, $nor
- Array operators: $elemMatch, $size, $all, $push, $pull, $addToSet
- Update operators: $set, $unset, $inc, $push, $pull, $addToSet, $rename
- Dot notation for nested document queries
- Aggregation Pipeline — the most powerful MongoDB feature
- Pipeline stages: $match, $group, $project, $sort, $limit,
  $skip, $unwind, $lookup, $addFields, $count, $facet, $bucket
- $unwind — expand arrays into separate documents (tag cloud)
- $facet — run multiple sub-pipelines simultaneously
- $bucket — group into price ranges
- $lookup — join with another collection
- Text indexes for full-text search with relevance scoring
- Compound indexes, sparse indexes, TTL indexes
- Embedding vs referencing — when to use each strategy
- pymongo — Python driver: MongoClient, insert, find, aggregate
- Connection pooling with pymongo
- BSON ObjectId handling in Python
- Repository pattern applied to MongoDB

## 🔨 Project Built

**Flexible E-commerce Product Catalog** — Multi-category catalog:
- 4 product types with completely different schemas:
  Laptops (specs: RAM, GPU, battery), Smartphones (variants by color/storage),
  Books (publication_details, ISBN), Clothing (size/color variants with stock)
- No NULL columns — each document has exactly what it needs
- 23 products across 4 categories, 167 reviews
- ProductRepository with 20 CRUD methods
- CatalogAnalytics class with 7 aggregation pipelines:
  1. Category performance (group + project + sort)
  2. Brand market analysis (group + conversion rate calculation)
  3. Price distribution ($bucket for price ranges)
  4. Rating analysis ($facet: multiple sub-pipelines at once)
  5. Tag cloud ($unwind to expand arrays + group + sort)
  6. Inventory health ($switch for stock level categorization)
  7. Review sentiment analysis (group by month)
- Text search index across name, description, brand, tags
- Automatic rating recalculation after each review
- $addToSet for tag uniqueness
- Atomic $inc for view counter

## 🚀 How to Run

```bash
# Option 1: Local MongoDB
brew install mongodb-community  # Mac
sudo apt install mongodb-org    # Ubuntu

# Option 2: Docker (easiest)
docker run -d -p 27017:27017 --name mongo mongo:7

# Option 3: Atlas (free cloud)
# Sign up at cloud.mongodb.com, get connection string

cd Day-18-MongoDB-Product-Catalog
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit if using Atlas
python src/main.py
```

## 🧠 Key Concepts

| Concept | MongoDB | SQL Equivalent |
|---------|---------|----------------|
| Database | database | database |
| Collection | collection | table |
| Document | `{field: value}` | row |
| Field | field | column |
| Filter | `{field: value}` | WHERE |
| Projection | `{field: 1}` | SELECT columns |
| $match | `{$match: filter}` | WHERE |
| $group | `{$group: {_id: "$field"}}` | GROUP BY |
| $sort | `{$sort: {field: -1}}` | ORDER BY |
| $lookup | join another collection | JOIN |
| $unwind | expand array to docs | UNNEST |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
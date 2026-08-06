# Day 28 — Natural Language Processing: Text Analysis, TF-IDF & Classification

> **Phase 3 — AI & Machine Learning** | Week 5 | Day 28 of 180

---

## 📌 What I Learned Today

- Why text is hard for computers — variable length, synonyms, context
- Text preprocessing pipeline: lowercase, URL removal, special chars
- Contraction expansion: "can't" → "cannot" before tokenizing
- Stopword removal — noise words vs important negations
- Stemming (PorterStemmer) vs lemmatization (WordNetLemmatizer)
- Bag of Words: vocabulary → count vectors for each document
- TF-IDF: Term Frequency × Inverse Document Frequency
- Why TF-IDF beats BoW: rare words are more informative
- sublinear_tf=True: log(1 + tf) smooths high frequency counts
- N-grams: unigrams + bigrams capture "not working" as a unit
- sklearn Pipeline: TfidfVectorizer → Classifier as one unit
- Pipeline.predict() accepts raw text — preprocessing inside
- LogisticRegression for text: fast, interpretable, strong baseline
- LinearSVC for text: often best on high-dimensional TF-IDF features
- CalibratedClassifierCV: adds predict_proba to SVC
- class_weight='balanced': handles imbalanced categories
- Sentiment analysis: lexicon-based with negation detection
- Negation handling: "not working" ≠ "working"
- Bigram matching for compound signals: "not working"
- Urgency detection from text signals: ASAP, URGENT, exclamation
- Named entity extraction with regex patterns
- Error code extraction: HTTP 500, Error 404
- Endpoint extraction: /api/v2/users, GET /api/tasks
- Auto-tagging from keyword patterns
- Pipeline + cross_val_score for reliable text model evaluation
- asdict() from dataclasses for JSON serialization

## 🔨 Project Built

**Task Description Analyzer** — Full NLP pipeline:

- DataGenerator: 1,500 labeled texts across 5 categories
- Preprocessor: lowercase, URL removal, contraction expansion,
  stopword removal, lemmatization
- IssueClassifier: TF-IDF (bigrams) + 3 classifiers compared
  LinearSVC wins at 89% accuracy
- Sentiment: lexicon-based with 30+ signals, negation handling,
  urgency scoring, CAPS detection, exclamation weighting
- EntityExtractor: 9 entity types via regex patterns
  (errors, endpoints, refs, versions, time, systems, technologies)
- Auto-tagger: keyword → tag mapping for 10 tag categories
- Analyzer: orchestrates all components into one AnalysisResult
- Priority recommender: weighted score from category + sentiment +
  entities → urgent/high/medium/low recommendation
- FastAPI: POST /analyze, POST /analyze/batch endpoints

## 🚀 How to Run

```bash
cd Day-28-NLP-Text-Analysis
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -c "import nltk; nltk.download('stopwords'); nltk.download('wordnet')"

python src/main.py    # train + demo

uvicorn src.api:app --reload
# Open: http://localhost:8000/docs
```

## 🧠 Key NLP Concepts

| Concept          | What it does                          |
| ---------------- | ------------------------------------- |
| Tokenization     | Split text into words/tokens          |
| Stopword removal | Remove "the", "is", "a" — no signal   |
| Lemmatization    | "running" → "run", "better" → "good"  |
| TF               | Count of word in this document        |
| IDF              | log(N / docs containing word)         |
| TF-IDF           | TF × IDF — rare words score higher    |
| N-grams          | Word sequences: "not working" as unit |
| Pipeline         | TF-IDF + classifier in one object     |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)

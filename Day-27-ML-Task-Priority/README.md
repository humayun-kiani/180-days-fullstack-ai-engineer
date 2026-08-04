# Day 27 — Introduction to Machine Learning: scikit-learn, Training & Evaluation

> **Phase 3 — AI & Machine Learning** | Week 5 | Day 27 of 180

---

## 📌 What I Learned Today

- What machine learning is: examples → patterns → predictions
- Three types of ML: supervised, unsupervised, reinforcement
- Supervised learning: X features + y labels → learn f(X) = y
- The ML workflow: data → features → train → evaluate → deploy
- Train/validation/test split — why three sets, not two
- stratify=y — ensure class balance across splits
- sklearn.model_selection.train_test_split
- Feature engineering: transform raw data to numeric features
- Text analysis: word count, urgency keywords, verb detection
- Temporal features: is_overdue, days_until_due, business_hours
- scikit-learn consistent API: fit(), predict(), predict_proba()
- sklearn.pipeline.Pipeline: chain scaler + classifier
- LogisticRegression, DecisionTree, RandomForest, GradientBoosting
- Cross-validation: StratifiedKFold with 5 folds
- cross_val_score: CV mean ± std for model stability
- Why CV is more reliable than single train/val split
- Overfitting vs underfitting detection with train/val gap
- Evaluation metrics: accuracy, precision, recall, F1
- Why accuracy alone is misleading (imbalanced classes)
- Weighted vs macro averaging for multi-class F1
- classification_report from sklearn.metrics
- Confusion matrix — where the model makes mistakes
- Feature importance from RandomForestClassifier
- GridSearchCV for hyperparameter tuning
- joblib for saving and loading trained models
- Pipeline pattern: scaler + classifier as one unit
- class_weight="balanced" for imbalanced datasets
- n_jobs=-1 for parallel training on all CPU cores

## 🔨 Project Built

**Task Priority Predictor** — Complete ML pipeline:

- DataGenerator: 2,000 synthetic tasks across 4 priority levels
- Feature engineering: 35 features from title text, due dates,
  tags, time context, keyword detection
- 5 competing algorithms compared with CV
- Random Forest wins with 89%+ accuracy on test set
- Hyperparameter tuning with GridSearchCV
- Confusion matrix showing which priorities are confused
- Feature importance ranking (is_overdue #1, urgency words #2)
- Model saved with joblib for production reuse
- Prediction with confidence scores and plain-English explanations
- FastAPI endpoint: POST /predict for real-time predictions
- Batch prediction: POST /predict/batch for multiple tasks
- GET /model/info: model metadata endpoint

## 🚀 How to Run

```bash
cd Day-27-ML-Task-Priority
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Train the model (generates data, trains, evaluates, saves)
python src/main.py

# Start prediction API
uvicorn src.api:app --reload

# Test prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"title": "URGENT: Production is down!", "tags": ["production"]}'
```

## 🧠 Key ML Concepts

| Concept          | What it is                                    |
| ---------------- | --------------------------------------------- |
| Training set     | Data the model learns from                    |
| Validation set   | Data used to tune model selection             |
| Test set         | Data used ONCE for final evaluation           |
| Overfitting      | Model memorized training data                 |
| Underfitting     | Model too simple to learn pattern             |
| Accuracy         | % of correct predictions                      |
| Precision        | Of predicted positives, how many are real?    |
| Recall           | Of real positives, how many did we find?      |
| F1 Score         | Harmonic mean of precision and recall         |
| Cross-validation | Multiple train/val splits for stable estimate |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)

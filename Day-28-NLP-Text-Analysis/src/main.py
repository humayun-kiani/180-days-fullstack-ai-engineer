# ============================================================
# src/main.py
# Main entry point — train classifier and run demo analysis
# ============================================================

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_generator import generate_training_data
from src.classifiers import (
    compare_classifiers, save_classifier,
    load_classifier, predict_category
)
from src.analyzer import analyze_text
from src.sentiment import analyze_sentiment
from src.entity_extractor import extract_entities

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        CYAN = GREEN = YELLOW = RED = BLUE = WHITE = ""
    class Style:
        RESET_ALL = BRIGHT = ""


def header(title):
    print(f"\n{Fore.CYAN}{'═' * 66}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  {title}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'═' * 66}{Style.RESET_ALL}")


def section(title):
    print(f"\n{Fore.YELLOW}  ── {title} ──{Style.RESET_ALL}")


def main():
    header("TASK DESCRIPTION ANALYZER — NLP PIPELINE")
    print(f"\n  Day 28 — Natural Language Processing")
    print(f"  Components: TF-IDF, Logistic Regression, Sentiment, Entity Extraction")

    # ── Step 1: Generate Training Data ───────────────────────
    section("STEP 1: GENERATING TRAINING DATA")
    print("\n  Generating 1,500 labeled task descriptions...")

    df = generate_training_data(n_per_category=300)
    print(f"  Total: {len(df)} examples across {df['category'].nunique()} categories\n")

    for cat, count in df["category"].value_counts().items():
        bar = "█" * int(count / len(df) * 50)
        print(f"    {cat:<20} {count:4d}  {Fore.CYAN}{bar}{Style.RESET_ALL}")

    # ── Step 2: Train and Compare Classifiers ─────────────────
    section("STEP 2: TRAINING AND COMPARING CLASSIFIERS")
    print()

    texts = df["text"].tolist()
    labels = df["category"].tolist()

    best_pipeline, best_name, all_results = compare_classifiers(texts, labels)

    best_result = all_results[best_name]
    print(f"\n  {Fore.GREEN}Best: {best_name}{Style.RESET_ALL}")
    print(f"  Accuracy:    {best_result['test_accuracy']:.1%}")
    print(f"  F1 Score:    {best_result['test_f1_weighted']:.3f}")
    print(f"  CV Mean:     {best_result['cv_mean']:.3f} ± {best_result['cv_std']:.3f}")

    # ── Step 3: Detailed Metrics ──────────────────────────────
    section("STEP 3: PER-CLASS PERFORMANCE")
    report = best_result["classification_report"]
    print(f"\n  {'Category':<22} {'Precision':>10} {'Recall':>8} {'F1':>8} {'Support':>8}")
    print(f"  {'─' * 58}")

    categories = ["bug", "feature_request", "performance", "question", "maintenance"]
    for cat in categories:
        if cat in report:
            m = report[cat]
            color = Fore.GREEN if m["f1-score"] >= 0.8 else Fore.YELLOW
            print(
                f"  {cat:<22} "
                f"{m['precision']:>10.3f} "
                f"{m['recall']:>8.3f} "
                f"{color}{m['f1-score']:>8.3f}{Style.RESET_ALL} "
                f"{int(m['support']):>8}"
            )

    # ── Step 4: Save Model ────────────────────────────────────
    section("STEP 4: SAVING MODEL")
    save_classifier(best_pipeline, best_name, best_result)
    print(f"  {Fore.GREEN}✅ Saved to models/issue_classifier.joblib{Style.RESET_ALL}")

    # ── Step 5: Demo Full Analysis ────────────────────────────
    section("STEP 5: DEMO — FULL TEXT ANALYSIS")

    demo_texts = [
        "URGENT: Production API returning HTTP 500 errors for /api/v2/users endpoint after v2.3.1 deployment. All customers affected, revenue impact. Need immediate fix!",
        "Feature request: Please add ability to export task data as Excel format. This would greatly improve our workflow and save 2 hours per week.",
        "The dashboard is loading extremely slowly — taking 30+ seconds on mobile. Performance degraded significantly since last week's update.",
        "How do I configure webhook notifications for task completion events? I couldn't find documentation for this feature.",
        "Update SSL certificates for the production environment before expiration on June 30th.",
    ]

    for i, text in enumerate(demo_texts, 1):
        print(f"\n  {'─' * 62}")
        print(f"  {Fore.WHITE}Text {i}:{Style.RESET_ALL} {text[:70]}...")

        result = analyze_text(text)

        # Category
        cat_colors = {
            "bug": Fore.RED, "performance": Fore.YELLOW,
            "feature_request": Fore.BLUE, "question": Fore.CYAN,
            "maintenance": Fore.MAGENTA
        }
        cat_color = cat_colors.get(result.category, "")
        print(f"\n  Category:   {cat_color}[{result.category.upper()}]{Style.RESET_ALL} ({result.category_confidence:.0%} confidence)")

        # Sentiment + Urgency
        sent_colors = {"positive": Fore.GREEN, "negative": Fore.RED,
                       "neutral": Fore.WHITE, "mixed": Fore.YELLOW}
        sent_color = sent_colors.get(result.sentiment, "")
        urg_colors = {"high": Fore.RED, "medium": Fore.YELLOW, "low": Fore.GREEN}
        urg_color = urg_colors.get(result.urgency_level, "")
        print(f"  Sentiment:  {sent_color}{result.sentiment}{Style.RESET_ALL} | "
              f"Urgency: {urg_color}{result.urgency_level}{Style.RESET_ALL}")

        # Entities
        if result.error_codes:
            print(f"  Errors:     {', '.join(result.error_codes)}")
        if result.systems:
            print(f"  Systems:    {', '.join(result.systems[:4])}")
        if result.time_mentions:
            print(f"  Time refs:  {', '.join(result.time_mentions[:3])}")

        # Tags and priority
        if result.suggested_tags:
            print(f"  Tags:       {', '.join(result.suggested_tags[:5])}")

        pri_colors = {"urgent": Fore.RED, "high": Fore.YELLOW,
                      "medium": Fore.CYAN, "low": Fore.GREEN}
        pri_color = pri_colors.get(result.recommended_priority, "")
        print(f"  Priority:   {pri_color}[{result.recommended_priority.upper()}]{Style.RESET_ALL} — {result.priority_reasoning}")

    # ── Summary ───────────────────────────────────────────────
    header("COMPLETE")
    print(f"\n  ✅ Classifier trained: {best_result['test_accuracy']:.1%} accuracy")
    print(f"  ✅ Model saved to models/")
    print(f"\n  Start the API:")
    print(f"  {Fore.CYAN}uvicorn src.api:app --reload{Style.RESET_ALL}")
    print(f"  Then: http://localhost:8000/docs\n")


if __name__ == "__main__":
    main()
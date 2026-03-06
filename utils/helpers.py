from database.db import SessionLocal
from database.models import Transaction
from services.categorizer import categorize_transaction
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

def _sentiment_label(score: float) -> str:
    if score >= 0.05:
        return "Positive"
    if score <= -0.05:
        return "Negative"
    return "Neutral"

def save_transactions(user_id: int, txns: list[dict], source: str = "csv") -> int:
    inserted = 0
    db = SessionLocal()

    try:
        for t in txns:
            if not t.get("date") or not t.get("description"):
                continue

            desc = str(t["description"]).strip()
            if not desc:
                continue

            try:
                amount = float(t.get("amount"))
            except Exception:
                continue

            # ✅ category
            category = t.get("category") or categorize_transaction(desc, amount)

            # ✅ sentiment
            score = analyzer.polarity_scores(desc)["compound"]
            label = _sentiment_label(score)

            # dedupe
            exists = (
                db.query(Transaction)
                .filter(
                    Transaction.user_id == int(user_id),
                    Transaction.date == t["date"],
                    Transaction.amount == amount,
                    Transaction.description == desc,
                )
                .first()
            )
            if exists:
                continue

            db.add(
                Transaction(
                    user_id=int(user_id),
                    date=t["date"],
                    description=desc[:500],
                    amount=amount,
                    category=category,
                    source=source,
                    raw_text=t.get("raw_text"),
                    sentiment_score=score,      # ✅ saved
                    sentiment_label=label,      # ✅ saved
                )
            )
            inserted += 1

        db.commit()
        return inserted
    finally:
        db.close()
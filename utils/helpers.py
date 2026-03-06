from database.db import SessionLocal
from database.models import Transaction
from services.categorizer import categorize_transaction


def save_transactions(user_id: int, txns: list[dict], source: str = "csv") -> int:
    if not user_id:
        raise ValueError("Missing user_id")

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

            # ✅ auto category (if not provided)
            category = t.get("category") or categorize_transaction(desc, amount)

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
                    category=category,   # ✅ NOW FILLS CATEGORY
                    source=source,
                    raw_text=t.get("raw_text"),
                )
            )
            inserted += 1

        db.commit()
        return inserted

    finally:
        db.close()
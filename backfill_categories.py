from database.db import SessionLocal
from database.models import Transaction
from services.categorizer import categorize_transaction
from sqlalchemy import or_

db = SessionLocal()

try:
    # Update rows where category is NULL OR empty OR "Other"
    rows = (
        db.query(Transaction)
        .filter(
            or_(
                Transaction.category.is_(None),
                Transaction.category == "",
                Transaction.category == "Other",
            )
        )
        .all()
    )

    for t in rows:
        # make sure amount is float
        amt = float(t.amount) if t.amount is not None else 0.0
        t.category = categorize_transaction(t.description, amt)

    db.commit()
    print(f"✅ Updated {len(rows)} transactions with categories.")

finally:
    db.close()
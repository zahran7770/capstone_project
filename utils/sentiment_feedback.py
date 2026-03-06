from database.db import SessionLocal
from database.models import SentimentFeedback

def save_feedback(user_id: int, transaction_id: int, predicted: str, user_label: str):
    db = SessionLocal()
    try:
        is_correct = 1 if predicted == user_label else 0
        db.add(SentimentFeedback(
            user_id=user_id,
            transaction_id=transaction_id,
            predicted_label=predicted,
            user_label=user_label,
            is_correct=is_correct,
        ))
        db.commit()
    finally:
        db.close()
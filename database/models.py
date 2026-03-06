from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Text
import datetime
from sqlalchemy.orm import relationship
from database.db import Base


# -------------------
# USERS TABLE
# -------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True)
    password = Column(String)

    transactions = relationship("Transaction", back_populates="owner")
    limits = relationship("Limit", back_populates="owner")


# -------------------
# TRANSACTIONS TABLE
# -------------------class Transaction(Base):
#     __tablename__ = "transactions"
#
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)

    date = Column(Date, nullable=False)
    description = Column(String(500), nullable=False)
    amount = Column(Float, nullable=False)

    category = Column(String(100), nullable=True)
    source = Column(String(50), nullable=True)   # ← ADD THIS
    raw_text = Column(Text, nullable=True)       # ← ADD THIS
    sentiment_score = Column(Float, nullable=True)  # compound score [-1..1]
    sentiment_label = Column(String(20), nullable=True)  # Positive/Neutral/Negative

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    owner = relationship("User", back_populates="transactions")


# -------------------
# LIMITS TABLE
# -------------------
class Limit(Base):
    __tablename__ = "limits"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String)
    monthly_limit = Column(Float)

    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="limits")

class SentimentFeedback(Base):
    __tablename__ = "sentiment_feedback"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False)

    predicted_label = Column(String(20), nullable=False)
    user_label = Column(String(20), nullable=False)      # what user says is correct
    is_correct = Column(Integer, nullable=False)         # 1 = correct, 0 = wrong

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

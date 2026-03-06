from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Text
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

from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, DateTime, Date, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from database.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Hybrid property to maintain compatibility with code using user.name
    @hybrid_property
    def name(self):
        return self.username
        
    @name.setter
    def name(self, value):
        self.username = value

# Alias AuthUser to User to reuse users table for authentication
AuthUser = User


class Group(Base):
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, default="")
    currency = Column(String, default="INR")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="group", cascade="all, delete-orphan")


class GroupMember(Base):
    __tablename__ = "group_members"
    
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    joined_on = Column(Date, default=date.today)
    left_on = Column(Date, nullable=True)
    status = Column(String, default="ACTIVE") # e.g. ACTIVE, LEFT
    
    # Relationships
    group = relationship("Group", back_populates="members")
    user = relationship("User")
    
    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_group_user"),
    )


class Expense(Base):
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    paid_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=False)
    category = Column(String, default="General")
    date = Column(Date, nullable=False)
    currency = Column(String, default="INR")
    split_type = Column(String, default="equal")
    notes = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Hybrid property to maintain compatibility with expense.expense_date
    @hybrid_property
    def expense_date(self):
        return self.date
        
    @expense_date.setter
    def expense_date(self, value):
        self.date = value
        
    # Relationships
    group = relationship("Group", back_populates="expenses")
    payer = relationship("User", foreign_keys=[paid_by])
    participants = relationship("ExpenseParticipant", back_populates="expense", cascade="all, delete-orphan")


class ExpenseParticipant(Base):
    __tablename__ = "expense_splits"
    
    id = Column(Integer, primary_key=True)
    expense_id = Column(Integer, ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    share_amount = Column(Float, nullable=False)
    share_percentage = Column(Float, nullable=True)
    share_units = Column(Float, nullable=True)
    
    # Relationships
    expense = relationship("Expense", back_populates="participants")
    user = relationship("User")
    
    __table_args__ = (
        UniqueConstraint("expense_id", "user_id", name="uq_expense_user"),
    )


class Anomaly(Base):
    __tablename__ = "anomalies"
    
    id = Column(Integer, primary_key=True)
    row_number = Column(Integer, nullable=True)
    anomaly_type = Column(String, nullable=True)
    severity = Column(String, nullable=True)
    description = Column(String, nullable=True)
    action_taken = Column(String, nullable=True)
    status = Column(String, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)


class ImportLog(Base):
    __tablename__ = "import_logs"
    
    id = Column(Integer, primary_key=True)
    file_name = Column(String, nullable=True)
    total_rows = Column(Integer, nullable=True)
    imported_rows = Column(Integer, nullable=True)
    anomalies_found = Column(Integer, nullable=True)
    imported_at = Column(DateTime, default=datetime.utcnow)


class Settlement(Base):
    __tablename__ = "settlements"
    
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=True)
    payer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    settlement_date = Column(Date, default=date.today)
    notes = Column(String, default="")
    
    # Relationships
    group = relationship("Group")
    payer = relationship("User", foreign_keys=[payer_id])
    receiver = relationship("User", foreign_keys=[receiver_id])

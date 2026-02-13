from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(64), nullable=False)
    password_salt = Column(String(32), nullable=False)
    full_name = Column(String(100), default="")
    role = Column(String(20), default="user")
    created_at = Column(DateTime, default=datetime.utcnow)


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    doc_number = Column(String(50), nullable=False)
    doc_type = Column(String(20), nullable=False)
    subject = Column(String(200), nullable=False)
    sender = Column(String(100), default="")
    receiver = Column(String(100), default="")
    content = Column(Text, default="")
    status = Column(String(30), default="pending")
    notes = Column(Text, default="")
    created_by = Column(String(50), default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    history = relationship("DocumentHistory", back_populates="document", cascade="all, delete-orphan")


class DocumentHistory(Base):
    __tablename__ = "document_history"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(50), nullable=False)
    details = Column(Text, default="")
    performed_by = Column(String(50), default="")
    performed_at = Column(DateTime, default=datetime.utcnow)
    document = relationship("Document", back_populates="history")

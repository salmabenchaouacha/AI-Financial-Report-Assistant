import uuid
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSONB

db = SQLAlchemy()


class Document(db.Model):
    __tablename__ = "documents"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), nullable=False, default="uploaded")
    path = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "document_id": self.id,
            "filename": self.filename,
            "status": self.status,
            "path": self.path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Conversation(db.Model):
    __tablename__ = "conversations"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(255), nullable=False, default="Nouvelle discussion")
    document_ids = db.Column(JSONB, nullable=False, default=list)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = db.relationship(
        "ChatMessage", backref="conversation", cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )

    def to_dict(self, include_messages=False):
        data = {
            "conversation_id": self.id,
            "title": self.title,
            "document_ids": self.document_ids,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_messages:
            data["messages"] = [m.to_dict() for m in self.messages]
        return data


class ChatMessage(db.Model):
    __tablename__ = "chat_history"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    conversation_id = db.Column(db.String(36), db.ForeignKey("conversations.id"), nullable=False)
    document_id = db.Column(db.String(36), nullable=True)  # référence indicative, pas de FK stricte
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    sources = db.Column(JSONB, nullable=True)
    chart_url = db.Column(db.String(500), nullable=True)
    saved_to_report = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "question": self.question,
            "answer": self.answer,
            "sources": self.sources,
            "chart_url": self.chart_url,
            "saved_to_report": self.saved_to_report,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
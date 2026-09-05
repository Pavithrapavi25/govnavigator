from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# =========================================================
# STATE / UNION TERRITORY MODEL
# =========================================================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(
        String(100),
        nullable=False
    )

    email = Column(
        String(150),
        unique=True,
        index=True,
        nullable=False
    )

    password_hash = Column(
        String(255),
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )
class State(Base):
    __tablename__ = "states"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(100),
        unique=True,
        nullable=False
    )

    state_type = Column(
        String(20),
        nullable=False,
        default="State"
    )

    services = relationship(
        "Service",
        back_populates="state",
        cascade="all, delete-orphan"
    )


# =========================================================
# GOVERNMENT SERVICE MODEL
# =========================================================

class Service(Base):
    __tablename__ = "services"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(150),
        nullable=False
    )

    category = Column(
        String(100),
        nullable=True
    )

    description = Column(
        Text,
        nullable=True
    )

    eligibility = Column(
        Text,
        nullable=True
    )

    documents = Column(
        Text,
        nullable=True
    )

    steps = Column(
        Text,
        nullable=True
    )

    fees = Column(
        Text,
        nullable=True
    )

    processing_time = Column(
        String(200),
        nullable=True
    )

    official_portal_name = Column(
        String(200),
        nullable=True
    )

    official_portal_url = Column(
        Text,
        nullable=True
    )

    state_id = Column(
        Integer,
        ForeignKey("states.id"),
        nullable=True
    )

    state = relationship(
        "State",
        back_populates="services"
    )


# =========================================================
# AI CHAT HISTORY MODEL
# =========================================================

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Connect chat to a browser/user session
    session_id = Column(
        String(100),
        ForeignKey("user_sessions.session_id"),
        nullable=True,
        index=True
    )

    user_message = Column(
        Text,
        nullable=False
    )

    ai_response = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    # Relationship with UserSession
    session = relationship(
        "UserSession",
        back_populates="chat_history"
    )


# =========================================================
# SEARCH HISTORY MODEL
# =========================================================

class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )
    user_id = Column(
    Integer,
    ForeignKey("users.id"),
    nullable=True
)

    search_query = Column(
        Text,
        nullable=False
    )

    matched_service = Column(
        String(150),
        nullable=True
    )

    selected_state = Column(
        String(100),
        nullable=True
    )

    match_score = Column(
        Integer,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


# =========================================================
# USER SESSION MODEL
# =========================================================

class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    session_id = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    selected_state = Column(
        String(100),
        nullable=True
    )

    last_service = Column(
        String(150),
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationship with ChatHistory
    chat_history = relationship(
        "ChatHistory",
        back_populates="session",
        cascade="all, delete-orphan"
    )

# =========================================================
# FAVORITE / SAVED SERVICE MODEL
# =========================================================

class FavoriteService(Base):
    __tablename__ = "favorite_services"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    service_id = Column(
        Integer,
        ForeignKey("services.id"),
        nullable=False,
        index=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

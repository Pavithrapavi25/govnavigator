from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from google import genai
from google.genai import types

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from database import engine, SessionLocal, Base

from models import (
    State,
    Service,
    ChatHistory,
    SearchHistory,
    UserSession,
    User,
    FavoriteService,
)

from schemas import (
    StateResponse,
    ServiceResponse,
    SearchRequest,
    SearchResponse,
)

import os
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. Check backend/.env"
    )


# =========================================================
# PASSWORD + JWT CONFIGURATION
# =========================================================

password_hash = PasswordHash.recommended()

security = HTTPBearer()

APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
JWT_SECRET = os.getenv("JWT_SECRET", "").strip()

# Never use the development fallback in production.
if APP_ENV == "production" and not JWT_SECRET:
    raise RuntimeError(
        "JWT_SECRET is required when APP_ENV=production."
    )

if not JWT_SECRET:
    JWT_SECRET = "govnavigator-development-secret-change-in-production"

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24


# =========================================================
# DATABASE TABLE CREATION
# =========================================================

Base.metadata.create_all(bind=engine)


# =========================================================
# GEMINI CLIENT
# =========================================================

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(
    title="GovNavigator API",
    description="AI + SQL backend for GovNavigator",
    version="5.2.0"
)


# =========================================================
# CORS
# =========================================================

frontend_urls = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173,http://127.0.0.1:5173"
)

allow_origins = [
    origin.strip().rstrip("/")
    for origin in frontend_urls.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


# =========================================================
# DATABASE SESSION
# =========================================================

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# =========================================================
# REQUEST MODELS
# =========================================================

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(..., min_length=1, max_length=100)


class SessionRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=100)
    selected_state: str | None = Field(default=None, max_length=100)
    last_service: str | None = Field(default=None, max_length=200)


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=3, max_length=150)
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=150)
    password: str = Field(..., min_length=1, max_length=128)


# =========================================================
# HEALTH CHECK
# =========================================================

class FavoriteRequest(BaseModel):
    service_id: int


@app.get("/")
def home():
    return {
        "status": "online",
        "message": "GovNavigator AI backend is running.",
        "version": "5.2.0",
        "database": "SQLite + SQLAlchemy"
    }


# =========================================================
# CURRENT AUTHENTICATED USER
# =========================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )

        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token"
            )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Authentication token has expired"
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )

    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return user


# =========================================================
# DATABASE HEALTH CHECK
# =========================================================

@app.get("/api/database")
def database_health(
    db: Session = Depends(get_db)
):
    chat_count = db.query(ChatHistory).count()
    state_count = db.query(State).count()
    service_count = db.query(Service).count()
    search_count = db.query(SearchHistory).count()
    session_count = db.query(UserSession).count()

    return {
        "status": "connected",
        "database": "SQLite",
        "chat_history_records": chat_count,
        "states": state_count,
        "services": service_count,
        "search_history_records": search_count,
        "user_sessions": session_count
    }


# =========================================================
# AUTH — REGISTER
# =========================================================

@app.post("/api/auth/register")
def register_user(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    name = request.name.strip()
    email = request.email.strip().lower()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Name cannot be empty"
        )

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Email cannot be empty"
        )

    if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        raise HTTPException(
            status_code=400,
            detail="Please enter a valid email address."
        )

    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email is already registered"
        )

    if len(request.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters"
        )

    if len(name) > 100:
        raise HTTPException(
            status_code=400,
            detail="Name is too long."
        )

    hashed_password = password_hash.hash(
        request.password
    )

    user = User(
        name=name,
        email=email,
        password_hash=hashed_password
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "Registration successful",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    }


# =========================================================
# AUTH — LOGIN
# =========================================================

@app.post("/api/auth/login")
def login_user(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    email = request.email.strip().lower()

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not password_hash.verify(
        request.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(minutes=JWT_EXPIRE_MINUTES)
    )

    payload = {
        "sub": str(user.id),
        "email": user.email,
        "exp": expires_at
    }

    token = jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )

    return {
        "message": "Login successful",
        "token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    }


# =========================================================
# STATES API
# =========================================================

@app.get(
    "/api/states",
    response_model=list[StateResponse]
)
def get_states(
    db: Session = Depends(get_db)
):
    states = (
        db.query(State)
        .order_by(State.name.asc())
        .all()
    )

    return states


# =========================================================
# SINGLE STATE API
# =========================================================

@app.get(
    "/api/states/{state_id}",
    response_model=StateResponse
)
def get_state(
    state_id: int,
    db: Session = Depends(get_db)
):
    state = (
        db.query(State)
        .filter(State.id == state_id)
        .first()
    )

    if not state:
        raise HTTPException(
            status_code=404,
            detail="State or Union Territory not found."
        )

    return state


# =========================================================
# SERVICES API
# =========================================================

@app.get(
    "/api/services",
    response_model=list[ServiceResponse]
)
def get_services(
    db: Session = Depends(get_db)
):
    services = (
        db.query(Service)
        .order_by(Service.name.asc())
        .all()
    )

    return services


# =========================================================
# SINGLE SERVICE API
# =========================================================

@app.get(
    "/api/services/{service_id}",
    response_model=ServiceResponse
)
def get_service(
    service_id: int,
    db: Session = Depends(get_db)
):
    service = (
        db.query(Service)
        .filter(Service.id == service_id)
        .first()
    )

    if not service:
        raise HTTPException(
            status_code=404,
            detail="Government service not found."
        )

    return service


# =========================================================
# SERVICES BY STATE
# =========================================================

@app.get(
    "/api/services/state/{state_id}",
    response_model=list[ServiceResponse]
)
def get_services_by_state(
    state_id: int,
    db: Session = Depends(get_db)
):
    state = (
        db.query(State)
        .filter(State.id == state_id)
        .first()
    )

    if not state:
        raise HTTPException(
            status_code=404,
            detail="State or Union Territory not found."
        )

    services = (
        db.query(Service)
        .filter(Service.state_id == state_id)
        .order_by(Service.name.asc())
        .all()
    )

    return services


# ============================================================
# INTELLIGENT SMART SEARCH
# ============================================================

SEARCH_SYNONYMS = {

    "pan": [
        "pan",
        "permanent account number",
        "tax card",
        "income tax card",
    ],

    "aadhaar": [
        "aadhaar",
        "aadhar",
        "uid",
        "uidai",
        "identity",
        "biometric",
    ],

    "passport": [
        "passport",
        "travel document",
        "international travel",
        "passport renewal",
        "passport application",
    ],

    "voter": [
        "voter",
        "voter id",
        "voter card",
        "election",
        "electoral",
        "epic",
    ],

    "driving": [
        "driving",
        "driving licence",
        "driving license",
        "dl",
        "learner licence",
        "learner license",
    ],

    "vehicle": [
        "vehicle",
        "vehicle registration",
        "registration certificate",
        "rc",
        "car registration",
        "bike registration",
    ],

    "income": [
        "income",
        "income certificate",
        "family income",
        "earnings",
        "income proof",
    ],

    "caste": [
        "caste",
        "caste certificate",
        "community",
        "community certificate",
        "social category",
    ],

    "birth": [
        "birth",
        "birth certificate",
        "newborn",
        "new born",
        "baby birth",
    ],

    "death": [
        "death",
        "death certificate",
        "deceased",
        "death registration",
    ],

    "schemes": [
        "scheme",
        "government scheme",
        "government benefits",
        "welfare",
        "subsidy",
        "benefits",
    ],

    "national": [
        "government service",
        "national service",
        "central government",
        "online government service",
    ],
}


def normalize_search_text(text):
    """
    Convert text into a clean searchable format.
    """

    if not text:
        return ""

    text = str(text).lower()

    cleaned = ""

    for character in text:
        if character.isalnum() or character.isspace():
            cleaned += character
        else:
            cleaned += " "

    return " ".join(cleaned.split())


def calculate_service_search_score(query, service):
    """
    Calculate a relevance score for a service.

    Higher score = stronger match.

    The final score is ALWAYS capped at 100.
    """

    normalized_query = normalize_search_text(query)

    if not normalized_query:
        return 0

    query_words = set(
        normalized_query.split()
    )

    service_name = normalize_search_text(
        service.name
    )

    category = normalize_search_text(
        service.category
    )

    description = normalize_search_text(
        service.description
    )

    eligibility = normalize_search_text(
        service.eligibility
    )

    documents = normalize_search_text(
        service.documents
    )

    searchable_text = " ".join([
        service_name,
        category,
        description,
        eligibility,
        documents,
    ])

    score = 0

    # --------------------------------------------------------
    # 1. Exact service name match
    # --------------------------------------------------------

    if normalized_query == service_name:
        score += 100

    elif normalized_query in service_name:
        score += 70

    elif service_name and service_name in normalized_query:
        score += 65

    # --------------------------------------------------------
    # 2. Individual word matching
    # --------------------------------------------------------

    service_name_words = set(
        service_name.split()
    )

    for word in query_words:

        if len(word) < 2:
            continue

        if word in service_name_words:
            score += 25

        elif word in category.split():
            score += 15

        elif word in searchable_text:
            score += 5

    # --------------------------------------------------------
    # 3. Synonym matching
    # --------------------------------------------------------

    for service_key, synonyms in SEARCH_SYNONYMS.items():

        normalized_synonyms = [
            normalize_search_text(item)
            for item in synonyms
        ]

        synonym_matched = False

        for synonym in normalized_synonyms:

            if not synonym:
                continue

            if synonym in normalized_query:
                synonym_matched = True
                break

            synonym_words = set(
                synonym.split()
            )

            if query_words.intersection(
                synonym_words
            ):
                synonym_matched = True
                break

        if synonym_matched:

            service_combined = " ".join([
                service_name,
                category,
                description,
            ])

            if service_key in service_combined:
                score += 45

    # --------------------------------------------------------
    # 4. Multi-word query bonus
    # --------------------------------------------------------

    matched_words = 0

    for word in query_words:

        if len(word) < 2:
            continue

        if word in searchable_text:
            matched_words += 1

    if len(query_words) >= 2:

        if matched_words == len(query_words):
            score += 30

        elif matched_words >= 2:
            score += 15

    # --------------------------------------------------------
    # 5. FINAL SCORE CAP
    # --------------------------------------------------------

    return min(score, 100)


# ============================================================
# SEARCH HISTORY HELPER
# ============================================================

def save_search_history(
    db,
    search_query,
    selected_state=None,
    matched_service=None,
    match_score=None,
    user_id=None
):
    """
    Save a user's search into the search_history table.
    """

    try:

        if match_score is not None:
            match_score = min(int(match_score), 100)

        record = SearchHistory(
            user_id=user_id,
            search_query=search_query,
            selected_state=selected_state,
            matched_service=matched_service,
            match_score=match_score
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        return record

    except Exception as error:

        db.rollback()

        print(
            "Search history save error:",
            error
        )

        return None


# ============================================================
# SMART SEARCH
# ============================================================

@app.get("/api/search")
def smart_search(
    q: str,
    state_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Intelligent government-service search.

    Features:
    - Exact name matching
    - Keyword matching
    - Category matching
    - Description matching
    - Document matching
    - Synonym matching
    - State filtering
    - Relevance scoring
    - Search history tracking
    """

    query = q.strip()

    # --------------------------------------------------------
    # Empty query
    # --------------------------------------------------------

    if not query:
        return []

    # --------------------------------------------------------
    # Get services
    # --------------------------------------------------------

    services_query = db.query(Service)

    # Include:
    # 1. State-specific services
    # 2. National services

    if state_id is not None:

        services_query = services_query.filter(
            or_(
                Service.state_id == state_id,
                Service.state_id.is_(None)
            )
        )

    services = services_query.all()

    results = []

    # --------------------------------------------------------
    # Calculate scores
    # --------------------------------------------------------

    for service in services:

        score = calculate_service_search_score(
            query,
            service
        )

        # Extra safety: never allow more than 100
        score = min(score, 100)

        # Ignore very weak matches
        if score < 10:
            continue

        results.append({

            "id": service.id,

            "name": service.name,

            "category": service.category,

            "description": service.description,

            "eligibility": service.eligibility,

            "documents": service.documents,

            "steps": service.steps,

            "fees": service.fees,

            "processing_time":
                service.processing_time,

            "official_portal_name":
                service.official_portal_name,

            "official_portal_url":
                service.official_portal_url,

            "state_id": service.state_id,

            "match_score": score,
        })

    # --------------------------------------------------------
    # Sort highest score first
    # --------------------------------------------------------

    results.sort(
        key=lambda item: item["match_score"],
        reverse=True
    )

    # --------------------------------------------------------
    # Top 5 results
    # --------------------------------------------------------

    top_results = results[:5]

    # --------------------------------------------------------
    # SAVE SEARCH HISTORY
    # --------------------------------------------------------

    selected_state_name = None

    if state_id is not None:

        state = (
            db.query(State)
            .filter(State.id == state_id)
            .first()
        )

        if state:
            selected_state_name = state.name

    if top_results:

        best_result = top_results[0]

        save_search_history(
            db=db,
            search_query=query,
            selected_state=selected_state_name,
            matched_service=best_result["name"],
            match_score=min(
                best_result["match_score"],
                100
            ),
            user_id=current_user.id
        )

    else:

        save_search_history(
            db=db,
            search_query=query,
            selected_state=selected_state_name,
            matched_service=None,
            match_score=0,
            user_id=current_user.id
        )

    return top_results


# =========================================================
# SEARCH HISTORY — MANUAL CREATE
# CURRENT USER ONLY
# =========================================================

@app.post(
    "/api/search-history",
    response_model=SearchResponse
)
def create_search_history(
    request: SearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    search_query = request.search_query.strip()

    if not search_query:
        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty."
        )

    record = SearchHistory(
        user_id=current_user.id,
        search_query=search_query,
        selected_state=request.selected_state
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "search_query": record.search_query,
        "matched_service": record.matched_service,
        "selected_state": record.selected_state,
        "match_score": record.match_score
    }


# =========================================================
# GET SEARCH HISTORY
# CURRENT USER ONLY
# =========================================================

@app.get("/api/search-history")
def get_search_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    records = (
        db.query(SearchHistory)
        .filter(
            SearchHistory.user_id == current_user.id
        )
        .order_by(
            SearchHistory.created_at.desc()
        )
        .all()
    )

    return [
        {
            "id": record.id,

            "search_query":
                record.search_query,

            "matched_service":
                record.matched_service,

            "selected_state":
                record.selected_state,

            "match_score":
                min(
                    record.match_score,
                    100
                ) if record.match_score is not None else 0,

            "created_at":
                record.created_at
        }

        for record in records
    ]


# =========================================================
# DELETE ONE SEARCH HISTORY ITEM
# CURRENT USER ONLY
# =========================================================

@app.delete("/api/search-history/{history_id}")
def delete_search_history(
    history_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    record = (
        db.query(SearchHistory)
        .filter(
            SearchHistory.id == history_id,
            SearchHistory.user_id == current_user.id
        )
        .first()
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Search history item not found."
        )

    db.delete(record)
    db.commit()

    return {
        "message": "Search history item deleted.",
        "id": history_id
    }


# =========================================================
# DELETE ALL SEARCH HISTORY
# CURRENT USER ONLY
# =========================================================

@app.delete("/api/search-history")
def clear_search_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    deleted_count = (
        db.query(SearchHistory)
        .filter(SearchHistory.user_id == current_user.id)
        .delete(synchronize_session=False)
    )

    db.commit()

    return {
        "message": "Search history cleared.",
        "deleted_count": deleted_count
    }


# =========================================================
# GET RECENT SEARCH HISTORY
# CURRENT USER ONLY
# =========================================================

@app.get("/api/search-history/recent")
def get_recent_search_history(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if limit < 1:
        limit = 1

    if limit > 50:
        limit = 50

    records = (
        db.query(SearchHistory)
        .filter(
            SearchHistory.user_id == current_user.id
        )
        .order_by(
            SearchHistory.created_at.desc()
        )
        .limit(limit)
        .all()
    )

    return [
        {
            "id": record.id,

            "search_query":
                record.search_query,

            "matched_service":
                record.matched_service,

            "selected_state":
                record.selected_state,

            "match_score":
                min(
                    record.match_score,
                    100
                ) if record.match_score is not None else 0,

            "created_at":
                record.created_at
        }

        for record in records
    ]


# =========================================================
# ALL CHAT HISTORY
# =========================================================

@app.get("/api/chat-history")
def get_chat_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    records = (
        db.query(ChatHistory)
        .order_by(
            ChatHistory.created_at.asc()
        )
        .all()
    )

    return [
        {
            "id": record.id,

            "session_id":
                record.session_id,

            "user_message":
                record.user_message,

            "ai_response":
                record.ai_response,

            "created_at":
                record.created_at
        }

        for record in records
    ]


# =========================================================
# CHAT HISTORY FOR ONE SESSION
# =========================================================

@app.get("/api/chat-history/{session_id}")
def get_session_chat_history(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = (
        db.query(UserSession)
        .filter(
            UserSession.session_id == session_id
        )
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found."
        )

    records = (
        db.query(ChatHistory)
        .filter(
            ChatHistory.session_id == session_id
        )
        .order_by(
            ChatHistory.created_at.asc()
        )
        .all()
    )

    return [
        {
            "id": record.id,

            "session_id":
                record.session_id,

            "user_message":
                record.user_message,

            "ai_response":
                record.ai_response,

            "created_at":
                record.created_at
        }

        for record in records
    ]


# =========================================================
# AI CHAT
# =========================================================

@app.post("/api/chat")
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_message = request.message.strip()

    session_id = request.session_id.strip()

    if len(user_message) > 2000:
        raise HTTPException(
            status_code=400,
            detail="Message is too long. Maximum 2000 characters."
        )

    if len(session_id) > 100:
        raise HTTPException(
            status_code=400,
            detail="Invalid session ID."
        )

    # -------------------------------------------------------
    # Validate session ID
    # -------------------------------------------------------

    if not session_id:

        raise HTTPException(
            status_code=400,
            detail="session_id is required."
        )

    # -------------------------------------------------------
    # Check session
    # -------------------------------------------------------

    session = (
        db.query(UserSession)
        .filter(
            UserSession.session_id == session_id
        )
        .first()
    )

    if not session:

        raise HTTPException(
            status_code=404,
            detail="Session not found. Please create a session first."
        )

    # -------------------------------------------------------
    # Empty message
    # -------------------------------------------------------

    if not user_message:

        empty_response = (
            '{"related_to_government_service":false,'
            '"service_name":"",'
            '"recommendation":"Please enter a question.",'
            '"why":"No question was provided.",'
            '"documents":[],'
            '"steps":[],'
            '"important_note":"Please describe the government service you need.",'
            '"disclaimer":"GovNavigator is an independent prototype."}'
        )

        return {
            "response": empty_response,
            "session_id": session_id
        }

    # -------------------------------------------------------
    # Update session
    # -------------------------------------------------------

    session.updated_at = datetime.utcnow()

    # -------------------------------------------------------
    # Gemini prompt
    # -------------------------------------------------------

    prompt = f"""
You are GovNavigator AI.

GovNavigator is an independent prototype designed to help
Indian citizens understand government services, certificates,
documents, schemes and administrative procedures.

USER QUESTION:
{user_message}

IMPORTANT RULES:

1. First determine whether the question is actually related
   to an Indian government service.

2. A government-service question can involve:
   - certificates
   - government documents
   - government schemes
   - applications
   - eligibility
   - government departments
   - civic services
   - administrative procedures
   - official government portals

3. If the question is unrelated to government services,
   DO NOT recommend a government service.

4. Examples of unrelated questions:
   - weather
   - sports
   - entertainment
   - cooking
   - general knowledge
   - jokes
   - programming
   - mathematics
   - casual conversation

5. For unrelated questions, explain politely that
   GovNavigator specializes in Indian government-service
   guidance.

6. Never invent a government service.

7. Never invent official URLs, fees, deadlines,
   documents or legal requirements.

8. Government requirements can vary by state and may change.

9. Keep the answer simple and useful.

10. Always recommend verification with the relevant
    official government authority.

11. Return ONLY valid JSON matching the required schema.
"""

    # -------------------------------------------------------
    # Gemini response schema
    # -------------------------------------------------------

    response_schema = {

        "type": "object",

        "properties": {

            "related_to_government_service": {
                "type": "boolean"
            },

            "service_name": {
                "type": "string"
            },

            "recommendation": {
                "type": "string"
            },

            "why": {
                "type": "string"
            },

            "documents": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            },

            "steps": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            },

            "important_note": {
                "type": "string"
            },

            "disclaimer": {
                "type": "string"
            }
        },

        "required": [

            "related_to_government_service",

            "service_name",

            "recommendation",

            "why",

            "documents",

            "steps",

            "important_note",

            "disclaimer"
        ]
    }

    # -------------------------------------------------------
    # Call Gemini
    # -------------------------------------------------------

    try:

        response = client.models.generate_content(

            model="gemini-3.6-flash",

            contents=prompt,

            config=types.GenerateContentConfig(

                response_mime_type="application/json",

                response_schema=response_schema,

                temperature=0.2,
            ),
        )

        ai_response = response.text

        # ---------------------------------------------------
        # Fallback
        # ---------------------------------------------------

        if not ai_response:

            ai_response = (
                '{"related_to_government_service":false,'
                '"service_name":"",'
                '"recommendation":"Sorry, I could not generate a response.",'
                '"why":"The AI did not return a response.",'
                '"documents":[],'
                '"steps":[],'
                '"important_note":"Please try again.",'
                '"disclaimer":"GovNavigator is an independent prototype."}'
            )

        # ---------------------------------------------------
        # Save chat
        # ---------------------------------------------------

        chat_record = ChatHistory(

            session_id=session_id,

            user_message=user_message,

            ai_response=ai_response
        )

        db.add(chat_record)

        session.updated_at = datetime.utcnow()

        db.commit()

        db.refresh(chat_record)

        # ---------------------------------------------------
        # Return
        # ---------------------------------------------------

        return {

            "response": ai_response,

            "session_id": session_id,

            "chat_id": chat_record.id
        }

    except Exception as error:

        print(
            "Gemini API Error:",
            error
        )

        db.rollback()

        error_response = (
            '{"related_to_government_service":false,'
            '"service_name":"",'
            '"recommendation":"Sorry, I could not process your request.",'
            '"why":"The AI service returned an error.",'
            '"documents":[],'
            '"steps":[],'
            '"important_note":"Please try again later.",'
            '"disclaimer":"GovNavigator is an independent prototype."}'
        )

        return {

            "response": error_response,

            "session_id": session_id
        }


# =========================================================
# CREATE / UPDATE USER SESSION
# =========================================================

@app.post("/api/session")
def create_session(
    request: SessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session_id = request.session_id.strip()

    if not session_id:

        raise HTTPException(
            status_code=400,
            detail="session_id cannot be empty."
        )

    # -------------------------------------------------------
    # Existing session
    # -------------------------------------------------------

    existing_session = (
        db.query(UserSession)
        .filter(
            UserSession.session_id == session_id
        )
        .first()
    )

    if existing_session:

        if request.selected_state is not None:

            existing_session.selected_state = (
                request.selected_state
            )

        if request.last_service is not None:

            existing_session.last_service = (
                request.last_service
            )

        existing_session.updated_at = datetime.utcnow()

        db.commit()

        db.refresh(existing_session)

        return {

            "status": "updated",

            "session_id":
                existing_session.session_id,

            "selected_state":
                existing_session.selected_state,

            "last_service":
                existing_session.last_service,

            "created_at":
                existing_session.created_at,

            "updated_at":
                existing_session.updated_at
        }

    # -------------------------------------------------------
    # Create new session
    # -------------------------------------------------------

    new_session = UserSession(

        session_id=session_id,

        selected_state=request.selected_state,

        last_service=request.last_service
    )

    db.add(new_session)

    db.commit()

    db.refresh(new_session)

    return {

        "status": "created",

        "session_id":
            new_session.session_id,

        "selected_state":
            new_session.selected_state,

        "last_service":
            new_session.last_service,

        "created_at":
            new_session.created_at,

        "updated_at":
            new_session.updated_at
    }


# =========================================================
# GET USER SESSION + CHAT HISTORY
# =========================================================

@app.get("/api/session/{session_id}")
def get_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = (
        db.query(UserSession)
        .filter(
            UserSession.session_id == session_id
        )
        .first()
    )

    if not session:

        raise HTTPException(
            status_code=404,
            detail="Session not found."
        )

    # -------------------------------------------------------
    # Chat history
    # -------------------------------------------------------

    chats = (
        db.query(ChatHistory)
        .filter(
            ChatHistory.session_id == session_id
        )
        .order_by(
            ChatHistory.created_at.asc()
        )
        .all()
    )

    return {

        "session_id":
            session.session_id,

        "selected_state":
            session.selected_state,

        "last_service":
            session.last_service,

        "created_at":
            session.created_at,

        "updated_at":
            session.updated_at,

        "chat_history": [

            {

                "id":
                    chat.id,

                "user_message":
                    chat.user_message,

                "ai_response":
                    chat.ai_response,

                "created_at":
                    chat.created_at
            }

            for chat in chats
        ]
    }


# ============================================================
# SEARCH ANALYTICS
# ============================================================
  # ============================================================
# SEARCH ANALYTICS
# CURRENT USER ONLY
# ============================================================

@app.get("/api/analytics/search-summary")
def get_search_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:

        # ----------------------------------------------------
        # Base query — only current user's searches
        # ----------------------------------------------------

        user_searches = (
            db.query(SearchHistory)
            .filter(
                SearchHistory.user_id == current_user.id
            )
        )

        # ----------------------------------------------------
        # Total searches
        # ----------------------------------------------------

        total_searches = (
            user_searches.count()
        )

        # ----------------------------------------------------
        # Successful searches
        # ----------------------------------------------------

        successful_searches = (
            db.query(func.count(SearchHistory.id))
            .filter(
                SearchHistory.user_id == current_user.id,
                SearchHistory.matched_service.isnot(None)
            )
            .scalar()
        ) or 0

        # ----------------------------------------------------
        # Failed searches
        # ----------------------------------------------------

        failed_searches = (
            total_searches - successful_searches
        )

        # Safety
        if failed_searches < 0:
            failed_searches = 0

        # ----------------------------------------------------
        # Success rate
        # ----------------------------------------------------

        if total_searches > 0:

            success_rate = round(
                (
                    successful_searches
                    / total_searches
                ) * 100,
                2
            )

        else:

            success_rate = 0

        # ----------------------------------------------------
        # Average match score
        # Only current user's successful searches
        # ----------------------------------------------------

        average_match_score = (
            db.query(
                func.avg(
                    SearchHistory.match_score
                )
            )
            .filter(
                SearchHistory.user_id == current_user.id,
                SearchHistory.match_score.isnot(None),
                SearchHistory.matched_service.isnot(None)
            )
            .scalar()
        )

        if average_match_score is not None:

            average_match_score = round(
                min(
                    float(average_match_score),
                    100
                ),
                2
            )

        else:

            average_match_score = 0

        # ----------------------------------------------------
        # Top searched queries
        # ----------------------------------------------------

        top_queries = (
            db.query(
                SearchHistory.search_query,
                func.count(
                    SearchHistory.id
                ).label("count")
            )
            .filter(
                SearchHistory.user_id == current_user.id,
                SearchHistory.search_query.isnot(None)
            )
            .group_by(
                SearchHistory.search_query
            )
            .order_by(
                func.count(
                    SearchHistory.id
                ).desc()
            )
            .limit(10)
            .all()
        )

        # ----------------------------------------------------
        # Top matched services
        # ----------------------------------------------------

        top_services = (
            db.query(
                SearchHistory.matched_service,
                func.count(
                    SearchHistory.id
                ).label("count")
            )
            .filter(
                SearchHistory.user_id == current_user.id,
                SearchHistory.matched_service.isnot(None)
            )
            .group_by(
                SearchHistory.matched_service
            )
            .order_by(
                func.count(
                    SearchHistory.id
                ).desc()
            )
            .limit(10)
            .all()
        )

        # ----------------------------------------------------
        # Top selected states
        # ----------------------------------------------------

        top_states = (
            db.query(
                SearchHistory.selected_state,
                func.count(
                    SearchHistory.id
                ).label("count")
            )
            .filter(
                SearchHistory.user_id == current_user.id,
                SearchHistory.selected_state.isnot(None)
            )
            .group_by(
                SearchHistory.selected_state
            )
            .order_by(
                func.count(
                    SearchHistory.id
                ).desc()
            )
            .limit(10)
            .all()
        )

        # ----------------------------------------------------
        # Recent searches
        # ----------------------------------------------------

        recent_searches = (
            db.query(SearchHistory)
            .filter(
                SearchHistory.user_id == current_user.id
            )
            .order_by(
                SearchHistory.created_at.desc()
            )
            .limit(10)
            .all()
        )

        # ----------------------------------------------------
        # Return analytics
        # ----------------------------------------------------

        return {

            "summary": {

                "total_searches":
                    total_searches,

                "successful_searches":
                    successful_searches,

                "failed_searches":
                    failed_searches,

                "success_rate":
                    success_rate,

                "average_match_score":
                    average_match_score
            },

            "top_queries": [

                {
                    "query": query,
                    "count": count
                }

                for query, count in top_queries
            ],

            "top_services": [

                {
                    "service": service,
                    "count": count
                }

                for service, count in top_services
            ],

            "top_states": [

                {
                    "state": state,
                    "count": count
                }

                for state, count in top_states
            ],

            "recent_searches": [

                {
                    "id":
                        record.id,

                    "query":
                        record.search_query,

                    "service":
                        record.matched_service,

                    "state":
                        record.selected_state,

                    "match_score":
                        min(
                            record.match_score,
                            100
                        )
                        if record.match_score is not None
                        else 0,

                    "created_at":
                        record.created_at
                }

                for record in recent_searches
            ]
        }

    except Exception as error:

        print(
            "Search analytics error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to generate search analytics"
        )

# ============================================================
# FAVORITES / SAVED SERVICES
# CURRENT USER ONLY
# ============================================================

@app.get("/api/favorites")
def get_favorites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    favorites = (
        db.query(FavoriteService, Service)
        .join(Service, FavoriteService.service_id == Service.id)
        .filter(FavoriteService.user_id == current_user.id)
        .order_by(FavoriteService.created_at.desc())
        .all()
    )

    return [
        {
            "id": service.id,
            "name": service.name,
            "category": service.category,
            "description": service.description,
            "eligibility": service.eligibility,
            "documents": service.documents,
            "steps": service.steps,
            "fees": service.fees,
            "processing_time": service.processing_time,
            "official_portal_name": service.official_portal_name,
            "official_portal_url": service.official_portal_url,
            "state_id": service.state_id,
            "favorite_id": favorite.id,
            "saved_at": favorite.created_at.isoformat() if favorite.created_at else None,
        }
        for favorite, service in favorites
    ]


@app.post("/api/favorites")
def add_favorite(
    request: FavoriteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = db.query(Service).filter(Service.id == request.service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Government service not found.")

    existing = (
        db.query(FavoriteService)
        .filter(
            FavoriteService.user_id == current_user.id,
            FavoriteService.service_id == service.id,
        )
        .first()
    )

    if existing:
        return {
            "message": "Service already saved.",
            "favorite_id": existing.id,
            "service_id": service.id,
            "saved": True,
        }

    favorite = FavoriteService(user_id=current_user.id, service_id=service.id)
    db.add(favorite)
    db.commit()
    db.refresh(favorite)

    return {
        "message": "Service saved successfully.",
        "favorite_id": favorite.id,
        "service_id": service.id,
        "saved": True,
    }


@app.delete("/api/favorites/{service_id}")
def remove_favorite(
    service_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    favorite = (
        db.query(FavoriteService)
        .filter(
            FavoriteService.user_id == current_user.id,
            FavoriteService.service_id == service_id,
        )
        .first()
    )

    if not favorite:
        raise HTTPException(status_code=404, detail="Service is not saved in your favorites.")

    db.delete(favorite)
    db.commit()

    return {
        "message": "Service removed from saved services.",
        "service_id": service_id,
        "saved": False,
    }


@app.get("/api/favorites/{service_id}")
def check_favorite(
    service_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    favorite = (
        db.query(FavoriteService)
        .filter(
            FavoriteService.user_id == current_user.id,
            FavoriteService.service_id == service_id,
        )
        .first()
    )

    return {"service_id": service_id, "saved": favorite is not None}

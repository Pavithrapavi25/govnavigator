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
import re
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

APP_ENV = os.getenv(
    "APP_ENV",
    "development"
).strip().lower()

JWT_SECRET = os.getenv(
    "JWT_SECRET",
    ""
).strip()

# Never use the development fallback in production.
if APP_ENV == "production" and not JWT_SECRET:
    raise RuntimeError(
        "JWT_SECRET is required when APP_ENV=production."
    )

if not JWT_SECRET:
    JWT_SECRET = (
        "govnavigator-development-secret-change-in-production"
    )

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
    allow_methods=[
        "GET",
        "POST",
        "DELETE",
        "OPTIONS"
    ],
    allow_headers=[
        "Authorization",
        "Content-Type"
    ],
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
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000
    )
    session_id: str = Field(
        ...,
        min_length=1,
        max_length=100
    )


class SessionRequest(BaseModel):
    session_id: str = Field(
        ...,
        min_length=1,
        max_length=100
    )

    selected_state: str | None = Field(
        default=None,
        max_length=100
    )

    last_service: str | None = Field(
        default=None,
        max_length=200
    )


class RegisterRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=100
    )

    email: str = Field(
        ...,
        min_length=3,
        max_length=150
    )

    password: str = Field(
        ...,
        min_length=8,
        max_length=128
    )


class LoginRequest(BaseModel):
    email: str = Field(
        ...,
        min_length=3,
        max_length=150
    )

    password: str = Field(
        ...,
        min_length=1,
        max_length=128
    )


class FavoriteRequest(BaseModel):
    service_id: int


# =========================================================
# HEALTH CHECK
# =========================================================

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
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
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
        .filter(
            User.id == user_id
        )
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

    chat_count = (
        db.query(ChatHistory).count()
    )

    state_count = (
        db.query(State).count()
    )

    service_count = (
        db.query(Service).count()
    )

    search_count = (
        db.query(SearchHistory).count()
    )

    session_count = (
        db.query(UserSession).count()
    )

    return {

        "status": "connected",

        "database": "SQLite",

        "chat_history_records":
            chat_count,

        "states":
            state_count,

        "services":
            service_count,

        "search_history_records":
            search_count,

        "user_sessions":
            session_count
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

    email = (
        request.email
        .strip()
        .lower()
    )

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

    if (
        "@" not in email
        or "." not in email.rsplit(
            "@",
            1
        )[-1]
    ):

        raise HTTPException(
            status_code=400,
            detail="Please enter a valid email address."
        )

    existing_user = (
        db.query(User)
        .filter(
            User.email == email
        )
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

        "message":
            "Registration successful",

        "user": {

            "id":
                user.id,

            "name":
                user.name,

            "email":
                user.email
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

    email = (
        request.email
        .strip()
        .lower()
    )

    user = (
        db.query(User)
        .filter(
            User.email == email
        )
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
        + timedelta(
            minutes=JWT_EXPIRE_MINUTES
        )
    )

    payload = {

        "sub":
            str(user.id),

        "email":
            user.email,

        "exp":
            expires_at
    }

    token = jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )

    return {

        "message":
            "Login successful",

        "token":
            token,

        "token_type":
            "bearer",

        "user": {

            "id":
                user.id,

            "name":
                user.name,

            "email":
                user.email
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
        .order_by(
            State.name.asc()
        )
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
        .filter(
            State.id == state_id
        )
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
        .order_by(
            Service.name.asc()
        )
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
        .filter(
            Service.id == service_id
        )
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
        .filter(
            State.id == state_id
        )
        .first()
    )

    if not state:

        raise HTTPException(
            status_code=404,
            detail="State or Union Territory not found."
        )

    services = (
        db.query(Service)
        .filter(
            Service.state_id == state_id
        )
        .order_by(
            Service.name.asc()
        )
        .all()
    )

    return services


# ============================================================
# INTELLIGENT SEARCH CONFIGURATION
# ============================================================

SEARCH_SYNONYMS = {

    "pan": [
        "pan",
        "pan card",
        "permanent account number",
        "tax card",
        "income tax card",
    ],

    "aadhaar": [
        "aadhaar",
        "aadhar",
        "aadhaar card",
        "aadhar card",
        "uid",
        "uidai",
        "identity",
        "biometric",
    ],

    "passport": [
        "passport",
        "passport card",
        "travel document",
        "international travel",
        "passport renewal",
        "passport application",
    ],

    "voter": [
        "voter",
        "voter id",
        "voter id card",
        "voter card",
        "election",
        "electoral",
        "electoral roll",
        "epic",
    ],

    "driving": [
        "driving",
        "driving licence",
        "driving license",
        "driving licence card",
        "driving license card",
        "dl",
        "learner licence",
        "learner license",
        "learner permit",
    ],

    "vehicle": [
        "vehicle",
        "vehicle registration",
        "registration certificate",
        "rc",
        "rc book",
        "car registration",
        "bike registration",
        "motor vehicle",
    ],

    "income": [
        "income",
        "income certificate",
        "family income",
        "family income certificate",
        "earnings",
        "income proof",
        "proof of income",
        "salary proof",
        "income verification",
    ],

    "caste": [
        "caste",
        "caste certificate",
        "community",
        "community certificate",
        "social category",
        "social category certificate",
        "scheduled caste",
        "scheduled tribe",
        "sc certificate",
        "st certificate",
        "obc certificate",
    ],

    "birth": [
        "birth",
        "birth certificate",
        "birth registration",
        "newborn",
        "new born",
        "baby birth",
        "child birth",
    ],

    "death": [
        "death",
        "death certificate",
        "death registration",
        "deceased",
        "death record",
    ],

    "schemes": [
        "scheme",
        "government scheme",
        "government benefits",
        "welfare",
        "subsidy",
        "benefits",
        "financial assistance",
        "government assistance",
    ],

    "national": [
        "government service",
        "national service",
        "central government",
        "online government service",
    ],
}


# ============================================================
# SEARCH INTENT TARGET TERMS
# ============================================================

SEARCH_INTENT_TARGETS = {

    "pan": [
        "pan",
        "permanent account",
        "tax"
    ],

    "aadhaar": [
        "aadhaar",
        "aadhar",
        "uid",
        "identity"
    ],

    "passport": [
        "passport",
        "travel"
    ],

    "voter": [
        "voter",
        "electoral",
        "election",
        "epic"
    ],

    "driving": [
        "driving",
        "licence",
        "license",
        "learner"
    ],

    "vehicle": [
        "vehicle",
        "registration",
        "motor"
    ],

    "income": [
        "income",
        "earnings",
        "family income"
    ],

    "caste": [
        "caste",
        "community",
        "social category",
        "scheduled caste",
        "scheduled tribe",
        "obc"
    ],

    "birth": [
        "birth",
        "newborn",
        "child"
    ],

    "death": [
        "death",
        "deceased"
    ],

    "schemes": [
        "scheme",
        "benefit",
        "welfare",
        "subsidy",
        "assistance"
    ],

    "national": [
        "government service",
        "national service",
        "central government"
    ],
}


# ============================================================
# SEARCH FILLER WORDS
# ============================================================

SEARCH_STOP_WORDS = {

    "i",
    "me",
    "my",
    "we",
    "our",
    "the",
    "a",
    "an",
    "am",
    "is",
    "are",
    "was",
    "were",
    "want",
    "need",
    "needs",
    "needed",
    "looking",
    "look",
    "for",
    "please",
    "can",
    "could",
    "would",
    "help",
    "helping",
    "get",
    "getting",
    "give",
    "show",
    "tell",
    "how",
    "to",
    "apply",
    "application",
    "obtain",
    "obtain",
    "make",
    "myself",
    "certificate",
    "card",
    "document",
    "documents",
    "proof",
    "government",
    "govt",
    "online",
}


# ============================================================
# NORMALIZE SEARCH TEXT
# ============================================================

def normalize_search_text(text):
    """
    Convert arbitrary search text into a clean
    lowercase searchable representation.
    """

    if not text:
        return ""

    text = str(text).lower()

    # Replace punctuation with spaces.
    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text
    )

    # Collapse repeated spaces.
    text = " ".join(
        text.split()
    )

    return text


# ============================================================
# SEARCH TOKENIZATION
# ============================================================

def get_search_words(text):
    """
    Return useful words from a search query.
    """

    normalized = normalize_search_text(text)

    words = normalized.split()

    return {
        word
        for word in words
        if (
            len(word) >= 2
            and word not in SEARCH_STOP_WORDS
        )
    }


# ============================================================
# DETECT SEARCH INTENTS
# ============================================================

def detect_search_intents(query):
    """
    Detect the user's intended government service category.

    Example:

    "I need proof of my family income"

    -> ["income"]

    "I want a caste certificate"

    -> ["caste"]
    """

    normalized_query = normalize_search_text(
        query
    )

    query_words = set(
        normalized_query.split()
    )

    detected = []

    for service_key, synonyms in SEARCH_SYNONYMS.items():

        for synonym in synonyms:

            normalized_synonym = (
                normalize_search_text(
                    synonym
                )
            )

            if not normalized_synonym:
                continue

            # Strong phrase match.
            if (
                normalized_synonym
                in normalized_query
            ):
                detected.append(
                    service_key
                )
                break

            # Word-level match.
            synonym_words = set(
                normalized_synonym.split()
            )

            if synonym_words.intersection(
                query_words
            ):
                detected.append(
                    service_key
                )
                break

    return list(
        dict.fromkeys(detected)
    )


# ============================================================
# CHECK WHETHER SERVICE BELONGS TO INTENT
# ============================================================

def service_matches_intent(
    service,
    service_key
):
    """
    Determine whether a database service belongs
    to a detected search intent.

    This is intentionally based primarily on the
    actual service name, category and description.
    """

    target_terms = (
        SEARCH_INTENT_TARGETS.get(
            service_key,
            []
        )
    )

    if not target_terms:
        return False

    service_name = normalize_search_text(
        service.name
    )

    category = normalize_search_text(
        service.category
    )

    description = normalize_search_text(
        service.description
    )

    combined = " ".join([
        service_name,
        category,
        description,
    ])

    for target in target_terms:

        normalized_target = (
            normalize_search_text(
                target
            )
        )

        if not normalized_target:
            continue

        if normalized_target in combined:
            return True

    return False


# ============================================================
# SERVICE SEARCH SCORE
# ============================================================

def calculate_service_search_score(
    query,
    service
):
    """
    Calculate a robust relevance score.

    Scoring includes:

    1. Exact service name
    2. Service name phrase match
    3. Individual service-name words
    4. Category words
    5. Description words
    6. Intent/synonym matching
    7. Strong intent-to-service matching
    8. Multi-word query matching

    Final score is capped at 100.
    """

    normalized_query = normalize_search_text(
        query
    )

    if not normalized_query:
        return 0

    query_words = get_search_words(
        normalized_query
    )

    all_query_words = set(
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

    steps = normalize_search_text(
        service.steps
    )

    searchable_text = " ".join([
        service_name,
        category,
        description,
        eligibility,
        documents,
        steps,
    ])

    searchable_words = set(
        searchable_text.split()
    )

    score = 0

    # ========================================================
    # 1. EXACT SERVICE NAME
    # ========================================================

    if normalized_query == service_name:

        score += 100

    elif (
        service_name
        and normalized_query
        in service_name
    ):

        score += 80

    elif (
        service_name
        and service_name
        in normalized_query
    ):

        score += 70

    # ========================================================
    # 2. SERVICE NAME WORD MATCH
    # ========================================================

    service_name_words = set(
        service_name.split()
    )

    for word in query_words:

        if word in service_name_words:

            score += 25

    # ========================================================
    # 3. CATEGORY MATCH
    # ========================================================

    category_words = set(
        category.split()
    )

    for word in query_words:

        if word in category_words:

            score += 15

    # ========================================================
    # 4. DESCRIPTION MATCH
    # ========================================================

    for word in query_words:

        if word in searchable_words:

            score += 5

    # ========================================================
    # 5. DETECT USER INTENT
    # ========================================================

    detected_intents = detect_search_intents(
        normalized_query
    )

    # ========================================================
    # 6. STRONG INTENT MATCH
    # ========================================================

    for service_key in detected_intents:

        if service_matches_intent(
            service,
            service_key
        ):

            # This is the important improvement.
            #
            # Example:
            #
            # Query:
            # "I need proof of my family income"
            #
            # Intent:
            # income
            #
            # Service:
            # Income Certificate
            #
            # Therefore this service receives
            # a strong relevance score.

            score += 60

            # Additional bonus when service name
            # itself clearly contains the intent.

            if any(
                normalize_search_text(term)
                in service_name
                for term in
                SEARCH_INTENT_TARGETS.get(
                    service_key,
                    []
                )
            ):

                score += 20

    # ========================================================
    # 7. SYNONYM MATCH
    # ========================================================

    for service_key in detected_intents:

        synonyms = SEARCH_SYNONYMS.get(
            service_key,
            []
        )

        for synonym in synonyms:

            normalized_synonym = (
                normalize_search_text(
                    synonym
                )
            )

            if not normalized_synonym:
                continue

            if (
                normalized_synonym
                in normalized_query
            ):

                if service_matches_intent(
                    service,
                    service_key
                ):

                    score += 20

                break

    # ========================================================
    # 8. MULTI-WORD QUERY MATCH
    # ========================================================

    if len(query_words) >= 2:

        matched_words = sum(
            1
            for word in query_words
            if word in searchable_words
        )

        if (
            matched_words
            == len(query_words)
        ):

            score += 30

        elif matched_words >= 3:

            score += 20

        elif matched_words >= 2:

            score += 10

    # ========================================================
    # 9. IMPORTANT WORD PAIRS
    # ========================================================

    # Certificate-related searches.
    if (
        "certificate"
        in all_query_words
    ):

        if (
            "certificate"
            in service_name
        ):

            score += 15

    # Card-related searches.
    if (
        "card"
        in all_query_words
    ):

        if (
            "card"
            in service_name
        ):

            score += 15

    # Registration-related searches.
    if (
        "registration"
        in all_query_words
    ):

        if (
            "registration"
            in service_name
            or
            "registration"
            in category
        ):

            score += 15

    # ========================================================
    # 10. FINAL CAP
    # ========================================================

    return min(
        int(score),
        100
    )


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
    Save a user's search.

    Successful searches have:
        matched_service != None
        match_score > 0

    Failed searches have:
        matched_service = None
        match_score = 0
    """

    try:

        if match_score is not None:

            match_score = min(
                int(match_score),
                100
            )

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
    current_user: User = Depends(
        get_current_user
    )
):
    """
    Intelligent government-service search.

    Supports:

    - Natural language queries
    - Exact service names
    - Keywords
    - Categories
    - Descriptions
    - Synonyms
    - Service intent detection
    - State filtering
    - National services
    - Relevance scoring
    - Search history tracking
    """

    query = q.strip()

    # ========================================================
    # EMPTY QUERY
    # ========================================================

    if not query:

        return []

    # ========================================================
    # STATE VALIDATION
    # ========================================================

    selected_state_name = None

    if state_id is not None:

        state = (
            db.query(State)
            .filter(
                State.id == state_id
            )
            .first()
        )

        if not state:

            raise HTTPException(
                status_code=404,
                detail="State or Union Territory not found."
            )

        selected_state_name = state.name

    # ========================================================
    # GET SERVICES
    # ========================================================

    services_query = db.query(Service)

    # When a state is selected:
    #
    # - Include services for that state
    # - Include national services
    #
    # National services have state_id = NULL.

    if state_id is not None:

        services_query = (
            services_query
            .filter(
                or_(
                    Service.state_id == state_id,
                    Service.state_id.is_(None)
                )
            )
        )

    services = (
        services_query
        .all()
    )

    # ========================================================
    # DETECT USER INTENT
    # ========================================================

    detected_intents = detect_search_intents(
        query
    )

    print(
        "Search query:",
        query
    )

    print(
        "Detected intents:",
        detected_intents
    )

    # ========================================================
    # CALCULATE SERVICE SCORES
    # ========================================================

    results = []

    for service in services:

        score = calculate_service_search_score(
            query,
            service
        )

        score = min(
            score,
            100
        )

        # Ignore extremely weak matches.
        if score < 10:

            continue

        results.append({

            "id":
                service.id,

            "name":
                service.name,

            "category":
                service.category,

            "description":
                service.description,

            "eligibility":
                service.eligibility,

            "documents":
                service.documents,

            "steps":
                service.steps,

            "fees":
                service.fees,

            "processing_time":
                service.processing_time,

            "official_portal_name":
                service.official_portal_name,

            "official_portal_url":
                service.official_portal_url,

            "state_id":
                service.state_id,

            "match_score":
                score,
        })

    # ========================================================
    # SORT RESULTS
    # ========================================================

    results.sort(
        key=lambda item:
            item["match_score"],
        reverse=True
    )

    # ========================================================
    # TOP 5
    # ========================================================

    top_results = results[:5]

    # ========================================================
    # SEARCH HISTORY
    # ========================================================

    if top_results:

        best_result = top_results[0]

        print(
            "Search success:",
            best_result["name"],
            "score:",
            best_result["match_score"]
        )

        save_search_history(

            db=db,

            search_query=query,

            selected_state=
                selected_state_name,

            matched_service=
                best_result["name"],

            match_score=
                best_result["match_score"],

            user_id=
                current_user.id
        )

    else:

        print(
            "Search failed:",
            query
        )

        save_search_history(

            db=db,

            search_query=query,

            selected_state=
                selected_state_name,

            matched_service=None,

            match_score=0,

            user_id=
                current_user.id
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
    current_user: User = Depends(
        get_current_user
    )
):

    search_query = (
        request.search_query
        .strip()
    )

    if not search_query:

        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty."
        )

    record = SearchHistory(

        user_id=
            current_user.id,

        search_query=
            search_query,

        selected_state=
            request.selected_state
    )

    db.add(record)

    db.commit()

    db.refresh(record)

    return {

        "search_query":
            record.search_query,

        "matched_service":
            record.matched_service,

        "selected_state":
            record.selected_state,

        "match_score":
            record.match_score
    }


# =========================================================
# GET SEARCH HISTORY
# CURRENT USER ONLY
# =========================================================

@app.get("/api/search-history")
def get_search_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    records = (
        db.query(SearchHistory)
        .filter(
            SearchHistory.user_id
            == current_user.id
        )
        .order_by(
            SearchHistory.created_at.desc()
        )
        .all()
    )

    return [

        {

            "id":
                record.id,

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
                )
                if record.match_score
                is not None
                else 0,

            "created_at":
                record.created_at
        }

        for record in records
    ]


# =========================================================
# DELETE ONE SEARCH HISTORY ITEM
# CURRENT USER ONLY
# =========================================================

@app.delete(
    "/api/search-history/{history_id}"
)
def delete_search_history(
    history_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    record = (
        db.query(SearchHistory)
        .filter(
            SearchHistory.id
            == history_id,

            SearchHistory.user_id
            == current_user.id
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

        "message":
            "Search history item deleted.",

        "id":
            history_id
    }


# =========================================================
# DELETE ALL SEARCH HISTORY
# CURRENT USER ONLY
# =========================================================

@app.delete("/api/search-history")
def clear_search_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    deleted_count = (
        db.query(SearchHistory)
        .filter(
            SearchHistory.user_id
            == current_user.id
        )
        .delete(
            synchronize_session=False
        )
    )

    db.commit()

    return {

        "message":
            "Search history cleared.",

        "deleted_count":
            deleted_count
    }


# =========================================================
# GET RECENT SEARCH HISTORY
# CURRENT USER ONLY
# =========================================================

@app.get(
    "/api/search-history/recent"
)
def get_recent_search_history(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    if limit < 1:

        limit = 1

    if limit > 50:

        limit = 50

    records = (
        db.query(SearchHistory)
        .filter(
            SearchHistory.user_id
            == current_user.id
        )
        .order_by(
            SearchHistory.created_at.desc()
        )
        .limit(limit)
        .all()
    )

    return [

        {

            "id":
                record.id,

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
                )
                if record.match_score
                is not None
                else 0,

            "created_at":
                record.created_at
        }

        for record in records
    ]


# =========================================================
# CHAT HISTORY
# =========================================================

@app.get("/api/chat-history")
def get_chat_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
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

            "id":
                record.id,

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

@app.get(
    "/api/chat-history/{session_id}"
)
def get_session_chat_history(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    session = (
        db.query(UserSession)
        .filter(
            UserSession.session_id
            == session_id
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
            ChatHistory.session_id
            == session_id
        )
        .order_by(
            ChatHistory.created_at.asc()
        )
        .all()
    )

    return [

        {

            "id":
                record.id,

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
    current_user: User = Depends(
        get_current_user
    )
):

    user_message = (
        request.message
        .strip()
    )

    session_id = (
        request.session_id
        .strip()
    )

    if len(user_message) > 2000:

        raise HTTPException(
            status_code=400,
            detail=(
                "Message is too long. "
                "Maximum 2000 characters."
            )
        )

    if len(session_id) > 100:

        raise HTTPException(
            status_code=400,
            detail="Invalid session ID."
        )

    if not session_id:

        raise HTTPException(
            status_code=400,
            detail="session_id is required."
        )

    # ======================================================
    # CHECK SESSION
    # ======================================================

    session = (
        db.query(UserSession)
        .filter(
            UserSession.session_id
            == session_id
        )
        .first()
    )

    if not session:

        raise HTTPException(
            status_code=404,
            detail=(
                "Session not found. "
                "Please create a session first."
            )
        )

    # ======================================================
    # EMPTY MESSAGE
    # ======================================================

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

            "response":
                empty_response,

            "session_id":
                session_id
        }

    # ======================================================
    # UPDATE SESSION
    # ======================================================

    session.updated_at = datetime.utcnow()

    # ======================================================
    # GEMINI PROMPT
    # ======================================================

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

    # ======================================================
    # GEMINI RESPONSE SCHEMA
    # ======================================================

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

    # ======================================================
    # CALL GEMINI
    # ======================================================

    try:

        response = client.models.generate_content(

            model="gemini-3.6-flash",

            contents=prompt,

            config=types.GenerateContentConfig(

                response_mime_type=
                    "application/json",

                response_schema=
                    response_schema,

                temperature=0.2,
            ),
        )

        ai_response = response.text

        # ==================================================
        # FALLBACK
        # ==================================================

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

        # ==================================================
        # SAVE CHAT
        # ==================================================

        chat_record = ChatHistory(

            session_id=
                session_id,

            user_message=
                user_message,

            ai_response=
                ai_response
        )

        db.add(chat_record)

        session.updated_at = datetime.utcnow()

        db.commit()

        db.refresh(chat_record)

        # ==================================================
        # RETURN
        # ==================================================

        return {

            "response":
                ai_response,

            "session_id":
                session_id,

            "chat_id":
                chat_record.id
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

            "response":
                error_response,

            "session_id":
                session_id
        }


# =========================================================
# CREATE / UPDATE USER SESSION
# =========================================================

@app.post("/api/session")
def create_session(
    request: SessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    session_id = (
        request.session_id
        .strip()
    )

    if not session_id:

        raise HTTPException(
            status_code=400,
            detail="session_id cannot be empty."
        )

    # ======================================================
    # EXISTING SESSION
    # ======================================================

    existing_session = (
        db.query(UserSession)
        .filter(
            UserSession.session_id
            == session_id
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

        existing_session.updated_at = (
            datetime.utcnow()
        )

        db.commit()

        db.refresh(
            existing_session
        )

        return {

            "status":
                "updated",

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

    # ======================================================
    # CREATE NEW SESSION
    # ======================================================

    new_session = UserSession(

        session_id=
            session_id,

        selected_state=
            request.selected_state,

        last_service=
            request.last_service
    )

    db.add(new_session)

    db.commit()

    db.refresh(
        new_session
    )

    return {

        "status":
            "created",

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

@app.get(
    "/api/session/{session_id}"
)
def get_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    session = (
        db.query(UserSession)
        .filter(
            UserSession.session_id
            == session_id
        )
        .first()
    )

    if not session:

        raise HTTPException(
            status_code=404,
            detail="Session not found."
        )

    # ======================================================
    # CHAT HISTORY
    # ======================================================

    chats = (
        db.query(ChatHistory)
        .filter(
            ChatHistory.session_id
            == session_id
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
# CURRENT USER ONLY
# ============================================================

@app.get(
    "/api/analytics/search-summary"
)
def get_search_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    try:

        # ====================================================
        # BASE USER SEARCH QUERY
        # ====================================================

        user_searches = (
            db.query(SearchHistory)
            .filter(
                SearchHistory.user_id
                == current_user.id
            )
        )

        # ====================================================
        # TOTAL SEARCHES
        # ====================================================

        total_searches = (
            user_searches.count()
        )

        # ====================================================
        # SUCCESSFUL SEARCHES
        # ====================================================

        successful_searches = (
            db.query(
                func.count(
                    SearchHistory.id
                )
            )
            .filter(

                SearchHistory.user_id
                == current_user.id,

                SearchHistory.matched_service
                .isnot(None)
            )
            .scalar()
        ) or 0

        # ====================================================
        # FAILED SEARCHES
        # ====================================================

        failed_searches = (
            total_searches
            - successful_searches
        )

        if failed_searches < 0:

            failed_searches = 0

        # ====================================================
        # SUCCESS RATE
        # ====================================================

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

        # ====================================================
        # AVERAGE MATCH SCORE
        # ====================================================

        average_match_score = (
            db.query(
                func.avg(
                    SearchHistory.match_score
                )
            )
            .filter(

                SearchHistory.user_id
                == current_user.id,

                SearchHistory.match_score
                .isnot(None),

                SearchHistory.matched_service
                .isnot(None)
            )
            .scalar()
        )

        if average_match_score is not None:

            average_match_score = round(

                min(
                    float(
                        average_match_score
                    ),
                    100
                ),

                2
            )

        else:

            average_match_score = 0

        # ====================================================
        # TOP QUERIES
        # ====================================================

        top_queries = (
            db.query(

                SearchHistory.search_query,

                func.count(
                    SearchHistory.id
                ).label("count")
            )
            .filter(

                SearchHistory.user_id
                == current_user.id,

                SearchHistory.search_query
                .isnot(None)
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

        # ====================================================
        # TOP SERVICES
        # ====================================================

        top_services = (
            db.query(

                SearchHistory.matched_service,

                func.count(
                    SearchHistory.id
                ).label("count")
            )
            .filter(

                SearchHistory.user_id
                == current_user.id,

                SearchHistory.matched_service
                .isnot(None)
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

        # ====================================================
        # TOP STATES
        # ====================================================

        top_states = (
            db.query(

                SearchHistory.selected_state,

                func.count(
                    SearchHistory.id
                ).label("count")
            )
            .filter(

                SearchHistory.user_id
                == current_user.id,

                SearchHistory.selected_state
                .isnot(None)
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

        # ====================================================
        # RECENT SEARCHES
        # ====================================================

        recent_searches = (
            db.query(SearchHistory)
            .filter(

                SearchHistory.user_id
                == current_user.id
            )
            .order_by(
                SearchHistory.created_at.desc()
            )
            .limit(10)
            .all()
        )

        # ====================================================
        # RETURN
        # ====================================================

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

                    "query":
                        query,

                    "count":
                        count
                }

                for query, count
                in top_queries
            ],

            "top_services": [

                {

                    "service":
                        service,

                    "count":
                        count
                }

                for service, count
                in top_services
            ],

            "top_states": [

                {

                    "state":
                        state,

                    "count":
                        count
                }

                for state, count
                in top_states
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
                        if record.match_score
                        is not None
                        else 0,

                    "created_at":
                        record.created_at
                }

                for record
                in recent_searches
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
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    favorites = (
        db.query(
            FavoriteService,
            Service
        )
        .join(
            Service,
            FavoriteService.service_id
            == Service.id
        )
        .filter(
            FavoriteService.user_id
            == current_user.id
        )
        .order_by(
            FavoriteService.created_at.desc()
        )
        .all()
    )

    return [

        {

            "id":
                service.id,

            "name":
                service.name,

            "category":
                service.category,

            "description":
                service.description,

            "eligibility":
                service.eligibility,

            "documents":
                service.documents,

            "steps":
                service.steps,

            "fees":
                service.fees,

            "processing_time":
                service.processing_time,

            "official_portal_name":
                service.official_portal_name,

            "official_portal_url":
                service.official_portal_url,

            "state_id":
                service.state_id,

            "favorite_id":
                favorite.id,

            "saved_at":
                (
                    favorite.created_at.isoformat()
                    if favorite.created_at
                    else None
                ),
        }

        for favorite, service
        in favorites
    ]


# ============================================================
# ADD FAVORITE
# ============================================================

@app.post("/api/favorites")
def add_favorite(
    request: FavoriteRequest,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    service = (
        db.query(Service)
        .filter(
            Service.id
            == request.service_id
        )
        .first()
    )

    if not service:

        raise HTTPException(
            status_code=404,
            detail="Government service not found."
        )

    existing = (
        db.query(FavoriteService)
        .filter(

            FavoriteService.user_id
            == current_user.id,

            FavoriteService.service_id
            == service.id
        )
        .first()
    )

    if existing:

        return {

            "message":
                "Service already saved.",

            "favorite_id":
                existing.id,

            "service_id":
                service.id,

            "saved":
                True
        }

    favorite = FavoriteService(

        user_id=
            current_user.id,

        service_id=
            service.id
    )

    db.add(favorite)

    db.commit()

    db.refresh(favorite)

    return {

        "message":
            "Service saved successfully.",

        "favorite_id":
            favorite.id,

        "service_id":
            service.id,

        "saved":
            True
    }


# ============================================================
# REMOVE FAVORITE
# ============================================================

@app.delete(
    "/api/favorites/{service_id}"
)
def remove_favorite(
    service_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    favorite = (
        db.query(FavoriteService)
        .filter(

            FavoriteService.user_id
            == current_user.id,

            FavoriteService.service_id
            == service_id
        )
        .first()
    )

    if not favorite:

        raise HTTPException(
            status_code=404,
            detail=(
                "Service is not saved "
                "in your favorites."
            )
        )

    db.delete(favorite)

    db.commit()

    return {

        "message":
            "Service removed from saved services.",

        "service_id":
            service_id,

        "saved":
            False
    }


# ============================================================
# CHECK FAVORITE
# ============================================================

@app.get(
    "/api/favorites/{service_id}"
)
def check_favorite(
    service_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    favorite = (
        db.query(FavoriteService)
        .filter(

            FavoriteService.user_id
            == current_user.id,

            FavoriteService.service_id
            == service_id
        )
        .first()
    )

    return {

        "service_id":
            service_id,

        "saved":
            favorite is not None
    }
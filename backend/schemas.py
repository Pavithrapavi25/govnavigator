from pydantic import BaseModel


# =========================================================
# STATE RESPONSE
# =========================================================

class StateResponse(BaseModel):
    id: int
    name: str
    state_type: str

    class Config:
        from_attributes = True


# =========================================================
# SERVICE RESPONSE
# =========================================================

class ServiceResponse(BaseModel):
    id: int
    name: str
    category: str | None = None
    description: str | None = None
    eligibility: str | None = None
    documents: str | None = None
    steps: str | None = None
    fees: str | None = None
    processing_time: str | None = None
    official_portal_name: str | None = None
    official_portal_url: str | None = None
    state_id: int | None = None

    class Config:
        from_attributes = True


# =========================================================
# SEARCH REQUEST
# =========================================================

class SearchRequest(BaseModel):
    search_query: str
    selected_state: str | None = None


# =========================================================
# SEARCH RESPONSE
# =========================================================

class SearchResponse(BaseModel):
    search_query: str
    matched_service: str | None = None
    selected_state: str | None = None
    match_score: int | None = None


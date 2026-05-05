from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ArtifactCreate(BaseModel):
    name: str = Field(..., max_length=300)
    catalog_number: Optional[str] = Field(None, max_length=200)
    quantity: Optional[str] = Field(None, max_length=50)
    region: Optional[str] = Field(None, max_length=100)
    site_name: Optional[str] = Field(None, max_length=300)
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="经度 WGS84")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="纬度 WGS84")
    period_label: Optional[str] = Field(None, max_length=100)
    period_start: Optional[int] = None
    period_end: Optional[int] = None
    culture: Optional[str] = Field(None, max_length=200)
    material: Optional[str] = Field(None, max_length=100)
    production_method: Optional[str] = Field(None, max_length=200)
    artifact_type: Optional[str] = Field(None, max_length=100)
    context_desc: Optional[str] = None
    location_desc: Optional[str] = None
    source_reference: Optional[str] = None
    source_pdf: Optional[str] = Field(None, max_length=300)
    image_url: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None


class ArtifactUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=300)
    catalog_number: Optional[str] = Field(None, max_length=200)
    quantity: Optional[str] = Field(None, max_length=50)
    region: Optional[str] = Field(None, max_length=100)
    site_name: Optional[str] = Field(None, max_length=300)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    period_label: Optional[str] = Field(None, max_length=100)
    period_start: Optional[int] = None
    period_end: Optional[int] = None
    culture: Optional[str] = Field(None, max_length=200)
    material: Optional[str] = Field(None, max_length=100)
    production_method: Optional[str] = Field(None, max_length=200)
    artifact_type: Optional[str] = Field(None, max_length=100)
    context_desc: Optional[str] = None
    location_desc: Optional[str] = None
    source_reference: Optional[str] = None
    source_pdf: Optional[str] = Field(None, max_length=300)
    image_url: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None


class ArtifactImageCreate(BaseModel):
    filename: str = Field(..., max_length=300)
    caption: Optional[str] = Field(None, max_length=200)
    sort_order: int = 0


class ArtifactImageResponse(BaseModel):
    id: int
    artifact_id: int
    filename: str
    caption: Optional[str] = None
    sort_order: int = 0
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ArtifactResponse(BaseModel):
    id: int
    name: str
    catalog_number: Optional[str] = None
    quantity: Optional[str] = None
    region: Optional[str] = None
    site_name: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    period_label: Optional[str] = None
    period_start: Optional[int] = None
    period_end: Optional[int] = None
    culture: Optional[str] = None
    material: Optional[str] = None
    production_method: Optional[str] = None
    artifact_type: Optional[str] = None
    context_desc: Optional[str] = None
    location_desc: Optional[str] = None
    source_reference: Optional[str] = None
    source_pdf: Optional[str] = None
    image_url: Optional[str] = None
    notes: Optional[str] = None
    images: list[ArtifactImageResponse] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ArtifactFilter(BaseModel):
    materials: Optional[list[str]] = None
    artifact_types: Optional[list[str]] = None
    cultures: Optional[list[str]] = None
    regions: Optional[list[str]] = None
    period_start_min: Optional[int] = None
    period_start_max: Optional[int] = None
    search: Optional[str] = None
    bbox: Optional[str] = None  # "min_lon,min_lat,max_lon,max_lat"


# ── Auth ────────────────────────────────────────────────────

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6, max_length=100)


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    is_admin: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ── Pending Edit ─────────────────────────────────────────────

class PendingEditCreate(BaseModel):
    artifact_id: Optional[int] = None  # None = new artifact
    action_type: str = Field(..., pattern="^(create|update)$")
    payload: dict


class PendingEditResponse(BaseModel):
    id: int
    user_id: int
    submitter_name: Optional[str] = None
    artifact_id: Optional[int] = None
    artifact_name: Optional[str] = None
    artifact_data: Optional[dict] = None  # current artifact state (for "update" diff)
    action_type: str
    payload: dict
    status: str
    reviewer_id: Optional[int] = None
    reviewer_name: Optional[str] = None
    review_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class RejectBody(BaseModel):
    notes: Optional[str] = None

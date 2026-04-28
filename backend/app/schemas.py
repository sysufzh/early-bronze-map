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
    image_url: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None


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
    image_url: Optional[str] = None
    notes: Optional[str] = None
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

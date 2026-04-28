from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from geoalchemy2.shape import to_shape
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Artifact
from ..schemas import ArtifactCreate, ArtifactResponse, ArtifactUpdate

router = APIRouter(prefix="/api/artifacts", tags=["artifacts"])


def _to_response(a: Artifact) -> ArtifactResponse:
    """Convert ORM object to response, extracting lon/lat from geometry."""
    lon = lat = None
    if a.geom is not None:
        pt = to_shape(a.geom)
        lon, lat = pt.x, pt.y
    return ArtifactResponse(
        id=a.id,
        name=a.name,
        catalog_number=a.catalog_number,
        quantity=a.quantity,
        region=a.region,
        site_name=a.site_name,
        longitude=lon,
        latitude=lat,
        period_label=a.period_label,
        period_start=a.period_start,
        period_end=a.period_end,
        culture=a.culture,
        material=a.material,
        production_method=a.production_method,
        artifact_type=a.artifact_type,
        context_desc=a.context_desc,
        location_desc=a.location_desc,
        source_reference=a.source_reference,
        image_url=a.image_url,
        notes=a.notes,
        created_at=a.created_at,
        updated_at=a.updated_at,
    )


@router.get("/")
def list_artifacts(
    materials: Optional[str] = Query(None, description="材质，逗号分隔"),
    artifact_types: Optional[str] = Query(None, description="器型，逗号分隔"),
    cultures: Optional[str] = Query(None, description="文化，逗号分隔"),
    regions: Optional[str] = Query(None, description="区域，逗号分隔"),
    period_start_min: Optional[int] = Query(None),
    period_start_max: Optional[int] = Query(None),
    search: Optional[str] = Query(None, description="全字段搜索"),
    limit: int = Query(2000, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = select(Artifact)

    if materials:
        mat_list = [m.strip() for m in materials.split(",")]
        stmt = stmt.where(Artifact.material.in_(mat_list))
    if artifact_types:
        type_list = [t.strip() for t in artifact_types.split(",")]
        stmt = stmt.where(Artifact.artifact_type.in_(type_list))
    if cultures:
        cult_list = [c.strip() for c in cultures.split(",")]
        stmt = stmt.where(Artifact.culture.in_(cult_list))
    if regions:
        r_list = [r.strip() for r in regions.split(",")]
        stmt = stmt.where(Artifact.region.in_(r_list))
    if period_start_min is not None:
        stmt = stmt.where(Artifact.period_start >= period_start_min)
    if period_start_max is not None:
        stmt = stmt.where(Artifact.period_start <= period_start_max)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            Artifact.name.ilike(pattern)
            | Artifact.site_name.ilike(pattern)
            | Artifact.culture.ilike(pattern)
            | Artifact.region.ilike(pattern)
            | Artifact.catalog_number.ilike(pattern)
            | Artifact.context_desc.ilike(pattern)
            | Artifact.notes.ilike(pattern)
            | Artifact.source_reference.ilike(pattern)
        )

    stmt = stmt.order_by(Artifact.id).offset(offset).limit(limit)
    results = db.execute(stmt).scalars().all()
    return [_to_response(r) for r in results]


@router.get("/{artifact_id}", response_model=ArtifactResponse)
def get_artifact(artifact_id: int, db: Session = Depends(get_db)):
    a = db.get(Artifact, artifact_id)
    if not a:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return _to_response(a)


@router.post("/", response_model=ArtifactResponse, status_code=201)
def create_artifact(data: ArtifactCreate, db: Session = Depends(get_db)):
    geom = None
    if data.longitude is not None and data.latitude is not None:
        geom = func.ST_SetSRID(
            func.ST_MakePoint(data.longitude, data.latitude), 4326
        )
    a = Artifact(
        name=data.name,
        catalog_number=data.catalog_number,
        quantity=data.quantity,
        region=data.region,
        site_name=data.site_name,
        geom=geom,
        period_label=data.period_label,
        period_start=data.period_start,
        period_end=data.period_end,
        culture=data.culture,
        material=data.material,
        production_method=data.production_method,
        artifact_type=data.artifact_type,
        context_desc=data.context_desc,
        location_desc=data.location_desc,
        source_reference=data.source_reference,
        image_url=data.image_url,
        notes=data.notes,
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return _to_response(a)


@router.put("/{artifact_id}", response_model=ArtifactResponse)
def update_artifact(artifact_id: int, data: ArtifactUpdate, db: Session = Depends(get_db)):
    a = db.get(Artifact, artifact_id)
    if not a:
        raise HTTPException(status_code=404, detail="Artifact not found")

    update_data = data.model_dump(exclude_unset=True)
    lon = update_data.pop("longitude", None)
    lat = update_data.pop("latitude", None)

    for key, value in update_data.items():
        setattr(a, key, value)

    if lon is not None and lat is not None:
        a.geom = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)

    db.commit()
    db.refresh(a)
    return _to_response(a)


@router.delete("/{artifact_id}", status_code=204)
def delete_artifact(artifact_id: int, db: Session = Depends(get_db)):
    a = db.get(Artifact, artifact_id)
    if not a:
        raise HTTPException(status_code=404, detail="Artifact not found")
    db.delete(a)
    db.commit()

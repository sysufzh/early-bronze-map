import os
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from geoalchemy2.shape import to_shape
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from ..config import settings
from ..auth import require_admin
from ..database import get_db
from ..models import Artifact, ArtifactImage, User
from ..schemas import (
    ArtifactCreate, ArtifactResponse, ArtifactUpdate,
    ArtifactImageCreate, ArtifactImageResponse,
)

UPLOAD_DIR = os.path.join(settings.STATIC_DIR, "images", "artifacts")
PDF_DIR = os.path.join(settings.STATIC_DIR, "pdfs")

router = APIRouter(prefix="/api/artifacts", tags=["artifacts"])


def _to_response(a: Artifact) -> ArtifactResponse:
    """Convert ORM object to response, extracting lon/lat from geometry."""
    lon = lat = None
    if a.geom is not None:
        pt = to_shape(a.geom)
        lon, lat = pt.x, pt.y
    images = [
        ArtifactImageResponse(
            id=img.id,
            artifact_id=img.artifact_id,
            filename=img.filename,
            caption=img.caption,
            sort_order=img.sort_order or 0,
            created_at=img.created_at,
        )
        for img in (sorted(a.images, key=lambda i: i.sort_order or 0) if a.images else [])
    ]
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
        source_pdf=a.source_pdf,
        image_url=a.image_url,
        notes=a.notes,
        images=images,
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
    stmt = select(Artifact).options(joinedload(Artifact.images))

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
    results = db.execute(stmt).unique().scalars().all()
    return [_to_response(r) for r in results]


@router.get("/{artifact_id}", response_model=ArtifactResponse)
def get_artifact(artifact_id: int, db: Session = Depends(get_db)):
    stmt = select(Artifact).options(joinedload(Artifact.images)).where(Artifact.id == artifact_id)
    a = db.execute(stmt).unique().scalar_one_or_none()
    if not a:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return _to_response(a)


@router.post("/", response_model=ArtifactResponse, status_code=201)
def create_artifact(data: ArtifactCreate, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
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
def update_artifact(artifact_id: int, data: ArtifactUpdate, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    stmt = select(Artifact).options(joinedload(Artifact.images)).where(Artifact.id == artifact_id)
    a = db.execute(stmt).unique().scalar_one_or_none()
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
def delete_artifact(artifact_id: int, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    a = db.get(Artifact, artifact_id)
    if not a:
        raise HTTPException(status_code=404, detail="Artifact not found")
    db.delete(a)
    db.commit()


# ── Image CRUD ──────────────────────────────────────────────

@router.post("/{artifact_id}/images", response_model=ArtifactImageResponse, status_code=201)
def add_image(artifact_id: int, data: ArtifactImageCreate, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    a = db.get(Artifact, artifact_id)
    if not a:
        raise HTTPException(status_code=404, detail="Artifact not found")
    img = ArtifactImage(
        artifact_id=artifact_id,
        filename=data.filename,
        caption=data.caption,
        sort_order=data.sort_order,
    )
    db.add(img)
    db.commit()
    db.refresh(img)
    return img


@router.delete("/{artifact_id}/images/{image_id}", status_code=204)
def delete_image(artifact_id: int, image_id: int, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    img = db.get(ArtifactImage, image_id)
    if not img or img.artifact_id != artifact_id:
        raise HTTPException(status_code=404, detail="Image not found")
    # Remove physical file
    filepath = os.path.join(UPLOAD_DIR, img.filename)
    if os.path.isfile(filepath):
        os.remove(filepath)
    db.delete(img)
    db.commit()


@router.post("/{artifact_id}/images/upload", response_model=ArtifactImageResponse, status_code=201)
def upload_image(
    artifact_id: int,
    file: UploadFile = File(...),
    caption: str = Form(""),
    sort_order: int = Form(0),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    a = db.get(Artifact, artifact_id)
    if not a:
        raise HTTPException(status_code=404, detail="Artifact not found")
    # Generate unique filename while preserving original extension
    ext = os.path.splitext(file.filename or ".jpg")[1] or ".jpg"
    unique_name = f"{artifact_id}_{uuid.uuid4().hex[:8]}{ext}"
    # Ensure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filepath = os.path.join(UPLOAD_DIR, unique_name)
    # Write file
    content = file.file.read()
    with open(filepath, "wb") as f:
        f.write(content)
    # Create DB record
    img = ArtifactImage(
        artifact_id=artifact_id,
        filename=unique_name,
        caption=caption,
        sort_order=sort_order,
    )
    db.add(img)
    db.commit()
    db.refresh(img)
    return img


@router.post("/{artifact_id}/pdf", status_code=201)
def upload_pdf(
    artifact_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    a = db.get(Artifact, artifact_id)
    if not a:
        raise HTTPException(status_code=404, detail="Artifact not found")
    # Only accept PDF
    ext = os.path.splitext(file.filename or ".pdf")[1].lower()
    if ext not in (".pdf",):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    unique_name = f"{artifact_id}_{uuid.uuid4().hex[:8]}{ext}"
    os.makedirs(PDF_DIR, exist_ok=True)
    filepath = os.path.join(PDF_DIR, unique_name)
    with open(filepath, "wb") as f:
        f.write(file.file.read())
    # Remove old PDF if exists
    if a.source_pdf:
        old_path = os.path.join(PDF_DIR, a.source_pdf)
        if os.path.isfile(old_path):
            os.remove(old_path)
    a.source_pdf = unique_name
    db.commit()
    return {"filename": unique_name}


@router.delete("/{artifact_id}/pdf")
def delete_pdf(
    artifact_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    a = db.get(Artifact, artifact_id)
    if not a:
        raise HTTPException(status_code=404, detail="Artifact not found")
    if a.source_pdf:
        filepath = os.path.join(PDF_DIR, a.source_pdf)
        if os.path.isfile(filepath):
            os.remove(filepath)
        a.source_pdf = None
        db.commit()
    return {"ok": True}

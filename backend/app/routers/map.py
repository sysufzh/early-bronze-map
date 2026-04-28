"""GeoJSON endpoint for map visualization."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from geoalchemy2.shape import to_shape
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Artifact

router = APIRouter(prefix="/api/map", tags=["map"])


@router.get("/geojson")
def get_geojson(
    materials: Optional[str] = Query(None, description="材质，逗号分隔"),
    artifact_types: Optional[str] = Query(None, description="器型，逗号分隔"),
    cultures: Optional[str] = Query(None, description="文化，逗号分隔"),
    regions: Optional[str] = Query(None, description="区域，逗号分隔"),
    period_start_min: Optional[int] = Query(None),
    period_start_max: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    stmt = select(Artifact).where(Artifact.geom.isnot(None))

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

    stmt = stmt.order_by(Artifact.id)
    artifacts = db.execute(stmt).scalars().all()

    features = []
    for a in artifacts:
        pt = to_shape(a.geom)
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [pt.x, pt.y],
            },
            "properties": {
                "id": a.id,
                "name": a.name,
                "catalog_number": a.catalog_number,
                "quantity": a.quantity,
                "region": a.region,
                "site_name": a.site_name,
                "period_label": a.period_label,
                "period_start": a.period_start,
                "period_end": a.period_end,
                "culture": a.culture,
                "material": a.material,
                "production_method": a.production_method,
                "artifact_type": a.artifact_type,
                "context_desc": a.context_desc,
                "source_reference": a.source_reference,
                "image_url": a.image_url,
            },
        })

    return {
        "type": "FeatureCollection",
        "features": features,
    }


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Return aggregated stats for filter options."""
    total = db.execute(select(Artifact.id)).scalars().all()
    materials = db.execute(
        select(Artifact.material, func.count(Artifact.id))
        .where(Artifact.material.isnot(None))
        .group_by(Artifact.material)
    ).all()
    types = db.execute(
        select(Artifact.artifact_type, func.count(Artifact.id))
        .where(Artifact.artifact_type.isnot(None))
        .group_by(Artifact.artifact_type)
    ).all()
    cultures = db.execute(
        select(Artifact.culture, func.count(Artifact.id))
        .where(Artifact.culture.isnot(None))
        .group_by(Artifact.culture)
    ).all()

    return {
        "total": len(total),
        "materials": {m: c for m, c in materials if m},
        "artifact_types": {t: c for t, c in types if t},
        "cultures": {c: cnt for c, cnt in cultures if c},
    }

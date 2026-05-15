from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from geoalchemy2.shape import to_shape
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..auth import get_current_user, require_admin
from ..database import get_db
from ..models import PrehistoricSite, User
from ..schemas import PrehistoricSiteCreate, PrehistoricSiteUpdate, PrehistoricSiteResponse

router = APIRouter(prefix="/api/prehistoric-sites", tags=["prehistoric-sites"])


def _to_response(s: PrehistoricSite) -> PrehistoricSiteResponse:
    d = PrehistoricSiteResponse(
        id=s.id,
        name=s.name,
        catalog_number=s.catalog_number,
        region=s.region,
        site_name=s.site_name,
        period_label=s.period_label,
        period_start=s.period_start,
        period_end=s.period_end,
        culture=s.culture,
        site_type=s.site_type,
        area_desc=s.area_desc,
        description=s.description,
        excavation_history=s.excavation_history,
        key_findings=s.key_findings,
        preservation_status=s.preservation_status,
        source_reference=s.source_reference,
        notes=s.notes,
        created_at=s.created_at,
        updated_at=s.updated_at,
    )
    if s.geom is not None:
        pt = to_shape(s.geom)
        d.longitude = pt.x
        d.latitude = pt.y
    return d


@router.get("/", response_model=list[PrehistoricSiteResponse])
def list_sites(
    name: Optional[str] = Query(None, description="遗址名称搜索"),
    region: Optional[str] = Query(None, description="区域筛选"),
    period_label: Optional[str] = Query(None, description="时代筛选"),
    period_start_min: Optional[int] = Query(None),
    period_start_max: Optional[int] = Query(None),
    culture: Optional[str] = Query(None),
    site_type: Optional[str] = Query(None),
    limit: int = Query(5000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = select(PrehistoricSite).order_by(PrehistoricSite.name)
    if name:
        stmt = stmt.where(PrehistoricSite.name.ilike(f"%{name}%"))
    if region:
        stmt = stmt.where(PrehistoricSite.region == region)
    if period_label:
        stmt = stmt.where(PrehistoricSite.period_label == period_label)
    if period_start_min is not None:
        stmt = stmt.where(PrehistoricSite.period_start >= period_start_min)
    if period_start_max is not None:
        stmt = stmt.where(PrehistoricSite.period_start <= period_start_max)
    if culture:
        stmt = stmt.where(PrehistoricSite.culture == culture)
    if site_type:
        stmt = stmt.where(PrehistoricSite.site_type == site_type)

    results = db.execute(stmt.limit(limit).offset(offset)).scalars().all()
    return [_to_response(s) for s in results]


@router.get("/filters", response_model=dict)
def get_filters(db: Session = Depends(get_db)):
    """Return distinct values for each filter dropdown."""
    regions = db.execute(
        select(PrehistoricSite.region).where(PrehistoricSite.region.isnot(None)).distinct().order_by(PrehistoricSite.region)
    ).scalars().all()
    periods = db.execute(
        select(PrehistoricSite.period_label).where(PrehistoricSite.period_label.isnot(None)).distinct().order_by(PrehistoricSite.period_label)
    ).scalars().all()
    cultures = db.execute(
        select(PrehistoricSite.culture).where(PrehistoricSite.culture.isnot(None)).distinct().order_by(PrehistoricSite.culture)
    ).scalars().all()
    site_types = db.execute(
        select(PrehistoricSite.site_type).where(PrehistoricSite.site_type.isnot(None)).distinct().order_by(PrehistoricSite.site_type)
    ).scalars().all()
    return {
        "regions": list(regions),
        "period_labels": list(periods),
        "cultures": list(cultures),
        "site_types": list(site_types),
    }


@router.get("/geojson", response_model=dict)
def get_geojson(
    region: Optional[str] = Query(None),
    period_label: Optional[str] = Query(None),
    period_start_min: Optional[int] = Query(None),
    period_start_max: Optional[int] = Query(None),
    culture: Optional[str] = Query(None),
    site_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    stmt = select(PrehistoricSite)
    if region:
        stmt = stmt.where(PrehistoricSite.region == region)
    if period_label:
        stmt = stmt.where(PrehistoricSite.period_label == period_label)
    if period_start_min is not None:
        stmt = stmt.where(PrehistoricSite.period_start >= period_start_min)
    if period_start_max is not None:
        stmt = stmt.where(PrehistoricSite.period_start <= period_start_max)
    if culture:
        stmt = stmt.where(PrehistoricSite.culture == culture)
    if site_type:
        stmt = stmt.where(PrehistoricSite.site_type == site_type)

    sites = db.execute(stmt).scalars().all()

    features = []
    for s in sites:
        if s.geom is None:
            continue
        pt = to_shape(s.geom)
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [pt.x, pt.y]},
            "properties": {
                "id": s.id,
                "name": s.name,
                "region": s.region,
                "period_label": s.period_label,
                "period_start": s.period_start,
                "period_end": s.period_end,
                "culture": s.culture,
                "site_type": s.site_type,
            },
        })

    return {"type": "FeatureCollection", "features": features}


@router.get("/stats", response_model=dict)
def get_stats(db: Session = Depends(get_db)):
    """Aggregate stats: count by region, by period, by site_type."""
    total = db.execute(select(func.count(PrehistoricSite.id))).scalar()

    region_counts = db.execute(
        select(PrehistoricSite.region, func.count(PrehistoricSite.id))
        .where(PrehistoricSite.region.isnot(None))
        .group_by(PrehistoricSite.region)
        .order_by(func.count(PrehistoricSite.id).desc())
    ).all()

    period_counts = db.execute(
        select(PrehistoricSite.period_label, func.count(PrehistoricSite.id))
        .where(PrehistoricSite.period_label.isnot(None))
        .group_by(PrehistoricSite.period_label)
        .order_by(func.count(PrehistoricSite.id).desc())
    ).all()

    return {
        "total": total,
        "by_region": [{"region": r, "count": c} for r, c in region_counts],
        "by_period": [{"period_label": p, "count": c} for p, c in period_counts],
    }


@router.get("/{site_id}", response_model=PrehistoricSiteResponse)
def get_site(site_id: int, db: Session = Depends(get_db)):
    site = db.get(PrehistoricSite, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return _to_response(site)


@router.post("/", response_model=PrehistoricSiteResponse, status_code=201)
def create_site(
    data: PrehistoricSiteCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    geom = None
    if data.longitude is not None and data.latitude is not None:
        geom = func.ST_SetSRID(func.ST_MakePoint(data.longitude, data.latitude), 4326)

    site = PrehistoricSite(
        name=data.name,
        catalog_number=data.catalog_number,
        region=data.region,
        site_name=data.site_name,
        geom=geom,
        period_label=data.period_label,
        period_start=data.period_start,
        period_end=data.period_end,
        culture=data.culture,
        site_type=data.site_type,
        area_desc=data.area_desc,
        description=data.description,
        excavation_history=data.excavation_history,
        key_findings=data.key_findings,
        preservation_status=data.preservation_status,
        source_reference=data.source_reference,
        notes=data.notes,
    )
    db.add(site)
    db.commit()
    db.refresh(site)
    return _to_response(site)


@router.put("/{site_id}", response_model=PrehistoricSiteResponse)
def update_site(
    site_id: int,
    data: PrehistoricSiteUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    site = db.get(PrehistoricSite, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    update_data = data.model_dump(exclude_unset=True)
    lon = update_data.pop("longitude", None)
    lat = update_data.pop("latitude", None)

    for key, value in update_data.items():
        if hasattr(site, key):
            setattr(site, key, value)

    if lon is not None and lat is not None:
        site.geom = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)

    db.commit()
    db.refresh(site)
    return _to_response(site)


@router.delete("/{site_id}", status_code=204)
def delete_site(
    site_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    site = db.get(PrehistoricSite, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    db.delete(site)
    db.commit()

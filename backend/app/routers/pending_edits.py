from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from sqlalchemy import func

from ..auth import get_current_user, require_admin
from ..database import get_db
from ..models import Artifact, PendingEdit, User
from ..schemas import PendingEditCreate, PendingEditResponse, RejectBody

router = APIRouter(prefix="/api/pending-edits", tags=["pending-edits"])


DIFF_FIELDS = [
    "name", "catalog_number", "quantity", "region", "site_name",
    "period_label", "period_start", "period_end", "culture", "material",
    "production_method", "artifact_type", "context_desc", "location_desc",
    "source_reference", "notes",
]


def _artifact_dict(a: Artifact) -> dict:
    """Extract key fields from artifact for diff display."""
    if a is None:
        return {}
    from geoalchemy2.shape import to_shape
    d = {}
    for f in DIFF_FIELDS:
        d[f] = getattr(a, f, None)
    if a.geom is not None:
        pt = to_shape(a.geom)
        d["longitude"] = pt.x
        d["latitude"] = pt.y
    else:
        d["longitude"] = None
        d["latitude"] = None
    return d


def _to_response(pe: PendingEdit) -> PendingEditResponse:
    return PendingEditResponse(
        id=pe.id,
        user_id=pe.user_id,
        submitter_name=pe.submitter.username if pe.submitter else None,
        artifact_id=pe.artifact_id,
        artifact_name=None,  # populated below for "update" type
        artifact_data=None,
        action_type=pe.action_type,
        payload=pe.payload,
        status=pe.status,
        reviewer_id=pe.reviewer_id,
        reviewer_name=pe.reviewer.username if pe.reviewer else None,
        review_notes=pe.review_notes,
        approved_fields=pe.approved_fields,
        created_at=pe.created_at,
        updated_at=pe.updated_at,
    )


@router.post("/", response_model=PendingEditResponse, status_code=201)
def submit_edit(
    data: PendingEditCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Registered user submits a create or update for admin approval."""
    # Validate: update requires existing artifact_id
    if data.action_type == "update":
        if not data.artifact_id:
            raise HTTPException(status_code=400, detail="artifact_id is required for update")
        a = db.get(Artifact, data.artifact_id)
        if not a:
            raise HTTPException(status_code=404, detail="Artifact not found")

    pe = PendingEdit(
        user_id=current_user.id,
        artifact_id=data.artifact_id,
        action_type=data.action_type,
        payload=data.payload,
        status="pending",
    )
    db.add(pe)
    db.commit()
    db.refresh(pe)
    # Reload with relationships
    pe = db.execute(
        select(PendingEdit)
        .options(joinedload(PendingEdit.submitter), joinedload(PendingEdit.reviewer))
        .where(PendingEdit.id == pe.id)
    ).unique().scalar_one()
    return _to_response(pe)


@router.get("/", response_model=list[PendingEditResponse])
def list_pending_edits(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Admin lists pending edits. Filter by status (pending/approved/rejected)."""
    stmt = (
        select(PendingEdit)
        .options(joinedload(PendingEdit.submitter), joinedload(PendingEdit.reviewer))
        .order_by(PendingEdit.created_at.desc())
    )
    if status_filter:
        stmt = stmt.where(PendingEdit.status == status_filter)

    results = db.execute(stmt).unique().scalars().all()

    resp_list = []
    for pe in results:
        r = _to_response(pe)
        # Populate artifact name for "update" type
        if pe.artifact_id and pe.action_type == "update":
            a = db.get(Artifact, pe.artifact_id)
            if a:
                r.artifact_name = a.name
                r.artifact_data = _artifact_dict(a)
        resp_list.append(r)
    return resp_list


@router.get("/mine", response_model=list[PendingEditResponse])
def list_my_edits(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Registered user lists their own pending edits."""
    stmt = (
        select(PendingEdit)
        .options(joinedload(PendingEdit.submitter), joinedload(PendingEdit.reviewer))
        .where(PendingEdit.user_id == current_user.id)
        .order_by(PendingEdit.created_at.desc())
    )
    results = db.execute(stmt).unique().scalars().all()
    resp_list = []
    for pe in results:
        r = _to_response(pe)
        if pe.artifact_id and pe.action_type == "update":
            a = db.get(Artifact, pe.artifact_id)
            if a:
                r.artifact_name = a.name
                r.artifact_data = _artifact_dict(a)
        resp_list.append(r)
    return resp_list


@router.get("/{edit_id}", response_model=PendingEditResponse)
def get_pending_edit(
    edit_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    pe = db.execute(
        select(PendingEdit)
        .options(joinedload(PendingEdit.submitter), joinedload(PendingEdit.reviewer))
        .where(PendingEdit.id == edit_id)
    ).unique().scalar_one_or_none()
    if not pe:
        raise HTTPException(status_code=404, detail="Pending edit not found")
    r = _to_response(pe)
    if pe.artifact_id and pe.action_type == "update":
        a = db.get(Artifact, pe.artifact_id)
        if a:
            r.artifact_name = a.name
            r.artifact_data = _artifact_dict(a)
    return r


@router.post("/{edit_id}/approve", response_model=PendingEditResponse)
async def approve_edit(
    edit_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    pe = db.get(PendingEdit, edit_id)
    if not pe:
        raise HTTPException(status_code=404, detail="Pending edit not found")
    if pe.status != "pending":
        raise HTTPException(status_code=400, detail=f"Edit already {pe.status}")

    req_body = await request.json()
    approved = req_body.get("approved_fields", [])
    payload = pe.payload

    if pe.action_type == "create":
        geom = None
        if "longitude" in approved and "latitude" in approved:
            if payload.get("longitude") is not None and payload.get("latitude") is not None:
                geom = func.ST_SetSRID(
                    func.ST_MakePoint(payload["longitude"], payload["latitude"]), 4326
                )
        a = Artifact(
            name=payload.get("name", ""),
            catalog_number=payload.get("catalog_number") if "catalog_number" in approved else None,
            quantity=payload.get("quantity") if "quantity" in approved else None,
            region=payload.get("region") if "region" in approved else None,
            site_name=payload.get("site_name") if "site_name" in approved else None,
            geom=geom,
            period_label=payload.get("period_label") if "period_label" in approved else None,
            period_start=payload.get("period_start") if "period_start" in approved else None,
            period_end=payload.get("period_end") if "period_end" in approved else None,
            culture=payload.get("culture") if "culture" in approved else None,
            material=payload.get("material") if "material" in approved else None,
            production_method=payload.get("production_method") if "production_method" in approved else None,
            artifact_type=payload.get("artifact_type") if "artifact_type" in approved else None,
            context_desc=payload.get("context_desc") if "context_desc" in approved else None,
            location_desc=payload.get("location_desc") if "location_desc" in approved else None,
            source_reference=payload.get("source_reference") if "source_reference" in approved else None,
            image_url=payload.get("image_url") if "image_url" in approved else None,
            notes=payload.get("notes") if "notes" in approved else None,
        )
        db.add(a)
        pe.status = "approved"

    elif pe.action_type == "update":
        a = db.get(Artifact, pe.artifact_id)
        if not a:
            raise HTTPException(status_code=404, detail="Target artifact not found")
        # Capture original values BEFORE modification for points calculation
        orig = _artifact_dict(a)
        for key, value in payload.items():
            if key not in approved:
                continue
            if key in ("longitude", "latitude"):
                continue  # handle lon/lat together
            if hasattr(a, key):
                setattr(a, key, value)
        # Handle geometry only if both lon and lat are approved
        if "longitude" in approved and "latitude" in approved:
            lon = payload.get("longitude")
            lat = payload.get("latitude")
            if lon is not None and lat is not None:
                a.geom = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
        pe.status = "approved"

    # Track which fields were accepted, note rejected fields
    all_fields = set(payload.keys()) - {"longitude", "latitude"}  # lon/lat handled together
    rejected = all_fields - set(approved)
    pe.approved_fields = approved
    if rejected:
        rejected_note = "未接受字段: " + ", ".join(sorted(rejected))
        if pe.review_notes:
            pe.review_notes = pe.review_notes + "; " + rejected_note
        else:
            pe.review_notes = rejected_note

    pe.reviewer_id = admin_user.id
    # Award points: 1 point per field the user actually changed (not all payload fields)
    submitter = db.get(User, pe.user_id)
    if submitter:
        if pe.action_type == "update":
            changed = [f for f in approved if str(payload.get(f)) != str(orig.get(f))]
            submitter.points += len(changed)
        else:
            submitter.points += len(approved)
    db.commit()
    db.refresh(pe)

    pe = db.execute(
        select(PendingEdit)
        .options(joinedload(PendingEdit.submitter), joinedload(PendingEdit.reviewer))
        .where(PendingEdit.id == pe.id)
    ).unique().scalar_one()
    return _to_response(pe)


@router.post("/{edit_id}/reject", response_model=PendingEditResponse)
def reject_edit(
    edit_id: int,
    body: RejectBody,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    pe = db.get(PendingEdit, edit_id)
    if not pe:
        raise HTTPException(status_code=404, detail="Pending edit not found")
    if pe.status != "pending":
        raise HTTPException(status_code=400, detail=f"Edit already {pe.status}")

    pe.status = "rejected"
    pe.reviewer_id = admin_user.id
    if body.notes:
        pe.review_notes = body.notes
    db.commit()
    db.refresh(pe)

    pe = db.execute(
        select(PendingEdit)
        .options(joinedload(PendingEdit.submitter), joinedload(PendingEdit.reviewer))
        .where(PendingEdit.id == pe.id)
    ).unique().scalar_one()
    return _to_response(pe)

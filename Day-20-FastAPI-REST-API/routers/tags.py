# ============================================================
# routers/tags.py
# Tag management endpoints
# ============================================================

from fastapi import APIRouter, HTTPException
from src.models import TagCreate, TagResponse
from src.dependencies import CurrentUser, AdminUser, Database

router = APIRouter(prefix="/tags", tags=["Tags"])


@router.get("/", response_model=list[TagResponse], summary="List all tags")
def list_tags(
    current_user: CurrentUser = None,
    db: Database = None
):
    return db.get_tags()


@router.post(
    "/",
    response_model=TagResponse,
    status_code=201,
    summary="Create a tag"
)
def create_tag(
    tag_data: TagCreate,
    current_user: CurrentUser = None,
    db: Database = None
):
    # Check for duplicate
    existing = [t for t in db.get_tags() if t["name"] == tag_data.name]
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Tag '{tag_data.name}' already exists"
        )
    return db.create_tag(tag_data.model_dump())


@router.get("/{tag_id}", response_model=TagResponse, summary="Get a tag")
def get_tag(
    tag_id: int,
    current_user: CurrentUser = None,
    db: Database = None
):
    tag = db.get_tag(tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail=f"Tag {tag_id} not found")
    return tag


@router.delete(
    "/{tag_id}",
    status_code=204,
    summary="Delete a tag",
    description="Requires admin privileges."
)
def delete_tag(
    tag_id: int,
    admin: AdminUser = None,    # requires admin
    db: Database = None
):
    tag = db.get_tag(tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail=f"Tag {tag_id} not found")
    db.delete_tag(tag_id)
    return None
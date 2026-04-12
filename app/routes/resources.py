"""
FocuseMate – Resource Routes (Room-Scoped)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.resource import ResourceCreate, ResourceListOut, ResourceOut
from app.services.resource_service import add_resource, delete_resource, get_room_resources
from app.services.room_service import get_room_by_id, get_user_role_in_room

router = APIRouter(prefix="/rooms/{room_id}/resources", tags=["Resources"])


@router.post("/", response_model=ResourceOut, status_code=status.HTTP_201_CREATED)
async def create_resource(
    room_id: int,
    body: ResourceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a resource to a room."""
    room = await get_room_by_id(db, room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    role = await get_user_role_in_room(db, room_id, current_user.id)
    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this room")

    resource = await add_resource(
        db,
        room_id=room_id,
        user_id=current_user.id,
        title=body.title,
        description=body.description,
        resource_type=body.resource_type,
        link=body.link,
    )
    return ResourceOut(**resource)


@router.get("/", response_model=ResourceListOut)
async def list_resources(
    room_id: int,
    resource_type: str | None = Query(None, description="Filter by type (video, pdf, link, note, pyq)"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List resources in a room."""
    room = await get_room_by_id(db, room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    role = await get_user_role_in_room(db, room_id, current_user.id)
    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this room")

    resources, total = await get_room_resources(
        db, room_id, resource_type=resource_type, limit=limit, offset=offset
    )
    return ResourceListOut(
        resources=[ResourceOut(**r) for r in resources],
        total=total,
    )


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_resource(
    room_id: int,
    resource_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a resource (creator, admin, or owner only)."""
    deleted = await delete_resource(db, resource_id, current_user.id, room_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Resource not found or insufficient permissions",
        )

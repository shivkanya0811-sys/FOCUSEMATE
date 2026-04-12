"""
FocuseMate – Support Routes
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.support import (
    SupportTicketCreate,
    SupportTicketListOut,
    SupportTicketOut,
    SupportTicketStatusUpdate,
)
from app.services.support_service import (
    create_ticket,
    get_all_tickets,
    get_ticket_by_id,
    get_user_tickets,
    update_ticket_status,
)

router = APIRouter(prefix="/support", tags=["Support"])


@router.post("/tickets", response_model=SupportTicketOut, status_code=status.HTTP_201_CREATED)
async def submit_ticket(
    body: SupportTicketCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a support ticket."""
    ticket = await create_ticket(
        db,
        user_id=current_user.id,
        subject=body.subject,
        description=body.description,
        category=body.category,
    )
    return SupportTicketOut.model_validate(ticket)


@router.get("/tickets", response_model=SupportTicketListOut)
async def list_my_tickets(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List current user's support tickets."""
    tickets, total = await get_user_tickets(db, current_user.id, limit, offset)
    return SupportTicketListOut(
        tickets=[SupportTicketOut.model_validate(t) for t in tickets],
        total=total,
    )


@router.get("/tickets/{ticket_id}", response_model=SupportTicketOut)
async def get_ticket(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific support ticket."""
    ticket = await get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    if ticket.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return SupportTicketOut.model_validate(ticket)


@router.patch("/tickets/{ticket_id}/status", response_model=SupportTicketOut)
async def change_ticket_status(
    ticket_id: int,
    body: SupportTicketStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update ticket status (admin only, or user can close own tickets)."""
    ticket = await get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    # Users can only close their own tickets
    if not current_user.is_admin:
        if ticket.user_id != current_user.id or body.status != "closed":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can change ticket status (users can only close their own)",
            )

    updated = await update_ticket_status(db, ticket_id, body.status)
    return SupportTicketOut.model_validate(updated)


# ── Admin endpoint ───────────────────────────────────────────────
@router.get("/admin/tickets", response_model=SupportTicketListOut)
async def admin_list_tickets(
    status_filter: str | None = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Admin: List all support tickets."""
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    tickets, total = await get_all_tickets(db, status_filter=status_filter, limit=limit, offset=offset)
    return SupportTicketListOut(
        tickets=[SupportTicketOut.model_validate(t) for t in tickets],
        total=total,
    )

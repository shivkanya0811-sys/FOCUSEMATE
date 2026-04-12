"""
FocuseMate – Support Ticket Service
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.support_ticket import SupportTicket


async def create_ticket(
    db: AsyncSession,
    user_id: int,
    subject: str,
    description: str,
    category: str = "general",
) -> SupportTicket:
    ticket = SupportTicket(
        user_id=user_id,
        subject=subject,
        description=description,
        category=category,
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    return ticket


async def get_user_tickets(
    db: AsyncSession,
    user_id: int,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[SupportTicket], int]:
    total_result = await db.execute(
        select(func.count(SupportTicket.id)).where(SupportTicket.user_id == user_id)
    )
    total = total_result.scalar() or 0

    result = await db.execute(
        select(SupportTicket)
        .where(SupportTicket.user_id == user_id)
        .order_by(SupportTicket.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    tickets = result.scalars().all()
    return tickets, total


async def get_ticket_by_id(
    db: AsyncSession,
    ticket_id: int,
) -> SupportTicket | None:
    result = await db.execute(
        select(SupportTicket).where(SupportTicket.id == ticket_id)
    )
    return result.scalar_one_or_none()


async def update_ticket_status(
    db: AsyncSession,
    ticket_id: int,
    status: str,
) -> SupportTicket | None:
    ticket = await get_ticket_by_id(db, ticket_id)
    if not ticket:
        return None
    ticket.status = status
    await db.commit()
    await db.refresh(ticket)
    return ticket


async def get_all_tickets(
    db: AsyncSession,
    status_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[SupportTicket], int]:
    """Admin: list all tickets with optional status filter."""
    count_query = select(func.count(SupportTicket.id))
    query = select(SupportTicket)

    if status_filter:
        count_query = count_query.where(SupportTicket.status == status_filter)
        query = query.where(SupportTicket.status == status_filter)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    result = await db.execute(
        query.order_by(SupportTicket.created_at.desc()).offset(offset).limit(limit)
    )
    tickets = result.scalars().all()
    return tickets, total

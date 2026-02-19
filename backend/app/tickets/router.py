from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import User, Ticket, TICKET_STATUSES, TICKET_STATUS_LABELS
from app.auth.deps import get_current_user, require_admin
from app.tickets.schemas import TicketCreate, TicketResponse, TicketUpdate

router = APIRouter(prefix="/api/tickets", tags=["문의"])


def _display_name(user: User) -> str:
    return user.discord_username or user.display_name or user.username


def _build_response(ticket: Ticket, user: User = None, replier: User = None) -> TicketResponse:
    return TicketResponse(
        id=ticket.id,
        user_id=ticket.user_id,
        requester_name=_display_name(user) if user else "(알 수 없음)",
        requester_email=user.email if user else None,
        container_name=ticket.container_name,
        title=ticket.title,
        description=ticket.description,
        status=ticket.status,
        status_label=TICKET_STATUS_LABELS.get(ticket.status, ticket.status),
        admin_reply=ticket.admin_reply,
        replied_by_name=_display_name(replier) if replier else None,
        replied_at=ticket.replied_at.isoformat() if ticket.replied_at else None,
        created_at=ticket.created_at.isoformat(),
        updated_at=ticket.updated_at.isoformat(),
    )


async def _get_user(db: AsyncSession, user_id: str) -> User | None:
    if not user_id:
        return None
    r = await db.execute(select(User).where(User.id == user_id))
    return r.scalar_one_or_none()


# ─── 문의 접수 (사용자) ───

@router.post("/", response_model=TicketResponse)
async def create_ticket(
    body: TicketCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ticket = Ticket(
        user_id=user.id,
        container_name=body.container_name,
        title=body.title,
        description=body.description,
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)

    # 관리자 알림 (이메일 + Discord)
    requester_name = _display_name(user)
    try:
        from app.mail.service import send_ticket_submitted_notification
        await send_ticket_submitted_notification(
            requester_name=requester_name,
            requester_email=user.email or "",
            title=body.title,
            description=body.description,
            container_name=body.container_name,
        )
    except Exception as e:
        print(f"[MAIL ERROR] 문의 접수 알림 발송 실패: {e}")

    try:
        from app.discord.notify import notify_ticket_submitted
        await notify_ticket_submitted(
            requester_name=requester_name,
            title=body.title,
            container_name=body.container_name,
        )
    except Exception:
        pass

    return _build_response(ticket, user)


# ─── 내 문의 목록 (사용자) ───

@router.get("/my", response_model=list[TicketResponse])
async def my_tickets(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Ticket)
        .where(Ticket.user_id == user.id)
        .order_by(Ticket.created_at.desc())
    )
    tickets = result.scalars().all()

    # replier 캐시
    replier_cache = {}
    responses = []
    for t in tickets:
        replier = None
        if t.replied_by:
            if t.replied_by not in replier_cache:
                replier_cache[t.replied_by] = await _get_user(db, t.replied_by)
            replier = replier_cache[t.replied_by]
        responses.append(_build_response(t, user, replier))
    return responses


# ─── 관리 중인 게임서버 목록 (티켓 폼 드롭다운용) ───

@router.get("/containers")
async def list_containers_for_ticket(
    user: User = Depends(get_current_user),
):
    from app.containers.service import list_game_containers
    containers = list_game_containers()
    return [c["name"] for c in containers]


# ─── 전체 문의 목록 (관리자) ───

@router.get("/", response_model=list[TicketResponse])
async def list_tickets(
    status_filter: str = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(Ticket).order_by(Ticket.created_at.desc())
    if status_filter:
        query = query.where(Ticket.status == status_filter)

    result = await db.execute(query)
    tickets = result.scalars().all()

    user_cache = {}
    responses = []
    for t in tickets:
        if t.user_id not in user_cache:
            user_cache[t.user_id] = await _get_user(db, t.user_id)
        replier = None
        if t.replied_by:
            if t.replied_by not in user_cache:
                user_cache[t.replied_by] = await _get_user(db, t.replied_by)
            replier = user_cache[t.replied_by]
        responses.append(_build_response(t, user_cache[t.user_id], replier))
    return responses


# ─── 상태 변경 + 답변 (관리자) ───

@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: str,
    body: TicketUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if ticket is None:
        raise HTTPException(404, "문의를 찾을 수 없습니다")

    old_status = ticket.status

    if body.status is not None:
        if body.status not in TICKET_STATUSES:
            raise HTTPException(400, f"유효하지 않은 상태: {body.status}")
        ticket.status = body.status

    if body.admin_reply is not None:
        ticket.admin_reply = body.admin_reply
        ticket.replied_by = admin.id
        ticket.replied_at = datetime.utcnow()

    await db.commit()
    await db.refresh(ticket)

    # 사용자에게 상태 변경/답변 이메일 알림
    requester = await _get_user(db, ticket.user_id)
    if requester and requester.email and (old_status != ticket.status or body.admin_reply):
        try:
            from app.mail.service import send_ticket_status_notification
            await send_ticket_status_notification(
                to=requester.email,
                username=_display_name(requester),
                title=ticket.title,
                new_status=ticket.status,
                admin_reply=ticket.admin_reply,
            )
        except Exception as e:
            print(f"[MAIL ERROR] 문의 상태 알림 실패: {e}")

    replier = await _get_user(db, ticket.replied_by) if ticket.replied_by else None
    return _build_response(ticket, requester, replier)


# ─── 상태 목록 (프론트엔드용) ───

@router.get("/statuses/list")
async def get_statuses():
    return {"statuses": TICKET_STATUSES, "labels": TICKET_STATUS_LABELS}

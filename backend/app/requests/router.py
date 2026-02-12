from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import User, GameRequest
from app.auth.deps import get_current_user, require_admin, require_discord_role
from app.requests.schemas import GameRequestCreate, GameRequestResponse, GameRequestReview
from app.mail.service import send_game_request_notification
from app.discord.notify import notify_game_request

router = APIRouter(prefix="/api/game-requests", tags=["게임 신청"])


# ─── 게임 서버 신청 (로그인 + Discord 역할 필요) ───

@router.post("/", response_model=GameRequestResponse)
async def submit_game_request(
    req: GameRequestCreate,
    user: User = Depends(require_discord_role),
    db: AsyncSession = Depends(get_db),
):
    game_req = GameRequest(
        requester_name=req.requester_name,
        requester_email=req.requester_email,
        game_name=req.game_name,
        player_count=req.player_count,
        preferred_time=req.preferred_time,
        notes=req.notes,
    )
    db.add(game_req)
    await db.commit()
    await db.refresh(game_req)

    # SMTP 알림 (비동기, 실패해도 신청은 접수)
    try:
        await send_game_request_notification(
            requester_name=req.requester_name,
            requester_email=req.requester_email or "",
            game_name=req.game_name,
            player_count=req.player_count,
            preferred_time=req.preferred_time or "",
            notes=req.notes or "",
        )
    except Exception as e:
        # 메일 실패는 로그만 남기고 넘어감
        print(f"[MAIL ERROR] 게임 신청 알림 발송 실패: {e}")

    # Discord 채널 알림
    try:
        await notify_game_request(
            requester_name=req.requester_name,
            game_name=req.game_name,
            player_count=req.player_count,
            notes=req.notes,
        )
    except Exception:
        pass

    return GameRequestResponse(
        id=game_req.id,
        requester_name=game_req.requester_name,
        requester_email=game_req.requester_email,
        game_name=game_req.game_name,
        player_count=game_req.player_count,
        preferred_time=game_req.preferred_time,
        notes=game_req.notes,
        status=game_req.status,
        admin_notes=game_req.admin_notes,
        created_at=game_req.created_at.isoformat(),
    )


# ─── 신청 목록 조회 (관리자) ───

@router.get("/", response_model=list[GameRequestResponse])
async def list_game_requests(
    status_filter: str = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(GameRequest).order_by(GameRequest.created_at.desc())
    if status_filter:
        query = query.where(GameRequest.status == status_filter)

    result = await db.execute(query)
    requests = result.scalars().all()

    return [
        GameRequestResponse(
            id=r.id, requester_name=r.requester_name, requester_email=r.requester_email,
            game_name=r.game_name, player_count=r.player_count,
            preferred_time=r.preferred_time, notes=r.notes,
            status=r.status, admin_notes=r.admin_notes,
            created_at=r.created_at.isoformat(),
        )
        for r in requests
    ]


# ─── 신청 승인/거절 (관리자) ───

@router.patch("/{request_id}", response_model=GameRequestResponse)
async def review_game_request(
    request_id: str,
    review: GameRequestReview,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if review.status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="status는 approved 또는 rejected만 가능합니다")

    result = await db.execute(select(GameRequest).where(GameRequest.id == request_id))
    game_req = result.scalar_one_or_none()
    if game_req is None:
        raise HTTPException(status_code=404, detail="신청을 찾을 수 없습니다")

    game_req.status = review.status
    game_req.admin_notes = review.admin_notes
    game_req.reviewed_by = admin.id
    game_req.reviewed_at = datetime.utcnow()
    await db.commit()
    await db.refresh(game_req)

    return GameRequestResponse(
        id=game_req.id, requester_name=game_req.requester_name,
        requester_email=game_req.requester_email,
        game_name=game_req.game_name, player_count=game_req.player_count,
        preferred_time=game_req.preferred_time, notes=game_req.notes,
        status=game_req.status, admin_notes=game_req.admin_notes,
        created_at=game_req.created_at.isoformat(),
    )

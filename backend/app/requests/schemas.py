from pydantic import BaseModel
from typing import Optional


class GameRequestCreate(BaseModel):
    requester_name: str
    requester_email: Optional[str] = None
    game_name: str
    player_count: int = 1
    preferred_time: Optional[str] = None
    notes: Optional[str] = None


class GameRequestResponse(BaseModel):
    id: str
    requester_name: str
    requester_email: Optional[str]
    game_name: str
    player_count: int
    preferred_time: Optional[str]
    notes: Optional[str]
    status: str
    admin_notes: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class GameRequestReview(BaseModel):
    status: str  # approved / rejected
    admin_notes: Optional[str] = None

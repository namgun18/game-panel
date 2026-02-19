from pydantic import BaseModel, Field
from typing import Optional


class TicketCreate(BaseModel):
    container_name: Optional[str] = None
    title: str = Field(..., max_length=200)
    description: str


class TicketResponse(BaseModel):
    id: str
    user_id: str
    requester_name: str
    requester_email: Optional[str] = None
    container_name: Optional[str] = None
    title: str
    description: str
    status: str
    status_label: str = ""
    admin_reply: Optional[str] = None
    replied_by_name: Optional[str] = None
    replied_at: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class TicketUpdate(BaseModel):
    status: Optional[str] = None
    admin_reply: Optional[str] = None

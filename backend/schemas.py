from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class HCPBase(BaseModel):
    name: str
    speciality: Optional[str] = None
    hospital: Optional[str] = None
    location: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class HCPResponse(HCPBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class InteractionBase(BaseModel):
    hcp_id: int
    interaction_type: Optional[str] = "Meeting"
    date: Optional[str] = None
    time: Optional[str] = None
    attendees: Optional[str] = None
    topics_discussed: Optional[str] = None
    materials_shared: Optional[str] = None
    samples_distributed: Optional[str] = None
    sentiment: Optional[str] = "Neutral"
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None


class InteractionCreate(InteractionBase):
    raw_chat_input: Optional[str] = None


class InteractionUpdate(BaseModel):
    interaction_type: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    attendees: Optional[str] = None
    topics_discussed: Optional[str] = None
    materials_shared: Optional[str] = None
    samples_distributed: Optional[str] = None
    sentiment: Optional[str] = None
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None


class InteractionResponse(InteractionBase):
    id: int
    ai_suggested_followups: Optional[str] = None
    raw_chat_input: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    hcp: Optional[HCPResponse] = None

    class Config:
        from_attributes = True


class ChatInput(BaseModel):
    message: str
    hcp_id: Optional[int] = None


class AgentResponse(BaseModel):
    tool_used: str
    result: dict
    message: str

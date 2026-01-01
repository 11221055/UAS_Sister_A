from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List
from datetime import datetime

class Event(BaseModel):
    topic: str = Field(min_length=1)
    event_id: str = Field(min_length=8)   # kamu bisa perketat (UUID/ULID)
    timestamp: datetime
    source: str = Field(min_length=1)
    payload: Dict[str, Any]

class PublishResponse(BaseModel):
    received: int
    enqueued: int

class StatsResponse(BaseModel):
    received: int
    unique_processed: int
    duplicate_dropped: int
    topics: List[str]
    uptime_seconds: int

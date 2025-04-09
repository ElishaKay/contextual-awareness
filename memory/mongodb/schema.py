from pydantic import BaseModel, Field
from typing import List, Dict
from datetime import datetime

class Report(BaseModel):
    report_id: str = Field(..., description="Unique report identifier")
    content: str = Field(..., description="The content of the report")
    created_at: str = Field(..., description="Timestamp when the report was created")

class Log(BaseModel):
    log_id: str = Field(..., description="Unique log identifier")
    type: str = Field(..., description="Type of log entry")
    content: str = Field(..., description="Log message content")
    metadata: str = Field(None, description="Relevant metadata for this log entry")
    created_at: str = Field(..., description="Timestamp of log creation")

class Chat(BaseModel):
    chat_id: str = Field(..., description="Unique chat identifier")
    conversation: List[str] = Field(..., description="The conversation log as a list of messages")
    created_at: str = Field(..., description="Timestamp when the conversation was saved")

class User(BaseModel):
    user_id: str = Field(..., description="Unique identifier for the user")
    profile: Dict[str, str] = Field(default_factory=dict, description="A dictionary containing user's profile information")
    todos: List[str] = Field(default_factory=list, description="A list of todo items")
    instructions: str = Field("", description="User instructions content")
    research_goals: str = Field("", description="User research goals")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Timestamp when the record was created")
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Timestamp when the record was last updated")
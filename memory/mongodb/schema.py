from pydantic import BaseModel, Field
from typing import List

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
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
import uuid


class ContactSubmissionCreate(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str


class ContactSubmission(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: EmailStr
    subject: str
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
class ContactSubmissionCreate(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str

from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field

ExperienceType = Literal["project", "internship", "research", "competition", "award", "certificate", "education", "other"]
ExperienceStatus = Literal["idea", "draft", "active", "verified", "archived"]


class ExperienceCreate(BaseModel):
    type: ExperienceType = "project"
    title: str = Field(min_length=1, max_length=200)
    organization: str = ""
    role: str = ""
    start: str = ""
    end: str = ""
    status: ExperienceStatus = "active"
    domains: list[str] = []
    skills: list[str] = []
    resume_ready: bool = False
    summary: str = ""
    facts: str = ""
    results: str = ""
    notes: str = ""


class ExperienceUpdate(BaseModel):
    type: ExperienceType | None = None
    title: str | None = None
    organization: str | None = None
    role: str | None = None
    start: str | None = None
    end: str | None = None
    status: ExperienceStatus | None = None
    domains: list[str] | None = None
    skills: list[str] | None = None
    resume_ready: bool | None = None
    summary: str | None = None
    facts: str | None = None
    results: str | None = None
    notes: str | None = None


class MigrationReviewComplete(BaseModel):
    resume_ready: bool = False


class InboxCreate(BaseModel):
    content: str = Field(min_length=1)
    title: str = ""
    related_experience_id: str = ""
    kind: Literal["note", "idea", "log"] = "note"


class ProfileUpdate(BaseModel):
    name: str = ""
    city: str = ""
    headline: str = ""
    email: str = ""
    phone: str = ""
    github: str = ""
    portfolio: str = ""
    education: list[dict] = []
    skills: list[str] = []

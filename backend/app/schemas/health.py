from datetime import datetime
from typing import Dict, Any
from pydantic import BaseModel, Field


class ModuleStatus(BaseModel):
    name: str
    phase: str
    status: str = Field(..., description="Status of the module: initialized, pending, or ready")
    description: str


class HealthCheckResponse(BaseModel):
    status: str = Field(default="ok", example="ok")
    project: str = Field(default="Mining Document Intelligence & Reporting Platform")
    version: str = Field(default="0.1.0")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    environment: str = Field(default="development")
    phase: str = Field(default="Phase 1 - Monorepo Foundation & API Shell")
    gemini_configured: bool = Field(default=False)
    modules: Dict[str, ModuleStatus] = Field(default_factory=dict)
    system: Dict[str, Any] = Field(default_factory=dict)

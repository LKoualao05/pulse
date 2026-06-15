"""Metadata endpoints: health, data sources, and the precomputed summary."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud
from app.config import PROCESSED_DIR
from app.db import get_db
from app.schemas import HealthResponse, SourceOut, SummaryResponse

router = APIRouter(tags=["meta"])


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    c = crud.counts(db)
    status = "ok" if c["observations"] > 0 else "empty"
    return HealthResponse(
        status=status,
        indicators=c["indicators"],
        observations=c["observations"],
        sources=c["sources"],
    )


@router.get("/sources", response_model=list[SourceOut])
def sources(db: Session = Depends(get_db)) -> list[SourceOut]:
    return [SourceOut.model_validate(s) for s in crud.list_sources(db)]


@router.get("/summary", response_model=SummaryResponse)
def summary() -> SummaryResponse:
    path = PROCESSED_DIR / "summary.json"
    if not path.exists():
        raise HTTPException(status_code=503, detail="Summary not generated yet.")
    data = json.loads(path.read_text(encoding="utf-8"))
    return SummaryResponse.model_validate(data)

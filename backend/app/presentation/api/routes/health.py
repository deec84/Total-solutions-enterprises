"""Orchestrator probes with stable, intentionally small payloads."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import database_session

router = APIRouter()


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


async def check_database(
    session: Annotated[AsyncSession, Depends(database_session)],
) -> None:
    try:
        await session.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "database unavailable"
        ) from error


def check_observability(request: Request) -> None:
    runtime = request.app.state.observability
    if not runtime.ready:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "observability provider unavailable"
        )


@router.get("/live", response_model=HealthResponse, summary="Process liveness")
async def liveness() -> HealthResponse:
    return HealthResponse()


@router.get("/ready", response_model=HealthResponse, summary="Service readiness")
async def readiness(
    _: Annotated[None, Depends(check_database)],
    __: Annotated[None, Depends(check_observability)],
) -> HealthResponse:
    return HealthResponse()

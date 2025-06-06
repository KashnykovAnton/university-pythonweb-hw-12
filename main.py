"""Main application module for Contacts Management API.

This module configures:
- FastAPI application instance
- Database connection health checks
- Scheduled background tasks
- Rate limiting and CORS policies
- API route registration
"""

from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager
from slowapi.errors import RateLimitExceeded
from src.database.db import get_db, sessionmanager
from src.routes import contacts, auth, users
from src.conf import messages

scheduler = AsyncIOScheduler()


async def cleanup_expired_tokens():
    """Background task to periodically clean up expired refresh tokens.

    Runs every hour to:
    - Remove tokens past their expiration date
    - Remove revoked tokens older than 7 days
    """
    async with sessionmanager.session() as db:
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=7)
        stmt = text(
            "DELETE FROM refresh_tokens WHERE expired_at < :now OR revoked_at IS NOT NULL AND revoked_at < :cutoff"
        )
        await db.execute(stmt, {"now": now, "cutoff": cutoff})
        await db.commit()
        print(f"Expired tokens cleaned up [{now.strftime('%Y-%m-%d %H:%M:%S')}]")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management.

    On startup:
    - Initializes token cleanup job (runs hourly)

    On shutdown:
    - Stops the scheduler gracefully
    """
    scheduler.add_job(cleanup_expired_tokens, "interval", hours=1)
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    lifespan=lifespan,
    title="Contacts application v1.0",
    description="This is contacts management application",
    version="1.0",
)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded errors.

    Returns:
        JSONResponse: 429 status with localized error message
    """
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"error": messages.requests_limit.get("ua")},
    )


# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(contacts.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")


@app.get("/")
def read_root(request: Request):
    """Root endpoint providing API identification.

    Returns:
        dict: Basic API information
    """
    return {"message": "Contacts Management API v1.0"}


@app.get("/healthchecker")
async def healthchecker(db: AsyncSession = Depends(get_db)):
    """Database connectivity health check.

    Verifies:
    - Ability to execute simple SQL query
    - Database connection validity

    Raises:
        HTTPException: 500 if database is unreachable
    """
    try:
        result = await db.execute(text("SELECT 1"))
        result = result.fetchone()
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database is not configured correctly",
            )
        return {"message": "Welcome to FastAPI!"}
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error connecting to the database",
        )

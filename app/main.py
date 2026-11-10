
from fastapi import FastAPI
from app.core.config import settings
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.accounts import router as accounts_router
from app.routers.admin import router as admin_router
from app.routers.posts import router as posts_router
from app.routers.likes import router as likes_router
from app.routers.comments import router as comments_router 
from app.routers.follows import router as follows_router
from app.routers.follow_request import router as follow_request_router

app = FastAPI(
    description="A social media API built with FastAPI and SQLAlchemy",
)


@app.get("/")
def root():
    return {
        "message": "Social Media API is running",
        "version": "1.0.0",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
    }

app.include_router(
    auth_router,
    prefix="/api/v1/auth",
    tags=["Authentication"],
)
app.include_router(
    users_router,
    prefix="/api/v1/users",
    tags=["Users"],
)

app.include_router(
    accounts_router,
    prefix="/api/v1/accounts",
    tags=["Accounts"],
)   

app.include_router(
    admin_router,
    prefix="/api/v1/admin",
    tags=["Admin"],
)

app.include_router(
    posts_router,
    prefix="/api/v1",
    tags=["Posts"],
)

app.include_router(
    likes_router,
    prefix="/api/v1",
)

app.include_router(
    comments_router,
    prefix="/api/v1",
)

app.include_router(
    follows_router,
    prefix="/api/v1",
)

app.include_router(
    follow_request_router,
    prefix="/api/v1",
)


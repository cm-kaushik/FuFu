from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.init_db import init_database
from app.database.connection import init_pool
from app.api import auth, stocks, portfolio, transactions, indexes, ai_advisor

app = FastAPI(
    title="Stock Investment App",
    description="Indian Stock Trading Platform with NSE/BSE stocks",
    version="1.0.0"
)

import os

# CORS middleware for React frontend
cors_origins_env = os.getenv("ALLOWED_ORIGINS", "")
if cors_origins_env and cors_origins_env.strip() != "*":
    allowed_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Allow all origins with credentials for cloud deployments
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"https?://.*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include API routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(stocks.router, prefix="/api/stocks", tags=["Stocks"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["Portfolio"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["Transactions"])
app.include_router(indexes.router, prefix="/api/indexes", tags=["Custom Indexes"])
app.include_router(ai_advisor.router, prefix="/api/ai", tags=["AI Advisor"])


@app.on_event("startup")
async def startup():
    """Initialize database and connection pool on startup."""
    init_database()
    init_pool()
    print("[OK] Stock Investment App is running!")


@app.get("/")
async def root():
    return {"message": "Stock Investment App API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import budgets, categories, expenses, receipts, summary


def create_app() -> FastAPI:
    app = FastAPI(title="Expense Tracker API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(expenses.router, prefix="/api")
    app.include_router(receipts.router, prefix="/api")
    app.include_router(categories.router, prefix="/api")
    app.include_router(budgets.router, prefix="/api")
    app.include_router(summary.router, prefix="/api")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app

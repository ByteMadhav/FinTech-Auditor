import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import api_router
from app.db.session import engine, Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

def create_application() -> FastAPI:
    application = FastAPI(title="Expense Auditor", version="1.0.0")
    application.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
    )
    application.include_router(api_router, prefix="/api/v1")
    
    @application.get("/health", tags=["System"])
    async def health_check():
        return {"status": "healthy"}

    return application

app = create_application()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
from fastapi import FastAPI
from app.database import engine
from app.auth.models import Base
from app.auth.routes import router as auth_router

# IMPORTANT: This drops old corrupted tables and recreates them perfectly
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Healthcare AI Assistant")
app.include_router(auth_router)

@app.get("/")
def root():
    return {"message": "System Online"}
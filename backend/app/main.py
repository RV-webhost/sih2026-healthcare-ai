from fastapi import FastAPI
from app.database import engine, Base
from app.tokens.routes import router as tokens_router

# Neon DB ke andar tables banayega agar exist nahi karti
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart OPD - Hospital Management System")

# Token routes include karo
app.include_router(tokens_router)
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Hardcoded to your exact Neon database to prevent test failures
DATABASE_URL = "postgresql://neondb_owner:npg_k6xtAFP9Ozvu@ep-small-frog-azoa1fuu.c-3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
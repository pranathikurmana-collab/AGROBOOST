from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables from your .env file
load_dotenv()

# Get your database URL (make sure this matches what is in your .env file)
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL") 

# Create the SQLAlchemy engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create a SessionLocal class. Each instance of this class will be a database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for your models to inherit from
Base = declarative_base()

# The dependency function you added
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
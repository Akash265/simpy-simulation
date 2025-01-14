from sqlalchemy import Column, Integer, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
engine = create_engine("sqlite:///configurations.db")  # Replace with your DB setup
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class ConfigurationModel(Base):
    __tablename__ = "configurations"
    id = Column(Integer, primary_key=True, index=True)
    config = Column(JSON)

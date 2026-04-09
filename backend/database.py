from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# SQLite - no installation needed, file created automatically
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'hcp_crm.db')}")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class HCP(Base):
    __tablename__ = "hcps"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    speciality = Column(String(255))
    hospital = Column(String(255))
    location = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    interactions = relationship("Interaction", back_populates="hcp")


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    hcp_id = Column(Integer, ForeignKey("hcps.id"), nullable=False)
    interaction_type = Column(
        Enum("Meeting", "Call", "Email", "Conference", "Other", name="interaction_type_enum"),
        default="Meeting"
    )
    date = Column(String(20))
    time = Column(String(10))
    attendees = Column(Text)
    topics_discussed = Column(Text)
    materials_shared = Column(Text)
    samples_distributed = Column(Text)
    sentiment = Column(
        Enum("Positive", "Neutral", "Negative", name="sentiment_enum"),
        default="Neutral"
    )
    outcomes = Column(Text)
    follow_up_actions = Column(Text)
    ai_suggested_followups = Column(Text)
    raw_chat_input = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hcp = relationship("HCP", back_populates="interactions")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    # Seed some sample HCPs
    db = SessionLocal()
    if db.query(HCP).count() == 0:
        sample_hcps = [
            HCP(name="Dr. Anjali Sharma", speciality="Oncology", hospital="AIIMS Hyderabad", location="Hyderabad"),
            HCP(name="Dr. Ravi Kumar", speciality="Cardiology", hospital="Apollo Hospitals", location="Hyderabad"),
            HCP(name="Dr. Priya Nair", speciality="Neurology", hospital="Yashoda Hospitals", location="Secunderabad"),
            HCP(name="Dr. Suresh Patel", speciality="Endocrinology", hospital="Care Hospitals", location="Hyderabad"),
            HCP(name="Dr. Meena Reddy", speciality="Pulmonology", hospital="Kims Hospital", location="Hyderabad"),
        ]
        db.add_all(sample_hcps)
        db.commit()
    db.close()

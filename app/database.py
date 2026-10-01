from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
import os

DB_URL = os.getenv("DATABASE_URL", "sqlite:///./signals.db")
connect_args = {"check_same_thread": False} if DB_URL.startswith("sqlite") else {}
engine = create_engine(DB_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class Signal(Base):
    __tablename__ = "signals"
    id = Column(Integer, primary_key=True)
    asset_symbol = Column(String(40), nullable=False)
    asset_name = Column(String(80), nullable=False)
    is_otc = Column(Boolean, default=False)
    direction = Column(String(10), nullable=False)
    strength = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    expiry_seconds = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expiry_at = Column(DateTime(timezone=True), nullable=False)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(10), default="PENDING")
    reason = Column(Text, nullable=True)

    def to_dict(self):
        def iso(v):
            return v.isoformat() if v else None
        return {
            "id": self.id, "asset_symbol": self.asset_symbol,
            "asset_name": self.asset_name, "is_otc": self.is_otc,
            "direction": self.direction, "strength": round(self.strength, 1),
            "entry_price": self.entry_price, "exit_price": self.exit_price,
            "expiry_seconds": self.expiry_seconds, "created_at": iso(self.created_at),
            "expiry_at": iso(self.expiry_at), "closed_at": iso(self.closed_at),
            "status": self.status, "reason": self.reason,
        }

def init_db():
    Base.metadata.create_all(bind=engine)

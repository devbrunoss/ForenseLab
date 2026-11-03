import uuid
from datetime import datetime,timezone
from sqlalchemy import String,Text,Integer,DateTime,ForeignKey
from sqlalchemy.orm import Mapped,mapped_column
from .db import Base
def uid(): return str(uuid.uuid4())
def utc(): return datetime.now(timezone.utc)
class Case(Base):
    __tablename__="cases"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    title:Mapped[str]=mapped_column(String(200))
    description:Mapped[str]=mapped_column(Text,default="")
    status:Mapped[str]=mapped_column(String(30),default="open")
    priority:Mapped[str]=mapped_column(String(20),default="medium")
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utc)
class Evidence(Base):
    __tablename__="evidence"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    case_id:Mapped[str]=mapped_column(ForeignKey("cases.id"),index=True)
    original_name:Mapped[str]=mapped_column(String(255))
    storage_name:Mapped[str]=mapped_column(String(80),unique=True)
    size:Mapped[int]=mapped_column(Integer)
    sha256:Mapped[str]=mapped_column(String(64))
    integrity_status:Mapped[str]=mapped_column(String(30),default="not_checked")
    imported_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utc)
class Audit(Base):
    __tablename__="audit"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    case_id:Mapped[str|None]=mapped_column(String(36),nullable=True)
    action:Mapped[str]=mapped_column(String(80))
    description:Mapped[str]=mapped_column(Text)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utc)
class Timeline(Base):
    __tablename__="timeline"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    case_id:Mapped[str]=mapped_column(ForeignKey("cases.id"))
    occurred_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    recorded_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utc)
    description:Mapped[str]=mapped_column(Text)
    source:Mapped[str]=mapped_column(Text,default="Não informado")

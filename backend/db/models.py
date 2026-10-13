"""
DeepClaw Database Models - SQLAlchemy 2.0
Modèles pour sessions de recherche, sources, faits, graphes et rapports
"""
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, String, Text, Integer, Float, DateTime, Boolean, 
    ForeignKey, Index, JSON, Enum as SQLEnum
)
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()


class ResearchStatus(str, enum.Enum):
    """Statuts d'une session de recherche"""
    PENDING = "pending"
    COLLECTING_SOURCES = "collecting_sources"
    EXTRACTING_FACTS = "extracting_facts"
    DETECTING_CONTRADICTIONS = "detecting_contradictions"
    SYNTHESIZING = "synthesizing"
    GENERATING_REPORT = "generating_report"
    COMPLETED = "completed"
    FAILED = "failed"


class SourceType(str, enum.Enum):
    """Types de sources"""
    WEB = "web"
    PDF = "pdf"
    ACADEMIC = "academic"
    NEWS = "news"
    BLOG = "blog"
    DOCUMENTATION = "documentation"


class Session(Base):
    """Session de recherche principale"""
    __tablename__ = "sessions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    topic: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    depth: Mapped[int] = mapped_column(Integer, default=3)
    max_sources: Mapped[int] = mapped_column(Integer, default=10)
    status: Mapped[str] = mapped_column(
        SQLEnum(ResearchStatus), 
        default=ResearchStatus.PENDING,
        nullable=False,
        index=True
    )
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Configuration LLM utilisée
    llm_providers: Mapped[Optional[List[str]]] = mapped_column(SQLiteJSON, nullable=True)
    llm_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Résultats
    total_sources: Mapped[int] = mapped_column(Integer, default=0)
    total_facts: Mapped[int] = mapped_column(Integer, default=0)
    total_contradictions: Mapped[int] = mapped_column(Integer, default=0)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Chemins des fichiers générés
    report_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    pdf_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    markdown_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Relations
    sources: Mapped[List["Source"]] = relationship("Source", back_populates="session", cascade="all, delete-orphan")
    facts: Mapped[List["Fact"]] = relationship("Fact", back_populates="session", cascade="all, delete-orphan")
    contradictions: Mapped[List["Contradiction"]] = relationship("Contradiction", back_populates="session", cascade="all, delete-orphan")
    reports: Mapped[List["Report"]] = relationship("Report", back_populates="session", cascade="all, delete-orphan")
    
    # Index composés
    __table_args__ = (
        Index("ix_sessions_status_created", "status", "created_at"),
    )


class Source(Base):
    """Source de référence (page web, document, etc.)"""
    __tablename__ = "sources"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("sessions.id"), nullable=False, index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(SQLEnum(SourceType), default=SourceType.WEB)
    relevance_score: Mapped[float] = mapped_column(Float, default=0.5)
    credibility_score: Mapped[float] = mapped_column(Float, default=0.5)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    accessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Métadonnées
    extra_metadata: Mapped[Optional[dict]] = mapped_column("metadata", SQLiteJSON, nullable=True)
    
    # Relations
    session: Mapped["Session"] = relationship("Session", back_populates="sources")
    facts: Mapped[List["Fact"]] = relationship("Fact", back_populates="source", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_sources_session_relevance", "session_id", "relevance_score"),
    )


class Fact(Base):
    """Fait extrait d'une source"""
    __tablename__ = "facts"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("sessions.id"), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(36), ForeignKey("sources.id"), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    entity: Mapped[str] = mapped_column(String(255), nullable=True)
    predicate: Mapped[str] = mapped_column(String(255), nullable=True)
    object: Mapped[str] = mapped_column(String(255), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relations
    session: Mapped["Session"] = relationship("Session", back_populates="facts")
    source: Mapped["Source"] = relationship("Source", back_populates="facts")
    contradictions: Mapped[List["Contradiction"]] = relationship(
        "Contradiction", 
        secondary="fact_contradictions",
        back_populates="facts"
    )


class Contradiction(Base):
    """Contradiction détectée entre plusieurs faits"""
    __tablename__ = "contradictions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("sessions.id"), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="low")  # low, medium, high
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relations
    session: Mapped["Session"] = relationship("Session", back_populates="contradictions")
    facts: Mapped[List["Fact"]] = relationship(
        "Fact",
        secondary="fact_contradictions",
        back_populates="contradictions"
    )


# Table de liaison pour faits-contradictions (many-to-many)
from sqlalchemy import Table

fact_contradictions = Table(
    "fact_contradictions",
    Base.metadata,
    Column("fact_id", String(36), ForeignKey("facts.id"), primary_key=True),
    Column("contradiction_id", String(36), ForeignKey("contradictions.id"), primary_key=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now())
)


class Report(Base):
    """Rapport généré"""
    __tablename__ = "reports"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("sessions.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    executive_summary: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)  # Markdown
    format: Mapped[str] = mapped_column(String(20), default="markdown")
    citations: Mapped[Optional[List[dict]]] = mapped_column(SQLiteJSON, nullable=True)  # BibTeX
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relations
    session: Mapped["Session"] = relationship("Session", back_populates="reports")
#!/usr/bin/env python3
"""
SQLAlchemy ORM Models for Test Results Database
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, BigInteger,
    DateTime, ForeignKey, Index, CheckConstraint
)
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


class Campaign(Base):
    __tablename__ = 'campaigns'

    campaign_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    campaign_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    campaign_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    tests: Mapped[List["Test"]] = relationship("Test", back_populates="campaign", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_campaign_date', 'campaign_date'),
        Index('idx_campaign_name', 'campaign_name'),
    )


class Test(Base):
    __tablename__ = 'tests'

    test_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(Integer, ForeignKey('campaigns.campaign_id', ondelete='CASCADE'), nullable=False)
    test_name: Mapped[str] = mapped_column(String(255), nullable=False)
    test_path: Mapped[Optional[str]] = mapped_column(String(500))
    status: Mapped[Optional[str]] = mapped_column(String(20))
    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    start_timestamp: Mapped[Optional[int]] = mapped_column(BigInteger)
    docstring: Mapped[Optional[str]] = mapped_column(Text)
    analyzer_html_path: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="tests")
    params: Mapped[List["TestParam"]] = relationship("TestParam", back_populates="test", cascade="all, delete-orphan")
    results: Mapped[List["TestResult"]] = relationship("TestResult", back_populates="test", cascade="all, delete-orphan")
    logs: Mapped[List["TestLog"]] = relationship("TestLog", back_populates="test", cascade="all, delete-orphan")
    failure_messages: Mapped[List["FailureMessage"]] = relationship("FailureMessage", back_populates="test", cascade="all, delete-orphan")
    artefacts: Mapped[List["Artefact"]] = relationship("Artefact", back_populates="test")

    __table_args__ = (
        Index('idx_campaign_test', 'campaign_id', 'test_name'),
        Index('idx_status', 'status'),
        Index('idx_start_time', 'start_time'),
        CheckConstraint("status IN ('passed', 'failed', 'unknown')", name='check_status'),
    )


class TestParam(Base):
    __tablename__ = 'test_params'

    param_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    test_id: Mapped[int] = mapped_column(Integer, ForeignKey('tests.test_id', ondelete='CASCADE'), nullable=False)
    param_name: Mapped[str] = mapped_column(String(255), nullable=False)
    param_value: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    test: Mapped["Test"] = relationship("Test", back_populates="params")

    __table_args__ = (
        Index('idx_test_params', 'test_id'),
    )


class TestResult(Base):
    __tablename__ = 'test_results'

    result_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    test_id: Mapped[int] = mapped_column(Integer, ForeignKey('tests.test_id', ondelete='CASCADE'), nullable=False)
    row_index: Mapped[Optional[int]] = mapped_column(Integer)
    timestamp: Mapped[Optional[int]] = mapped_column(BigInteger)
    timestamp_formatted: Mapped[Optional[str]] = mapped_column(String(50))
    pass_: Mapped[Optional[bool]] = mapped_column('pass', Boolean)
    command_method: Mapped[Optional[str]] = mapped_column(String(255))
    command_str: Mapped[Optional[str]] = mapped_column(Text)
    raw_response: Mapped[Optional[str]] = mapped_column(Text)
    peak_frequency: Mapped[Optional[float]] = mapped_column(Float)
    peak_amplitude: Mapped[Optional[float]] = mapped_column(Float)
    failure_messages: Mapped[Optional[str]] = mapped_column(Text)
    is_result_row: Mapped[bool] = mapped_column(Boolean, default=True)
    row_class: Mapped[Optional[str]] = mapped_column(String(50))
    full_data_json: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    test: Mapped["Test"] = relationship("Test", back_populates="results")

    __table_args__ = (
        Index('idx_test_results', 'test_id', 'row_index'),
        Index('idx_pass', 'pass'),
        Index('idx_timestamp', 'timestamp'),
    )


class TestLog(Base):
    __tablename__ = 'test_logs'

    log_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    test_id: Mapped[int] = mapped_column(Integer, ForeignKey('tests.test_id', ondelete='CASCADE'), nullable=False)
    row_index: Mapped[Optional[int]] = mapped_column(Integer)
    timestamp: Mapped[Optional[int]] = mapped_column(BigInteger)
    timestamp_formatted: Mapped[Optional[str]] = mapped_column(String(50))
    level: Mapped[Optional[str]] = mapped_column(String(20))
    message: Mapped[Optional[str]] = mapped_column(Text)
    log_type: Mapped[Optional[str]] = mapped_column(String(50))
    line_number: Mapped[Optional[int]] = mapped_column(Integer)
    full_data_json: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    test: Mapped["Test"] = relationship("Test", back_populates="logs")

    __table_args__ = (
        Index('idx_test_logs', 'test_id', 'row_index'),
        Index('idx_level', 'level'),
        Index('idx_log_timestamp', 'timestamp'),
    )


class FailureMessage(Base):
    __tablename__ = 'failure_messages'

    failure_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    test_id: Mapped[int] = mapped_column(Integer, ForeignKey('tests.test_id', ondelete='CASCADE'), nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    test: Mapped["Test"] = relationship("Test", back_populates="failure_messages")

    __table_args__ = (
        Index('idx_test_failures', 'test_id'),
    )


class Artefact(Base):
    __tablename__ = 'artefacts'

    artefact_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    test_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('tests.test_id', ondelete='SET NULL'))
    artefact_type: Mapped[Optional[str]] = mapped_column(String(20))
    file_path: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64))
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    test: Mapped[Optional["Test"]] = relationship("Test", back_populates="artefacts")
    processing_logs: Mapped[List["ProcessingLog"]] = relationship("ProcessingLog", back_populates="artefact", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_test_artefacts', 'test_id', 'artefact_type'),
        Index('idx_processed', 'processed'),
        Index('idx_file_hash', 'file_hash'),
        CheckConstraint("artefact_type IN ('csv', 'analyzer_html', 'log', 'json', 'screenshot')", name='check_artefact_type'),
    )


class ProcessingLog(Base):
    __tablename__ = 'processing_log'

    log_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    artefact_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('artefacts.artefact_id', ondelete='CASCADE'))
    processing_status: Mapped[Optional[str]] = mapped_column(String(20))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    artefact: Mapped[Optional["Artefact"]] = relationship("Artefact", back_populates="processing_logs")

    __table_args__ = (
        Index('idx_processing_status', 'processing_status'),
        CheckConstraint("processing_status IN ('pending', 'processing', 'completed', 'failed')", name='check_processing_status'),
    )

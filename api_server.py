#!/usr/bin/env python3
"""
FastAPI REST API Server for Test Results Database

Provides RESTful API endpoints for querying test results, campaigns, and analytics.
"""

import os
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from io import StringIO

from fastapi import FastAPI, HTTPException, Query, Depends, Response
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, func, or_, desc, asc
from sqlalchemy.orm import Session, sessionmaker, joinedload

from models import (
    Base, Campaign, Test, TestParam, TestResult,
    TestLog, FailureMessage, Artefact
)


# ============================================================================
# Configuration
# ============================================================================

DB_PATH = os.getenv("DB_PATH", "test_results.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite specific
    echo=False  # Set to True for SQL debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ============================================================================
# Pydantic Models (API Request/Response Schemas)
# ============================================================================

class CampaignSummary(BaseModel):
    campaign_id: int
    campaign_name: str
    campaign_date: Optional[datetime]
    total_tests: int
    passed_tests: int
    failed_tests: int
    unknown_tests: int

    class Config:
        from_attributes = True


class CampaignDetail(BaseModel):
    campaign_id: int
    campaign_name: str
    campaign_date: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class TestSummary(BaseModel):
    test_id: int
    test_name: str
    test_path: Optional[str]
    status: Optional[str]
    start_time: Optional[datetime]
    campaign_id: int
    campaign_name: str
    failure_count: int = 0

    class Config:
        from_attributes = True


class TestDetail(BaseModel):
    test_id: int
    test_name: str
    test_path: Optional[str]
    status: Optional[str]
    start_time: Optional[datetime]
    start_timestamp: Optional[int]
    docstring: Optional[str]
    analyzer_html_path: Optional[str]
    campaign_id: int
    campaign_name: str
    params: Dict[str, str] = {}
    failure_messages: List[str] = []

    class Config:
        from_attributes = True


class TestResultRow(BaseModel):
    result_id: int
    row_index: Optional[int]
    timestamp: Optional[int]
    pass_: Optional[bool] = Field(alias="pass")
    command_method: Optional[str]
    command_str: Optional[str]
    raw_response: Optional[str]
    peak_frequency: Optional[float]
    peak_amplitude: Optional[float]
    failure_messages: Optional[str]

    class Config:
        from_attributes = True
        populate_by_name = True


class TestLogRow(BaseModel):
    log_id: int
    row_index: Optional[int]
    timestamp: Optional[int]
    level: Optional[str]
    message: Optional[str]
    log_type: Optional[str]
    line_number: Optional[int]

    class Config:
        from_attributes = True


class GlobalSummary(BaseModel):
    total_campaigns: int
    total_tests: int
    passed_tests: int
    failed_tests: int
    unknown_tests: int
    pass_rate: float
    total_results: int
    total_logs: int


class CommonFailure(BaseModel):
    message: str
    count: int
    test_names: List[str]


# ============================================================================
# Database Dependency
# ============================================================================

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="Test Results API",
    description="REST API for querying test results, campaigns, and analytics",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Campaign Endpoints
# ============================================================================

@app.get("/api/campaigns", response_model=List[CampaignSummary])
async def list_campaigns(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    order_by: str = Query("date", regex="^(date|name)$"),
    direction: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    """List all campaigns with summary statistics"""

    # Build query
    query = db.query(
        Campaign.campaign_id,
        Campaign.campaign_name,
        Campaign.campaign_date,
        func.count(Test.test_id).label('total_tests'),
        func.sum(func.case((Test.status == 'passed', 1), else_=0)).label('passed_tests'),
        func.sum(func.case((Test.status == 'failed', 1), else_=0)).label('failed_tests'),
        func.sum(func.case((Test.status == 'unknown', 1), else_=0)).label('unknown_tests'),
    ).outerjoin(Test).group_by(Campaign.campaign_id)

    # Apply ordering
    if order_by == "date":
        order_col = Campaign.campaign_date
    else:
        order_col = Campaign.campaign_name

    if direction == "desc":
        query = query.order_by(desc(order_col))
    else:
        query = query.order_by(asc(order_col))

    # Apply pagination
    query = query.limit(limit).offset(offset)

    results = query.all()

    return [
        CampaignSummary(
            campaign_id=r.campaign_id,
            campaign_name=r.campaign_name,
            campaign_date=r.campaign_date,
            total_tests=r.total_tests or 0,
            passed_tests=r.passed_tests or 0,
            failed_tests=r.failed_tests or 0,
            unknown_tests=r.unknown_tests or 0,
        )
        for r in results
    ]


@app.get("/api/campaigns/{campaign_id}", response_model=CampaignDetail)
async def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """Get campaign details"""
    campaign = db.query(Campaign).filter(Campaign.campaign_id == campaign_id).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return campaign


@app.get("/api/campaigns/{campaign_id}/tests", response_model=List[TestSummary])
async def get_campaign_tests(
    campaign_id: int,
    status: Optional[str] = Query(None, regex="^(passed|failed|unknown)$"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List tests in a campaign"""

    # Verify campaign exists
    campaign = db.query(Campaign).filter(Campaign.campaign_id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Build query
    query = db.query(Test).filter(Test.campaign_id == campaign_id)

    # Apply status filter
    if status:
        query = query.filter(Test.status == status)

    # Order by start time
    query = query.order_by(Test.start_time)

    # Pagination
    query = query.limit(limit).offset(offset)

    tests = query.all()

    # Get failure counts
    test_summaries = []
    for test in tests:
        failure_count = db.query(func.count(FailureMessage.failure_id)).filter(
            FailureMessage.test_id == test.test_id
        ).scalar()

        test_summaries.append(TestSummary(
            test_id=test.test_id,
            test_name=test.test_name,
            test_path=test.test_path,
            status=test.status,
            start_time=test.start_time,
            campaign_id=test.campaign_id,
            campaign_name=campaign.campaign_name,
            failure_count=failure_count or 0
        ))

    return test_summaries


# ============================================================================
# Test Endpoints
# ============================================================================

@app.get("/api/tests", response_model=List[TestSummary])
async def search_tests(
    status: Optional[str] = Query(None, regex="^(passed|failed|unknown)$"),
    campaign_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Search and filter tests across all campaigns"""

    # Build query
    query = db.query(Test).join(Campaign)

    # Apply filters
    if status:
        query = query.filter(Test.status == status)

    if campaign_id:
        query = query.filter(Test.campaign_id == campaign_id)

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(Test.start_time >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use ISO format.")

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(Test.start_time <= end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use ISO format.")

    if search:
        # Search in test name and failure messages
        query = query.outerjoin(FailureMessage).filter(
            or_(
                Test.test_name.like(f"%{search}%"),
                FailureMessage.message.like(f"%{search}%")
            )
        ).distinct()

    # Order by start time descending
    query = query.order_by(desc(Test.start_time))

    # Pagination
    query = query.limit(limit).offset(offset)

    tests = query.all()

    # Build response with campaign names
    test_summaries = []
    for test in tests:
        failure_count = db.query(func.count(FailureMessage.failure_id)).filter(
            FailureMessage.test_id == test.test_id
        ).scalar()

        test_summaries.append(TestSummary(
            test_id=test.test_id,
            test_name=test.test_name,
            test_path=test.test_path,
            status=test.status,
            start_time=test.start_time,
            campaign_id=test.campaign_id,
            campaign_name=test.campaign.campaign_name,
            failure_count=failure_count or 0
        ))

    return test_summaries


@app.get("/api/tests/{test_id}", response_model=TestDetail)
async def get_test(test_id: int, db: Session = Depends(get_db)):
    """Get complete test details"""

    test = db.query(Test).options(
        joinedload(Test.campaign),
        joinedload(Test.params),
        joinedload(Test.failure_messages)
    ).filter(Test.test_id == test_id).first()

    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    # Build params dict
    params_dict = {p.param_name: p.param_value for p in test.params}

    # Build failure messages list
    failure_msgs = [f.message for f in test.failure_messages if f.message]

    return TestDetail(
        test_id=test.test_id,
        test_name=test.test_name,
        test_path=test.test_path,
        status=test.status,
        start_time=test.start_time,
        start_timestamp=test.start_timestamp,
        docstring=test.docstring,
        analyzer_html_path=test.analyzer_html_path,
        campaign_id=test.campaign_id,
        campaign_name=test.campaign.campaign_name,
        params=params_dict,
        failure_messages=failure_msgs
    )


@app.get("/api/tests/{test_id}/results", response_model=List[TestResultRow])
async def get_test_results(
    test_id: int,
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get test results (result rows from CSV)"""

    # Verify test exists
    test = db.query(Test).filter(Test.test_id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    # Get results
    results = db.query(TestResult).filter(
        TestResult.test_id == test_id
    ).order_by(TestResult.row_index).limit(limit).offset(offset).all()

    return results


@app.get("/api/tests/{test_id}/logs", response_model=List[TestLogRow])
async def get_test_logs(
    test_id: int,
    level: Optional[str] = None,
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get test logs"""

    # Verify test exists
    test = db.query(Test).filter(Test.test_id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    # Build query
    query = db.query(TestLog).filter(TestLog.test_id == test_id)

    if level:
        query = query.filter(TestLog.level == level.upper())

    logs = query.order_by(TestLog.row_index).limit(limit).offset(offset).all()

    return logs


@app.get("/api/tests/{test_id}/failures", response_model=List[str])
async def get_test_failures(test_id: int, db: Session = Depends(get_db)):
    """Get failure messages for a test"""

    # Verify test exists
    test = db.query(Test).filter(Test.test_id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    failures = db.query(FailureMessage).filter(
        FailureMessage.test_id == test_id
    ).all()

    return [f.message for f in failures if f.message]


# ============================================================================
# Statistics & Analytics Endpoints
# ============================================================================

@app.get("/api/stats/summary", response_model=GlobalSummary)
async def get_global_summary(db: Session = Depends(get_db)):
    """Get global summary statistics"""

    total_campaigns = db.query(func.count(Campaign.campaign_id)).scalar()
    total_tests = db.query(func.count(Test.test_id)).scalar()
    passed_tests = db.query(func.count(Test.test_id)).filter(Test.status == 'passed').scalar()
    failed_tests = db.query(func.count(Test.test_id)).filter(Test.status == 'failed').scalar()
    unknown_tests = db.query(func.count(Test.test_id)).filter(Test.status == 'unknown').scalar()
    total_results = db.query(func.count(TestResult.result_id)).scalar()
    total_logs = db.query(func.count(TestLog.log_id)).scalar()

    pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0.0

    return GlobalSummary(
        total_campaigns=total_campaigns or 0,
        total_tests=total_tests or 0,
        passed_tests=passed_tests or 0,
        failed_tests=failed_tests or 0,
        unknown_tests=unknown_tests or 0,
        pass_rate=round(pass_rate, 2),
        total_results=total_results or 0,
        total_logs=total_logs or 0
    )


@app.get("/api/failures/common", response_model=List[CommonFailure])
async def get_common_failures(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get most common failure messages"""

    # Group by message and count
    failures = db.query(
        FailureMessage.message,
        func.count(FailureMessage.failure_id).label('count')
    ).filter(
        FailureMessage.message.isnot(None),
        FailureMessage.message != ''
    ).group_by(FailureMessage.message).order_by(
        desc('count')
    ).limit(limit).all()

    # For each failure, get test names
    common_failures = []
    for failure in failures:
        test_names = db.query(Test.test_name).join(FailureMessage).filter(
            FailureMessage.message == failure.message
        ).distinct().limit(10).all()

        common_failures.append(CommonFailure(
            message=failure.message,
            count=failure.count,
            test_names=[t.test_name for t in test_names]
        ))

    return common_failures


# ============================================================================
# Export Endpoints
# ============================================================================

@app.get("/api/export/failures")
async def export_failures(
    campaign_id: Optional[int] = None,
    format: str = Query("csv", regex="^(csv|json)$"),
    db: Session = Depends(get_db)
):
    """Export all failures to CSV or JSON"""

    # Build query
    query = db.query(
        Campaign.campaign_name,
        Campaign.campaign_date,
        Test.test_name,
        Test.test_path,
        Test.start_time,
        Test.start_timestamp,
        FailureMessage.message
    ).join(Test).join(FailureMessage).filter(
        Test.status == 'failed'
    )

    if campaign_id:
        query = query.filter(Campaign.campaign_id == campaign_id)

    query = query.order_by(Test.start_time)

    results = query.all()

    if format == "csv":
        # Generate CSV
        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            'Campaign',
            'Campaign Date',
            'Test Name',
            'Test Path',
            'Start Time',
            'Failure Message'
        ])

        # Data
        for r in results:
            writer.writerow([
                r.campaign_name,
                r.campaign_date.isoformat() if r.campaign_date else '',
                r.test_name,
                r.test_path or '',
                r.start_time.isoformat() if r.start_time else '',
                r.message or ''
            ])

        output.seek(0)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"failures_{len(results)}_items_{timestamp}.csv"

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    else:
        # Generate JSON
        data = [
            {
                "campaign": r.campaign_name,
                "campaign_date": r.campaign_date.isoformat() if r.campaign_date else None,
                "test_name": r.test_name,
                "test_path": r.test_path,
                "start_time": r.start_time.isoformat() if r.start_time else None,
                "start_timestamp": r.start_timestamp,
                "failure_message": r.message
            }
            for r in results
        ]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"failures_{len(results)}_items_{timestamp}.json"

        return Response(
            content=json.dumps(data, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )


@app.get("/api/export/tests")
async def export_tests(
    status: Optional[str] = Query(None, regex="^(passed|failed|unknown)$"),
    campaign_id: Optional[int] = None,
    format: str = Query("csv", regex="^(csv|json)$"),
    db: Session = Depends(get_db)
):
    """Export test results based on filters"""

    # Build query
    query = db.query(
        Campaign.campaign_name,
        Campaign.campaign_date,
        Test.test_name,
        Test.test_path,
        Test.status,
        Test.start_time,
        Test.docstring
    ).join(Campaign)

    if status:
        query = query.filter(Test.status == status)

    if campaign_id:
        query = query.filter(Test.campaign_id == campaign_id)

    query = query.order_by(Test.start_time)

    results = query.all()

    if format == "csv":
        output = StringIO()
        writer = csv.writer(output)

        writer.writerow([
            'Campaign',
            'Campaign Date',
            'Test Name',
            'Test Path',
            'Status',
            'Start Time',
            'Docstring'
        ])

        for r in results:
            writer.writerow([
                r.campaign_name,
                r.campaign_date.isoformat() if r.campaign_date else '',
                r.test_name,
                r.test_path or '',
                r.status or '',
                r.start_time.isoformat() if r.start_time else '',
                r.docstring or ''
            ])

        output.seek(0)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tests_{len(results)}_items_{timestamp}.csv"

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    else:
        data = [
            {
                "campaign": r.campaign_name,
                "campaign_date": r.campaign_date.isoformat() if r.campaign_date else None,
                "test_name": r.test_name,
                "test_path": r.test_path,
                "status": r.status,
                "start_time": r.start_time.isoformat() if r.start_time else None,
                "docstring": r.docstring
            }
            for r in results
        ]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tests_{len(results)}_items_{timestamp}.json"

        return Response(
            content=json.dumps(data, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )


# ============================================================================
# Artefact Access Endpoints
# ============================================================================

@app.get("/api/artefacts/{test_id}/analyzer")
async def get_analyzer_html(test_id: int, db: Session = Depends(get_db)):
    """Serve the analyzer.html file for a test"""

    test = db.query(Test).filter(Test.test_id == test_id).first()

    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    if not test.analyzer_html_path:
        raise HTTPException(status_code=404, detail="Analyzer HTML not found for this test")

    html_path = Path(test.analyzer_html_path)

    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Analyzer HTML file does not exist")

    return FileResponse(
        path=str(html_path),
        media_type="text/html",
        filename=html_path.name
    )


@app.get("/api/artefacts/{test_id}/csv")
async def get_test_csv(test_id: int, db: Session = Depends(get_db)):
    """Serve the raw combined CSV file for a test"""

    # Find CSV artefact
    artefact = db.query(Artefact).filter(
        Artefact.test_id == test_id,
        Artefact.artefact_type == 'csv'
    ).first()

    if not artefact:
        raise HTTPException(status_code=404, detail="CSV file not found for this test")

    csv_path = Path(artefact.file_path)

    if not csv_path.exists():
        raise HTTPException(status_code=404, detail="CSV file does not exist")

    return FileResponse(
        path=str(csv_path),
        media_type="text/csv",
        filename=csv_path.name
    )


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """API health check"""
    try:
        # Test database connection
        db.query(Campaign).first()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print("Starting Test Results API Server...")
    print(f"Database: {DB_PATH}")
    print("API Documentation: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/health")

    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )

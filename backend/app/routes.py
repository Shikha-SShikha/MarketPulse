"""API routes for the STM Intelligence Brief System."""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Header, Query, Response, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.schemas import (
    SignalCreate,
    SignalResponse,
    SignalListResponse,
    SemanticSearchResponse,
    SemanticSearchResult,
    ErrorResponse,
    ThemeResponse,
    ThemeWithSignalsResponse,
    WeeklyBriefResponse,
    WeeklyBriefSummary,
    WeeklyBriefFullResponse,
    GenerateBriefResponse,
    CollectSignalsResponse,
    SignalStatusUpdate,
    DataSourceCreate,
    DataSourceResponse,
    DataSourceUpdate,
    NotificationResponse,
    NotificationUpdate,
    EntityCreate,
    EntityUpdate,
    EntityResponse,
    EntityListResponse,
    SegmentStatsResponse,
    SignalSummaryResponse,
    EvaluationRunResponse,
    EvaluationIssueResponse,
    EvaluationStatsResponse,
)
from app.services import (
    create_signal,
    get_signal,
    get_signals,
    soft_delete_signal,
    get_current_brief,
    get_brief_by_id,
    get_themes_by_ids,
    get_signals_by_ids,
    create_notification,
    get_entities,
    get_entity_by_id,
    create_entity,
    update_entity,
    delete_entity,
    get_segment_statistics,
    generate_signal_summary,
)
from app.models import Signal, DataSource, Notification, WeeklyBrief
from app.jobs import generate_weekly_brief_job, collect_signals_job_sync


router = APIRouter()


def verify_curator_token(authorization: Optional[str] = Header(None)) -> str:
    """
    Verify the curator token from Authorization header.

    Args:
        authorization: Authorization header value (Bearer <token>)

    Returns:
        Curator name extracted from token (for now, just "curator")

    Raises:
        HTTPException: If token is missing or invalid
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing Authorization header",
        )

    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Authorization header format. Use 'Bearer <token>'",
        )

    token = parts[1]
    settings = get_settings()
    if token != settings.curator_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid curator token",
        )

    return "curator"


@router.post(
    "/signals",
    response_model=SignalResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        403: {"model": ErrorResponse, "description": "Forbidden - invalid token"},
    },
)
def create_signal_endpoint(
    signal_data: SignalCreate,
    db: Session = Depends(get_db),
    curator_name: str = Depends(verify_curator_token),
):
    """
    Create a new signal.

    Requires valid curator token in Authorization header.
    """
    signal = create_signal(db, signal_data, curator_name)
    return signal


def _signal_to_response(signal: Signal) -> SignalResponse:
    """Convert Signal ORM object to SignalResponse with entities populated."""
    from .schemas import EntityResponse

    # Convert Signal to dict
    signal_dict = {
        "id": signal.id,
        "entity": signal.entity,
        "event_type": signal.event_type,
        "topic": signal.topic,
        "source_url": signal.source_url,
        "evidence_snippet": signal.evidence_snippet,
        "confidence": signal.confidence,
        "impact_areas": signal.impact_areas,
        "entity_tags": signal.entity_tags,
        "created_at": signal.created_at,
        "curator_name": signal.curator_name,
        "notes": signal.notes,
        "status": signal.status,
        "data_source_id": signal.data_source_id,
        "reviewed_at": signal.reviewed_at,
        "reviewed_by": signal.reviewed_by,
    }

    # Add entities if available
    if signal.entity_links:
        signal_dict["entities"] = [
            EntityResponse.model_validate(link.entity) for link in signal.entity_links
        ]

    return SignalResponse(**signal_dict)


@router.get(
    "/signals",
    response_model=SignalListResponse,
)
def list_signals_endpoint(
    limit: int = Query(default=50, ge=1, le=100, description="Max signals to return"),
    offset: int = Query(default=0, ge=0, description="Number of signals to skip"),
    entity: Optional[str] = Query(default=None, description="Filter by entity name"),
    topic: Optional[str] = Query(default=None, description="Filter by topic"),
    segment: Optional[str] = Query(default=None, description="Filter by entity segment (customer, competitor, industry, influencer)"),
    impact_area: Optional[str] = Query(default=None, description="Filter by impact area (Ops, Tech, Integrity, Procurement)"),
    start_date: Optional[str] = Query(default=None, description="Filter signals created on or after this date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="Filter signals created on or before this date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """
    List signals with optional filtering.

    No authentication required for reading.
    """
    from datetime import datetime

    # Parse date strings to date objects
    start_date_obj = None
    end_date_obj = None

    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD"
            )

    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD"
            )

    signals, total = get_signals(
        db,
        limit=limit,
        offset=offset,
        entity=entity,
        topic=topic,
        segment=segment,
        impact_area=impact_area,
        start_date=start_date_obj,
        end_date=end_date_obj
    )
    return SignalListResponse(
        signals=[_signal_to_response(s) for s in signals],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/signals/search",
    response_model=SemanticSearchResponse,
)
def semantic_search_signals_endpoint(
    q: str = Query(..., description="Natural language search query", min_length=3),
    limit: int = Query(default=20, ge=1, le=50, description="Max results to return"),
    threshold: float = Query(default=0.7, ge=0.0, le=1.0, description="Minimum similarity threshold (0-1)"),
    entity: Optional[str] = Query(default=None, description="Filter by entity name"),
    topic: Optional[str] = Query(default=None, description="Filter by topic"),
    days_back: Optional[int] = Query(default=None, ge=1, le=365, description="Limit to signals from last N days"),
    db: Session = Depends(get_db),
):
    """
    Perform semantic search on signals using natural language queries.

    This endpoint uses RAG (Retrieval Augmented Generation) with vector embeddings
    to find signals semantically similar to your query, even if they don't contain
    the exact keywords.

    **Example queries:**
    - "AI tools for detecting manuscript fraud"
    - "What are competitors doing with integrity checking?"
    - "Publishers complaining about peer review quality"
    - "New partnerships in open access"

    Returns signals ranked by semantic similarity with similarity scores.

    No authentication required for reading.
    """
    from app.services import semantic_search_signals

    # Perform semantic search
    results = semantic_search_signals(
        db=db,
        query=q,
        limit=limit,
        similarity_threshold=threshold,
        entity=entity,
        topic=topic,
        days_back=days_back,
    )

    # Convert to response format
    search_results = [
        SemanticSearchResult(
            signal=_signal_to_response(signal),
            similarity_score=round(score, 3)  # Round to 3 decimal places
        )
        for signal, score in results
    ]

    return SemanticSearchResponse(
        query=q,
        results=search_results,
        total=len(search_results),
    )


@router.get(
    "/signals/summary",
    response_model=SignalSummaryResponse,
)
def get_signals_summary_endpoint(
    entity: Optional[str] = Query(default=None, description="Filter by entity name"),
    topic: Optional[str] = Query(default=None, description="Filter by topic"),
    segment: Optional[str] = Query(default=None, description="Filter by entity segment (customer, competitor, industry, influencer)"),
    start_date: Optional[str] = Query(default=None, description="Filter signals created on or after this date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="Filter signals created on or before this date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """
    Generate an AI-powered executive summary of filtered signals.

    Accepts the same filter parameters as GET /signals.
    Returns a structured summary with key insights and traceability to source signals.

    No authentication required for reading.
    """
    from datetime import datetime

    # Parse date strings to date objects
    start_date_obj = None
    end_date_obj = None

    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD"
            )

    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD"
            )

    # Get signals with filters (no limit for summary)
    signals, total = get_signals(
        db,
        limit=1000,  # Reasonable limit for summary generation
        offset=0,
        entity=entity,
        topic=topic,
        segment=segment,
        start_date=start_date_obj,
        end_date=end_date_obj,
        include_entities=True,  # Need entity relationships for segments
    )

    # Generate summary
    summary_dict = generate_signal_summary(signals)

    return SignalSummaryResponse(**summary_dict)


@router.get(
    "/signals/{signal_id}",
    response_model=SignalResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Signal not found"},
    },
)
def get_signal_endpoint(
    signal_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get a signal by ID.

    No authentication required for reading.
    """
    signal = get_signal(db, signal_id)
    if not signal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Signal {signal_id} not found",
        )
    return signal


@router.delete(
    "/signals/{signal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        403: {"model": ErrorResponse, "description": "Forbidden - invalid token"},
        404: {"model": ErrorResponse, "description": "Signal not found"},
    },
)
def delete_signal_endpoint(
    signal_id: UUID,
    db: Session = Depends(get_db),
    curator_name: str = Depends(verify_curator_token),
):
    """
    Soft delete a signal.

    Requires valid curator token in Authorization header.
    """
    signal = soft_delete_signal(db, signal_id)
    if not signal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Signal {signal_id} not found",
        )
    return None


# =============================================================================
# Weekly Brief Endpoints
# =============================================================================

def build_full_brief_response(brief, db: Session) -> WeeklyBriefFullResponse:
    """
    Build a full brief response with themes and signals.

    Args:
        brief: WeeklyBrief ORM object
        db: Database session

    Returns:
        WeeklyBriefFullResponse with all data
    """
    # Get themes in order
    themes = get_themes_by_ids(db, brief.theme_ids)

    # Collect all signal IDs from all themes
    all_signal_ids = []
    for theme in themes:
        all_signal_ids.extend(theme.signal_ids or [])

    # Get all signals in one query
    signals_map = get_signals_by_ids(db, all_signal_ids)

    # Build themes with signals
    themes_with_signals = []
    for theme in themes:
        theme_signals = [
            SignalResponse.model_validate(signals_map[sid])
            for sid in (theme.signal_ids or [])
            if sid in signals_map
        ]
        themes_with_signals.append(
            ThemeWithSignalsResponse(
                id=theme.id,
                title=theme.title,
                key_players=theme.key_players or [],
                aggregate_confidence=theme.aggregate_confidence,
                impact_areas=theme.impact_areas or [],
                so_what=theme.so_what,
                now_what=theme.now_what or [],
                created_at=theme.created_at,
                signals=theme_signals,
            )
        )

    return WeeklyBriefFullResponse(
        id=brief.id,
        week_start=brief.week_start,
        week_end=brief.week_end,
        generated_at=brief.generated_at,
        total_signals=brief.total_signals,
        coverage_areas=brief.coverage_areas or [],
        themes=themes_with_signals,
    )


@router.get(
    "/briefs",
    response_model=List[WeeklyBriefSummary],
)
def list_briefs_endpoint(db: Session = Depends(get_db)):
    """
    List all weekly briefs in reverse chronological order.

    Returns brief summaries without full theme/signal details.
    No authentication required for reading.
    """
    briefs = db.query(WeeklyBrief).order_by(WeeklyBrief.generated_at.desc()).all()

    return [
        WeeklyBriefSummary(
            id=brief.id,
            week_start=brief.week_start,
            week_end=brief.week_end,
            generated_at=brief.generated_at,
            total_signals=brief.total_signals,
            coverage_areas=brief.coverage_areas,
            theme_count=len(brief.theme_ids),
        )
        for brief in briefs
    ]


@router.get(
    "/briefs/current",
    response_model=WeeklyBriefFullResponse,
    responses={
        204: {"description": "No brief available"},
    },
)
def get_current_brief_endpoint(db: Session = Depends(get_db)):
    """
    Get the current (most recent) weekly brief.

    Returns the full brief with all themes and contributing signals.
    No authentication required for reading.
    """
    brief = get_current_brief(db)
    if not brief:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return build_full_brief_response(brief, db)


@router.get(
    "/briefs/{brief_id}",
    response_model=WeeklyBriefFullResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Brief not found"},
    },
)
def get_brief_endpoint(
    brief_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get a specific weekly brief by ID.

    Returns the full brief with all themes and contributing signals.
    No authentication required for reading.
    """
    brief = get_brief_by_id(db, brief_id)
    if not brief:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brief {brief_id} not found",
        )

    return build_full_brief_response(brief, db)


@router.get(
    "/briefs/{brief_id}/download",
    responses={
        200: {"description": "PDF file", "content": {"application/pdf": {}}},
        404: {"model": ErrorResponse, "description": "Brief not found"},
    },
)
def download_brief_pdf_endpoint(
    brief_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Download a weekly brief as a PDF file.

    Generates a professionally formatted PDF with:
    - Carbon Design System styling
    - AI-GENERATED CONTENT watermark on every page
    - All brief content: themes, "Why It Matters", "Next Steps", Key Players
    - Supporting signals with evidence

    No authentication required for reading.
    """
    from datetime import datetime
    from app.pdf_generator import generate_brief_pdf

    # Get the brief
    brief = get_brief_by_id(db, brief_id)
    if not brief:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brief {brief_id} not found",
        )

    # Get themes in order
    themes = get_themes_by_ids(db, brief.theme_ids)

    # Get all signals
    all_signal_ids = []
    for theme in themes:
        all_signal_ids.extend(theme.signal_ids or [])

    signals_map = get_signals_by_ids(db, all_signal_ids)

    # Generate PDF
    pdf_buffer = generate_brief_pdf(db, brief, themes, signals_map)

    # Generate filename with date
    week_start = datetime.fromisoformat(str(brief.week_start)).strftime('%Y-%m-%d')
    filename = f"STM_Intelligence_Brief_{week_start}.pdf"

    # Return PDF as download
    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.post(
    "/admin/generate-brief",
    response_model=GenerateBriefResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Forbidden - invalid token"},
    },
)
def generate_brief_endpoint(
    db: Session = Depends(get_db),
    curator_name: str = Depends(verify_curator_token),
):
    """
    Manually trigger weekly brief generation.

    Generates a brief for the current week. Idempotent - if a brief
    already exists for the week, returns the existing brief info.

    Requires valid curator token in Authorization header.
    """
    result = generate_weekly_brief_job()

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["message"],
        )

    return GenerateBriefResponse(
        message=result["message"],
        brief_id=result["brief_id"],
        week_start=result["week_start"],
        week_end=result["week_end"],
        themes_created=result["themes_created"],
        signals_processed=result["signals_processed"],
    )


@router.post(
    "/admin/collect-signals",
    response_model=CollectSignalsResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Forbidden - invalid token"},
    },
)
def collect_signals_endpoint(
    db: Session = Depends(get_db),
    curator_name: str = Depends(verify_curator_token),
):
    """
    Manually trigger signal collection from all enabled data sources.

    Collects signals from RSS feeds, LinkedIn, web scraping, and email
    sources that are configured and enabled.

    Requires valid curator token in Authorization header.
    """
    result = collect_signals_job_sync()

    if not result["success"]:
        # Still return the result even if there were errors
        # The errors list will contain details
        pass

    return CollectSignalsResponse(
        message=result["message"],
        signals_collected=result["signals_collected"],
        signals_pending_review=result["signals_pending_review"],
        sources_processed=result["sources_processed"],
        errors=result["errors"],
    )


@router.post(
    "/admin/evaluate-brief",
    responses={
        403: {"model": ErrorResponse, "description": "Forbidden - invalid token"},
    },
)
def evaluate_brief_endpoint(
    db: Session = Depends(get_db),
    curator_name: str = Depends(verify_curator_token),
):
    """
    Manually trigger evaluation of all themes in the current brief.

    Runs quality evaluations (hallucination checks, grounding, relevance, etc.)
    on all themes in the most recent weekly brief.

    Requires valid curator token in Authorization header.
    """
    from app import evaluations
    from app.services import get_current_brief, get_themes_by_ids

    # Get current brief
    brief = get_current_brief(db)
    if not brief:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No current brief found. Generate a brief first."
        )

    # Get all themes
    themes = get_themes_by_ids(db, brief.theme_ids)

    if not themes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No themes found in current brief."
        )

    # Evaluate each theme
    evaluated_count = 0
    passed_count = 0
    failed_count = 0
    errors = []

    for theme in themes:
        try:
            content_data = {
                'title': theme.title,
                'so_what': theme.so_what,
                'now_what': theme.now_what,
                'key_players': theme.key_players,
                'signal_ids': [str(sid) for sid in theme.signal_ids],
            }

            eval_run = evaluations.evaluate_content(
                db=db,
                content_type='theme',
                content_id=theme.id,
                content_data=content_data,
            )

            evaluated_count += 1
            if eval_run.passed:
                passed_count += 1
            else:
                failed_count += 1

        except Exception as e:
            logger.error(f"Error evaluating theme {theme.id}: {e}")
            errors.append(f"Theme {theme.id}: {str(e)}")

    return {
        "message": "Brief evaluation completed",
        "brief_id": str(brief.id),
        "evaluated_count": evaluated_count,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "errors": errors,
    }


# =============================================================================
# Signal Review Endpoints
# =============================================================================

@router.get(
    "/admin/signals/pending",
    response_model=SignalListResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Forbidden - invalid token"},
    },
)
def get_pending_signals_endpoint(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    curator_name: str = Depends(verify_curator_token),
):
    """
    Get signals pending curator review.

    Returns signals with status='pending_review' that need manual approval.
    Requires valid curator token in Authorization header.
    """
    signals, total = get_signals(
        db,
        limit=limit,
        offset=offset,
        status="pending_review"
    )

    return SignalListResponse(
        signals=[SignalResponse.model_validate(s) for s in signals],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.patch(
    "/admin/signals/{signal_id}/status",
    response_model=SignalResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Forbidden - invalid token"},
        404: {"model": ErrorResponse, "description": "Signal not found"},
    },
)
def update_signal_status_endpoint(
    signal_id: UUID,
    status_update: SignalStatusUpdate,
    db: Session = Depends(get_db),
    curator_name: str = Depends(verify_curator_token),
):
    """
    Update signal status (approve or reject).

    Allows curators to approve or reject signals pending review.
    Requires valid curator token in Authorization header.
    """
    from datetime import datetime
    from app.models import Signal

    signal = db.query(Signal).filter(Signal.id == signal_id).first()

    if not signal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signal not found"
        )

    # Update status and review metadata
    signal.status = status_update.status.value
    signal.reviewed_at = datetime.utcnow()
    signal.reviewed_by = status_update.reviewer_name or curator_name

    db.commit()
    db.refresh(signal)

    return SignalResponse.model_validate(signal)


# =============================================================================
# Data Source Management Endpoints
# =============================================================================

@router.get(
    "/admin/data-sources",
    response_model=List[DataSourceResponse],
    responses={
        403: {"model": ErrorResponse, "description": "Forbidden - invalid token"},
    },
)
def list_data_sources_endpoint(
    db: Session = Depends(get_db),
    curator_name: str = Depends(verify_curator_token),
):
    """
    List all data sources.

    Returns all configured data sources with their collection metadata.
    Requires valid curator token in Authorization header.
    """
    sources = db.query(DataSource).order_by(DataSource.created_at.desc()).all()
    return [DataSourceResponse.model_validate(s) for s in sources]


@router.post(
    "/admin/data-sources",
    response_model=DataSourceResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        403: {"model": ErrorResponse, "description": "Forbidden - invalid token"},
    },
)
def create_data_source_endpoint(
    source_data: DataSourceCreate,
    db: Session = Depends(get_db),
    curator_name: str = Depends(verify_curator_token),
):
    """
    Create a new data source.

    Adds a new RSS feed, web scraper, or other data source.
    Requires valid curator token in Authorization header.
    """
    from datetime import datetime
    from uuid import uuid4

    source = DataSource(
        id=uuid4(),
        name=source_data.name,
        source_type=source_data.source_type.value,
        url=source_data.url,
        config=source_data.config,
        enabled=source_data.enabled,
        default_confidence=source_data.default_confidence.value,
        default_impact_areas=[area.value for area in (source_data.default_impact_areas or [])],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(source)
    db.commit()
    db.refresh(source)

    return DataSourceResponse.model_validate(source)


@router.patch(
    "/admin/data-sources/{source_id}",
    response_model=DataSourceResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Forbidden - invalid token"},
        404: {"model": ErrorResponse, "description": "Data source not found"},
    },
)
def update_data_source_endpoint(
    source_id: UUID,
    source_update: DataSourceUpdate,
    db: Session = Depends(get_db),
    curator_name: str = Depends(verify_curator_token),
):
    """
    Update a data source.

    Modify data source configuration, enable/disable collection, etc.
    Requires valid curator token in Authorization header.
    """
    from datetime import datetime

    source = db.query(DataSource).filter(DataSource.id == source_id).first()

    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data source not found"
        )

    # Update fields if provided
    if source_update.name is not None:
        source.name = source_update.name
    if source_update.url is not None:
        source.url = source_update.url
    if source_update.config is not None:
        source.config = source_update.config
    if source_update.enabled is not None:
        source.enabled = source_update.enabled
    if source_update.default_confidence is not None:
        source.default_confidence = source_update.default_confidence.value
    if source_update.default_impact_areas is not None:
        source.default_impact_areas = [area.value for area in source_update.default_impact_areas]

    source.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(source)

    return DataSourceResponse.model_validate(source)


@router.delete(
    "/admin/data-sources/{source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        403: {"model": ErrorResponse, "description": "Forbidden - invalid token"},
        404: {"model": ErrorResponse, "description": "Data source not found"},
    },
)
def delete_data_source_endpoint(
    source_id: UUID,
    db: Session = Depends(get_db),
    curator_name: str = Depends(verify_curator_token),
):
    """
    Delete a data source.

    Removes a data source from the system. Signals collected from this
    source will remain in the database.
    Requires valid curator token in Authorization header.
    """
    source = db.query(DataSource).filter(DataSource.id == source_id).first()

    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data source not found"
        )

    db.delete(source)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# =============================================================================
# Notification Endpoints
# =============================================================================

@router.get(
    "/notifications",
    response_model=List[NotificationResponse],
)
def get_notifications_endpoint(
    unread_only: bool = Query(default=True),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Get notifications.

    Returns recent notifications for the curator dashboard.
    No authentication required (public endpoint).
    """
    query = db.query(Notification)

    if unread_only:
        query = query.filter(
            Notification.read == False,
            Notification.dismissed == False
        )

    notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()

    return [NotificationResponse.model_validate(n) for n in notifications]


@router.patch(
    "/notifications/{notification_id}/read",
    response_model=NotificationResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Notification not found"},
    },
)
def mark_notification_read_endpoint(
    notification_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Mark a notification as read.

    Updates the notification status to read.
    No authentication required (public endpoint).
    """
    notification = db.query(Notification).filter(Notification.id == notification_id).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    notification.read = True
    db.commit()
    db.refresh(notification)

    return NotificationResponse.model_validate(notification)


# =============================================================================
# Entity Management Endpoints
# =============================================================================

@router.get(
    "/admin/entities",
    response_model=EntityListResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Forbidden - invalid token"},
    },
)
def list_entities_endpoint(
    segment: Optional[str] = Query(default=None, description="Filter by segment"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    curator_name: str = Depends(verify_curator_token),
):
    """
    List all entities with optional segment filtering.

    Returns entities sorted alphabetically by name.
    Requires valid curator token in Authorization header.
    """
    entities, total = get_entities(
        db,
        segment=segment,
        limit=limit,
        offset=offset
    )

    return EntityListResponse(
        entities=[EntityResponse.model_validate(e) for e in entities],
        total=total,
    )


@router.post(
    "/admin/entities",
    response_model=EntityResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        403: {"model": ErrorResponse, "description": "Forbidden - invalid token"},
    },
)
def create_entity_endpoint(
    entity_data: EntityCreate,
    db: Session = Depends(get_db),
    curator_name: str = Depends(verify_curator_token),
):
    """
    Create a new entity.

    Adds a new entity to the system for tracking in signals.
    Requires valid curator token in Authorization header.
    """
    entity = create_entity(db, entity_data)
    return EntityResponse.model_validate(entity)


@router.get(
    "/admin/entities/{entity_id}",
    response_model=EntityResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Forbidden - invalid token"},
        404: {"model": ErrorResponse, "description": "Entity not found"},
    },
)
def get_entity_endpoint(
    entity_id: UUID,
    db: Session = Depends(get_db),
    curator_name: str = Depends(verify_curator_token),
):
    """
    Get an entity by ID.

    Returns detailed entity information.
    Requires valid curator token in Authorization header.
    """
    entity = get_entity_by_id(db, entity_id)

    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity {entity_id} not found",
        )

    return EntityResponse.model_validate(entity)


@router.patch(
    "/admin/entities/{entity_id}",
    response_model=EntityResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Forbidden - invalid token"},
        404: {"model": ErrorResponse, "description": "Entity not found"},
    },
)
def update_entity_endpoint(
    entity_id: UUID,
    entity_update: EntityUpdate,
    db: Session = Depends(get_db),
    curator_name: str = Depends(verify_curator_token),
):
    """
    Update an existing entity.

    Modify entity metadata, segment, aliases, etc.
    Requires valid curator token in Authorization header.
    """
    entity = update_entity(db, entity_id, entity_update)

    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity {entity_id} not found",
        )

    return EntityResponse.model_validate(entity)


@router.delete(
    "/admin/entities/{entity_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        403: {"model": ErrorResponse, "description": "Forbidden - invalid token"},
        404: {"model": ErrorResponse, "description": "Entity not found"},
    },
)
def delete_entity_endpoint(
    entity_id: UUID,
    db: Session = Depends(get_db),
    curator_name: str = Depends(verify_curator_token),
):
    """
    Delete an entity.

    Removes an entity from the system. Signal-entity relationships
    will be automatically cascade deleted.
    Requires valid curator token in Authorization header.
    """
    deleted = delete_entity(db, entity_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity {entity_id} not found",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# =============================================================================
# Segment Statistics Endpoints
# =============================================================================

@router.get(
    "/segments/stats",
    response_model=SegmentStatsResponse,
)
def get_segment_stats_endpoint(
    days: int = Query(default=7, ge=1, le=365, description="Days to look back for recent signals"),
    db: Session = Depends(get_db),
):
    """
    Get signal statistics by segment for dashboard widgets.

    Returns counts of signals and entities per segment (customer, competitor, industry, influencer).
    No authentication required (public endpoint).
    """
    stats_dict = get_segment_statistics(db, days=days)

    # Convert dict to list of SegmentStats
    from app.schemas import SegmentStats

    stats_list = [SegmentStats(**stats_data) for stats_data in stats_dict.values()]
    total_signals = sum(s.signal_count for s in stats_list)

    return SegmentStatsResponse(
        stats=stats_list,
        total_signals=total_signals,
    )


# =============================================================================
# Evaluation Endpoints
# =============================================================================

@router.post(
    "/evaluations/run",
    response_model=EvaluationRunResponse,
)
def run_evaluation_endpoint(
    content_type: str = Query(..., description="Type of content to evaluate (signal_summary, theme, weekly_brief)"),
    content_id: UUID = Query(..., description="ID of the content to evaluate"),
    db: Session = Depends(get_db),
):
    """
    Run quality evaluation on AI-generated content.

    Performs rule-based hallucination checks and LLM-as-judge quality scoring.
    Saves results to evaluation_runs and evaluation_issues tables.

    No authentication required (public endpoint for testing).
    """
    from app import evaluations

    # Fetch the content based on type
    if content_type == "signal_summary":
        # For signal summary, we need to fetch it from somewhere
        # Since summaries are generated on-the-fly, we'll need the summary data passed in
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Signal summary evaluation not yet implemented. Use /signals/summary?run_evaluation=true instead."
        )

    elif content_type == "theme":
        from app.models import Theme
        theme = db.query(Theme).filter(Theme.id == content_id).first()
        if not theme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Theme {content_id} not found"
            )

        content_data = {
            'title': theme.title,
            'so_what': theme.so_what,
            'now_what': theme.now_what,
            'key_players': theme.key_players,
            'signal_ids': [str(sid) for sid in theme.signal_ids],
        }

    elif content_type == "weekly_brief":
        from app.models import WeeklyBrief, Theme
        brief = db.query(WeeklyBrief).filter(WeeklyBrief.id == content_id).first()
        if not brief:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Weekly brief {content_id} not found"
            )

        # Load all themes
        themes = db.query(Theme).filter(Theme.id.in_(brief.theme_ids)).all()
        content_data = {
            'themes': [
                {
                    'title': t.title,
                    'so_what': t.so_what,
                    'now_what': t.now_what,
                    'key_players': t.key_players,
                    'signal_ids': [str(sid) for sid in t.signal_ids],
                }
                for t in themes
            ]
        }

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content_type: {content_type}. Must be one of: signal_summary, theme, weekly_brief"
        )

    # Run evaluation
    eval_run = evaluations.evaluate_content(
        db=db,
        content_type=content_type,
        content_id=content_id,
        content_data=content_data,
    )

    return eval_run


@router.get(
    "/evaluations",
    response_model=List[EvaluationRunResponse],
)
def list_evaluations_endpoint(
    content_type: Optional[str] = Query(default=None, description="Filter by content type"),
    passed: Optional[bool] = Query(default=None, description="Filter by pass/fail status"),
    limit: int = Query(default=50, ge=1, le=500, description="Maximum number of evaluations to return"),
    offset: int = Query(default=0, ge=0, description="Number of evaluations to skip"),
    db: Session = Depends(get_db),
):
    """
    List evaluation runs with optional filtering.

    No authentication required (public endpoint).
    """
    from app.models import EvaluationRun

    query = db.query(EvaluationRun)

    if content_type:
        query = query.filter(EvaluationRun.content_type == content_type)

    if passed is not None:
        query = query.filter(EvaluationRun.passed == passed)

    # Order by most recent first
    query = query.order_by(EvaluationRun.created_at.desc())

    # Apply pagination
    evaluations = query.limit(limit).offset(offset).all()

    return evaluations


@router.get(
    "/evaluations/stats",
    response_model=EvaluationStatsResponse,
)
def get_evaluation_stats_endpoint(
    content_type: Optional[str] = Query(default=None, description="Filter by content type"),
    days: int = Query(default=30, ge=1, le=365, description="Number of days to look back"),
    db: Session = Depends(get_db),
):
    """
    Get evaluation statistics for monitoring dashboard.

    Returns:
    - Pass/fail rates
    - Average scores across all dimensions
    - Issue breakdown by type
    - Recent failures for investigation

    No authentication required (public endpoint).
    """
    from app.models import EvaluationRun, EvaluationIssue
    from datetime import datetime, timedelta
    from sqlalchemy import func

    # Calculate cutoff date
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Build base query
    query = db.query(EvaluationRun).filter(
        EvaluationRun.created_at >= cutoff_date
    )

    if content_type:
        query = query.filter(EvaluationRun.content_type == content_type)

    # Get all evaluations in time range
    evaluations = query.all()

    if not evaluations:
        return EvaluationStatsResponse(
            total_evaluations=0,
            passed_count=0,
            failed_count=0,
            pass_rate=0.0,
            avg_hallucination_score=0.0,
            avg_grounding_score=0.0,
            avg_relevance_score=0.0,
            avg_actionability_score=0.0,
            avg_coherence_score=0.0,
            avg_overall_score=0.0,
            issue_counts={},
            recent_failures=[],
        )

    # Calculate statistics
    total_evaluations = len(evaluations)
    passed_count = sum(1 for e in evaluations if e.passed)
    failed_count = total_evaluations - passed_count
    pass_rate = (passed_count / total_evaluations) * 100 if total_evaluations > 0 else 0.0

    # Calculate average scores
    avg_hallucination_score = sum(e.hallucination_score for e in evaluations) / total_evaluations
    avg_grounding_score = sum(e.grounding_score for e in evaluations) / total_evaluations
    avg_relevance_score = sum(e.relevance_score for e in evaluations) / total_evaluations
    avg_actionability_score = sum(e.actionability_score for e in evaluations) / total_evaluations
    avg_coherence_score = sum(e.coherence_score for e in evaluations) / total_evaluations
    avg_overall_score = sum(e.overall_score for e in evaluations) / total_evaluations

    # Get issue counts by type
    issue_query = db.query(
        EvaluationIssue.issue_type,
        func.count(EvaluationIssue.id).label('count')
    ).join(
        EvaluationRun,
        EvaluationIssue.evaluation_run_id == EvaluationRun.id
    ).filter(
        EvaluationRun.created_at >= cutoff_date
    )

    if content_type:
        issue_query = issue_query.filter(EvaluationRun.content_type == content_type)

    issue_counts = {
        row.issue_type: row.count
        for row in issue_query.group_by(EvaluationIssue.issue_type).all()
    }

    # Get recent failures
    recent_failures = query.filter(
        EvaluationRun.passed == False
    ).order_by(
        EvaluationRun.created_at.desc()
    ).limit(10).all()

    return EvaluationStatsResponse(
        total_evaluations=total_evaluations,
        passed_count=passed_count,
        failed_count=failed_count,
        pass_rate=pass_rate,
        avg_hallucination_score=avg_hallucination_score,
        avg_grounding_score=avg_grounding_score,
        avg_relevance_score=avg_relevance_score,
        avg_actionability_score=avg_actionability_score,
        avg_coherence_score=avg_coherence_score,
        avg_overall_score=avg_overall_score,
        issue_counts=issue_counts,
        recent_failures=recent_failures,
    )

"""Pydantic schemas for request/response validation."""

from datetime import datetime, date
from enum import Enum
from typing import Dict, List, Optional, TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, HttpUrl

if TYPE_CHECKING:
    from typing import ForwardRef


class EventType(str, Enum):
    """Valid event types for signals."""
    ANNOUNCEMENT = "announcement"
    HIRE = "hire"
    POLICY = "policy"
    PARTNERSHIP = "partnership"
    MA = "m&a"
    RETRACTION = "retraction"
    LAUNCH = "launch"
    OTHER = "other"


class Confidence(str, Enum):
    """Confidence levels for signals."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class ImpactArea(str, Enum):
    """Impact areas for signals and themes."""
    OPS = "Ops"
    TECH = "Tech"
    INTEGRITY = "Integrity"
    PROCUREMENT = "Procurement"


class SignalStatus(str, Enum):
    """Status values for signal review workflow."""
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class SourceType(str, Enum):
    """Data source types for automated collection."""
    RSS = "rss"
    LINKEDIN = "linkedin"
    WEB = "web"
    EMAIL = "email"


class EntitySegment(str, Enum):
    """Entity segment types for market intelligence."""
    CUSTOMER = "customer"
    COMPETITOR = "competitor"
    INDUSTRY = "industry"
    INFLUENCER = "influencer"


class SignalCreate(BaseModel):
    """Request schema for creating a signal."""

    entity: str = Field(..., min_length=1, max_length=255, description="Entity name (e.g., Springer Nature)")
    event_type: EventType = Field(..., description="Type of event")
    topic: str = Field(..., min_length=1, max_length=255, description="Topic (e.g., OA Mandate)")
    source_url: HttpUrl = Field(..., description="Source URL for the signal")
    evidence_snippet: str = Field(..., min_length=50, max_length=500, description="Evidence snippet (50-500 chars)")
    confidence: Confidence = Field(..., description="Confidence level")
    impact_areas: List[ImpactArea] = Field(..., min_length=1, description="Impact areas (at least one)")
    entity_tags: Optional[List[str]] = Field(default=[], description="Optional entity tags")
    notes: Optional[str] = Field(default=None, max_length=2000, description="Optional notes")

    @field_validator('entity', 'topic')
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Strip leading/trailing whitespace from string fields."""
        return v.strip()

    @field_validator('entity_tags', mode='before')
    @classmethod
    def ensure_tags_list(cls, v):
        """Ensure entity_tags is a list."""
        if v is None:
            return []
        return v


class SignalResponse(BaseModel):
    """Response schema for a signal."""

    id: UUID
    entity: str
    event_type: str
    topic: str
    source_url: str
    evidence_snippet: str
    confidence: str
    impact_areas: List[str]
    entity_tags: List[str]
    created_at: datetime
    curator_name: Optional[str] = None
    notes: Optional[str] = None

    # Automation fields
    status: str = "approved"
    data_source_id: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None

    # Entity relationships (populated when requested)
    entities: Optional[List['EntityResponse']] = None

    model_config = {"from_attributes": True}


class SignalListResponse(BaseModel):
    """Response schema for list of signals."""

    signals: List[SignalResponse]
    total: int
    limit: int
    offset: int


class SemanticSearchResult(BaseModel):
    """Single result from semantic search with similarity score."""

    signal: SignalResponse
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Cosine similarity score (0-1)")


class SemanticSearchResponse(BaseModel):
    """Response schema for semantic search."""

    query: str
    results: List[SemanticSearchResult]
    total: int


class ErrorDetail(BaseModel):
    """Error detail for validation errors."""

    field: str
    message: str


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    details: Optional[List[ErrorDetail]] = None


# =============================================================================
# Theme Schemas
# =============================================================================

class ThemeResponse(BaseModel):
    """Response schema for a theme."""

    id: UUID
    title: str
    signal_ids: List[UUID]
    key_players: List[str]
    aggregate_confidence: str
    impact_areas: List[str]
    so_what: str
    now_what: List[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ThemeWithSignalsResponse(BaseModel):
    """Theme response with full signal data included."""

    id: UUID
    title: str
    key_players: List[str]
    aggregate_confidence: str
    impact_areas: List[str]
    so_what: str
    now_what: List[str]
    created_at: datetime
    signals: List[SignalResponse]

    model_config = {"from_attributes": True}


# =============================================================================
# Weekly Brief Schemas
# =============================================================================

class WeeklyBriefResponse(BaseModel):
    """Response schema for a weekly brief."""

    id: UUID
    week_start: date
    week_end: date
    generated_at: datetime
    total_signals: int
    coverage_areas: List[str]
    theme_ids: List[UUID]

    model_config = {"from_attributes": True}


class WeeklyBriefFullResponse(BaseModel):
    """Full weekly brief response with themes and signals."""

    id: UUID
    week_start: date
    week_end: date
    generated_at: datetime
    total_signals: int
    coverage_areas: List[str]
    themes: List[ThemeWithSignalsResponse]

    model_config = {"from_attributes": True}


class WeeklyBriefSummary(BaseModel):
    """Summary of a weekly brief (without full theme/signal details)."""

    id: UUID
    week_start: date
    week_end: date
    generated_at: datetime
    total_signals: int
    coverage_areas: List[str]
    theme_count: int

    model_config = {"from_attributes": True}


class GenerateBriefResponse(BaseModel):
    """Response when generating a brief."""

    message: str
    brief_id: Optional[UUID] = None
    week_start: Optional[date] = None
    week_end: Optional[date] = None
    themes_created: int = 0
    signals_processed: int = 0


class CollectSignalsResponse(BaseModel):
    """Response when collecting signals."""

    message: str
    signals_collected: int = 0
    signals_pending_review: int = 0
    sources_processed: int = 0
    errors: List[str] = []


# =============================================================================
# Data Source Schemas
# =============================================================================

class DataSourceCreate(BaseModel):
    """Request schema for creating a data source."""

    name: str = Field(..., min_length=1, max_length=255, description="Data source name")
    source_type: SourceType = Field(..., description="Type of data source")
    url: Optional[str] = Field(default=None, description="Feed URL or website URL")
    config: Optional[Dict] = Field(default=None, description="Source-specific configuration")
    enabled: bool = Field(default=True, description="Whether source is enabled")
    default_confidence: Confidence = Field(default=Confidence.MEDIUM, description="Default confidence for signals")
    default_impact_areas: Optional[List[ImpactArea]] = Field(default=[], description="Default impact areas")


class DataSourceResponse(BaseModel):
    """Response schema for a data source."""

    id: UUID
    name: str
    source_type: str
    url: Optional[str] = None
    config: Optional[Dict] = None
    enabled: bool
    last_fetched_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    error_count: int
    last_error: Optional[str] = None
    default_confidence: str
    default_impact_areas: List[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DataSourceUpdate(BaseModel):
    """Request schema for updating a data source."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    url: Optional[str] = None
    config: Optional[Dict] = None
    enabled: Optional[bool] = None
    default_confidence: Optional[Confidence] = None
    default_impact_areas: Optional[List[ImpactArea]] = None


# =============================================================================
# Notification Schemas
# =============================================================================

class NotificationCreate(BaseModel):
    """Request schema for creating a notification."""

    type: str = Field(..., min_length=1, max_length=50, description="Notification type")
    title: str = Field(..., min_length=1, max_length=500, description="Notification title")
    message: str = Field(..., min_length=1, description="Notification message")
    link: Optional[str] = Field(default=None, description="Link to related resource")


class NotificationResponse(BaseModel):
    """Response schema for a notification."""

    id: UUID
    type: str
    title: str
    message: str
    link: Optional[str] = None
    read: bool
    dismissed: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationUpdate(BaseModel):
    """Request schema for updating a notification."""

    read: Optional[bool] = None
    dismissed: Optional[bool] = None


# =============================================================================
# Signal Review Schemas
# =============================================================================

class SignalStatusUpdate(BaseModel):
    """Request schema for updating signal status."""

    status: SignalStatus = Field(..., description="New status for the signal")
    reviewer_name: Optional[str] = Field(default=None, description="Name of reviewer")


# =============================================================================
# Entity Management Schemas
# =============================================================================

class EntityCreate(BaseModel):
    """Request schema for creating an entity."""

    name: str = Field(..., min_length=1, max_length=255, description="Entity name")
    segment: EntitySegment = Field(..., description="Entity segment classification")
    aliases: Optional[List[str]] = Field(default=[], description="Alternative names for the entity")
    entity_metadata: Optional[Dict] = Field(default=None, description="Additional metadata (JSON)")
    notes: Optional[str] = Field(default=None, description="Curator notes about the entity")


class EntityUpdate(BaseModel):
    """Request schema for updating an entity."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Entity name")
    segment: Optional[EntitySegment] = Field(None, description="Entity segment classification")
    aliases: Optional[List[str]] = Field(None, description="Alternative names for the entity")
    entity_metadata: Optional[Dict] = Field(None, description="Additional metadata (JSON)")
    notes: Optional[str] = Field(None, description="Curator notes about the entity")


class EntityResponse(BaseModel):
    """Response schema for an entity."""

    id: UUID
    name: str
    segment: str
    aliases: List[str]
    entity_metadata: Optional[Dict] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EntityListResponse(BaseModel):
    """Response schema for listing entities."""

    entities: List[EntityResponse]
    total: int


# =============================================================================
# Segment Statistics Schemas
# =============================================================================

class SegmentStats(BaseModel):
    """Statistics for a single segment."""

    segment: str = Field(..., description="Segment name (customer, competitor, industry, influencer)")
    signal_count: int = Field(..., description="Total signals for this segment")
    entity_count: int = Field(..., description="Number of entities in this segment")
    recent_signals: int = Field(..., description="Signals in the last N days")


class SegmentStatsResponse(BaseModel):
    """Response schema for segment statistics."""

    stats: List[SegmentStats]
    total_signals: int = Field(..., description="Total signals across all segments")


# =============================================================================
# Signal Summary Schemas
# =============================================================================

class SignalSummaryItem(BaseModel):
    """A single insight from the summary with traceability."""

    insight: str = Field(..., description="The key insight or finding")
    signal_ids: List[UUID] = Field(..., description="IDs of signals that support this insight")
    entities: List[str] = Field(..., description="Key entities mentioned in this insight")


class SignalSummaryResponse(BaseModel):
    """Response schema for AI-generated signal summary."""

    summary: str = Field(..., description="Overall executive summary paragraph")
    key_insights: List[SignalSummaryItem] = Field(..., description="Structured insights with traceability")
    total_signals: int = Field(..., description="Number of signals analyzed")
    date_range: str = Field(..., description="Date range of signals analyzed")
    segments_covered: List[str] = Field(..., description="Segments covered in this summary")
    impact_areas: List[str] = Field(..., description="Impact areas covered")


# Rebuild SignalResponse to resolve forward references
SignalResponse.model_rebuild()


# =============================================================================
# Evaluation Schemas
# =============================================================================

class EvaluationIssueResponse(BaseModel):
    """Response schema for a single evaluation issue."""

    id: UUID
    issue_type: str = Field(..., description="Type of issue (hallucination, poor_advice, etc.)")
    severity: str = Field(..., description="Severity level (critical, major, minor)")
    description: str = Field(..., description="Human-readable description of the issue")
    affected_signal_ids: Optional[List[UUID]] = Field(None, description="Signals involved in this issue")
    affected_entities: Optional[List[str]] = Field(None, description="Entities involved in this issue")
    details: Optional[dict] = Field(None, description="Additional structured details")
    created_at: datetime

    class Config:
        from_attributes = True


class EvaluationRunResponse(BaseModel):
    """Response schema for an evaluation run."""

    id: UUID
    content_type: str = Field(..., description="Type of content evaluated (theme, weekly_brief, signal_summary)")
    content_id: UUID = Field(..., description="ID of the content evaluated")

    # Quality scores (0-10 scale)
    hallucination_score: float = Field(..., description="Score for hallucination checks (10 = no hallucinations)")
    grounding_score: float = Field(..., description="Score for grounding in evidence (10 = perfectly grounded)")
    relevance_score: float = Field(..., description="Score for relevance (10 = highly relevant)")
    actionability_score: float = Field(..., description="Score for actionability (10 = clear actions)")
    coherence_score: float = Field(..., description="Score for coherence (10 = perfectly coherent)")

    overall_score: float = Field(..., description="Overall quality score (average of all scores)")
    passed: bool = Field(..., description="Whether evaluation passed threshold")
    threshold: float = Field(..., description="Threshold used for pass/fail")

    evaluator_model: Optional[str] = Field(None, description="LLM model used for evaluation")
    evaluation_method: str = Field(..., description="Evaluation method used (rule_based, llm_judge, hybrid)")
    created_at: datetime

    issues: List[EvaluationIssueResponse] = Field(default_factory=list, description="Issues found during evaluation")

    class Config:
        from_attributes = True


class EvaluationStatsResponse(BaseModel):
    """Response schema for evaluation monitoring statistics."""

    total_evaluations: int = Field(..., description="Total number of evaluations run")
    passed_count: int = Field(..., description="Number of evaluations that passed")
    failed_count: int = Field(..., description="Number of evaluations that failed")
    pass_rate: float = Field(..., description="Percentage of evaluations that passed")

    avg_hallucination_score: float = Field(..., description="Average hallucination score")
    avg_grounding_score: float = Field(..., description="Average grounding score")
    avg_relevance_score: float = Field(..., description="Average relevance score")
    avg_actionability_score: float = Field(..., description="Average actionability score")
    avg_coherence_score: float = Field(..., description="Average coherence score")
    avg_overall_score: float = Field(..., description="Average overall score")

    # Issue breakdown
    issue_counts: dict = Field(..., description="Count of issues by type")
    recent_failures: List[EvaluationRunResponse] = Field(..., description="Recent failed evaluations")

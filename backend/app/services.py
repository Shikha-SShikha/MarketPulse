"""Business logic services for the STM Intelligence Brief System."""

import logging
from collections import defaultdict
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session
from openai import OpenAI

from app.models import Signal, Theme, WeeklyBrief, Notification, Entity, SignalEntity
from app.schemas import SignalCreate, EntityCreate, EntityUpdate
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def create_signal_from_dict(db: Session, signal_data: Dict) -> Signal:
    """
    Create a signal from a dictionary (used by collectors).

    Args:
        db: Database session
        signal_data: Dictionary with signal fields
            - entity: Primary entity name (for backward compatibility)
            - entity_ids: Optional list of entity UUIDs to link
            - All other signal fields

    Returns:
        Created Signal ORM object
    """
    # Import here to avoid circular imports
    from app.embeddings import get_embeddings_service

    signal = Signal(
        entity=signal_data['entity'],
        event_type=signal_data['event_type'],
        topic=signal_data['topic'],
        source_url=signal_data['source_url'],
        evidence_snippet=signal_data['evidence_snippet'],
        confidence=signal_data['confidence'],
        impact_areas=signal_data['impact_areas'],
        entity_tags=signal_data.get('entity_tags', []),
        notes=signal_data.get('notes'),
        curator_name=signal_data.get('curator_name'),
        status=signal_data.get('status', 'approved'),
        data_source_id=signal_data.get('data_source_id'),
    )

    db.add(signal)
    db.commit()
    db.refresh(signal)

    # Generate embedding for semantic search
    embeddings_service = get_embeddings_service()
    if embeddings_service.is_available():
        embedding = embeddings_service.generate_signal_embedding({
            'title': signal_data.get('title', ''),
            'content': signal.evidence_snippet,
            'entity': signal.entity,
            'topics': signal.topic
        })

        if embedding:
            signal.embedding = embedding
            db.commit()
            logger.debug(f"Generated embedding for signal {signal.id}")

    # Create signal-entity relationships if entity_ids provided
    entity_ids = signal_data.get('entity_ids', [])

    # If no entity_ids provided, try to create/find entity for signal.entity
    if not entity_ids and signal.entity:
        # Try to find existing entity by name (case-insensitive)
        existing_entity = db.query(Entity).filter(
            Entity.name.ilike(signal.entity)
        ).first()

        if existing_entity:
            entity_ids = [existing_entity.id]
        else:
            # Auto-create entity if it doesn't exist
            # Infer segment from entity name using simple heuristics
            segment = infer_entity_segment(signal.entity)

            new_entity = Entity(
                name=signal.entity,
                segment=segment,
                notes=f"Auto-created from signal {signal.id}",
            )
            db.add(new_entity)
            db.commit()
            db.refresh(new_entity)
            entity_ids = [new_entity.id]
            logger.info(f"Auto-created entity '{signal.entity}' with segment '{segment}'")

    if entity_ids:
        for idx, entity_id in enumerate(entity_ids):
            signal_entity = SignalEntity(
                signal_id=signal.id,
                entity_id=entity_id,
                is_primary=(idx == 0),  # First entity is primary
            )
            db.add(signal_entity)

        db.commit()

    return signal


def infer_entity_segment(entity_name: str) -> str:
    """
    Infer entity segment from entity name using keywords.

    Returns one of: customer, competitor, industry, influencer
    """
    entity_lower = entity_name.lower()

    # Known competitors (production/editorial service providers)
    competitors = ['kriyadocs', 'knowledgeworks', 'cactus', 'editage', 'spi global',
                   'straive', 'integra', 'tnq', 'exeter', 'aptara', 'mps', 'newgen',
                   'aries', 'scholarone', 'ejournal']

    # Known influencers (blogs, news sites, thought leaders)
    influencers = ['scholarly kitchen', 'science editor', 'publishing perspectives',
                   'knowledge speak', 'retraction watch', 'plos blog', 'stm publishing']

    # Known industry organizations
    industry_orgs = ['stm association', 'ismte', 'cse', 'ssp', 'cope', 'doaj',
                     'crossref', 'orcid', 'oaspa']

    # Publishers (mostly customers)
    publishers = ['springer', 'elsevier', 'wiley', 'sage', 'taylor', 'oxford',
                  'cambridge', 'nature', 'science', 'plos', 'frontiers', 'mdpi',
                  'bmc', 'karger', 'thieme', 'wolters kluwer']

    # Check for matches
    if any(comp in entity_lower for comp in competitors):
        return 'competitor'
    elif any(inf in entity_lower for inf in influencers):
        return 'influencer'
    elif any(org in entity_lower for org in industry_orgs):
        return 'industry'
    elif any(pub in entity_lower for pub in publishers):
        return 'customer'
    else:
        # Default: if it's a blog/news site -> influencer, otherwise industry
        if any(kw in entity_lower for kw in ['blog', 'news', 'watch', 'kitchen', 'perspectives']):
            return 'influencer'
        return 'industry'


def create_signal(db: Session, signal_data: SignalCreate, curator_name: Optional[str] = None) -> Signal:
    """
    Create a new signal in the database.

    Args:
        db: Database session
        signal_data: Validated signal data from request
        curator_name: Name of the curator (from auth)

    Returns:
        Created Signal ORM object
    """
    # Import here to avoid circular imports
    from app.embeddings import get_embeddings_service

    signal = Signal(
        entity=signal_data.entity,
        event_type=signal_data.event_type.value,
        topic=signal_data.topic,
        source_url=str(signal_data.source_url),
        evidence_snippet=signal_data.evidence_snippet,
        confidence=signal_data.confidence.value,
        impact_areas=[area.value for area in signal_data.impact_areas],
        entity_tags=signal_data.entity_tags or [],
        notes=signal_data.notes,
        curator_name=curator_name,
    )

    db.add(signal)
    db.commit()
    db.refresh(signal)

    # Generate embedding for semantic search
    embeddings_service = get_embeddings_service()
    if embeddings_service.is_available():
        embedding = embeddings_service.generate_signal_embedding({
            'title': '',  # No separate title in manual creation
            'content': signal.evidence_snippet,
            'entity': signal.entity,
            'topics': signal.topic
        })

        if embedding:
            signal.embedding = embedding
            db.commit()
            logger.debug(f"Generated embedding for signal {signal.id}")

    return signal


def get_signal(db: Session, signal_id: UUID) -> Optional[Signal]:
    """
    Get a signal by ID.

    Args:
        db: Database session
        signal_id: UUID of the signal

    Returns:
        Signal if found and not deleted, None otherwise
    """
    return db.query(Signal).filter(
        Signal.id == signal_id,
        Signal.deleted_at.is_(None)
    ).first()


def get_signals(
    db: Session,
    limit: int = 50,
    offset: int = 0,
    entity: Optional[str] = None,
    topic: Optional[str] = None,
    status: Optional[str] = None,
    segment: Optional[str] = None,
    impact_area: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    include_entities: bool = True,
) -> tuple[List[Signal], int]:
    """
    Get a list of signals with optional filtering.

    Args:
        db: Database session
        limit: Maximum number of signals to return
        offset: Number of signals to skip
        entity: Filter by entity name (partial match)
        topic: Filter by topic (partial match)
        status: Filter by status (exact match: pending_review, approved, rejected)
        segment: Filter by entity segment (customer, competitor, industry, influencer)
        impact_area: Filter by impact area (Ops, Tech, Integrity, Procurement)
        start_date: Filter signals created on or after this date
        end_date: Filter signals created on or before this date
        include_entities: Whether to eager load entity relationships (default True)

    Returns:
        Tuple of (list of signals, total count)
    """
    from sqlalchemy.orm import joinedload

    query = db.query(Signal).filter(Signal.deleted_at.is_(None))

    if entity:
        query = query.filter(Signal.entity.ilike(f"%{entity}%"))

    if topic:
        query = query.filter(Signal.topic.ilike(f"%{topic}%"))

    if status:
        query = query.filter(Signal.status == status)

    if segment:
        # Join with signal_entities and entities to filter by segment
        query = query.join(SignalEntity, Signal.id == SignalEntity.signal_id).join(
            Entity, SignalEntity.entity_id == Entity.id
        ).filter(Entity.segment == segment).distinct()

    if impact_area:
        # Filter signals that have this impact area in their impact_areas array
        query = query.filter(Signal.impact_areas.contains([impact_area]))

    if start_date:
        # Filter signals created on or after start_date
        query = query.filter(Signal.created_at >= datetime.combine(start_date, datetime.min.time()))

    if end_date:
        # Filter signals created on or before end_date (end of day)
        query = query.filter(Signal.created_at <= datetime.combine(end_date, datetime.max.time()))

    total = query.count()

    # Eager load entity relationships if requested
    if include_entities:
        query = query.options(joinedload(Signal.entity_links).joinedload(SignalEntity.entity))

    signals = query.order_by(Signal.created_at.desc()).offset(offset).limit(limit).all()

    return signals, total


def soft_delete_signal(db: Session, signal_id: UUID) -> Optional[Signal]:
    """
    Soft delete a signal by setting deleted_at timestamp.

    Args:
        db: Database session
        signal_id: UUID of the signal to delete

    Returns:
        Deleted signal if found, None otherwise
    """
    from datetime import datetime

    signal = get_signal(db, signal_id)
    if signal:
        signal.deleted_at = datetime.utcnow()
        db.commit()
        db.refresh(signal)

    return signal


# =============================================================================
# Theme Synthesis Functions
# =============================================================================

def get_signals_for_week(db: Session, week_end: date) -> List[Signal]:
    """
    Get all non-deleted signals from the past 7 days.

    Args:
        db: Database session
        week_end: End date of the week (typically Sunday)

    Returns:
        List of signals from the past 7 days
    """
    week_start = week_end - timedelta(days=6)

    return db.query(Signal).filter(
        Signal.deleted_at.is_(None),
        Signal.created_at >= datetime.combine(week_start, datetime.min.time()),
        Signal.created_at <= datetime.combine(week_end, datetime.max.time()),
    ).order_by(Signal.created_at.desc()).all()


def semantic_search_signals(
    db: Session,
    query: str,
    limit: int = 20,
    similarity_threshold: float = 0.7,
    entity: Optional[str] = None,
    topic: Optional[str] = None,
    days_back: Optional[int] = None,
) -> List[Tuple[Signal, float]]:
    """
    Perform semantic search on signals using RAG (vector similarity).

    Args:
        db: Database session
        query: Natural language search query
        limit: Maximum number of results to return
        similarity_threshold: Minimum cosine similarity (0-1, higher = more similar)
        entity: Optional filter by entity name
        topic: Optional filter by topic
        days_back: Optional filter by signals from last N days

    Returns:
        List of (Signal, similarity_score) tuples, ordered by similarity descending
    """
    from app.embeddings import get_embeddings_service

    # Generate embedding for query
    embeddings_service = get_embeddings_service()
    if not embeddings_service.is_available():
        logger.warning("Embeddings service not available - cannot perform semantic search")
        return []

    query_embedding = embeddings_service.generate_embedding(query)
    if not query_embedding:
        logger.error("Failed to generate embedding for query")
        return []

    # Build base query
    query_builder = db.query(
        Signal,
        Signal.embedding.cosine_distance(query_embedding).label('distance')
    ).filter(
        Signal.deleted_at.is_(None),
        Signal.embedding.isnot(None)  # Only signals with embeddings
    )

    # Apply filters
    if entity:
        query_builder = query_builder.filter(Signal.entity.ilike(f'%{entity}%'))

    if topic:
        query_builder = query_builder.filter(Signal.topic.ilike(f'%{topic}%'))

    if days_back:
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        query_builder = query_builder.filter(Signal.created_at >= cutoff_date)

    # Order by similarity (lower distance = higher similarity)
    # Cosine distance range: 0 (identical) to 2 (opposite)
    # Convert to similarity: similarity = 1 - (distance / 2)
    query_builder = query_builder.order_by('distance')

    # Execute query
    results = query_builder.limit(limit * 2).all()  # Get 2x for threshold filtering

    # Filter by similarity threshold and convert distance to similarity score
    filtered_results = []
    for signal, distance in results:
        similarity = 1 - (distance / 2)  # Convert distance to similarity (0-1)

        if similarity >= similarity_threshold:
            filtered_results.append((signal, similarity))

    # Return top N results
    return filtered_results[:limit]


def cluster_signals_by_topic(signals: List[Signal]) -> Dict[str, List[Signal]]:
    """
    Group signals by topic for theme creation.

    Args:
        signals: List of signals to cluster

    Returns:
        Dictionary mapping topic to list of signals
    """
    clusters: Dict[str, List[Signal]] = defaultdict(list)

    for signal in signals:
        # Normalize topic for clustering (lowercase, strip whitespace)
        normalized_topic = signal.topic.lower().strip()
        clusters[normalized_topic].append(signal)

    return dict(clusters)


def aggregate_confidence(signals: List[Signal]) -> str:
    """
    Aggregate confidence levels from multiple signals.

    Rules:
    - All High → High
    - Any Low → Medium
    - Otherwise → High

    Args:
        signals: List of signals to aggregate

    Returns:
        Aggregated confidence level
    """
    confidences = [s.confidence for s in signals]

    if all(c == "High" for c in confidences):
        return "High"
    elif any(c == "Low" for c in confidences):
        return "Medium"
    else:
        return "High"


def collect_impact_areas(signals: List[Signal]) -> List[str]:
    """
    Collect unique impact areas from all signals.

    Args:
        signals: List of signals

    Returns:
        Sorted list of unique impact areas
    """
    areas = set()
    for signal in signals:
        areas.update(signal.impact_areas or [])
    return sorted(list(areas))


def collect_key_players(signals: List[Signal]) -> List[str]:
    """
    Collect unique entity names from signals.

    Args:
        signals: List of signals

    Returns:
        Sorted list of unique entity names
    """
    players = set()
    for signal in signals:
        players.add(signal.entity)
    return sorted(list(players))


def get_competitor_entities_from_signals(signals: List[Signal]) -> List[str]:
    """
    Extract competitor entities from signals by checking entity_links.

    Falls back to checking signal.entity field against known competitor names
    if entity_links are not populated.

    Args:
        signals: List of signals to analyze

    Returns:
        List of competitor entity names
    """
    # Known competitor names (fallback list)
    KNOWN_COMPETITORS = {
        'kriyadocs', 'knowledgeworks', 'cactus', 'editage',
        'spi global', 'straive', 'integra', 'tnq books', 'tnq',
        'exeter premedia', 'aptara', 'mps limited', 'mps',
        'newgen knowledgeworks', 'newgen', 'publishing technology', 'pubtech',
        'aries systems', 'editorial manager', 'scholarone', 'ejournal press',
    }

    competitors = set()

    for signal in signals:
        # Primary: Check entity_links for entities with segment='competitor'
        found_via_link = False
        for entity_link in signal.entity_links:
            if entity_link.entity and entity_link.entity.segment == 'competitor':
                competitors.add(entity_link.entity.name)
                found_via_link = True

        # Fallback: Check signal.entity field against known competitors
        if not found_via_link and signal.entity:
            entity_lower = signal.entity.lower()
            for known_comp in KNOWN_COMPETITORS:
                if known_comp in entity_lower:
                    competitors.add(signal.entity)
                    break

    return sorted(list(competitors))


def is_competitor_theme(signals: List[Signal]) -> bool:
    """
    Check if a theme primarily involves competitor entities.

    A theme is considered a competitor theme if at least 50% of its signals
    involve competitor entities. Falls back to checking signal.entity field
    against known competitors if entity_links are not populated.

    Args:
        signals: List of signals in the theme

    Returns:
        True if theme is competitor-focused, False otherwise
    """
    # Known competitor names (fallback list)
    KNOWN_COMPETITORS = {
        'kriyadocs', 'knowledgeworks', 'cactus', 'editage',
        'spi global', 'straive', 'integra', 'tnq books', 'tnq',
        'exeter premedia', 'aptara', 'mps limited', 'mps',
        'newgen knowledgeworks', 'newgen', 'publishing technology', 'pubtech',
        'aries systems', 'editorial manager', 'scholarone', 'ejournal press',
    }

    if not signals:
        return False

    competitor_signal_count = 0

    for signal in signals:
        is_competitor_signal = False

        # Primary: Check entity_links for entities with segment='competitor'
        for entity_link in signal.entity_links:
            if entity_link.entity and entity_link.entity.segment == 'competitor':
                is_competitor_signal = True
                break

        # Fallback: Check signal.entity field against known competitors
        if not is_competitor_signal and signal.entity:
            entity_lower = signal.entity.lower()
            for known_comp in KNOWN_COMPETITORS:
                if known_comp in entity_lower:
                    is_competitor_signal = True
                    break

        if is_competitor_signal:
            competitor_signal_count += 1

    # Theme is competitor-focused if >=25% of signals involve competitors
    # This ensures sales teams are alerted to any significant competitor activity
    return competitor_signal_count >= (len(signals) / 4)


def _convert_to_inline_citations(text: str) -> str:
    """
    Convert 'According to Signal X' format to inline citations [X].

    Examples:
    - "According to Signal 1, Taylor & Francis..." → "Taylor & Francis [1]..."
    - "Signal 2 shows that MDPI..." → "MDPI [2]..."
    - "Signals 3 and 5 indicate..." → "Signals indicate [3][5]..."
    """
    import re

    # Pattern 1: "According to Signal X, content..." - extract first complete clause
    # Matches until first comma, period, or "indicating/suggesting/highlighting"
    text = re.sub(
        r'According to Signal (\d+),\s*([^,]+?)(?:\s*,\s*(indicating|suggesting|highlighting|showing))',
        r'\2 [\1], \3',
        text
    )

    # Pattern 2: "Signal X shows/reveals/indicates that content..."
    text = re.sub(
        r'Signal (\d+) (?:shows|reveals|indicates) that\s+([^,]+)',
        r'\2 [\1]',
        text
    )

    # Pattern 3: "Signals X and Y indicate/show..." → "content [X][Y]..."
    text = re.sub(
        r'Signals (\d+) and (\d+) (?:indicate|show|reveal)(?:\s+that)?\s+([^,]+)',
        r'\3 [\1][\2]',
        text
    )

    # Pattern 4: Handle "Additionally, Signal X reveals that..." format
    text = re.sub(
        r'(?:Additionally|Furthermore),?\s+Signal (\d+) reveals that\s+([^,]+)',
        r'Additionally, \2 [\1]',
        text
    )

    # Pattern 5: Handle "as noted in Signals X and Y" → [X][Y]
    text = re.sub(
        r'as noted in Signals (\d+) and (\d+)',
        r'[\1][\2]',
        text
    )

    return text


def generate_so_what(topic: str, signals: List[Signal], impact_areas: List[str]) -> str:
    """
    Generate "So What" explanation for a theme using OpenAI.

    Args:
        topic: Theme topic
        signals: Contributing signals
        impact_areas: Impact areas for the theme

    Returns:
        AI-generated 1-2 sentence explanation
    """
    # Fallback to template if OpenAI is not configured
    if not settings.openai_api_key or settings.openai_api_key == "your-openai-api-key-here":
        return _generate_so_what_template(topic, signals, impact_areas)

    try:
        client = OpenAI(api_key=settings.openai_api_key)

        # Build context from signals
        entities = list(set(s.entity for s in signals))
        event_types = list(set(s.event_type for s in signals))
        impact_text = ", ".join(impact_areas) if impact_areas else "multiple areas"

        # Check if this is a competitor theme
        competitors = get_competitor_entities_from_signals(signals)
        is_competitor = is_competitor_theme(signals)

        # Create signal summaries for context with explicit numbering for citation
        signal_summaries = []
        for i, sig in enumerate(signals[:20], 1):
            signal_summaries.append(f"Signal {i}: {sig.entity} - {sig.evidence_snippet[:200]}")

        # Add competitor context to prompt if applicable
        competitor_context = ""
        if is_competitor:
            competitor_context = f"\n🔴 COMPETITIVE INTELLIGENCE: This theme involves your direct competitors: {', '.join(competitors)}\nFocus on competitive implications, market positioning, and strategic threats/opportunities."

        prompt = f"""STRICT RULE: You MUST write your response WITHOUT the phrases "According to Signal" or "Signal X shows/reveals/indicates".
Instead, write naturally and add [X] citations at the end of sentences, exactly like academic papers.

ACCEPTABLE START: "Taylor & Francis partnered with Hiroshima University [1], indicating..."
FORBIDDEN START: "According to Signal 1, Taylor & Francis..."
FORBIDDEN START: "Signal 1 shows that..."

Your task: Write a "Why This Matters" section for a weekly intelligence brief for STM (Scientific, Technical, Medical) publishing sales teams.

Topic: {topic}
Entities involved: {', '.join(entities)}
Event types: {', '.join(event_types)}
Impact areas: {impact_text}{competitor_context}

Evidence from signals:
{chr(10).join(signal_summaries)}

MANDATORY FORMAT REQUIREMENTS:
1. Start your first sentence with the key insight or entity name - NOT with "According to" or "Signal"
2. Add [X] citation at the end of each fact-based sentence
3. Write 1-2 sentences total
4. Be specific about business implications for STM publishing suppliers

CORRECT EXAMPLE: "Taylor & Francis established a new partnership agreement [1], highlighting the growing demand for collaborative publishing models that suppliers must adapt to support."

INCORRECT EXAMPLE: "According to Signal 1, Taylor & Francis..." (This format is FORBIDDEN)

EXAMPLES OF CORRECT VS INCORRECT CITATION FORMAT:

✅ CORRECT (Inline Citations):
"Taylor & Francis partnered with Hiroshima University to promote open research practices [1], indicating publishers are investing in transparency initiatives that could create new service opportunities for compliance vendors."

❌ INCORRECT (Old Format - DO NOT USE):
"According to Signal 1, Taylor & Francis partnered with Hiroshima University..."
(Never start with "According to Signal X" - use inline citations instead)

✅ CORRECT (Multiple Inline Citations):
"Major publishers are actively adopting AI technologies in editorial workflows, with Nature launching an AI-powered peer review tool [2] and Elsevier partnering with a machine learning company [4]."

❌ INCORRECT (Old Format - DO NOT USE):
"Signal 2 reveals that Nature launched an AI-powered peer review tool..."
(Never use "Signal X reveals" or similar - use inline citations instead)

❌ BAD (No Citations):
"Publishers are increasingly focused on transparency and collaboration with academic institutions."
(Missing citations - every claim needs [X])

CRITICAL GROUNDING REQUIREMENTS:
- Use ONLY inline citations [X] - never "According to Signal X" or "Signal X shows"
- Place [X] immediately after each claim that comes from that signal
- Base ALL analysis on the numbered signals provided above
- Do NOT make claims that go beyond what the evidence explicitly states
- Reference specific entities, data points, and events from the signals
- When mentioning insights from multiple signals, cite all relevant sources [1][3][5]

Write 1-2 sentences explaining WHY this matters for STM publishing suppliers (companies that provide editorial, production, and technology services to publishers). Focus on:
- Market shifts or competitive dynamics clearly evidenced in the signals
- Business implications that can be directly inferred from the specific events mentioned
- Strategic importance based on the actual entities and developments listed

REQUIRED FORMAT: Start with your key insight, then use inline citations [X] to ground claims in evidence.
NEVER use "According to Signal X" or "Signal X shows" - ONLY use inline citations [X]."""

        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "You are an expert analyst in STM publishing market intelligence, writing for sales teams at publishing service providers."},
                {"role": "user", "content": prompt}
            ],
            temperature=settings.openai_temperature,
            max_tokens=150
        )

        content = response.choices[0].message.content.strip()

        # Post-process: Convert "According to Signal X" to inline citations [X]
        content = _convert_to_inline_citations(content)

        return content

    except Exception as e:
        logger.error(f"Error generating So What with OpenAI: {e}")
        # Fallback to template on error
        return _generate_so_what_template(topic, signals, impact_areas)


def _generate_so_what_template(topic: str, signals: List[Signal], impact_areas: List[str]) -> str:
    """Fallback template-based So What generation."""
    entity_count = len(set(s.entity for s in signals))
    impact_text = ", ".join(impact_areas) if impact_areas else "multiple areas"

    if entity_count > 1:
        return (
            f"Multiple players ({entity_count} entities) are moving on {topic}, "
            f"indicating a broader market shift. This impacts {impact_text} for STM suppliers."
        )
    else:
        entity = signals[0].entity if signals else "Industry"
        return (
            f"{entity} is making moves on {topic}. "
            f"This development affects {impact_text} and may signal competitive positioning."
        )


def generate_now_what(topic: str, signals: List[Signal], impact_areas: List[str]) -> List[str]:
    """
    Generate "Now What" action bullets for sales team using OpenAI.

    Args:
        topic: Theme topic
        signals: Contributing signals
        impact_areas: Impact areas for the theme

    Returns:
        AI-generated list of 2-3 action bullets
    """
    # Fallback to template if OpenAI is not configured
    if not settings.openai_api_key or settings.openai_api_key == "your-openai-api-key-here":
        return _generate_now_what_template(topic, signals, impact_areas)

    try:
        client = OpenAI(api_key=settings.openai_api_key)

        # Build context from signals
        entities = list(set(s.entity for s in signals))
        event_types = list(set(s.event_type for s in signals))
        impact_text = ", ".join(impact_areas) if impact_areas else "multiple areas"

        # Check if this is a competitor theme
        competitors = get_competitor_entities_from_signals(signals)
        is_competitor = is_competitor_theme(signals)

        # Create signal summaries for context with explicit numbering for citation
        signal_summaries = []
        for i, sig in enumerate(signals[:20], 1):
            signal_summaries.append(f"Signal {i}: {sig.entity} - {sig.evidence_snippet[:200]}")

        # Add competitor context to prompt if applicable
        competitor_context = ""
        if is_competitor:
            competitor_context = f"\n🔴 COMPETITIVE INTELLIGENCE: This theme involves your direct competitors: {', '.join(competitors)}\nFocus on competitive response actions, defensive strategies, and opportunities to differentiate."

        prompt = f"""STRICT RULE: Do NOT start actions with "According to Signal" or "based on Signal".
Use inline citations [X] after entity/initiative names only when citing specific developments.

You are writing an "Action Items" section for a weekly intelligence brief for STM (Scientific, Technical, Medical) publishing sales teams.

Topic: {topic}
Entities involved: {', '.join(entities)}
Event types: {', '.join(event_types)}
Impact areas: {impact_text}{competitor_context}

Evidence from signals:
{chr(10).join(signal_summaries)}

CRITICAL REQUIREMENTS FOR ACTIONABILITY:
1. Be SPECIFIC about WHO (which clients/prospects, by name or category)
2. Be SPECIFIC about WHAT (exact action, not "discuss" or "engage")
3. Be SPECIFIC about HOW (talking points, offering, or approach)
4. Include CONCRETE details from the signals (entity names, specific initiatives)
5. Use inline citations [X] - NEVER "According to Signal X" or "based on Signal X"

EXAMPLES OF GOOD VS BAD ACTION ITEMS:

✅ EXCELLENT (Inline Citations):
"Schedule calls with your Taylor & Francis account contacts to discuss how their new Hiroshima University open research partnership [1] could inform similar transparency programs for your clients, positioning your editorial services as implementation partners."

❌ INCORRECT (Old Format - DO NOT USE):
"According to Signal 1, schedule calls with your Taylor & Francis account contacts..."
(Never start actions with "According to Signal X")

✅ EXCELLENT (Inline Citations):
"Reach out to editors-in-chief at mid-tier publishers to demo AI-assisted peer review capabilities similar to Nature's recently launched tool [2], emphasizing faster turnaround times and quality checks as key differentiators."

❌ BAD (Too Vague, No Citation):
"Discuss open access trends with publishing clients."
(Missing: WHO specifically, WHAT to discuss, HOW to position, NO citation)

CRITICAL GROUNDING REQUIREMENTS:
- Use ONLY inline citations [X] - NEVER "According to Signal X" or "based on Signal X"
- Base recommendations ONLY on the numbered signals provided above
- Do NOT suggest actions based on assumptions beyond what the evidence shows
- ALWAYS mention specific entity names from the signals in your actions
- Place [X] immediately after each entity/initiative reference from signals
- Tailor recommendations to the actual entities and developments mentioned
- Each action must reference at least one concrete entity or initiative from the signals

Generate 2-3 HIGHLY SPECIFIC, ACTIONABLE bullet points that sales teams at STM publishing service providers should take.

REQUIRED FORMAT for each action:
"[Specific Action Verb] with [Specific WHO] to [Specific WHAT] regarding [Specific Entity/Initiative from signals] [X], [HOW to position/approach]."

Each action MUST include:
1. WHO: Specific client segment, role, or publisher type (e.g., "editors-in-chief at mid-tier publishers", "your Wiley account contacts")
2. WHAT: Concrete action, not vague verbs (use "Schedule demo", "Send case study", "Propose pilot", NOT "discuss" or "engage")
3. ENTITY/INITIATIVE: Reference actual entity names and developments from the signals with inline citation [X]
4. HOW: Specific positioning, talking points, or value proposition

Return ONLY the bullet points, one per line, without numbering or bullet symbols."""

        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "You are an expert sales strategist for STM publishing service providers, creating actionable intelligence for sales teams."},
                {"role": "user", "content": prompt}
            ],
            temperature=settings.openai_temperature,
            max_tokens=200
        )

        # Parse response into list of actions
        content = response.choices[0].message.content.strip()
        actions = [line.strip() for line in content.split('\n') if line.strip()]

        # Ensure we have 2-3 actions
        return actions[:3] if len(actions) >= 2 else _generate_now_what_template(topic, signals, impact_areas)

    except Exception as e:
        logger.error(f"Error generating Now What with OpenAI: {e}")
        # Fallback to template on error
        return _generate_now_what_template(topic, signals, impact_areas)


def _generate_now_what_template(topic: str, signals: List[Signal], impact_areas: List[str]) -> List[str]:
    """Fallback template-based Now What generation."""
    actions = []
    entities = list(set(s.entity for s in signals))

    # Action 1: Monitor/track
    if len(entities) > 1:
        actions.append(f"Monitor developments from {', '.join(entities[:3])} on {topic}")
    else:
        actions.append(f"Track {entities[0]}'s progress on {topic} for competitive insights")

    # Action 2: Based on impact areas
    if "Ops" in impact_areas:
        actions.append("Review operational implications and prepare client talking points")
    elif "Tech" in impact_areas:
        actions.append("Assess technology implications for product roadmap discussions")
    elif "Integrity" in impact_areas:
        actions.append("Prepare integrity/compliance messaging for affected clients")
    elif "Procurement" in impact_areas:
        actions.append("Identify procurement opportunities arising from this development")
    else:
        actions.append("Prepare briefing materials for client conversations")

    # Action 3: Proactive outreach
    actions.append("Consider proactive outreach to clients who may be impacted")

    return actions[:3]


def create_theme_from_cluster(
    topic: str,
    signals: List[Signal],
) -> Dict:
    """
    Create a theme dictionary from a cluster of signals.

    Args:
        topic: Original topic string
        signals: List of signals in the cluster

    Returns:
        Dictionary with theme data (ready to create Theme model)
    """
    impact_areas = collect_impact_areas(signals)
    key_players = collect_key_players(signals)

    # Check if this is a competitor theme
    is_competitor = is_competitor_theme(signals)
    competitors = get_competitor_entities_from_signals(signals)

    # Create a readable title with competitor indicator
    title_prefix = "🔴 COMPETITOR: " if is_competitor else ""
    if len(key_players) > 2:
        title = f"{title_prefix}{topic.title()}: {key_players[0]}, {key_players[1]} and {len(key_players) - 2} others"
    elif len(key_players) == 2:
        title = f"{title_prefix}{topic.title()}: {key_players[0]} and {key_players[1]}"
    else:
        title = f"{title_prefix}{topic.title()}: {key_players[0]}" if key_players else f"{title_prefix}{topic.title()}"

    return {
        "title": title,
        "signal_ids": [s.id for s in signals],
        "key_players": key_players,
        "aggregate_confidence": aggregate_confidence(signals),
        "impact_areas": impact_areas,
        "so_what": generate_so_what(topic, signals, impact_areas),
        "now_what": generate_now_what(topic, signals, impact_areas),
        "is_competitor": is_competitor,  # Track competitor theme flag
        "competitors": competitors,  # List of competitor entities
    }


def rank_themes(themes: List[Dict]) -> List[Dict]:
    """
    Rank themes by competitor flag, impact area coverage, signal count, and confidence.

    Ranking criteria (priority order):
    1. Competitor theme flag (competitor themes ranked first)
    2. Impact area count (more = higher)
    3. Signal count (more = higher)
    4. Confidence (High > Medium > Low)

    Args:
        themes: List of theme dictionaries

    Returns:
        Sorted list of themes (highest rank first)
    """
    confidence_score = {"High": 3, "Medium": 2, "Low": 1}

    def sort_key(theme: Dict) -> Tuple:
        return (
            theme.get("is_competitor", False),  # Competitor themes first (True > False)
            len(theme["impact_areas"]),  # More impact areas = higher
            len(theme["signal_ids"]),     # More signals = higher
            confidence_score.get(theme["aggregate_confidence"], 0),  # Higher confidence = higher
        )

    return sorted(themes, key=sort_key, reverse=True)


def synthesize_weekly_themes(signals: List[Signal]) -> List[Dict]:
    """
    Main function to synthesize themes from signals.

    Args:
        signals: List of signals from the past week

    Returns:
        Ranked list of theme dictionaries
    """
    if not signals:
        return []

    # Step 1: Cluster signals by topic
    clusters = cluster_signals_by_topic(signals)

    # Step 2: Create themes from clusters
    themes = []
    for topic, cluster_signals in clusters.items():
        theme = create_theme_from_cluster(topic, cluster_signals)
        themes.append(theme)

    # Step 3: Rank themes
    ranked_themes = rank_themes(themes)

    return ranked_themes


# =============================================================================
# Weekly Brief Functions
# =============================================================================

def get_week_boundaries(reference_date: date = None) -> Tuple[date, date]:
    """
    Get the start and end dates for the past 7 days (rolling window).

    The week is the 7-day period ending on the reference date (inclusive).

    Args:
        reference_date: End date for the week (defaults to today)

    Returns:
        Tuple of (week_start, week_end) - 7 days ending on reference_date
    """
    if reference_date is None:
        reference_date = date.today()

    # Rolling 7-day window ending on reference_date
    week_end = reference_date
    week_start = reference_date - timedelta(days=6)

    return week_start, week_end


def get_existing_brief_for_week(db: Session, week_start: date, week_end: date) -> Optional[WeeklyBrief]:
    """
    Check if a brief already exists for the given week.

    Args:
        db: Database session
        week_start: Start of week
        week_end: End of week

    Returns:
        Existing WeeklyBrief if found, None otherwise
    """
    return db.query(WeeklyBrief).filter(
        WeeklyBrief.week_start == week_start,
        WeeklyBrief.week_end == week_end,
    ).first()


def create_weekly_brief(
    db: Session,
    week_start: date,
    week_end: date,
    themes: List[Theme],
    total_signals: int,
) -> WeeklyBrief:
    """
    Create a new WeeklyBrief record.

    Args:
        db: Database session
        week_start: Start of week
        week_end: End of week
        themes: List of Theme objects for this brief
        total_signals: Total number of signals processed

    Returns:
        Created WeeklyBrief object
    """
    # Collect all unique impact areas from themes
    coverage_areas = set()
    for theme in themes:
        coverage_areas.update(theme.impact_areas or [])

    brief = WeeklyBrief(
        week_start=week_start,
        week_end=week_end,
        theme_ids=[t.id for t in themes],
        total_signals=total_signals,
        coverage_areas=sorted(list(coverage_areas)),
    )

    db.add(brief)
    db.commit()
    db.refresh(brief)

    return brief


def save_themes(db: Session, theme_dicts: List[Dict]) -> List[Theme]:
    """
    Save theme dictionaries as Theme records.

    Args:
        db: Database session
        theme_dicts: List of theme data dictionaries

    Returns:
        List of created Theme objects
    """
    themes = []
    for theme_data in theme_dicts:
        theme = Theme(
            title=theme_data["title"],
            signal_ids=theme_data["signal_ids"],
            key_players=theme_data["key_players"],
            aggregate_confidence=theme_data["aggregate_confidence"],
            impact_areas=theme_data["impact_areas"],
            so_what=theme_data["so_what"],
            now_what=theme_data["now_what"],
        )
        db.add(theme)
        themes.append(theme)

    db.commit()
    for theme in themes:
        db.refresh(theme)

    return themes


def generate_weekly_brief(db: Session, reference_date: date = None) -> Optional[WeeklyBrief]:
    """
    Generate the weekly brief for a given week.

    This is the main entry point for brief generation.
    Idempotent: returns existing brief if one already exists for the week.

    Args:
        db: Database session
        reference_date: Date to generate brief for (defaults to today)

    Returns:
        WeeklyBrief object (new or existing), or None if no signals
    """
    week_start, week_end = get_week_boundaries(reference_date)

    # Check for existing brief (idempotency)
    existing = get_existing_brief_for_week(db, week_start, week_end)
    if existing:
        return existing

    # Get signals for the week
    signals = get_signals_for_week(db, week_end)

    if not signals:
        return None

    # Synthesize themes
    theme_dicts = synthesize_weekly_themes(signals)

    # Save themes to database
    themes = save_themes(db, theme_dicts)

    # Create and return brief
    brief = create_weekly_brief(db, week_start, week_end, themes, len(signals))

    return brief


def get_brief_by_id(db: Session, brief_id: UUID) -> Optional[WeeklyBrief]:
    """
    Get a weekly brief by ID.

    Args:
        db: Database session
        brief_id: UUID of the brief

    Returns:
        WeeklyBrief if found, None otherwise
    """
    return db.query(WeeklyBrief).filter(WeeklyBrief.id == brief_id).first()


def get_current_brief(db: Session) -> Optional[WeeklyBrief]:
    """
    Get the most recent weekly brief.

    Args:
        db: Database session

    Returns:
        Most recent WeeklyBrief, or None if no briefs exist
    """
    return db.query(WeeklyBrief).order_by(WeeklyBrief.generated_at.desc()).first()


def get_themes_by_ids(db: Session, theme_ids: List[UUID]) -> List[Theme]:
    """
    Get themes by their IDs, preserving order.

    Args:
        db: Database session
        theme_ids: List of theme UUIDs

    Returns:
        List of Theme objects in the same order as theme_ids
    """
    themes = db.query(Theme).filter(Theme.id.in_(theme_ids)).all()

    # Preserve order from theme_ids
    theme_map = {t.id: t for t in themes}
    return [theme_map[tid] for tid in theme_ids if tid in theme_map]


def get_signals_by_ids(db: Session, signal_ids: List[UUID]) -> Dict[UUID, Signal]:
    """
    Get signals by their IDs as a dictionary.

    Args:
        db: Database session
        signal_ids: List of signal UUIDs

    Returns:
        Dictionary mapping signal ID to Signal object
    """
    signals = db.query(Signal).filter(Signal.id.in_(signal_ids)).all()
    return {s.id: s for s in signals}


# =============================================================================
# Notification Functions
# =============================================================================

def create_notification(
    db: Session,
    notification_type: str,
    title: str,
    message: str,
    link: Optional[str] = None
) -> Notification:
    """
    Create a notification for the curator dashboard.

    Args:
        db: Database session
        notification_type: Type of notification (pending_signals, trigger_alert, system)
        title: Notification title
        message: Notification message
        link: Optional link to related resource

    Returns:
        Created Notification object
    """
    notification = Notification(
        type=notification_type,
        title=title,
        message=message,
        link=link,
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    return notification


# =============================================================================
# Entity Management Functions
# =============================================================================

def get_entities(
    db: Session,
    segment: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> Tuple[List[Entity], int]:
    """
    Get a list of entities with optional filtering.

    Args:
        db: Database session
        segment: Filter by segment (customer, competitor, industry, influencer)
        limit: Maximum number of entities to return
        offset: Number of entities to skip

    Returns:
        Tuple of (list of entities, total count)
    """
    query = db.query(Entity)

    if segment:
        query = query.filter(Entity.segment == segment)

    total = query.count()

    entities = query.order_by(Entity.name).offset(offset).limit(limit).all()

    return entities, total


def get_entity_by_id(db: Session, entity_id: UUID) -> Optional[Entity]:
    """
    Get an entity by ID.

    Args:
        db: Database session
        entity_id: UUID of the entity

    Returns:
        Entity if found, None otherwise
    """
    return db.query(Entity).filter(Entity.id == entity_id).first()


def get_entity_by_name(db: Session, name: str) -> Optional[Entity]:
    """
    Get an entity by name or alias (case-insensitive).

    Args:
        db: Database session
        name: Entity name or alias to search for

    Returns:
        Entity if found, None otherwise
    """
    from sqlalchemy import func, or_

    # Search by exact name (case-insensitive) or in aliases array
    return db.query(Entity).filter(
        or_(
            func.lower(Entity.name) == name.lower(),
            Entity.aliases.contains([name])  # PostgreSQL array contains
        )
    ).first()


def create_entity(db: Session, entity_data: EntityCreate) -> Entity:
    """
    Create a new entity.

    Args:
        db: Database session
        entity_data: Validated entity data from request

    Returns:
        Created Entity object
    """
    entity = Entity(
        name=entity_data.name,
        segment=entity_data.segment.value,
        aliases=entity_data.aliases or [],
        entity_metadata=entity_data.entity_metadata,
        notes=entity_data.notes,
    )

    db.add(entity)
    db.commit()
    db.refresh(entity)

    return entity


def update_entity(db: Session, entity_id: UUID, entity_data: EntityUpdate) -> Optional[Entity]:
    """
    Update an existing entity.

    Args:
        db: Database session
        entity_id: UUID of the entity to update
        entity_data: Validated update data

    Returns:
        Updated Entity if found, None otherwise
    """
    entity = get_entity_by_id(db, entity_id)

    if not entity:
        return None

    # Update only provided fields
    update_data = entity_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field == "segment" and value is not None:
            setattr(entity, field, value.value)
        else:
            setattr(entity, field, value)

    entity.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(entity)

    return entity


def delete_entity(db: Session, entity_id: UUID) -> bool:
    """
    Delete an entity (cascades to signal_entities).

    Args:
        db: Database session
        entity_id: UUID of the entity to delete

    Returns:
        True if deleted, False if not found
    """
    entity = get_entity_by_id(db, entity_id)

    if not entity:
        return False

    db.delete(entity)
    db.commit()

    return True


def get_segment_statistics(db: Session, days: int = 7) -> Dict[str, Dict]:
    """
    Get signal statistics by segment for dashboard widgets.

    Args:
        db: Database session
        days: Number of days to look back for recent signals (default: 7)

    Returns:
        Dictionary mapping segment to stats (signal_count, entity_count, recent_signals)
    """
    from sqlalchemy import func

    # Calculate the cutoff date for recent signals
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Get all segments
    segments = ["customer", "competitor", "industry", "influencer"]

    stats = {}

    for segment in segments:
        # Count entities in this segment
        entity_count = db.query(Entity).filter(Entity.segment == segment).count()

        # Get entity IDs for this segment
        entity_ids = [e.id for e in db.query(Entity.id).filter(Entity.segment == segment).all()]

        if entity_ids:
            # Count total signals linked to entities in this segment
            total_signals = db.query(SignalEntity).filter(
                SignalEntity.entity_id.in_(entity_ids)
            ).count()

            # Count recent signals (last N days) linked to entities in this segment
            recent_signals = db.query(SignalEntity).join(
                Signal, SignalEntity.signal_id == Signal.id
            ).filter(
                SignalEntity.entity_id.in_(entity_ids),
                Signal.created_at >= cutoff_date,
                Signal.deleted_at.is_(None)
            ).count()
        else:
            total_signals = 0
            recent_signals = 0

        stats[segment] = {
            "segment": segment,
            "signal_count": total_signals,
            "entity_count": entity_count,
            "recent_signals": recent_signals,
        }

    return stats


# =============================================================================
# Signal Summary Generation
# =============================================================================

def generate_signal_summary(signals: List[Signal]) -> Dict:
    """
    Generate AI-powered executive summary from a list of signals.

    Args:
        signals: List of Signal objects to summarize

    Returns:
        Dictionary with summary, key_insights, metadata
    """
    import json

    if not signals:
        return {
            "summary": "No signals to summarize.",
            "key_insights": [],
            "total_signals": 0,
            "date_range": "N/A",
            "segments_covered": [],
            "impact_areas": [],
        }

    # Extract metadata
    total_signals = len(signals)
    dates = [s.created_at for s in signals]
    date_range = f"{min(dates).strftime('%Y-%m-%d')} to {max(dates).strftime('%Y-%m-%d')}"

    # Collect unique segments and impact areas
    segments = set()
    impact_areas = set()
    entities = set()
    topics = set()

    for signal in signals:
        impact_areas.update(signal.impact_areas)
        entities.add(signal.entity)
        topics.add(signal.topic)

        # Get segments from entity relationships
        for entity_link in signal.entity_links:
            if entity_link.entity:
                segments.add(entity_link.entity.segment)

    # Fallback if OpenAI is not configured
    if not settings.openai_api_key or settings.openai_api_key == "your-openai-api-key-here":
        return _generate_summary_fallback(signals, total_signals, date_range, segments, impact_areas)

    try:
        client = OpenAI(api_key=settings.openai_api_key)

        # Group signals by topic for better analysis
        topic_groups = {}
        for signal in signals:
            if signal.topic not in topic_groups:
                topic_groups[signal.topic] = []
            topic_groups[signal.topic].append(signal)

        # Build comprehensive signal summaries grouped by topic
        grouped_summaries = {}
        signal_id_map = {}  # Track all signal IDs

        for topic, topic_signals in topic_groups.items():
            grouped_summaries[topic] = []
            for signal in topic_signals[:50]:  # Limit per topic to manage tokens
                signal_summary = {
                    "id": str(signal.id),
                    "entity": signal.entity,
                    "event_type": signal.event_type,
                    "evidence": signal.evidence_snippet[:150],
                    "impact_areas": signal.impact_areas,
                }
                grouped_summaries[topic].append(signal_summary)
                signal_id_map[str(signal.id)] = signal

        prompt = f"""You are analyzing {total_signals} market intelligence signals for STM publishing sales teams.

Date range: {date_range}
Segments covered: {', '.join(segments) if segments else 'various'}
Impact areas: {', '.join(impact_areas)}

Signals grouped by topic:
{json.dumps(grouped_summaries, indent=2)}

CRITICAL INSTRUCTIONS:
1. Analyze ALL {total_signals} signals provided across all topics
2. Each key insight MUST reference 10-30 signal IDs (not just 2-3)
3. Make sure insights are based on patterns across MANY signals, not individual signals
4. Reference signal IDs from multiple topics to show breadth of analysis

Generate an executive summary in JSON format with this structure:
{{
  "summary": "2-3 sentence overall summary synthesizing ALL {total_signals} signals",
  "key_insights": [
    {{
      "insight": "One clear insight based on multiple signals showing a pattern",
      "signal_ids": ["minimum", "10", "signal", "IDs", "from", "different", "topics"],
      "entities": ["key", "entities", "involved"]
    }}
  ]
}}

Focus on:
1. Patterns and trends across MULTIPLE signals (not individual events)
2. Market movements involving many entities
3. Strategic implications for STM sales teams

Include 3-5 key insights. Each insight MUST be supported by at least 10 signal IDs showing a real pattern."""

        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "You are an expert analyst in STM publishing market intelligence. You excel at identifying patterns across large datasets. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,  # Lower temperature for more factual summaries
            max_tokens=1500  # Increased to handle more comprehensive analysis
        )

        # Parse JSON response
        content = response.choices[0].message.content.strip()
        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        result = json.loads(content)

        return {
            "summary": result.get("summary", ""),
            "key_insights": result.get("key_insights", []),
            "total_signals": total_signals,
            "date_range": date_range,
            "segments_covered": sorted(list(segments)),
            "impact_areas": sorted(list(impact_areas)),
        }

    except Exception as e:
        logger.error(f"Error generating summary with OpenAI: {e}")
        return _generate_summary_fallback(signals, total_signals, date_range, segments, impact_areas)


def _generate_summary_fallback(
    signals: List[Signal],
    total_signals: int,
    date_range: str,
    segments: set,
    impact_areas: set
) -> Dict:
    """Template-based fallback summary generation."""

    # Group signals by topic
    topics = {}
    for signal in signals:
        if signal.topic not in topics:
            topics[signal.topic] = []
        topics[signal.topic].append(signal)

    # Generate simple insights by topic
    insights = []
    for topic, topic_signals in sorted(topics.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
        entities = list(set(s.entity for s in topic_signals))
        signal_ids = [str(s.id) for s in topic_signals]

        insights.append({
            "insight": f"{len(topic_signals)} signals related to {topic} involving {', '.join(entities[:3])}{'...' if len(entities) > 3 else ''}",
            "signal_ids": signal_ids,
            "entities": entities[:5],
        })

    summary = f"Analysis of {total_signals} signals from {date_range} covering {', '.join(sorted(list(impact_areas)))} impact areas across {', '.join(sorted(list(segments)))} segments."

    return {
        "summary": summary,
        "key_insights": insights,
        "total_signals": total_signals,
        "date_range": date_range,
        "segments_covered": sorted(list(segments)),
        "impact_areas": sorted(list(impact_areas)),
    }

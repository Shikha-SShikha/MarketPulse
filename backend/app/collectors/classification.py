"""Keyword-based signal classification for automated collectors."""

from functools import lru_cache
from typing import Dict, List, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session


# Event type detection keywords
EVENT_TYPE_KEYWORDS = {
    'announcement': ['announce', 'announces', 'announced', 'launch', 'introduce', 'unveil', 'reveal', 'release'],
    'policy': ['policy', 'policies', 'mandate', 'mandates', 'requirement', 'requirements', 'regulation', 'guideline', 'guidelines'],
    'partnership': ['partner', 'partnership', 'collaboration', 'collaborate', 'alliance', 'agreement', 'joint', 'together with'],
    'hire': ['appoint', 'appointed', 'hire', 'hired', 'join', 'joins', 'joined', 'promote', 'promoted', 'executive', 'ceo', 'cto', 'cio'],
    'm&a': ['acquire', 'acquired', 'acquisition', 'merger', 'merges', 'merged', 'buy', 'buys', 'bought', 'purchase', 'purchased'],
    'launch': ['release', 'released', 'debut', 'debuting', 'available', 'new product', 'new service', 'new platform'],
    'retraction': ['retract', 'retraction', 'withdraw', 'withdrawn', 'correction', 'erratum'],
    'service_model': ['onshore', 'offshore', 'nearshore', 'delivery model', 'staffing', 'team structure', 'service offering', 'editorial team'],
}

# Topic detection keywords
TOPIC_KEYWORDS = {
    'Open Access': ['open access', 'oa', 'plan s', 'green oa', 'gold oa', 'diamond oa', 'apc', 'article processing'],
    'Integrity': ['retraction', 'misconduct', 'plagiarism', 'ethics', 'peer review', 'research integrity', 'fabrication', 'falsification'],
    'AI/ML': ['artificial intelligence', 'machine learning', 'ai', 'ml', 'neural network', 'deep learning', 'chatgpt', 'generative ai'],
    'Workflow': ['workflow', 'editorial', 'submission', 'peer review system', 'manuscript', 'publishing platform'],
    'Data': ['data sharing', 'data policy', 'fair data', 'research data', 'data repository'],
    'Preprints': ['preprint', 'preprints', 'biorxiv', 'arxiv', 'medrxiv', 'prepublication'],
    'Accessibility': ['accessibility', 'wcag', 'ada', 'inclusive design', 'accessible publishing', 'screen reader', 'alt text', 'inclusive', 'disability'],
    'Production Platforms': ['publisher central', 'editorial system', 'publishing platform', 'cms', 'content management', 'production platform', 'manuscript system'],
    'Delivery Models': ['onshore', 'offshore', 'nearshore', 'outsourcing', 'delivery model', 'service model', 'team structure', 'staffing model'],
}

# Impact area detection keywords
IMPACT_AREA_KEYWORDS = {
    'Ops': ['operation', 'operational', 'workflow', 'process', 'editorial', 'production', 'publishing'],
    'Tech': ['technology', 'technical', 'platform', 'system', 'infrastructure', 'software', 'digital', 'api'],
    'Integrity': ['integrity', 'ethics', 'ethical', 'retraction', 'misconduct', 'compliance', 'standards'],
    'Procurement': ['contract', 'procurement', 'purchasing', 'vendor', 'cost', 'pricing', 'subscription', 'licensing'],
}

# Known STM publishing entities for entity extraction
# DEPRECATED: This list is kept for backward compatibility only.
# New code should use extract_entities_from_db() which queries the database.
KNOWN_ENTITIES = [
    # Major Publishers
    "Springer", "Springer Nature", "Elsevier", "Wiley", "Wiley-Blackwell",
    "Taylor & Francis", "Taylor and Francis", "SAGE", "SAGE Publishing",
    "Oxford University Press", "OUP", "Cambridge University Press", "CUP",
    "Nature", "Science", "Cell", "Lancet", "BMJ",

    # Societies
    "IEEE", "ACM", "ACS", "APS", "AIP", "RSC", "AMS",

    # Open Access
    "PLOS", "Public Library of Science", "BioMed Central", "BMC",
    "Frontiers", "MDPI", "PeerJ", "eLife",

    # Infrastructure
    "Crossref", "ORCID", "DOI", "DOAJ", "PubMed", "arXiv",

    # Production & Editorial Service Providers (Competitors)
    "Kriyadocs", "KnowledgeWorks", "Cactus", "Editage",
    "SPi Global", "Straive", "Integra", "TNQ Books", "TNQ",
    "Exeter Premedia", "Aptara", "MPS Limited", "MPS",
    "Newgen KnowledgeWorks", "Newgen", "Publishing Technology", "PubTech",
    "Aries Systems", "Editorial Manager", "ScholarOne", "eJournal Press",

    # Integrity Organizations
    "COPE", "Committee on Publication Ethics",
    "ICMJE", "International Committee of Medical Journal Editors",
    "Retraction Watch",

    # Funders
    "NIH", "National Institutes of Health",
    "Wellcome", "Wellcome Trust",
    "Gates Foundation", "Bill & Melinda Gates Foundation",
    "NSF", "National Science Foundation",
    "Plan S", "cOAlition S",
    "European Commission", "EU",
]


# Cache for entity data to avoid repeated database queries
_ENTITY_CACHE: Optional[List[Tuple[str, List[str], UUID]]] = None


def classify_text(text: str) -> Optional[Dict[str, any]]:
    """
    Classify text using keyword matching.

    Args:
        text: Text to classify (typically title + description)

    Returns:
        Dictionary with event_type, topic, impact_areas
        None if content is irrelevant or cannot be classified
    """
    text_lower = text.lower()

    # Filter out irrelevant content first
    if not is_relevant_to_stm(text_lower):
        return None

    # Detect event_type (required)
    event_type = None
    for evt, keywords in EVENT_TYPE_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            event_type = evt
            break

    # Detect topic (required - if no topic detected, signal is too generic)
    topic = None
    for top, keywords in TOPIC_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            topic = top
            break

    # Reject signals with no event type AND no topic (too generic)
    if not event_type and not topic:
        return None

    # If no event type but has topic, default to 'other'
    if not event_type:
        event_type = 'other'

    # If no topic detected, reject (every signal must have a topic)
    if not topic:
        return None

    # Detect impact areas (can be multiple)
    impact_areas = []
    for area, keywords in IMPACT_AREA_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            impact_areas.append(area)

    # Default to Ops if no impact areas detected
    if not impact_areas:
        impact_areas = ['Ops']

    return {
        'event_type': event_type,
        'topic': topic,
        'impact_areas': impact_areas,
    }


def is_relevant_to_stm(text_lower: str) -> bool:
    """
    Check if content is relevant to STM publishing intelligence.

    Filters out:
    - Journal TOC notices
    - Generic announcements without context
    - Non-publishing news

    Args:
        text_lower: Lowercased text to check

    Returns:
        True if relevant, False if should be filtered out
    """
    # Filter patterns for irrelevant content
    irrelevant_patterns = [
        # Journal TOC notices
        r'volume \d+, issue \d+',
        r'toc alert',
        r'table of contents',
        r'latest articles from',
        r'new articles in',

        # Generic journal announcements without context
        r'^\s*science\s*$',  # Just "Science" with no context
        r'^\s*nature\s*$',   # Just "Nature" with no context

        # Other generic patterns
        r'subscribe to',
        r'email alert',
        r'rss feed for',
    ]

    import re
    for pattern in irrelevant_patterns:
        if re.search(pattern, text_lower):
            return False

    # Must contain at least some publishing/research-related keywords
    relevant_keywords = [
        # Publishing activities
        'publish', 'publication', 'journal', 'article', 'manuscript',
        'peer review', 'editorial', 'editor', 'author',

        # Research topics
        'research', 'study', 'findings', 'discovery', 'breakthrough',

        # Publishing industry
        'open access', 'retraction', 'preprint', 'integrity',
        'ai', 'artificial intelligence', 'machine learning',
        'data', 'policy', 'mandate', 'guideline',

        # Business/market
        'acquire', 'merger', 'partnership', 'launch', 'announce',
        'platform', 'service', 'workflow', 'system',

        # Organizations
        'publisher', 'society', 'association', 'university press',
        'crossref', 'orcid', 'doi',
    ]

    # Check for at least one relevant keyword
    has_relevant_keyword = any(kw in text_lower for kw in relevant_keywords)

    # Too short and no relevant keywords = likely irrelevant
    if len(text_lower) < 100 and not has_relevant_keyword:
        return False

    return True


def extract_entities(text: str) -> List[str]:
    """
    Extract known entity names from text.

    Args:
        text: Text to extract entities from

    Returns:
        List of entity names found (empty list if none found)
    """
    entities = []
    text_lower = text.lower()

    for entity in KNOWN_ENTITIES:
        if entity.lower() in text_lower:
            # Avoid duplicates (e.g., "Springer" and "Springer Nature")
            if entity not in entities:
                # Check if it's not a substring of an already found entity
                is_substring = False
                for existing in entities:
                    if entity.lower() in existing.lower() or existing.lower() in entity.lower():
                        # Keep the longer one
                        if len(entity) > len(existing):
                            entities.remove(existing)
                            entities.append(entity)
                        is_substring = True
                        break

                if not is_substring:
                    entities.append(entity)

    return entities


def assign_confidence(source_type: str, classification_quality: str = 'good') -> str:
    """
    Assign confidence level based on source type and classification quality.

    Args:
        source_type: Type of data source (rss, linkedin, web, email)
        classification_quality: Quality of classification (good, medium, poor)

    Returns:
        Confidence level: High, Medium, or Low
    """
    # RSS feeds and email newsletters are generally reliable
    if source_type in ['rss', 'email']:
        if classification_quality == 'good':
            return 'High'
        else:
            return 'Medium'

    # Web scraping and LinkedIn are less reliable
    elif source_type in ['web', 'linkedin']:
        if classification_quality == 'good':
            return 'Medium'
        else:
            return 'Low'

    # Default to Medium
    return 'Medium'


# =============================================================================
# Database-Driven Entity Extraction
# =============================================================================

def _load_entity_cache(db: Session) -> List[Tuple[str, List[str], UUID]]:
    """
    Load all entities from database into cache.

    Returns list of tuples: (name, aliases, entity_id)
    """
    from app.models import Entity

    entities = db.query(Entity).all()

    cache = []
    for entity in entities:
        # Add primary name
        cache.append((entity.name, entity.aliases or [], entity.id))

    return cache


def extract_entities_from_db(db: Session, text: str, use_cache: bool = True) -> List[Tuple[str, UUID]]:
    """
    Extract known entity names from text using database lookup.

    Args:
        db: Database session
        text: Text to extract entities from
        use_cache: Whether to use cached entity data (default: True)

    Returns:
        List of tuples: (entity_name, entity_id)
    """
    global _ENTITY_CACHE

    # Load cache if not loaded or cache disabled
    if _ENTITY_CACHE is None or not use_cache:
        _ENTITY_CACHE = _load_entity_cache(db)

    found_entities = []
    text_lower = text.lower()

    for entity_name, aliases, entity_id in _ENTITY_CACHE:
        # Check primary name
        if entity_name.lower() in text_lower:
            found_entities.append((entity_name, entity_id))
            continue

        # Check aliases
        for alias in aliases:
            if alias.lower() in text_lower:
                # Use primary entity name, not alias
                found_entities.append((entity_name, entity_id))
                break

    # Remove duplicates (keep first occurrence)
    seen_ids = set()
    unique_entities = []
    for name, entity_id in found_entities:
        if entity_id not in seen_ids:
            seen_ids.add(entity_id)
            unique_entities.append((name, entity_id))

    return unique_entities


def clear_entity_cache():
    """
    Clear the entity cache.

    Call this after creating/updating/deleting entities to refresh the cache.
    """
    global _ENTITY_CACHE
    _ENTITY_CACHE = None

# Phase 2A: Automation - Implementation Plan

## Overview

Add automated signal collection from multiple sources (RSS feeds, LinkedIn, web scraping, email newsletters) to reduce curator burden from 5 hours/week to <2 hours/week (review only).

**Collection Schedule:** Daily at 9 AM UTC
**Review Process:** Auto-approve high-confidence signals, low-confidence requires curator review
**Alert Delivery:** Dashboard notifications only (no external integrations yet)

---

## Architecture Design

### Module Structure

```
backend/app/
├── collectors/           # NEW: Data collection modules
│   ├── __init__.py
│   ├── base.py          # Abstract base collector class
│   ├── rss_collector.py # RSS feed parser
│   ├── linkedin_collector.py  # LinkedIn scraper
│   ├── web_collector.py # Generic web scraper
│   └── email_collector.py  # Email ingestion
├── models.py            # MODIFY: Add DataSource, SignalStatus, Notification
├── services.py          # MODIFY: Add collector services
├── jobs.py              # MODIFY: Add collection job
├── scheduler.py         # MODIFY: Register collection job
├── config.py            # MODIFY: Add collector configuration
├── routes.py            # MODIFY: Add review & notification endpoints
└── schemas.py           # MODIFY: Add new schemas
```

### Data Flow

```
Scheduled Job (9 AM UTC)
  ↓
collectors/rss_collector.py → Parse RSS feeds → Extract signals
collectors/linkedin_collector.py → Scrape LinkedIn → Extract signals
collectors/web_collector.py → Scrape websites → Extract signals
collectors/email_collector.py → Parse emails → Extract signals
  ↓
Signal Classification (keyword matching + rules)
  ↓
Confidence Scoring (High for RSS/email, Medium for scraping)
  ↓
Auto-approve High confidence → DB (approved)
Low/Medium confidence → DB (pending_review) → Curator review UI
  ↓
Dashboard Notification (for curators)
  ↓
Weekly Brief Generation (existing flow)
```

---

## Database Schema Changes

### 1. New Model: DataSource

Track configured data sources and collection metadata.

```python
class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)  # e.g., "Springer Blog RSS"
    source_type = Column(String(50), nullable=False)  # rss, linkedin, web, email
    url = Column(Text, nullable=True)  # Feed URL or website URL
    config = Column(JSON, nullable=True)  # Source-specific config (selectors, keywords)

    # Collection metadata
    enabled = Column(Boolean, default=True)
    last_fetched_at = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    error_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)

    # Defaults for signals from this source
    default_confidence = Column(String(10), default="Medium")
    default_impact_areas = Column(ARRAY(String), default=[])

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 2. Modify Model: Signal

Add status and source tracking.

```python
class Signal(Base):
    # ... existing fields ...

    # NEW FIELDS:
    status = Column(String(20), default="approved")  # pending_review, approved, rejected
    data_source_id = Column(UUID, ForeignKey("data_sources.id"), nullable=True)

    # Change curator_name to optional (automated signals don't have curator)
    curator_name = Column(String(255), nullable=True)  # NULL for automated signals

    # Add reviewed_at and reviewed_by
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String(255), nullable=True)
```

### 3. New Model: Notification

Store dashboard notifications.

```python
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    type = Column(String(50), nullable=False)  # pending_signals, trigger_alert, system
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    link = Column(Text, nullable=True)  # Link to review page, signal, etc.

    # Notification state
    read = Column(Boolean, default=False)
    dismissed = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index('ix_notifications_unread', 'read', 'dismissed', 'created_at'),
    )
```

### Migration

Create migration: `alembic revision -m "add_automation_models"`

---

## Implementation Phases

### Phase 2A.1: Foundation (Week 1, Days 1-2)

**Goal:** Set up collector infrastructure and database schema.

#### Files to Create:
- `backend/app/collectors/__init__.py`
- `backend/app/collectors/base.py`

#### Files to Modify:
- `backend/app/models.py` - Add DataSource, Notification, modify Signal
- `backend/app/schemas.py` - Add DataSourceSchema, NotificationSchema, SignalStatusEnum
- `backend/app/config.py` - Add collector configuration
- `backend/requirements.txt` - Add dependencies

#### New Dependencies:
```
feedparser==6.0.11        # RSS/Atom feed parsing
beautifulsoup4==4.12.3    # HTML parsing for web scraping
selenium==4.17.2          # LinkedIn scraping (headless browser)
playwright==1.41.2        # Alternative for LinkedIn (more reliable)
aiohttp==3.9.3            # Async HTTP requests
python-dateutil==2.8.2    # Date parsing from feeds
```

#### Base Collector Interface:

```python
# backend/app/collectors/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime

class BaseCollector(ABC):
    """Abstract base class for all data collectors."""

    def __init__(self, data_source: DataSource, db: Session):
        self.data_source = data_source
        self.db = db

    @abstractmethod
    async def collect(self) -> List[Dict]:
        """
        Collect signals from the source.

        Returns:
            List of signal dictionaries ready for create_signal()
        """
        pass

    def classify_signal(self, raw_data: Dict) -> Dict:
        """
        Classify signal using keyword matching.

        Returns:
            Dict with event_type, topic, impact_areas, confidence
        """
        pass

    def extract_entities(self, text: str) -> List[str]:
        """Extract entity names from text."""
        pass

    def update_source_metadata(self, success: bool, error: str = None):
        """Update DataSource collection metadata."""
        pass
```

#### Configuration:

```python
# backend/app/config.py
class Settings(BaseSettings):
    # ... existing fields ...

    # Collector configuration
    enable_automated_collection: bool = True
    collection_schedule_hour: int = 9  # 9 AM UTC

    # LinkedIn scraping (optional)
    linkedin_email: Optional[str] = None
    linkedin_password: Optional[str] = None

    # Email ingestion
    email_ingestion_enabled: bool = False
    email_imap_server: Optional[str] = None
    email_username: Optional[str] = None
    email_password: Optional[str] = None
```

---

### Phase 2A.2: RSS Collector (Week 1, Days 3-4)

**Goal:** Implement RSS feed collection (highest priority, easiest to implement).

#### Files to Create:
- `backend/app/collectors/rss_collector.py`
- `backend/app/collectors/classification.py` (keyword matching rules)

#### RSS Collector Implementation:

```python
# backend/app/collectors/rss_collector.py
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict

class RSSCollector(BaseCollector):
    async def collect(self) -> List[Dict]:
        """Parse RSS feed and extract signals."""
        feed_url = self.data_source.url
        signals = []

        try:
            feed = feedparser.parse(feed_url)

            for entry in feed.entries:
                # Skip old entries (only last 24 hours)
                published = self.parse_date(entry.get('published'))
                if published and (datetime.utcnow() - published) > timedelta(days=1):
                    continue

                # Extract signal data
                raw_signal = {
                    'title': entry.title,
                    'description': entry.get('summary', ''),
                    'link': entry.link,
                    'published': published,
                }

                # Classify signal
                classified = self.classify_signal(raw_signal)

                if classified:  # Only include if classification succeeds
                    signals.append(classified)

            self.update_source_metadata(success=True)

        except Exception as e:
            self.update_source_metadata(success=False, error=str(e))
            raise

        return signals

    def classify_signal(self, raw_data: Dict) -> Optional[Dict]:
        """Classify RSS entry into signal."""
        title = raw_data['title']
        description = raw_data['description']
        text = f"{title} {description}"

        # Keyword matching for event_type, topic, impact_areas
        classification = classify_text(text)  # See classification.py

        if not classification:
            return None  # Skip if no classification

        return {
            'entity': self.extract_entities(text)[0] if self.extract_entities(text) else 'Unknown',
            'event_type': classification['event_type'],
            'topic': classification['topic'],
            'source_url': raw_data['link'],
            'evidence_snippet': description[:200],  # First 200 chars
            'confidence': 'High',  # RSS feeds are high confidence
            'impact_areas': classification['impact_areas'],
            'entity_tags': classification.get('entity_tags', []),
            'curator_name': None,  # Automated
            'status': 'approved',  # Auto-approve high confidence
            'data_source_id': self.data_source.id,
        }
```

#### Classification Rules:

```python
# backend/app/collectors/classification.py
"""Keyword-based signal classification."""

EVENT_TYPE_KEYWORDS = {
    'announcement': ['announce', 'launch', 'introduce', 'unveil', 'reveal'],
    'policy': ['policy', 'mandate', 'requirement', 'regulation', 'guideline'],
    'partnership': ['partner', 'collaboration', 'alliance', 'agreement', 'joint'],
    'hire': ['appoint', 'hire', 'join', 'promote', 'executive'],
    'm&a': ['acquire', 'merger', 'acquisition', 'buy', 'purchase'],
    'launch': ['release', 'debut', 'available', 'new product', 'new service'],
}

TOPIC_KEYWORDS = {
    'Open Access': ['open access', 'oa', 'plan s', 'green oa', 'gold oa'],
    'Integrity': ['retraction', 'misconduct', 'plagiarism', 'ethics', 'peer review'],
    'AI/ML': ['artificial intelligence', 'machine learning', 'ai', 'neural network'],
    'Workflow': ['workflow', 'editorial', 'submission', 'peer review system'],
}

IMPACT_AREA_KEYWORDS = {
    'Ops': ['operation', 'workflow', 'process', 'editorial', 'production'],
    'Tech': ['technology', 'platform', 'system', 'infrastructure', 'software'],
    'Integrity': ['integrity', 'ethics', 'retraction', 'misconduct'],
    'Procurement': ['contract', 'procurement', 'purchasing', 'vendor', 'cost'],
}

def classify_text(text: str) -> Optional[Dict]:
    """Classify text using keyword matching."""
    text_lower = text.lower()

    # Detect event_type
    event_type = None
    for evt, keywords in EVENT_TYPE_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            event_type = evt
            break

    if not event_type:
        return None  # Skip if no event type detected

    # Detect topic
    topic = 'General'
    for top, keywords in TOPIC_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            topic = top
            break

    # Detect impact areas
    impact_areas = []
    for area, keywords in IMPACT_AREA_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            impact_areas.append(area)

    if not impact_areas:
        impact_areas = ['Ops']  # Default

    return {
        'event_type': event_type,
        'topic': topic,
        'impact_areas': impact_areas,
    }
```

#### Testing:

Add test RSS feeds to database:
```sql
INSERT INTO data_sources (name, source_type, url, enabled, default_confidence) VALUES
('Springer Blog', 'rss', 'https://www.springernature.com/gp/researchers/campaigns-and-promotions/feed', true, 'High'),
('STM Solutions Blog', 'rss', 'https://www.stm-assoc.org/feed/', true, 'High');
```

---

### Phase 2A.3: Collection Job & Scheduler (Week 1, Day 5)

**Goal:** Add scheduled job to run collectors daily at 9 AM UTC.

#### Files to Modify:
- `backend/app/jobs.py` - Add `collect_signals_job()`
- `backend/app/scheduler.py` - Register collection job
- `backend/app/services.py` - Add collector orchestration

#### Collection Job:

```python
# backend/app/jobs.py
import logging
from app.database import SessionLocal
from app.models import DataSource
from app.collectors.rss_collector import RSSCollector

logger = logging.getLogger(__name__)

async def collect_signals_job() -> Dict:
    """
    Scheduled job to collect signals from all enabled data sources.

    Runs daily at 9 AM UTC.
    """
    db = SessionLocal()

    try:
        logger.info("Starting automated signal collection")

        # Get all enabled data sources
        sources = db.query(DataSource).filter(DataSource.enabled == True).all()

        total_signals = 0
        errors = []

        for source in sources:
            try:
                # Create appropriate collector
                if source.source_type == 'rss':
                    collector = RSSCollector(source, db)
                elif source.source_type == 'linkedin':
                    collector = LinkedInCollector(source, db)
                elif source.source_type == 'web':
                    collector = WebCollector(source, db)
                elif source.source_type == 'email':
                    collector = EmailCollector(source, db)
                else:
                    logger.warning(f"Unknown source type: {source.source_type}")
                    continue

                # Collect signals
                signals = await collector.collect()

                # Save signals to database
                for signal_data in signals:
                    signal = create_signal(db, signal_data)
                    total_signals += 1

                logger.info(f"Collected {len(signals)} signals from {source.name}")

            except Exception as e:
                error_msg = f"Error collecting from {source.name}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        # Create notification for curator if pending signals
        pending_count = db.query(Signal).filter(Signal.status == "pending_review").count()
        if pending_count > 0:
            create_notification(
                db,
                type="pending_signals",
                title=f"{pending_count} signals need review",
                message=f"{pending_count} automated signals are pending curator review.",
                link="/admin/signals?status=pending_review"
            )

        logger.info(f"Signal collection complete: {total_signals} signals collected")

        return {
            "success": len(errors) == 0,
            "signals_collected": total_signals,
            "sources_processed": len(sources),
            "errors": errors,
        }

    except Exception as e:
        logger.error(f"Signal collection job failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
        }
    finally:
        db.close()
```

#### Scheduler Registration:

```python
# backend/app/scheduler.py (modify)
def init_scheduler() -> BackgroundScheduler:
    # ... existing code ...

    # Add collection job (daily at 9 AM UTC)
    scheduler.add_job(
        collect_signals_job,
        trigger=CronTrigger(
            hour=9,
            minute=0,
            timezone="UTC",
        ),
        id="signal_collection",
        name="Collect Automated Signals",
        replace_existing=True,
    )

    # ... existing code ...
```

---

### Phase 2A.4: Curator Review UI (Week 2, Days 1-2)

**Goal:** Build curator interface to review pending signals.

#### Files to Modify:
- `backend/app/routes.py` - Add review endpoints
- `backend/app/schemas.py` - Add review schemas
- `frontend/src/pages/AdminSignalReview.tsx` (NEW)
- `frontend/src/App.tsx` - Add review route

#### API Endpoints:

```python
# backend/app/routes.py
@router.get("/signals/pending", response_model=SignalListResponse)
async def get_pending_signals(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    _: str = Depends(verify_curator_token),
):
    """Get signals pending curator review."""
    query = db.query(Signal).filter(
        Signal.status == "pending_review",
        Signal.deleted_at.is_(None)
    )

    total = query.count()
    signals = query.order_by(Signal.created_at.desc()).offset(offset).limit(limit).all()

    return SignalListResponse(signals=signals, total=total, limit=limit, offset=offset)


@router.patch("/signals/{signal_id}/status", response_model=SignalResponse)
async def update_signal_status(
    signal_id: UUID,
    status: str,  # "approved" or "rejected"
    curator_name: str,
    db: Session = Depends(get_db),
    _: str = Depends(verify_curator_token),
):
    """Approve or reject a signal."""
    signal = get_signal(db, signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    signal.status = status
    signal.reviewed_at = datetime.utcnow()
    signal.reviewed_by = curator_name
    db.commit()
    db.refresh(signal)

    return signal
```

#### Frontend Review UI:

```tsx
// frontend/src/pages/AdminSignalReview.tsx
export default function AdminSignalReview() {
  const [pendingSignals, setPendingSignals] = useState<Signal[]>([]);

  useEffect(() => {
    fetchPendingSignals();
  }, []);

  const handleApprove = async (signalId: string) => {
    await updateSignalStatus(signalId, "approved");
    fetchPendingSignals();  // Refresh list
  };

  const handleReject = async (signalId: string) => {
    await updateSignalStatus(signalId, "rejected");
    fetchPendingSignals();
  };

  return (
    <div>
      <h1>Review Automated Signals</h1>
      {pendingSignals.map(signal => (
        <SignalReviewCard
          key={signal.id}
          signal={signal}
          onApprove={() => handleApprove(signal.id)}
          onReject={() => handleReject(signal.id)}
        />
      ))}
    </div>
  );
}
```

---

### Phase 2A.5: Dashboard Notifications (Week 2, Days 3-4)

**Goal:** Show notifications in dashboard for pending signals and alerts.

#### Files to Modify:
- `backend/app/routes.py` - Add notification endpoints
- `frontend/src/components/NotificationBell.tsx` (NEW)
- `frontend/src/pages/Dashboard.tsx` - Add notification bell

#### API Endpoints:

```python
# backend/app/routes.py
@router.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    unread_only: bool = True,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Get notifications."""
    query = db.query(Notification)

    if unread_only:
        query = query.filter(Notification.read == False, Notification.dismissed == False)

    notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
    return notifications


@router.patch("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
):
    """Mark notification as read."""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if notification:
        notification.read = True
        db.commit()
    return {"success": True}
```

#### Frontend Notification Bell:

```tsx
// frontend/src/components/NotificationBell.tsx
export default function NotificationBell() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);

  useEffect(() => {
    fetchNotifications();

    // Poll every 30 seconds
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <div className="relative">
      <button onClick={() => setShowDropdown(!showDropdown)}>
        <Bell className="w-6 h-6" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5">
            {unreadCount}
          </span>
        )}
      </button>

      {showDropdown && (
        <NotificationDropdown
          notifications={notifications}
          onMarkRead={handleMarkRead}
        />
      )}
    </div>
  );
}
```

---

### Phase 2A.6: LinkedIn & Web Scrapers (Week 2, Day 5 - Week 3)

**Goal:** Implement LinkedIn and web scraping collectors (lower priority, more complex).

#### LinkedIn Collector (Optional - fragile due to LinkedIn's anti-scraping):

Use Playwright for headless browser automation. Requires LinkedIn credentials (risk of account ban).

**Recommendation:** Start with RSS + email, defer LinkedIn to Phase 2B based on pilot feedback.

#### Web Collector:

Generic scraper using BeautifulSoup4 + CSS selectors configured per source.

```python
# backend/app/collectors/web_collector.py
class WebCollector(BaseCollector):
    async def collect(self) -> List[Dict]:
        """Scrape website using configured selectors."""
        url = self.data_source.url
        config = self.data_source.config  # { "selectors": {...}, "patterns": {...} }

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                html = await response.text()

        soup = BeautifulSoup(html, 'html.parser')

        # Extract items using CSS selectors from config
        items = soup.select(config['selectors']['item'])

        signals = []
        for item in items:
            title = item.select_one(config['selectors']['title']).text
            link = item.select_one(config['selectors']['link'])['href']

            # Classify and create signal
            classified = self.classify_signal({'title': title, 'link': link})
            if classified:
                signals.append(classified)

        return signals
```

---

### Phase 2A.7: Email Ingestion (Week 3)

**Goal:** Allow curators to forward newsletters to a dedicated email for auto-ingestion.

**Approach:** Use IMAP to poll an email inbox and parse incoming messages.

```python
# backend/app/collectors/email_collector.py
import imaplib
import email
from email.header import decode_header

class EmailCollector(BaseCollector):
    async def collect(self) -> List[Dict]:
        """Poll IMAP inbox and parse emails."""
        imap_server = get_settings().email_imap_server
        username = get_settings().email_username
        password = get_settings().email_password

        signals = []

        # Connect to IMAP server
        with imaplib.IMAP4_SSL(imap_server) as mail:
            mail.login(username, password)
            mail.select('INBOX')

            # Search for unread messages
            _, message_ids = mail.search(None, 'UNSEEN')

            for msg_id in message_ids[0].split():
                _, msg_data = mail.fetch(msg_id, '(RFC822)')
                email_message = email.message_from_bytes(msg_data[0][1])

                # Extract text content
                body = self.extract_email_body(email_message)

                # Classify and create signal
                classified = self.classify_signal({'body': body})
                if classified:
                    signals.append(classified)

                # Mark as read
                mail.store(msg_id, '+FLAGS', '\\Seen')

        return signals
```

**Email Setup:** Create dedicated email (e.g., `intelligence-ingest@yourdomain.com`) and configure IMAP credentials in .env.

---

## Testing Strategy

### Unit Tests

```python
# backend/tests/test_collectors.py
def test_rss_collector():
    """Test RSS feed parsing."""
    collector = RSSCollector(mock_source, mock_db)
    signals = await collector.collect()
    assert len(signals) > 0
    assert signals[0]['confidence'] == 'High'

def test_classification():
    """Test keyword matching."""
    text = "Springer announces new open access policy"
    result = classify_text(text)
    assert result['event_type'] == 'policy'
    assert 'Open Access' in result['topic']
```

### Integration Tests

```python
# backend/tests/test_collection_job.py
def test_collection_job():
    """Test full collection job."""
    result = await collect_signals_job()
    assert result['success'] == True
    assert result['signals_collected'] > 0
```

### Manual Testing

1. Add test RSS feed to database
2. Manually trigger collection job: `POST /admin/collect-signals`
3. Verify signals appear in database with status="approved"
4. Create low-confidence signal, verify it requires review
5. Approve/reject pending signal via UI
6. Verify notification appears in dashboard

---

## Critical Files Summary

### New Files:
- `backend/app/collectors/__init__.py`
- `backend/app/collectors/base.py`
- `backend/app/collectors/rss_collector.py`
- `backend/app/collectors/linkedin_collector.py` (Phase 2A.6)
- `backend/app/collectors/web_collector.py` (Phase 2A.6)
- `backend/app/collectors/email_collector.py` (Phase 2A.7)
- `backend/app/collectors/classification.py`
- `frontend/src/pages/AdminSignalReview.tsx`
- `frontend/src/components/NotificationBell.tsx`

### Modified Files:
- `backend/app/models.py` - Add DataSource, Notification, modify Signal
- `backend/app/schemas.py` - Add new schemas
- `backend/app/services.py` - Add collector services
- `backend/app/jobs.py` - Add collect_signals_job()
- `backend/app/scheduler.py` - Register collection job
- `backend/app/config.py` - Add collector config
- `backend/app/routes.py` - Add review & notification endpoints
- `backend/requirements.txt` - Add dependencies
- `frontend/src/App.tsx` - Add review route
- `frontend/src/pages/Dashboard.tsx` - Add notification bell

---

## Success Metrics

After Phase 2A implementation:

- ✅ Curator time reduced from 5 hrs/week to <2 hrs/week
- ✅ 20+ automated signals collected daily
- ✅ RSS feeds from 5+ sources operational
- ✅ <5% false positive rate (signals requiring rejection)
- ✅ Curator can review and approve/reject pending signals in <10 minutes
- ✅ Dashboard shows notifications for pending signals
- ✅ Weekly brief generation includes automated signals

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| LinkedIn scraping breaks | Start with RSS + email only. Add LinkedIn only if pilot team requests it. |
| False positives (irrelevant signals) | Improve keyword matching based on feedback. Add "report false positive" button. |
| Email parsing fails | Test with common email formats. Provide curator UI to manually fix parsing errors. |
| Collection job takes too long | Run collectors in parallel (asyncio). Add timeout per source (5 min max). |
| Source websites change (scraping breaks) | Monitor error_count in DataSource. Alert curator if source fails 3+ times. |

---

## Next: Phase 2B (Sales Assets)

After Phase 2A is complete and validated:
- Competitor battlecards
- Pitch pack generator

These build on automated signals to create sales collateral.

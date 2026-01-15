"""Backfill embeddings for existing signals."""

import logging
from app.database import SessionLocal
from app.models import Signal
from app.embeddings import get_embeddings_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def backfill_embeddings():
    """Generate embeddings for all signals that don't have them."""
    db = SessionLocal()
    embeddings_service = get_embeddings_service()

    if not embeddings_service.is_available():
        logger.error("Embeddings service not available - OpenAI API key not configured")
        return

    try:
        # Get all signals without embeddings
        signals = db.query(Signal).filter(
            Signal.deleted_at.is_(None),
            Signal.embedding.is_(None)
        ).all()

        logger.info(f"Found {len(signals)} signals without embeddings")

        # Generate embeddings
        success_count = 0
        error_count = 0

        for i, signal in enumerate(signals, 1):
            try:
                embedding = embeddings_service.generate_signal_embedding({
                    'title': '',
                    'content': signal.evidence_snippet,
                    'entity': signal.entity,
                    'topics': signal.topic
                })

                if embedding:
                    signal.embedding = embedding
                    db.commit()
                    success_count += 1
                    logger.info(f"[{i}/{len(signals)}] Generated embedding for signal {signal.id}")
                else:
                    error_count += 1
                    logger.warning(f"[{i}/{len(signals)}] Failed to generate embedding for signal {signal.id}")

            except Exception as e:
                error_count += 1
                logger.error(f"[{i}/{len(signals)}] Error processing signal {signal.id}: {e}")

        logger.info(f"Backfill complete: {success_count} successful, {error_count} errors")

    finally:
        db.close()


if __name__ == "__main__":
    backfill_embeddings()

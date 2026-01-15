"""OpenAI embeddings service for RAG semantic search."""

import logging
from typing import List, Optional
import openai
from openai import OpenAI

from app.config import get_settings

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """Service for generating text embeddings using OpenAI API."""

    def __init__(self):
        """Initialize the embeddings service."""
        settings = get_settings()

        if not settings.openai_api_key:
            logger.warning("OpenAI API key not configured - embeddings will not be generated")
            self.client = None
        else:
            self.client = OpenAI(api_key=settings.openai_api_key)

        # Model configuration
        self.model = "text-embedding-3-small"  # 1536 dimensions, cheap and fast
        self.max_batch_size = 100  # OpenAI limit
        self.max_tokens = 8192  # Model limit

    def is_available(self) -> bool:
        """Check if embeddings service is available (API key configured)."""
        return self.client is not None

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed (will be truncated if too long)

        Returns:
            List of 1536 floats, or None if service unavailable or error
        """
        if not self.is_available():
            return None

        try:
            # Truncate text if needed (rough estimate: 1 token ~= 4 chars)
            max_chars = self.max_tokens * 4
            if len(text) > max_chars:
                text = text[:max_chars]
                logger.debug(f"Truncated text to {max_chars} characters for embedding")

            # Generate embedding
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )

            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding with {len(embedding)} dimensions")

            return embedding

        except openai.RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {e}")
            return None
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error generating embedding: {e}", exc_info=True)
            return None

    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in batches.

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings (same length as texts), None for failed items
        """
        if not self.is_available():
            return [None] * len(texts)

        embeddings = []

        # Process in batches
        for i in range(0, len(texts), self.max_batch_size):
            batch = texts[i:i + self.max_batch_size]

            try:
                # Truncate texts if needed
                truncated_batch = []
                max_chars = self.max_tokens * 4
                for text in batch:
                    if len(text) > max_chars:
                        truncated_batch.append(text[:max_chars])
                    else:
                        truncated_batch.append(text)

                # Generate embeddings for batch
                response = self.client.embeddings.create(
                    model=self.model,
                    input=truncated_batch
                )

                # Extract embeddings (maintain order)
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)

                logger.info(f"Generated {len(batch_embeddings)} embeddings (batch {i//self.max_batch_size + 1})")

            except Exception as e:
                logger.error(f"Error generating embeddings for batch: {e}", exc_info=True)
                # Fill with None for failed batch
                embeddings.extend([None] * len(batch))

        return embeddings

    def generate_signal_embedding(self, signal_dict: dict) -> Optional[List[float]]:
        """
        Generate embedding for a signal.

        Combines title, content, entity, and topic for rich context.

        Args:
            signal_dict: Signal dictionary with keys: title, content, entity, topics

        Returns:
            Embedding vector or None if error
        """
        # Build rich text representation
        parts = []

        if signal_dict.get("title"):
            parts.append(f"Title: {signal_dict['title']}")

        if signal_dict.get("content"):
            parts.append(f"Content: {signal_dict['content']}")

        if signal_dict.get("entity"):
            parts.append(f"Entity: {signal_dict['entity']}")

        if signal_dict.get("topics"):
            topics = signal_dict["topics"]
            if isinstance(topics, list):
                parts.append(f"Topics: {', '.join(topics)}")
            else:
                parts.append(f"Topics: {topics}")

        # Combine all parts
        text = "\n".join(parts)

        return self.generate_embedding(text)


# Global service instance
_embeddings_service = None


def get_embeddings_service() -> EmbeddingsService:
    """Get or create the global embeddings service instance."""
    global _embeddings_service
    if _embeddings_service is None:
        _embeddings_service = EmbeddingsService()
    return _embeddings_service

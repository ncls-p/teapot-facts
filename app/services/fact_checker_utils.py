import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def contains_refusal_phrases(text: str) -> bool:
    """Check if the response indicates a refusal to answer due to insufficient context"""
    refusal_phrases = [
        "cannot answer",
        "don't have enough information",
        "insufficient context",
        "cannot be determined",
        "not enough information",
        "cannot be verified",
        "I don't know",
        "No information provided",
    ]

    return any(phrase.lower() in text.lower() for phrase in refusal_phrases)


def estimate_confidence(text: str, has_context: bool = True) -> float:
    """
    Simple heuristic to estimate confidence in the answer
    Low confidence if it contains uncertainty markers or lacks context
    """
    uncertainty_markers = [
        "possibly",
        "perhaps",
        "maybe",
        "might",
        "could be",
        "appears to be",
        "seems",
        "likely",
    ]

    markers_count = sum(
        1 for marker in uncertainty_markers if marker.lower() in text.lower()
    )

    base_confidence = 0.9 if has_context else 0.3

    confidence = max(0.1, base_confidence - (0.1 * markers_count))

    if contains_refusal_phrases(text):
        confidence = 0.1

    return confidence


def create_error_response(error_message: str) -> Dict[str, Any]:
    """Create a standardized error response"""
    return {
        "error": error_message,
        "factual": False,
        "answer": error_message,
        "confidence": 0.0,
        "sources": [],
    }


def process_sources(
    stored_documents: List[Dict[str, Any]], model
) -> List[Dict[str, Any]]:
    """Get sources from the RAG model if available"""
    sources = []
    logger.debug("Retrieving sources")

    if stored_documents:
        logger.debug(f"Using {len(stored_documents)} stored documents as sources")
        for doc in stored_documents:
            content = doc.get("content", "")
            sources.append(
                {
                    "text": content[:200] + "..." if len(content) > 200 else content,
                    "metadata": doc.get("metadata", {}),
                }
            )

    if not sources:
        logger.debug("No stored documents, attempting to retrieve from model")
        try:
            if hasattr(model, "documents") and model.documents:
                model_docs = model.documents
                logger.debug(
                    f"Found {len(model_docs) if model_docs else 0} documents in model"
                )
                for doc in model_docs:
                    if isinstance(doc, str):
                        sources.append(
                            {
                                "text": doc[:200] + "..." if len(doc) > 200 else doc,
                                "metadata": {},
                            }
                        )
                    elif hasattr(doc, "content"):
                        content = doc.content
                        metadata = (
                            getattr(doc, "metadata", {})
                            if hasattr(doc, "metadata")
                            else {}
                        )
                        sources.append(
                            {
                                "text": content[:200] + "..."
                                if len(content) > 200
                                else content,
                                "metadata": metadata,
                            }
                        )
                    elif isinstance(doc, dict):
                        content = doc.get("content", str(doc))
                        sources.append(
                            {
                                "text": content[:200] + "..."
                                if len(content) > 200
                                else content,
                                "metadata": doc.get("metadata", {}),
                            }
                        )
                    else:
                        text = str(doc)
                        sources.append(
                            {
                                "text": text[:200] + "..." if len(text) > 200 else text,
                                "metadata": {},
                            }
                        )
        except AttributeError as e:
            logger.debug(f"AttributeError when retrieving sources: {e}")
        except TypeError as e:
            logger.debug(f"TypeError when retrieving sources: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error retrieving sources: {e}")

    logger.debug(f"Retrieved {len(sources)} sources")
    return sources

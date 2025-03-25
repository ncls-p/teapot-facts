import logging
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, cast

from pydantic import BaseModel
from teapotai import TeapotAI

from .fact_checker_utils import (
    contains_refusal_phrases,
    create_error_response,
    estimate_confidence,
    process_sources,
)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class TeapotFactChecker:
    """
    Fact checker using TeapotLLM model which is designed to be hallucination-resistant

    TeapotLLM is an open-source small language model (~800 million parameters)
    fine-tuned on synthetic data and optimized for hallucination-resistant QnA,
    Retrieval-Augmented Generation (RAG), and information extraction.
    """

    def __init__(self, log_level=logging.INFO):
        """
        Initialize the TeapotAI model

        Args:
            log_level: The logging level to use
        """
        logger.setLevel(log_level)
        logger.info("Initializing TeapotFactChecker")
        try:
            self.model = TeapotAI()
            logger.debug("TeapotAI model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize TeapotAI model: {e}")
            raise RuntimeError(f"Failed to initialize TeapotAI model: {str(e)}")

        self.stored_documents = []

    def check_fact(
        self,
        query: str,
        context: Optional[str] = None,
        documents: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Check if a statement is factual based on provided context

        Args:
            query: The statement or question to verify
            context: Optional text context to use for verification
            documents: Optional list of documents for RAG-based verification

        Returns:
            Dictionary with verification results
        """
        logger.info(f"Checking fact: {query[:50]}{'...' if len(query) > 50 else ''}")

        if not query:
            logger.warning("Empty query provided to check_fact")
            return create_error_response("Query cannot be empty")

        try:
            if documents:
                return self._process_with_documents(query, documents)

            elif context:
                return self._process_with_context(query, context)

            else:
                return self._process_without_context(query)

        except ConnectionError as e:
            logger.error(f"Connection error while checking fact: {e}")
            return create_error_response(f"Connection error: {str(e)}")
        except TimeoutError as e:
            logger.error(f"Timeout error while checking fact: {e}")
            return create_error_response(f"Request timed out: {str(e)}")
        except ValueError as e:
            logger.error(f"Value error in check_fact: {e}")
            return create_error_response(f"Invalid input: {str(e)}")
        except Exception as e:
            logger.exception(f"Unexpected error in check_fact: {e}")
            return create_error_response(
                f"Error occurred during fact checking: {str(e)}"
            )

    def _process_with_documents(
        self, query: str, documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process a query using RAG with provided documents"""
        logger.debug(f"Processing {len(documents)} documents")

        self.stored_documents = []
        for doc in documents:
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            self.stored_documents.append({"content": content, "metadata": metadata})

        combined_context = "\n\n".join(
            [
                doc.get("content", "")
                for doc in self.stored_documents
                if doc.get("content")
            ]
        )

        if not combined_context:
            logger.warning("Documents provided but no content extracted")
            return self._process_without_context(query)

        result = self.model.query(query=query, context=combined_context)

        return self._process_result(result, has_context=True)

    def _process_with_context(self, query: str, context: str) -> Dict[str, Any]:
        """Process a query with provided context"""
        logger.debug("Using provided context for query")

        result = self.model.query(query=query, context=context)

        return self._process_result(result, has_context=True)

    def _process_without_context(self, query: str) -> Dict[str, Any]:
        """Process a query without context (likely to get hallucination resistance)"""
        logger.debug("Using query without additional context")

        result = self.model.query(query=query)

        return self._process_result(result, has_context=False)

    def _process_result(self, result: str, has_context: bool = True) -> Dict[str, Any]:
        """Process the result from TeapotAI model"""
        is_factual = not contains_refusal_phrases(result)
        confidence = estimate_confidence(result, has_context)
        sources = process_sources(self.stored_documents, self.model)

        logger.info(
            f"Fact check complete. Factual: {is_factual}, Confidence: {confidence:.2f}"
        )

        return {
            "factual": is_factual,
            "answer": result,
            "confidence": confidence,
            "sources": sources,
        }

    def extract_information(
        self,
        model_class: Type[T],
        query: Optional[str] = None,
        context: Optional[str] = None,
        documents: Optional[List[Dict[str, Any]]] = None,
    ) -> Union[T, Dict[str, Any]]:
        """
        Extract structured information based on a Pydantic model

        Args:
            model_class: Pydantic model class defining the structure to extract
            query: Optional query to focus the extraction (if needed)
            context: Text to extract information from
            documents: Optional list of documents to extract from

        Returns:
            Instance of the provided model_class with extracted information,
            or error response dictionary if extraction fails
        """
        logger.info(f"Extracting information using {model_class.__name__} model")

        try:
            if documents and not context:
                logger.debug(f"Building context from {len(documents)} documents")
                self.stored_documents = documents
                context = "\n\n".join(
                    [
                        doc.get("content", "")
                        for doc in documents
                        if doc.get("content", "")
                    ]
                )

            if not context:
                logger.warning("No context provided for extraction")
                return create_error_response(
                    "Context is required for information extraction"
                )

            # Create a model instance for extraction
            model_instance = model_class()

            if query:
                logger.debug(f"Extracting with query: {query}")
                # Cast the return value to the appropriate type
                extracted_data = cast(
                    T, self.model.extract(model_instance, context=context, query=query)
                )
            else:
                extracted_data = cast(
                    T, self.model.extract(model_instance, context=context)
                )

            logger.info(f"Successfully extracted {model_class.__name__}")
            return extracted_data

        except Exception as e:
            logger.exception(f"Error during information extraction: {e}")
            return create_error_response(f"Extraction failed: {str(e)}")

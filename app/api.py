import time
from typing import Any, Dict, List, Optional, Tuple, Union

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .fact_checker import TeapotFactChecker

# Initialize the FastAPI app
app = FastAPI(
    title="Teapot Facts API",
    description="OpenAI-compatible API for fact-checking using TeapotLLM",
    version="1.0.0",
)

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize our fact checker
fact_checker = TeapotFactChecker()

# Define the OpenAI-compatible data models


class Message(BaseModel):
    role: str
    content: str
    name: Optional[str] = None


class CompletionRequest(BaseModel):
    model: str
    prompt: Union[str, List[str]]
    max_tokens: Optional[int] = 256
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    logprobs: Optional[int] = None


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    max_tokens: Optional[int] = 256
    stop: Optional[Union[str, List[str]]] = None
    stream: Optional[bool] = False


class CompletionUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class FactCheckRequest(BaseModel):
    query: str
    context: Optional[str] = None
    documents: Optional[List[Dict[str, Any]]] = None


class FactCheckResponse(BaseModel):
    factual: bool
    answer: str
    confidence: float
    sources: List[Dict[str, Any]] = Field(default_factory=list)


class ExtractionFieldDefinition(BaseModel):
    name: str
    description: Optional[str] = None
    type: str  # Could be "string", "number", "integer", "boolean", etc.


class ExtractionRequest(BaseModel):
    query: Optional[str] = None
    context: Optional[str] = None
    documents: Optional[List[Dict[str, Any]]] = None
    fields: List[ExtractionFieldDefinition]


class ExtractionResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# Helper functions


def _estimate_token_count(text: str) -> int:
    """Rough approximation of token count"""
    return len(text) // 4


def _extract_context_from_messages(messages: List[Message]) -> Tuple[str, str]:
    """Extract the user query and context from messages"""
    system_message = ""
    context = ""
    query = ""

    for message in messages:
        if message.role == "system":
            system_message = message.content
        elif message.role == "user":
            # Assume the latest user message is the query
            query = message.content
        elif message.role == "assistant" and not query:
            # If there are assistant messages before the user's last message,
            # include them as context
            context += f"Assistant: {message.content}\n"

    # Check if the system message contains context markers
    if "context:" in system_message.lower():
        context_parts = system_message.split("context:", 1)
        if len(context_parts) > 1:
            context = context_parts[1].strip() + "\n" + context

    return query, context


# API Routes


@app.post("/v1/completions")
async def completions(request: CompletionRequest):
    """OpenAI-compatible completion endpoint"""

    # Handle single prompt or list of prompts
    prompt = request.prompt
    if isinstance(prompt, list):
        prompt = prompt[0]  # Just use the first prompt for simplicity

    # Process with fact checker
    result = fact_checker.check_fact(prompt)

    # Format response like OpenAI API
    response = {
        "id": f"cmpl-{int(time.time())}",
        "object": "text_completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [
            {
                "text": result["answer"],
                "index": 0,
                "logprobs": None,
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": _estimate_token_count(prompt),
            "completion_tokens": _estimate_token_count(result["answer"]),
            "total_tokens": _estimate_token_count(prompt)
            + _estimate_token_count(result["answer"]),
        },
        # Custom fields for fact checking
        "fact_check": {
            "factual": result["factual"],
            "confidence": result["confidence"],
            "sources": result["sources"],
        },
    }

    return response


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """OpenAI-compatible chat completion endpoint"""

    # Extract the query and context from messages
    query, context = _extract_context_from_messages(request.messages)

    if not query:
        raise HTTPException(status_code=400, detail="No user query found in messages")

    # Process with fact checker
    result = fact_checker.check_fact(query, context=context if context else None)

    # Calculate token counts for usage info
    prompt_tokens = sum(_estimate_token_count(msg.content) for msg in request.messages)
    completion_tokens = _estimate_token_count(result["answer"])

    # Format response like OpenAI API
    response = {
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": result["answer"]},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
        # Custom fields for fact checking
        "fact_check": {
            "factual": result["factual"],
            "confidence": result["confidence"],
            "sources": result["sources"],
        },
    }

    return response


@app.post("/fact-check", response_model=FactCheckResponse)
async def fact_check(request: FactCheckRequest):
    """Direct fact-checking endpoint (non-OpenAI compatible)"""
    result = fact_checker.check_fact(
        query=request.query, context=request.context, documents=request.documents
    )
    return result


@app.post("/extract", response_model=ExtractionResponse)
async def extract_information(request: ExtractionRequest):
    """
    Extract structured information from provided context using TeapotLLM's information extraction capability

    This endpoint uses TeapotLLM's ability to extract structured data from text following
    a defined schema (in this case, provided in the request as field definitions).
    """
    try:
        # Dynamically create a Pydantic model from the field definitions
        field_annotations = {}
        field_descriptions = {}

        for field in request.fields:
            # Map types from request to Python types
            type_mapping = {
                "string": str,
                "number": float,
                "integer": int,
                "boolean": bool,
                # Add more type mappings as needed
            }

            # Get the appropriate Python type
            python_type = type_mapping.get(field.type.lower(), str)
            field_annotations[field.name] = python_type

            if field.description:
                field_descriptions[field.name] = field.description

        # Create a dynamic model class
        dynamic_model = type(
            "DynamicExtractionModel",
            (BaseModel,),
            {
                "__annotations__": field_annotations,
                # Add field descriptions as metadata if available
                **{
                    name: (type_, Field(description=desc))
                    for name, type_ in field_annotations.items()
                    if (desc := field_descriptions.get(name))
                },
            },
        )

        # Extract information using the dynamically created model
        extraction_result = fact_checker.extract_information(
            model_class=dynamic_model,
            query=request.query,
            context=request.context,
            documents=request.documents,
        )

        # Check if we got an error response (dictionary with error key)
        if isinstance(extraction_result, dict) and "error" in extraction_result:
            return ExtractionResponse(success=False, error=extraction_result["error"])

        # Convert result to dictionary, regardless of type
        try:
            # For Pydantic models (both v1 and v2)
            if isinstance(extraction_result, BaseModel):
                # Try Pydantic v2 method first
                if hasattr(extraction_result, "model_dump"):
                    data_dict = extraction_result.model_dump()
                # Fall back to Pydantic v1 method
                elif hasattr(extraction_result, "dict"):
                    data_dict = extraction_result.dict()
                else:
                    # If somehow it's a BaseModel with neither method (unlikely)
                    data_dict = {
                        key: getattr(extraction_result, key)
                        for key in extraction_result.__fields__
                    }
            # Handle dictionary case directly
            elif isinstance(extraction_result, dict):
                data_dict = extraction_result
            # Handle any other case
            else:
                data_dict = {"result": str(extraction_result)}

            return ExtractionResponse(success=True, data=data_dict)

        except Exception as e:
            # If any conversion error occurs
            return ExtractionResponse(
                success=True, data={"result": str(extraction_result), "error": str(e)}
            )

    except Exception as e:
        return ExtractionResponse(success=False, error=f"Extraction failed: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "model": "teapotllm"}

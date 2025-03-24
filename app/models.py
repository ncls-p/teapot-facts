from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


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
    type: str


class ExtractionRequest(BaseModel):
    query: Optional[str] = None
    context: Optional[str] = None
    documents: Optional[List[Dict[str, Any]]] = None
    fields: List[ExtractionFieldDefinition]


class ExtractionResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class Model(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str
    permission: List[Dict[str, Any]] = []
    root: str
    parent: Optional[str] = None

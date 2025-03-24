import time
from typing import List

from fastapi import APIRouter, HTTPException

from ..models import ChatCompletionRequest, CompletionRequest
from ..services.fact_checker import TeapotFactChecker
from ..utils import estimate_token_count, extract_context_from_messages

router = APIRouter()
fact_checker = TeapotFactChecker()


@router.post("/completions")
async def completions(request: CompletionRequest):
    """OpenAI-compatible completion endpoint"""
    prompt = request.prompt
    if isinstance(prompt, List):
        prompt = prompt[0]

    result = fact_checker.check_fact(prompt)

    return {
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
            "prompt_tokens": estimate_token_count(prompt),
            "completion_tokens": estimate_token_count(result["answer"]),
            "total_tokens": estimate_token_count(prompt)
            + estimate_token_count(result["answer"]),
        },
        "fact_check": {
            "factual": result["factual"],
            "confidence": result["confidence"],
            "sources": result["sources"],
        },
    }


@router.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """OpenAI-compatible chat completion endpoint"""
    query, context = extract_context_from_messages(request.messages)

    if not query:
        raise HTTPException(status_code=400, detail="No user query found in messages")

    result = fact_checker.check_fact(query, context=context if context else None)

    prompt_tokens = sum(estimate_token_count(msg.content) for msg in request.messages)
    completion_tokens = estimate_token_count(result["answer"])

    return {
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
        "fact_check": {
            "factual": result["factual"],
            "confidence": result["confidence"],
            "sources": result["sources"],
        },
    }

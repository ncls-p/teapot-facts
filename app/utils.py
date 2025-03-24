from typing import List, Tuple

from .models import Message


def estimate_token_count(text: str) -> int:
    """Rough approximation of token count"""
    return len(text) // 4


def extract_context_from_messages(messages: List[Message]) -> Tuple[str, str]:
    """Extract the user query and context from messages"""
    system_message = ""
    context = ""
    query = ""

    for message in messages:
        if message.role == "system":
            system_message = message.content
        elif message.role == "user":
            query = message.content
        elif message.role == "assistant" and not query:
            context += f"Assistant: {message.content}\n"

    if "context:" in system_message.lower():
        context_parts = system_message.split("context:", 1)
        if len(context_parts) > 1:
            context = context_parts[1].strip() + "\n" + context

    return query, context

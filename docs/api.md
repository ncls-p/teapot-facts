# TeapotFacts API Documentation

## Overview

TeapotFacts API is a fact-checking service that provides both OpenAI-compatible endpoints and direct fact-checking capabilities. The service uses TeapotLLM, an 800M parameter language model fine-tuned for hallucination-resistant question answering and information extraction.

## Authentication

Currently, the API does not require authentication. All endpoints are publicly accessible.

## Base URL

By default, the API runs on `http://localhost:8000`. You can configure the port using the `PORT` environment variable.

## Common Response Structure

All API responses follow a consistent structure:

- Successful responses include the requested data
- Error responses include:
  - HTTP status code
  - Error message
  - Optional additional details

## Available Endpoints

### OpenAI-Compatible Endpoints

#### 1. Text Completion (`POST /v1/completions`)

Generate text completions with fact-checking.

**Request:**

```json
{
  "model": "teapotllm",
  "prompt": "What is the capital of France?",
  "max_tokens": 50,
  "temperature": 0.7,
  "top_p": 1.0,
  "n": 1,
  "stream": false
}
```

**Response:**

```json
{
  "id": "cmpl-123",
  "object": "text_completion",
  "created": 1709645321,
  "model": "teapotllm",
  "choices": [
    {
      "text": "Paris is the capital of France.",
      "index": 0,
      "logprobs": null,
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 7,
    "completion_tokens": 7,
    "total_tokens": 14
  },
  "fact_check": {
    "factual": true,
    "confidence": 0.9,
    "sources": []
  }
}
```

#### 2. Chat Completion (`POST /v1/chat/completions`)

Generate chat completions with fact-checking.

**Request:**

```json
{
  "model": "teapotllm",
  "messages": [
    {
      "role": "system",
      "content": "Context: Paris is the capital of France."
    },
    {
      "role": "user",
      "content": "What is the capital of France?"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 50
}
```

**Response:**

```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1709645321,
  "model": "teapotllm",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Paris is the capital of France."
      },
      "finish_reason": "stop"
    }
  ],
  "fact_check": {
    "factual": true,
    "confidence": 0.9,
    "sources": []
  }
}
```

#### 3. Models (`GET /v1/models`, `GET /v1/models/{model_id}`)

List available models and get model details.

**Response:**

```json
{
  "object": "list",
  "data": [
    {
      "id": "teapot-llm",
      "object": "model",
      "created": 1709645321,
      "owned_by": "teapot-org",
      "permission": [],
      "root": "teapot-llm",
      "parent": null
    }
  ]
}
```

### TeapotFacts-Specific Endpoints

#### 1. Fact Check (`POST /fact-check`)

Direct fact-checking with optional context.

**Request:**

```json
{
  "query": "How tall is the Eiffel Tower?",
  "context": "The Eiffel Tower is 330 meters tall and located in Paris, France.",
  "documents": null
}
```

**Response:**

```json
{
  "factual": true,
  "answer": "The Eiffel Tower is 330 meters tall.",
  "confidence": 0.9,
  "sources": [
    {
      "text": "The Eiffel Tower is 330 meters tall and located in Paris, France.",
      "metadata": {}
    }
  ]
}
```

#### 2. Information Extraction (`POST /extract`)

Extract structured information from text.

**Request:**

```json
{
  "query": "Extract information about Paris",
  "context": "Paris is the capital of France and has a population of 2.2 million people.",
  "fields": [
    {
      "name": "city",
      "description": "The name of the city",
      "type": "string"
    },
    {
      "name": "country",
      "description": "The country where the city is located",
      "type": "string"
    },
    {
      "name": "population",
      "description": "The population of the city in millions",
      "type": "number"
    }
  ]
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "city": "Paris",
    "country": "France",
    "population": 2.2
  }
}
```

#### 3. Health Check (`GET /health`)

Check API health status.

**Response:**

```json
{
  "status": "ok",
  "model": "teapotllm"
}
```

## Error Handling

The API uses standard HTTP status codes:

- 200: Success
- 400: Bad Request (invalid input)
- 404: Not Found
- 500: Internal Server Error

Error responses include a message explaining the error:

```json
{
  "error": {
    "message": "Invalid request: query cannot be empty",
    "type": "invalid_request_error"
  }
}
```

## Rate Limiting

Currently, there are no rate limits implemented.

## Confidence Scores

The fact-checking system provides confidence scores (0.0-1.0) based on:

- Context availability (0.9 with context, 0.3 without)
- Uncertainty markers (each marker reduces confidence by 0.1)
- Refusal phrases (sets confidence to 0.1)

## RAG Support

The API supports Retrieval-Augmented Generation (RAG) through:

1. Document input in requests
2. Automatic context building from documents
3. Source tracking in responses

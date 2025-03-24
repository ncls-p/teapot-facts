# TeapotFacts API

A fact-checking API service with OpenAI-compatible endpoints. This service provides fact verification capabilities through both standard and chat-based interfaces.

## Features

- OpenAI-compatible completion endpoint (`/v1/completions`)
- OpenAI-compatible chat completion endpoint (`/v1/chat/completions`)
- Direct fact-checking endpoint (`/fact-check`)
- Health check endpoint (`/health`)
- Automatic fact verification for responses

## Getting Started

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:

```bash
git clone [repository-url]
cd teapot-facts
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

### Running the Server

You can start the server using:

```bash
python server.py
```

By default, the server runs on port 8000. You can configure the port using the `PORT` environment variable:

```bash
PORT=3000 python server.py
```

The server will start with auto-reload enabled for development.

## API Endpoints

### Health Check

```
GET /health
```

Returns the service status and model information.

### Completion API

```
POST /v1/completions
```

OpenAI-compatible completion endpoint.

Example request:

```json
{
  "model": "teapotllm",
  "prompt": "What is the capital of France?",
  "max_tokens": 50
}
```

### Chat Completion API

```
POST /v1/chat/completions
```

OpenAI-compatible chat completion endpoint.

Example request:

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
  ]
}
```

### Fact Check API

```
POST /fact-check
```

Direct fact-checking endpoint.

Example request:

```json
{
  "query": "How tall is the Eiffel Tower?",
  "context": "The Eiffel Tower is 330 meters tall and located in Paris, France."
}
```

### Testing the API

Once the server is running, you can test it using curl:

```bash
# Test the health endpoint
curl http://localhost:8000/health

# Test the fact-check endpoint
curl -X POST http://localhost:8000/fact-check \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How tall is the Eiffel Tower?",
    "context": "The Eiffel Tower is 330 meters tall and located in Paris, France."
  }'

# Test the chat completion endpoint
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "teapotllm",
    "messages": [
      {
        "role": "user",
        "content": "What is the capital of France?"
      }
    ]
  }'
```

## Testing

Run the test suite using pytest:

```bash
pytest
```

The test suite includes coverage for all API endpoints and the fact-checking functionality.

## Development

The project structure is organized as follows:

```
teapot-facts/
├── app/
│   ├── __init__.py
│   ├── api.py          # FastAPI application and routes
│   └── fact_checker.py # Fact checking implementation
├── tests/
│   ├── test_api.py
│   └── test_fact_checker.py
├── server.py           # Server startup script
└── requirements.txt    # Project dependencies
```

# TeapotFacts API

A fact-checking API service with OpenAI-compatible endpoints. This service provides fact verification capabilities through both standard and chat-based interfaces.

## Features

- OpenAI-compatible completion endpoint (`/v1/completions`)
- OpenAI-compatible chat completion endpoint (`/v1/chat/completions`)
- OpenAI-compatible models endpoints (`/v1/models`, `/v1/models/{model_id}`)
- Direct fact-checking endpoint (`/fact-check`)
- Information extraction endpoint (`/extract`)
- Health check endpoint (`/health`)
- Automatic fact verification for responses
- Support for RAG (Retrieval-Augmented Generation)

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

### Information Extraction API

```
POST /extract
```

Extract structured information from text.

Example request:

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

### Models API

```
GET /v1/models
GET /v1/models/{model_id}
```

OpenAI-compatible endpoints for listing available models and getting model details.

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

# Test the extraction endpoint
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{
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
│   ├── api.py              # FastAPI application setup
│   ├── models.py           # Pydantic data models
│   ├── utils.py            # Helper functions
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── completions.py  # OpenAI-compatible endpoints
│   │   ├── fact_check.py   # Fact-checking endpoints
│   │   ├── health.py       # Health check endpoint
│   │   └── models.py       # Model information endpoints
│   └── services/
│       └── fact_checker.py # Fact checking implementation
├── tests/
│   ├── test_api.py
│   └── test_fact_checker.py
├── server.py               # Server startup script
└── requirements.txt        # Project dependencies
```

### Project Components

- **Models (`app/models.py`)**: Contains all Pydantic data models used for request/response validation
- **Routes (`app/routes/`)**: API endpoint implementations split by functionality
- **Services (`app/services/`)**: Core business logic implementation
- **Utils (`app/utils.py`)**: Shared utility functions
- **Tests (`tests/`)**: Comprehensive test suite for all components

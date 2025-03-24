# TeapotFacts Architecture

## Overview

TeapotFacts is built using a modular architecture with FastAPI, following clean code principles and separation of concerns. The application is structured into distinct layers, each with a specific responsibility.

## Project Structure

```
teapot-facts/
├── app/
│   ├── __init__.py
│   ├── api.py              # FastAPI application setup
│   ├── models.py           # Data models and schemas
│   ├── utils.py            # Helper functions
│   ├── routes/             # API endpoints by feature
│   │   ├── __init__.py    # Router configuration
│   │   ├── completions.py  # OpenAI-compatible endpoints
│   │   ├── fact_check.py   # Fact-checking endpoints
│   │   ├── health.py       # Health check endpoint
│   │   └── models.py       # Model information endpoints
│   └── services/
│       └── fact_checker.py # Core fact checking logic
├── docs/                   # Documentation
├── tests/                  # Test suite
└── server.py              # Application entry point
```

## Architectural Layers

### 1. Entry Point (server.py)

- Application initialization
- Configuration loading
- Server startup with uvicorn

### 2. API Layer (app/api.py)

- FastAPI application configuration
- CORS middleware setup
- Route registration
- Global error handling

### 3. Routes Layer (app/routes/\*)

Each route module is dedicated to a specific feature set:

- **completions.py**: OpenAI-compatible completion endpoints
- **fact_check.py**: Direct fact-checking and extraction endpoints
- **health.py**: Health monitoring
- **models.py**: Model information endpoints

### 4. Models Layer (app/models.py)

Pydantic models for:

- Request/response validation
- Data structure definitions
- OpenAI-compatible schemas
- Custom endpoint schemas

### 5. Services Layer (app/services/)

Core business logic implementation:

- Fact checking
- Information extraction
- RAG functionality
- Confidence scoring

### 6. Utils Layer (app/utils.py)

Shared utility functions:

- Token counting
- Context extraction
- Message processing

## Key Components

### FastAPI Application

- Asynchronous request handling
- Automatic OpenAPI documentation
- Input validation via Pydantic
- Dependency injection

### TeapotLLM Integration

- 800M parameter language model
- Hallucination resistance
- RAG capabilities
- Information extraction

### Fact Checking System

Components:

1. Query Processing

   - Context extraction
   - Document handling
   - Query validation

2. RAG System

   - Document storage
   - Context building
   - Source tracking

3. Confidence Scoring

   - Context-based scoring
   - Uncertainty detection
   - Refusal recognition

4. Response Generation
   - Answer formatting
   - Source attribution
   - Confidence calculation

## Data Flow

1. **Request Reception**

   - FastAPI receives HTTP request
   - Request body validated against Pydantic models
   - Route handler processes request

2. **Business Logic**

   - Service layer processes request
   - Fact checking or extraction performed
   - Results validated and formatted

3. **Response Generation**
   - Response data structured
   - Additional metadata added
   - Response validated and sent

## Error Handling

Implemented at multiple levels:

1. **Route Level**

   - Input validation
   - HTTP error responses
   - Request format validation

2. **Service Level**

   - Business logic errors
   - Model interaction errors
   - Data processing errors

3. **Global Level**
   - Unhandled exceptions
   - Server errors
   - Timeout handling

## Testing Strategy

1. **Unit Tests**

   - Service layer testing
   - Utility function testing
   - Model validation testing

2. **Integration Tests**

   - API endpoint testing
   - Request/response flow testing
   - Error handling testing

3. **Component Tests**
   - Fact checker testing
   - Extraction system testing
   - RAG system testing

## Future Considerations

1. **Scalability**

   - Load balancing
   - Caching layer
   - Distributed processing

2. **Security**

   - Authentication
   - Rate limiting
   - Request validation

3. **Monitoring**
   - Performance metrics
   - Error tracking
   - Usage analytics

# TeapotFacts Development Guide

## Development Environment Setup

### Prerequisites

1. Python Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. Environment Variables

```bash
PORT=8000  # Optional, defaults to 8000
```

### Development Server

Run the development server with auto-reload:

```bash
python server.py
```

## Project Workflow

### Adding New Features

1. **Plan Your Changes**

   - Determine which layer needs modification
   - Review existing patterns
   - Consider test coverage

2. **Implementation Steps**

   1. Add data models in `app/models.py`
   2. Implement business logic in `app/services/`
   3. Create route handlers in `app/routes/`
   4. Add tests in `tests/`

3. **Testing**
   ```bash
   pytest  # Run all tests
   pytest tests/test_api.py  # Run specific test file
   pytest -k "test_fact_check"  # Run tests matching pattern
   ```

### Code Organization

#### 1. Routes

New endpoints should:

- Be grouped by feature
- Use appropriate HTTP methods
- Include OpenAPI documentation
- Validate inputs with Pydantic

Example:

```python
from fastapi import APIRouter, HTTPException
from ..models import NewFeatureRequest, NewFeatureResponse

router = APIRouter()

@router.post("/new-feature", response_model=NewFeatureResponse)
async def new_feature(request: NewFeatureRequest):
    """
    Endpoint documentation here.
    """
    try:
        # Implementation
        pass
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

#### 2. Models

Data models should:

- Use type hints
- Include field descriptions
- Set appropriate defaults
- Use validation when needed

Example:

```python
from pydantic import BaseModel, Field
from typing import Optional

class NewFeatureRequest(BaseModel):
    field: str = Field(..., description="Field description")
    optional_field: Optional[int] = Field(None, ge=0)
```

#### 3. Services

Business logic should:

- Be isolated from routes
- Handle errors gracefully
- Include logging
- Be well-documented

Example:

```python
import logging
logger = logging.getLogger(__name__)

class NewService:
    def __init__(self):
        logger.info("Initializing NewService")

    def process(self, data):
        try:
            # Implementation
            pass
        except Exception as e:
            logger.error(f"Error in processing: {e}")
            raise
```

### Testing Guidelines

#### 1. Unit Tests

- Test individual components
- Mock external dependencies
- Cover edge cases
- Include error scenarios

Example:

```python
def test_new_feature():
    service = NewService()
    result = service.process({"test": "data"})
    assert result.success is True
```

#### 2. Integration Tests

- Test component interactions
- Use test client for HTTP requests
- Verify response formats
- Check error handling

Example:

```python
def test_new_feature_api(client):
    response = client.post(
        "/new-feature",
        json={"test": "data"}
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
```

### Error Handling

1. **Route Level**

```python
from fastapi import HTTPException

@router.post("/endpoint")
async def handler():
    try:
        result = service.process()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

2. **Service Level**

```python
def process_data(self, data):
    if not self._validate(data):
        raise ValueError("Invalid data format")
    try:
        return self._process(data)
    except Exception as e:
        logger.error(f"Processing error: {e}")
        raise
```

### Logging

Use the logging system consistently:

```python
import logging
logger = logging.getLogger(__name__)

logger.debug("Detailed information")
logger.info("General information")
logger.warning("Warning messages")
logger.error("Error messages")
logger.critical("Critical errors")
```

### Documentation

1. **Code Documentation**

   - Use docstrings
   - Include type hints
   - Document exceptions
   - Add usage examples

2. **API Documentation**
   - Update OpenAPI descriptions
   - Include request/response examples
   - Document error responses
   - Update README.md

### Best Practices

1. **Code Style**

   - Follow PEP 8
   - Use meaningful names
   - Keep functions focused
   - Comment complex logic

2. **Performance**

   - Use async where appropriate
   - Avoid N+1 queries
   - Consider caching
   - Profile when needed

3. **Security**

   - Validate all inputs
   - Sanitize outputs
   - Handle sensitive data carefully
   - Use CORS appropriately

4. **Maintainability**
   - Keep modules small
   - Follow DRY principle
   - Write tests
   - Document changes

## Common Tasks

### Adding a New Endpoint

1. Create route handler:

```python
# app/routes/feature.py
from fastapi import APIRouter
router = APIRouter()

@router.post("/feature")
async def handle_feature():
    pass
```

2. Register in router:

```python
# app/routes/__init__.py
from .feature import router as feature_router
router.include_router(feature_router, tags=["feature"])
```

### Adding a New Model

```python
# app/models.py
from pydantic import BaseModel

class NewModel(BaseModel):
    field: str
```

### Adding a New Service

```python
# app/services/new_service.py
class NewService:
    def __init__(self):
        pass

    def process(self):
        pass
```

### Adding Tests

```python
# tests/test_feature.py
import pytest

def test_feature():
    pass
```

## Troubleshooting

### Common Issues

1. **Import Errors**

   - Check Python path
   - Verify virtual environment
   - Check file structure

2. **Runtime Errors**

   - Check logs
   - Verify input data
   - Test error handling

3. **Test Failures**
   - Isolate failing tests
   - Check test environment
   - Verify test data

### Debugging

1. Use logging:

```python
logger.debug(f"Processing data: {data}")
```

2. Use pytest debugging:

```bash
pytest -vv --pdb
```

3. Use FastAPI debug tools:

```python
from fastapi import Request

@router.post("/debug")
async def debug(request: Request):
    print(await request.json())
```

import time

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/models")
async def list_models():
    """OpenAI-compatible models endpoint"""
    current_time = int(time.time())
    return {
        "object": "list",
        "data": [
            {
                "id": "teapot-llm",
                "object": "model",
                "created": current_time,
                "owned_by": "teapot-org",
                "permission": [],
                "root": "teapot-llm",
                "parent": None,
            }
        ],
    }


@router.get("/models/{model_id}")
async def get_model(model_id: str):
    """OpenAI-compatible get model endpoint"""
    if model_id != "teapot-llm":
        raise HTTPException(status_code=404, detail="Model not found")

    current_time = int(time.time())
    return {
        "id": "teapot-llm",
        "object": "model",
        "created": current_time,
        "owned_by": "teapot-org",
        "permission": [],
        "root": "teapot-llm",
        "parent": None,
    }

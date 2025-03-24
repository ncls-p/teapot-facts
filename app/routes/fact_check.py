from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..models import (
    ExtractionRequest,
    ExtractionResponse,
    FactCheckRequest,
    FactCheckResponse,
)
from ..services.fact_checker import TeapotFactChecker

router = APIRouter()
fact_checker = TeapotFactChecker()


@router.post("/fact-check", response_model=FactCheckResponse)
async def fact_check(request: FactCheckRequest):
    """Direct fact-checking endpoint (non-OpenAI compatible)"""
    result = fact_checker.check_fact(
        query=request.query, context=request.context, documents=request.documents
    )
    return result


@router.post("/extract", response_model=ExtractionResponse)
async def extract_information(request: ExtractionRequest):
    """
    Extract structured information from provided context using TeapotLLM's information extraction capability

    This endpoint uses TeapotLLM's ability to extract structured data from text following
    a defined schema (in this case, provided in the request as field definitions).
    """
    try:
        field_annotations = {}
        field_descriptions = {}

        for field in request.fields:
            type_mapping = {
                "string": str,
                "number": float,
                "integer": int,
                "boolean": bool,
            }

            python_type = type_mapping.get(field.type.lower(), str)
            field_annotations[field.name] = python_type

            if field.description:
                field_descriptions[field.name] = field.description

        model_fields = {}
        for name, type_ in field_annotations.items():
            if desc := field_descriptions.get(name):
                model_fields[name] = (type_, Field(description=desc))
            else:
                model_fields[name] = (type_, Field())

        dynamic_model = type(
            "DynamicExtractionModel",
            (BaseModel,),
            {
                "__annotations__": field_annotations,
                "__fields__": model_fields,
            },
        )

        extraction_result = fact_checker.extract_information(
            model_class=dynamic_model,
            query=request.query,
            context=request.context,
            documents=request.documents,
        )

        if isinstance(extraction_result, dict) and "error" in extraction_result:
            return ExtractionResponse(success=False, error=extraction_result["error"])

        try:
            if isinstance(extraction_result, BaseModel):
                if hasattr(extraction_result, "model_dump"):
                    data_dict = extraction_result.model_dump()
                elif hasattr(extraction_result, "dict"):
                    data_dict = extraction_result.dict()
                else:
                    data_dict = {
                        key: getattr(extraction_result, key)
                        for key in extraction_result.__fields__
                    }
            elif isinstance(extraction_result, dict):
                data_dict = extraction_result
            else:
                data_dict = {"result": str(extraction_result)}

            return ExtractionResponse(success=True, data=data_dict)

        except Exception as e:
            return ExtractionResponse(
                success=True, data={"result": str(extraction_result), "error": str(e)}
            )

    except Exception as e:
        return ExtractionResponse(success=False, error=f"Extraction failed: {str(e)}")

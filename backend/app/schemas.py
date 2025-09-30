from typing import List, Literal
from pydantic import BaseModel, Field

class OperationRequest(BaseModel):
    numbers: List[float] = Field(..., min_items=1, description="Lista de números (mínimo 1)")

class OperationResult(BaseModel):
    type: Literal["sum", "sub", "mul", "div"]
    numbers: List[float]
    result: float

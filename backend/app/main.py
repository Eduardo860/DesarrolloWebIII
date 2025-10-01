from typing import List, Optional, Literal
from datetime import datetime
from fastapi import FastAPI, HTTPException, status, Query, Body
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import OperationRequest, OperationResult
from app.db import save_operation, list_history, list_history_filtered

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helpers de validación/errores

def _err_negatives(op: str, numbers: List[float]):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            "status": "error",
            "code": 400,
            "message": "No se permiten números negativos",
            "operation": op,
            "numbers": numbers
        }
    )

def _err_div_zero(op: str, numbers: List[float]):
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "status": "error",
            "code": 403,
            "message": "División entre cero no permitida",
            "operation": op,
            "numbers": numbers
        }
    )

def _validate_non_negative(op: str, numbers: List[float]):
    if any(n < 0 for n in numbers):
        _err_negatives(op, numbers)

def _parse_iso(dt_str: Optional[str]) -> Optional[datetime]:
    if not dt_str:
        return None
    try:
        clean = dt_str.rstrip("Z")
        return datetime.fromisoformat(clean)
    except Exception:
        return None


# Endpoints de operaciones

@app.post("/calculadora/sum", response_model=OperationResult)
def sumar(payload: OperationRequest):
    _validate_non_negative("sum", payload.numbers)
    result = sum(payload.numbers)
    save_operation("sum", payload.numbers, result)
    return {"type": "sum", "numbers": payload.numbers, "result": result}

@app.post("/calculadora/sub", response_model=OperationResult)
def restar(payload: OperationRequest):
    _validate_non_negative("sub", payload.numbers)
    it = iter(payload.numbers)
    try:
        result = next(it)
    except StopIteration:
        result = 0.0
    else:
        for x in it:
            result -= x
    save_operation("sub", payload.numbers, result)
    return {"type": "sub", "numbers": payload.numbers, "result": result}

@app.post("/calculadora/mul", response_model=OperationResult)
def multiplicar(payload: OperationRequest):
    _validate_non_negative("mul", payload.numbers)
    result = 1.0
    for x in payload.numbers:
        result *= x
    save_operation("mul", payload.numbers, result)
    return {"type": "mul", "numbers": payload.numbers, "result": result}

@app.post("/calculadora/div", response_model=OperationResult)
def dividir(payload: OperationRequest):
    _validate_non_negative("div", payload.numbers)
    it = iter(payload.numbers)
    try:
        result = next(it)
    except StopIteration:
        result = 0.0
    else:
        for x in it:
            if x == 0:
                _err_div_zero("div", payload.numbers)
            result /= x
    save_operation("div", payload.numbers, result)
    return {"type": "div", "numbers": payload.numbers, "result": result}


# Historial 

@app.get("/calculadora/historial")
def historial(
    limit: int = Query(20, ge=1, le=200),
    type: Optional[Literal["sum","sub","mul","div"]] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    order_by: Optional[Literal["date","result"]] = "date",
    direction: Optional[Literal["asc","desc"]] = "desc",
):
    f = _parse_iso(date_from)
    t = _parse_iso(date_to)

    if any([type, f, t, order_by, direction]) and (type or f or t or order_by != "date" or direction != "desc"):
        items = list_history_filtered(
            op_type=type,
            from_dt=f,
            to_dt=t,
            order_by=order_by or "date",
            direction=direction or "desc",
            limit=limit
        )
        return {"historial": items}

    return {"historial": list_history(limit)}


# Endpoint batch de operaciones

@app.post("/operaciones/lote")
def operaciones_lote(payload: dict = Body(...)):
    ops = payload.get("operations", [])
    if not isinstance(ops, list) or len(ops) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"status":"error","code":400,"message":"Campo 'operations' inválido o vacío"}
        )

    results = []
    for item in ops:
        op_type = (item.get("type") or "").lower()
        numbers = item.get("numbers", [])

        # Validaciones comunes
        if not isinstance(numbers, list) or len(numbers) < 1:
            results.append({"type": op_type, "error": {
                "status":"error","code":400,"message":"Lista 'numbers' vacía o inválida",
                "operation": op_type, "numbers": numbers
            }})
            continue
        if any(n < 0 for n in numbers):
            results.append({"type": op_type, "error": {
                "status":"error","code":400,"message":"No se permiten números negativos",
                "operation": op_type, "numbers": numbers
            }})
            continue

        try:
            if op_type == "sum":
                r = sum(numbers)
            elif op_type == "sub":
                it = iter(numbers); r = next(it)
                for x in it: r -= x
            elif op_type == "mul":
                r = 1.0
                for x in numbers: r *= x
            elif op_type == "div":
                it = iter(numbers); r = next(it)
                for x in it:
                    if x == 0:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail={"status":"error","code":403,"message":"División entre cero no permitida",
                                    "operation":"div","numbers":numbers}
                        )
                    r /= x
            else:
                results.append({"type": op_type, "error": {
                    "status":"error","code":400,"message":"Tipo de operación no soportado",
                    "operation": op_type, "numbers": numbers
                }})
                continue

            save_operation(op_type, numbers, r)
            results.append({"type": op_type, "result": r})

        except HTTPException as ex:
            results.append({"type": op_type, "error": ex.detail})

    return {"results": results}

# Root
@app.get("/")
def root():
    return {"ok": True, "service": "calculadora-api"}

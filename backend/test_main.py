# test_main.py
import pytest
import mongomock
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient


try:
    from app.main import app
    import app.db as db
except ImportError:
    from backend.app.main import app
    import backend.app.db as db



# FIXTURES

@pytest.fixture(autouse=True)
def mock_mongo(monkeypatch):
    client = mongomock.MongoClient()
    mock_db = client[db.DB_NAME]
    mock_hist = mock_db[db.COLLECTION]
    monkeypatch.setattr(db, "hist", mock_hist, raising=True)
    yield

@pytest.fixture
def client():
    return TestClient(app)

def iso_now():
    return datetime.now(timezone.utc).replace(microsecond=0)

def to_iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat()



# TESTS DE OPERACIONES

@pytest.mark.parametrize(
    "numbers, result",
    [
        ([1, 2, 3], 6),
        ([5], 5),
        ([0, 0, 0], 0),
        ([10, 5, 2, 3], 20),
    ],
)
def test_sum_ok(client, numbers, result):
    r = client.post("/calculadora/sum", json={"numbers": numbers})
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "sum"
    assert data["numbers"] == numbers
    assert data["result"] == result


@pytest.mark.parametrize(
    "numbers, result",
    [
        ([20, 4, 3], 13),     
        ([5], 5),
        ([100, 50], 50),
        ([10, 1, 2, 3], 4),   
    ],
)
def test_sub_ok(client, numbers, result):
    r = client.post("/calculadora/sub", json={"numbers": numbers})
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "sub"
    assert data["numbers"] == numbers
    assert data["result"] == result


@pytest.mark.parametrize(
    "numbers, result",
    [
        ([2, 3, 4], 24),
        ([5], 5),
        ([10, 0], 0),
        ([1, 2, 3, 4], 24),
    ],
)
def test_mul_ok(client, numbers, result):
    r = client.post("/calculadora/mul", json={"numbers": numbers})
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "mul"
    assert data["numbers"] == numbers
    assert data["result"] == result


@pytest.mark.parametrize(
    "numbers, result",
    [
        ([100, 5, 2], 10),   
        ([10, 2], 5),
        ([8], 8),
    ],
)
def test_div_ok(client, numbers, result):
    r = client.post("/calculadora/div", json={"numbers": numbers})
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "div"
    assert data["numbers"] == numbers
    assert data["result"] == result


def test_negativos_400_en_todas(client):
    for path in ["/calculadora/sum", "/calculadora/sub", "/calculadora/mul", "/calculadora/div"]:
        r = client.post(path, json={"numbers": [2, -5]})
        assert r.status_code == 400
        d = r.json()["detail"]
        assert d["status"] == "error"
        assert d["code"] == 400
        assert "No se permiten números negativos" in d["message"]
        assert "operation" in d and "numbers" in d


def test_division_por_cero_403(client):
    r = client.post("/calculadora/div", json={"numbers": [10, 0]})
    assert r.status_code == 403
    d = r.json()["detail"]
    assert d["status"] == "error"
    assert d["code"] == 403
    assert d["operation"] == "div"
    assert d["numbers"] == [10, 0]



# TESTS DE HISTORIAL

def test_historial_basico(client):

    client.post("/calculadora/sum", json={"numbers": [1, 2]})      # 3
    client.post("/calculadora/mul", json={"numbers": [2, 5]})      # 10
    client.post("/calculadora/sub", json={"numbers": [10, 3, 2]})  # 5

    r = client.get("/calculadora/historial?limit=5")
    assert r.status_code == 200
    hist = r.json()["historial"]
    assert 1 <= len(hist) <= 5

    for doc in hist:
        assert {"type", "numbers", "result", "date"} <= set(doc.keys())


def test_historial_filtros_tipo_fecha_y_orden(client):

    client.post("/calculadora/mul", json={"numbers": [2, 3]})      
    client.post("/calculadora/mul", json={"numbers": [5, 5]})      
    client.post("/calculadora/sum", json={"numbers": [10, 1]})     

    now = iso_now()

    r1 = client.get("/calculadora/historial?type=mul&limit=10")
    assert r1.status_code == 200
    items = r1.json()["historial"]
    assert len(items) >= 2
    assert all(doc["type"] == "mul" for doc in items)


    r2 = client.get("/calculadora/historial?order_by=result&direction=asc&limit=10")
    assert r2.status_code == 200
    items2 = r2.json()["historial"]
    results = [doc["result"] for doc in items2]
    assert results == sorted(results)


    r3 = client.get(f"/calculadora/historial?date_from={to_iso(now - timedelta(days=1))}&date_to={to_iso(now + timedelta(days=1))}")
    assert r3.status_code == 200
    assert len(r3.json()["historial"]) >= 1



# TESTS DE LOTES

def test_batch_mixto(client):
    payload = {
        "operations": [
            {"type": "sum", "numbers": [2, 3, 4]},   
            {"type": "div", "numbers": [10, 0]},     
            {"type": "mul", "numbers": [2, -5]},     
            {"type": "sub", "numbers": [20, 3, 2]}   
        ]
    }
    r = client.post("/operaciones/lote", json=payload)
    assert r.status_code == 200
    res = r.json()["results"]
    assert len(res) == 4


    assert res[0]["type"] == "sum" and "result" in res[0]
    assert res[1]["type"] == "div" and "error" in res[1] and res[1]["error"]["code"] == 403
    assert res[2]["type"] == "mul" and "error" in res[2] and res[2]["error"]["code"] == 400
    assert res[3]["type"] == "sub" and "result" in res[3]


    h = client.get("/calculadora/historial?limit=10").json()["historial"]
    tipos = [x["type"] for x in h]

    assert tipos.count("sum") >= 1
    assert tipos.count("sub") >= 1


# TESTS DE ERRORES 


def test_sum_con_negativos_da_400(client):
    r = client.post("/calculadora/sum", json={"numbers": [5, -10]})
    assert r.status_code == 400
    d = r.json()["detail"]
    assert d["code"] == 400
    assert "No se permiten números negativos" in d["message"]

def test_mul_con_negativos_da_400(client):
    r = client.post("/calculadora/mul", json={"numbers": [-2, 3]})
    assert r.status_code == 400
    d = r.json()["detail"]
    assert d["operation"] == "mul"

def test_division_por_cero_da_403(client):
    r = client.post("/calculadora/div", json={"numbers": [10, 0]})
    assert r.status_code == 403
    d = r.json()["detail"]
    assert d["code"] == 403
    assert d["operation"] == "div"

def test_batch_con_operaciones_invalidas(client):
    payload = {
        "operations": [
            {"type": "sum", "numbers": [1, -2]},  
            {"type": "div", "numbers": [5, 0]},   
            {"type": "foo", "numbers": [1, 2]}    
        ]
    }
    r = client.post("/operaciones/lote", json=payload)
    assert r.status_code == 200
    res = r.json()["results"]


    assert any(item["error"]["code"] == 400 for item in res if "error" in item)
    assert any(item["error"]["code"] == 403 for item in res if "error" in item)
    assert any(item["error"]["message"] == "Tipo de operación no soportado" for item in res if "error" in item)

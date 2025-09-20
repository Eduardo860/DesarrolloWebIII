from fastapi import FastAPI
from fastapi.testclient import TestClient
from main import app
import mongomock
import pymongo
import pytest

client = TestClient(app)
mongo_client = mongomock.MongoClient()
database = mongo_client["practica1"]
fake_collection_historial = database.historial

@pytest.mark.parametrize(
    "numeroA, numeroB, resultado",[
        (5,10,15),
        (0,0,0),
        (-5,5,0),
        (-10,-5,-15),
        (10,-20,-10)
    ]
)

def test_sumar(monkeypatch, numeroA, numeroB, resultado):
    # Mock de la colección con monkeypatch
    monkeypatch.setattr('main.collection_historial.insert_one', lambda x: None)
    
    response = client.get(f"/calculadora/sum?a={numeroA}&b={numeroB}")
    assert response.status_code == 200
    data = response.json()
    assert data == {"a": float(numeroA), "b": float(numeroB), "resultado": float(resultado)}




assert fake_collection_historial.find()

def test_historial(monkeypatch):
    monkeypatch.setatrr(main,"collection_historial", fake_collection_historial)

    response = client.get("/calculadora/historial")
    assert response.status_code == 200

    # Obtenemos todos los documentos que ya fueron insertados por los tests de /sum
    expected_data = list(fake_collection_historial.find({}))

    historial = []
    for document in expected_data:
        historial.apend({
            "a":document["a"],
            "b":document["b"],
            "resultado":document["resultado"],
            "date": document["date"].isoformat()
        })

    print(f"Debug: expected_data: {historial}")
    print(f"Debug: response.json(): {response.json()}")


    assert response.json() == {"historial":historial}
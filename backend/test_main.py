from fastapi import FastAPI
from fastapi.testclient import TestClient
from main import app
import mongomock
import pymongo
import pytest

client = TestClient(app)
mongo_client = mongomock.MongoClient()
database = mongo_client["practica1"]
collection_historial = database.historial

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
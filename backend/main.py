# main.py
import os
import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient, DESCENDING
from bson import ObjectId

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


MONGO_URL = os.getenv("MONGO_URL", "mongodb://admin_user:web3@mongo:27017/?authSource=admin")
mongo_client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)

try:
    mongo_client.admin.command("ping")
except Exception as e:
    print("Mongo no disponible aún:", e)

database = mongo_client["practica1"]
collection_historial = database["historial"]


def serialize_doc(doc: dict) -> dict:
    """Convierte ObjectId y datetime a strings para JSON"""
    out = dict(doc)
    if "_id" in out:
        out["_id"] = str(out["_id"])
    if "date" in out and isinstance(out["date"], (datetime.datetime, datetime.date)):
        out["date"] = out["date"].isoformat()
    return out

@app.get("/calculadora/sum")
def sumar(a: float, b: float):
    resultado = a + b
    document = {
        "resultado": resultado,
        "a": a,
        "b": b,
        "date": datetime.datetime.now(tz=datetime.timezone.utc),
    }
    collection_historial.insert_one(document)
    return {"a": a, "b": b, "resultado": resultado}

@app.get("/calculadora/historial")
def obtener_historial(limit: int = 20):
    """
    Devuelve las últimas operaciones guardadas en Mongo.
    """
    cursor = collection_historial.find().sort("date", DESCENDING).limit(limit)
    docs = [serialize_doc(d) for d in cursor]
    return {"historial": docs}
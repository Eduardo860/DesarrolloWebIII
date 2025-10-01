# main.py
import os
import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient, DESCENDING

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MONGO_URL = os.getenv("MONGO_URL", "mongodb://admin_user:web3@mongo:27017/?authSource=admin")
mongo_client = None
collection_historial = None

try:
    mongo_client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=3000)
    mongo_client.admin.command("ping")
    database = mongo_client["practica1"]
    collection_historial = database["historial"]
    print("✅ Mongo conectado")
except Exception as e:
    print("⚠️ Mongo no disponible aún:", e)

def serialize_doc(doc: dict) -> dict:
    out = dict(doc)
    _id = out.get("_id")
    if _id is not None:
        out["_id"] = str(_id)
    date = out.get("date")
    if isinstance(date, (datetime.datetime, datetime.date)):
        out["date"] = date.isoformat()
    return out

@app.get("/")
def health():
    return {"status": "ok", "mongo": bool(collection_historial)}

@app.get("/calculadora/sum")
def sumar(a: float, b: float):
    resultado = a + b
    doc = {"resultado": resultado, "a": a, "b": b, "date": datetime.datetime.now(datetime.timezone.utc)}
    if collection_historial is not None:
        try:
            collection_historial.insert_one(doc)
        except Exception as e:
            print("⚠️ No se pudo guardar en Mongo:", e)
    return {"a": a, "b": b, "resultado": resultado}

@app.get("/calculadora/historial")
def obtener_historial(limit: int = 20):
    if collection_historial is None:
        return {"historial": []}
    try:
        cursor = collection_historial.find().sort("date", DESCENDING).limit(limit)
        docs = [serialize_doc(d) for d in cursor]
        return {"historial": docs}
    except Exception as e:
        print("⚠️ No se pudo leer de Mongo:", e)
        return {"historial": []}

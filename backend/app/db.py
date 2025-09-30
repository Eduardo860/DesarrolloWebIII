import os
import datetime
from typing import Optional, List
from pymongo import MongoClient, DESCENDING, ASCENDING
from bson import ObjectId

MONGO_URL = os.getenv("MONGO_URL", "mongodb://admin_user:web3@mongo:27017/?authSource=admin")
DB_NAME = os.getenv("MONGO_DB", "practica1")
COLLECTION = os.getenv("MONGO_COL_HISTORY", "historial")

client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
try:
    client.admin.command("ping")
except Exception as e:
    print("Mongo no disponible aún:", e)

db = client[DB_NAME]
hist = db[COLLECTION]

def _serialize(doc: dict) -> dict:
    out = dict(doc)
    if "_id" in out and isinstance(out["_id"], ObjectId):
        out["_id"] = str(out["_id"])
    if "date" in out and isinstance(out["date"], (datetime.datetime, datetime.date)):
        out["date"] = out["date"].isoformat()
    return out

def save_operation(op_type: str, numbers: List[float], result: float):
    hist.insert_one({
        "type": op_type,
        "numbers": numbers,
        "result": result,
        "date": datetime.datetime.now(datetime.timezone.utc)
    })

def list_history(limit: int = 20) -> list[dict]:
    return [_serialize(d) for d in hist.find().sort("date", DESCENDING).limit(limit)]

def list_history_filtered(
    op_type: Optional[str] = None,
    from_dt: Optional[datetime.datetime] = None,
    to_dt: Optional[datetime.datetime] = None,
    order_by: str = "date",   
    direction: str = "desc",  
    limit: int = 50
) -> list[dict]:
    query: dict = {}
    if op_type:
        query["type"] = op_type
    if from_dt or to_dt:
        query["date"] = {}
        if from_dt:
            query["date"]["$gte"] = from_dt
        if to_dt:
            query["date"]["$lte"] = to_dt

    sort_key = order_by if order_by in ("date", "result") else "date"
    sort_dir = ASCENDING if direction == "asc" else DESCENDING

    cursor = hist.find(query).sort(sort_key, sort_dir).limit(limit)
    return [_serialize(d) for d in cursor]

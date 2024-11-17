from pymongo import MongoClient
from datetime import datetime

# Підключення до MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client['DatingAgency_Local']

# Оновлення дат
clients = db.clients.find()
for client in clients:
    if isinstance(client["registration_date"], str):
        formatted_date = datetime.strptime(client["registration_date"], "%Y-%m-%d")
        db.clients.update_one({"_id": client["_id"]}, {"$set": {"registration_date": formatted_date}})

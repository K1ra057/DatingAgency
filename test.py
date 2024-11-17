from pymongo import MongoClient

# Підключення до MongoDB
client = MongoClient("mongodb://localhost:27017/")

# Вибір бази даних
db = client['DatingAgency_Local']

print("Успішно підключено до бази даних:", db.name)

# Додавання нового клієнта
new_client = {
    "gender": "male",
    "registration_date": "2024-11-17",
    "age": 35,
    "height": 180,
    "weight": 80,
    "zodiac_sign": "Aries",
    "self_description": "Enjoys hiking and outdoor activities.",
    "partner_requirements": {
        "age": [28, 35],
        "height": [165, 180],
        "weight": [55, 70],
        "zodiac_sign": ["Libra", "Gemini"]
    }
}

# Додавання клієнта до бази
result = db.clients.insert_one(new_client)
print(f"Клієнт доданий з ID: {result.inserted_id}")

# Виведення всіх клієнтів
print("\nУсі клієнти:")
for client in db.clients.find():
    print(client)

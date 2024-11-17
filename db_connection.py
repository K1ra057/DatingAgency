from pymongo import MongoClient

# Підключення до MongoDB
def get_database():
    # Змінити URI, якщо база знаходиться не локально
    client = MongoClient("mongodb://localhost:27017/")
    return client['DatingAgency_Local']  # Назва бази даних

db = get_database()

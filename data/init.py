from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from datetime import datetime
import json
import torch

# Подключение к MongoDB
DATABASE_URL = "mongodb://senya:insecure@127.0.0.1:27017/dating"
client = MongoClient(DATABASE_URL)
db = client.dating

# Инициализация модели
if torch.cuda.is_available():
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', device='cuda')
else:
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', device='cpu')

# Удаление старых данных
db.cities.drop()
db.users.drop()

# Загрузка данных городов из JSON
with open('cities.json', 'r') as f:
    city_data = json.load(f)

# Добавление городов в базу данных
city_ids = {}
for city in city_data:
    result = db.cities.insert_one(city)
    city_ids[city["address"]] = result.inserted_id

# Загрузка данных пользователей из JSON
with open('users.json', 'r') as f:
    user_data = json.load(f)

# Обработка и добавление пользователей в базу данных
users = []
for user in user_data:
    city_name = f"г {user.pop('city')}"
    city_id = city_ids.get(city_name)

    if city_id:
        user["city_id"] = city_id

    # Кодирование биографии
    user["embedded_bio"] = model.encode(user["bio"]).tolist()

    # Добавление временных полей
    user["created_at"] = datetime.now()
    user["updated_at"] = datetime.now()
    user["last_active"] = datetime.now()

    users.append(user)

db.users.insert_many(users)

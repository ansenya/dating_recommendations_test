from sqlalchemy import create_engine, Column, Integer, String, Date, Text, TIMESTAMP, text, Float, ForeignKey, Double
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from sentence_transformers import SentenceTransformer, util

import torch

from random import randint

import json

DATABASE_URL = "postgresql://user:insecure@localhost:5432/dating"

if torch.cuda.is_available():
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', device='cuda')
else:
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', device='cpu')

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)  # Уникальный идентификатор
    first_name = Column(String(100), nullable=False)  # Имя пользователя
    last_name = Column(String(100))  # Фамилия
    date_of_birth = Column(Date)  # Дата рождения
    gender = Column(String(10))  # Пол
    city_id = Column(Integer, ForeignKey('cities.id'))  # Локация
    bio = Column(Text)  # Описание
    embedded_bio = Column(ARRAY(Double))
    preferred_gender = Column(String(10))  # Предпочитаемый пол
    preferred_age_bottom = Column(Integer)  # Нижний диапазон возраста
    preferred_age_top = Column(Integer)  # Верхний диапазон возраста
    max_distance = Column(Integer)  # Максимальное расстояние
    last_geo_lon = Column(Float)
    last_geo_lat = Column(Float)
    last_active = Column(TIMESTAMP, default=datetime.now)  # Время последней активности
    created_at = Column(TIMESTAMP, default=datetime.now)  # Дата создания
    updated_at = Column(TIMESTAMP, default=datetime.now)  # Дата последнего обновления
    city = relationship('City', back_populates='users')


class City(Base):
    __tablename__ = 'cities'

    id = Column(Integer, primary_key=True)
    address = Column(String(100), nullable=False)
    lat = Column(Float)
    lon = Column(Float)
    timezone = Column(String(100), nullable=False)
    users = relationship('User', back_populates='city')


sql_create_table_users = '''CREATE TABLE IF NOT EXISTS users
(
    id                   SERIAL PRIMARY KEY,      -- Уникальный идентификатор пользователя
    first_name           VARCHAR(100) NOT NULL,   -- Имя пользователя
    last_name            VARCHAR(100),            -- Фамилия пользователя
    date_of_birth        DATE,                    -- Дата рождения
    gender               VARCHAR(10),             -- Пол пользователя
    city_id              INT REFERENCES cities(id), -- Локация (город)
    bio                  TEXT,                    -- Описание о себе
    embedded_bio         DOUBLE PRECISION[],                    -- Описание о себе
    preferred_gender     VARCHAR(10),             -- Предпочитаемый пол партнера
    preferred_age_bottom INT,                     -- Диапазон возраста партнера
    preferred_age_top    INT,                     -- Диапазон возраста партнера
    max_distance         INT,                     -- Максимальное расстояние для поиска
    last_geo_lon         FLOAT,                     -- Максимальное расстояние для поиска
    last_geo_lat         FLOAT,                     -- Максимальное расстояние для поиска
    last_active          TIMESTAMP DEFAULT NOW(), -- Время последней активности
    created_at           TIMESTAMP DEFAULT NOW(), -- Дата и время создания пользователя
    updated_at           TIMESTAMP DEFAULT NOW()  -- Дата и время последнего обновления данных
);'''

sql_create_table_cities = '''CREATE TABLE IF NOT EXISTS cities
(
    id       SERIAL PRIMARY KEY,
    address  VARCHAR(100),
    lat      FLOAT,
    lon      FLOAT,
    timezone VARCHAR(10)
);'''

sql_create_table_recommendations = '''CREATE TABLE IF NOT EXISTS recommendations
(
    id       SERIAL PRIMARY KEY,
    user_id              INT REFERENCES users(id),
    
);'''

drop_users = '''DROP TABLE USERS
'''

dtop_cities = '''DROP TABLE cities;
'''

if __name__ == "__main__":
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    queries = [drop_users, dtop_cities, sql_create_table_cities, sql_create_table_users]
    for query in queries:
        if query.strip():
            session.execute(text(query))

    cities = [City(**city) for city in json.loads(open('cities.json').read())]
    session.add_all(cities)

    city_map = {city.address: city.id for city in session.query(City).all()}

    users = []
    for user_data in json.loads(open('users.json').read()):
        city = user_data.pop('city')
        location_id = city_map.get(f"г {city}")
        user_data["embedded_bio"] = model.encode(user_data["bio"]).tolist()
        if location_id:
            user_data['city_id'] = location_id
        users.append(User(**user_data))
    session.add_all(users)
    session.commit()

    users = [user.__dict__ for user in session.query(User).all()]
    for el in users:
        el.pop('_sa_instance_state', None)
        el["age"] = datetime.now().year - el["date_of_birth"].year

    random_id = randint(0, len(users) - 1)

    user = users[random_id]
    users.remove(user)

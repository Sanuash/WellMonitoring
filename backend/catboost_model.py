# backend/catboost_model.py

import pandas as pd
from catboost import CatBoostClassifier

MODEL_PATH = "catboost_model.cbm"

# Загружаем модель CatBoost
model = CatBoostClassifier()
model.load_model(MODEL_PATH)

def predict(features: dict) -> float:
    """
    Принимает словарь признаков, преобразует его в DataFrame и возвращает вероятность для класса 1.
    
    :param features: словарь с данными по скважине, ключи должны соответствовать признакам модели.
    :return: вероятность пескопроявления (например, вероятность для класса 1).
    """
    df = pd.DataFrame([features])
    # Метод predict_proba возвращает вероятности для каждого класса
    proba = model.predict_proba(df)[0][1]
    return proba

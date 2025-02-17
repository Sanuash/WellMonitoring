# 🚀 Well Monitoring – Мониторинг скважин с предсказанием пескопроявления

### 📊 FastAPI + CatBoost + Pandas

**Well Monitoring** – это веб-приложение для мониторинга скважин с анализом данных и предсказанием вероятности пескопроявления на основе модели машинного обучения (CatBoost). Приложение позволяет загружать Excel-файлы с данными, автоматически анализировать их и представлять результаты в виде удобной таблицы с фильтрацией, сортировкой и визуальным выделением рисков.

---

## 🔥 Возможности приложения

✔ **Загрузка файла с данными** (`.xls`)  
✔ **Автоматическая обработка данных** (чистка, фильтрация, расчет показателей)  
✔ **Предсказание вероятности пескопроявления** (на основе CatBoost)  
✔ **Отображение результатов в удобной таблице**  
✔ **Фильтрация по кусту, поиск по номеру скважины**  
✔ **Цветовая индикация риска (желтый/красный)**  

---

## 🛠 Установка и запуск

### 🚀 Запуск локально

1. **Создайте и активируйте виртуальное окружение (рекомендуется)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # для macOS/Linux
   venv\Scripts\activate     # для Windows```
2. **Установите зависимости:**
   ```
   pip install -r requirements.txt
   ```
4. **Запустите сервер:**
   ```
   uvicorn backend.main:app --reload
   ```
6. **Откройте браузер и перейдите на:**
   ```
   http://localhost:8000
   ```

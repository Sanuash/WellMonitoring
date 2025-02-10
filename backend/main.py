# backend/main.py

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from backend import data_handler, catboost_model
import shutil


app = FastAPI(title="Well Monitoring")

# Монтируем директорию с фронтендом
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/", response_class=HTMLResponse)
def read_index():
    """
    Возвращает HTML-страницу с таблицей результатов.
    """
    try:
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка загрузки страницы: " + str(e))

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Принимает файл с данными, сохраняет его и перезагружает данные.
    """
    try:
        upload_path = "uploaded_data.xls"  # имя файла, куда сохраняем загруженный файл
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        # Обновляем путь к файлу в data_handler
        data_handler.DATA_PATH = upload_path
        data_handler.reload_data()
        return {"filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка загрузки файла: " + str(e))

@app.get("/predict/{well_id}")
def predict_well(well_id: int):
    """
    Получает данные скважины по ID из CSV, рассчитывает вероятность пескопроявления и возвращает результат.
    """
    well = data_handler.get_well_by_id(well_id)
    if not well:
        raise HTTPException(status_code=404, detail="Скважина не найдена")
    
    probability = catboost_model.predict(well)
    return {"well_id": well_id, "probability": probability}

@app.get("/wells")
def get_all_wells():
    """
    Возвращает список всех скважин с рассчитанной вероятностью пескопроявления.
    Каждый элемент содержит: номер скважины, пластовое давление, затрубное давление,
    дебит по жидкости, обводненность, температуру и вероятность.
    """
    wells_df = data_handler.get_all_wells()
    wells_list = []
    
    for _, row in wells_df.iterrows():
        well_data = row.to_dict()
        probability = catboost_model.predict(well_data)
        wells_list.append({
            "kust": well_data.get("Куст"),
            "n_sk": well_data.get("№ скв"),
            "q_teor": well_data.get("Фактический режим Q жид- кости"),
            "gas_factor": well_data.get("Фактический режим ГФ пг"),
            "p_u": well_data.get("P затр"),
            "p_zab": well_data.get("Фактический режим Р заб"),
            "temp": well_data.get("Н д"),
            "probability": probability
        })
    
    return wells_list

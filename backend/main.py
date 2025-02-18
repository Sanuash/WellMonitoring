import threading
import webbrowser
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from backend import data_handler, catboost_model
import math, time, asyncio
import shutil

app = FastAPI(title="Well Monitoring")

# Монтируем директорию с фронтендом
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Глобальный словарь для динамических параметров для каждой скважины по её ID
wells_dynamic = {}

def simulate_dynamic_value(base_value, amplitude, period):
    """
    Вычисляет динамическое значение на основе базового значения,
    амплитуды и периода колебаний.
    """
    t = time.time()
    delta = amplitude * math.sin(2 * math.pi * (t % period) / period)
    return base_value + delta

async def update_wells_dynamic():
    """
    Фоновая задача, которая обновляет динамические параметры для каждой скважины каждые 3 секунды.
    Для каждой скважины берём базовые значения из загруженных данных (data_handler.get_all_wells())
    и пересчитываем динамические значения.
    """
    global wells_dynamic
    while True:
        wells_df = data_handler.get_all_wells()
        for _, row in wells_df.iterrows():
            well_data = row.to_dict()
            well_id = well_data.get("№ скв")  # используем номер скважины как идентификатор
            if well_id is None:
                continue

            # Получаем базовые значения
            q_teor_base = well_data.get("Фактический режим Q жид- кости", 0)
            gas_factor_base = well_data.get("Фактический режим ГФ пг", 0)
            p_zatr_base = well_data.get("P затр", 0)
            p_zab_base = well_data.get("Фактический режим Р заб", 0)
            oil_debit_base = well_data.get("Фактический режим Q нефти", 0)

            # Вычисляем динамические значения
            q_teor_dynamic = simulate_dynamic_value(q_teor_base, amplitude=5, period=90)
            gas_factor_dynamic = simulate_dynamic_value(gas_factor_base, amplitude=7, period=80)
            p_zatr_dynamic = simulate_dynamic_value(p_zatr_base, amplitude=3, period=80)
            p_zab_dynamic = simulate_dynamic_value(p_zab_base, amplitude=2, period=90)
            oil_debit_dynamic = simulate_dynamic_value(oil_debit_base, amplitude=2, period=75)

            # Сохраняем динамические значения для данной скважины
            wells_dynamic[well_id] = {
                "q_teor": q_teor_dynamic,
                "gas_factor": gas_factor_dynamic,
                "p_zatr": p_zatr_dynamic,
                "p_zab": p_zab_dynamic,
                "oil_debit": oil_debit_dynamic,
            }
        await asyncio.sleep(3)  # обновление каждые 3 секунды

@app.on_event("startup")
async def startup_event():
    threading.Timer(1, lambda: webbrowser.open("http://127.0.0.1:8000/")).start()
    asyncio.create_task(update_wells_dynamic())

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
        upload_path = "uploaded_data.xls"  
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
    Получает данные скважины по ID из CSV (XLS), объединяет с динамическими данными и рассчитывает вероятность.
    """
    well = data_handler.get_well_by_id(well_id)
    if not well:
        raise HTTPException(status_code=404, detail="Скважина не найдена")
    
    # Подменяем статические показатели динамическими значениями, если они есть
    dynamic = wells_dynamic.get(well_id, {})
    if dynamic:
        well["Фактический режим Q жид- кости"] = dynamic.get("q_teor", well.get("Фактический режим Q жид- кости"))
        well["Фактический режим ГФ пг"] = dynamic.get("gas_factor", well.get("Фактический режим ГФ пг"))
        well["P затр"] = dynamic.get("p_zatr", well.get("P затр"))
        well["Фактический режим Р заб"] = dynamic.get("p_zab", well.get("Фактический режим Р заб"))
        well["Фактический режим Q нефти"] = dynamic.get("oil_debit", well.get("Фактический режим Q нефти"))
    
    probability = catboost_model.predict(well)
    return {"well_id": well_id, "probability": probability}

@app.get("/wells")
def get_all_wells():
    """
    Возвращает список всех скважин с рассчитанной вероятностью пескопроявления.
    Для каждого объекта объединяются статические данные из CSV (XLS) и динамические значения,
    обновляемые каждые 3 секунды.
    """
    wells_df = data_handler.get_all_wells()
    wells_list = []
    
    for _, row in wells_df.iterrows():
        well_data = row.to_dict()
        well_id = well_data.get("№ скв")
        if well_id is None:
            continue

        # Получаем динамические данные, если они обновлены
        dynamic = wells_dynamic.get(well_id, {})
        if dynamic:
            well_data["Фактический режим Q жид- кости"] = dynamic.get("q_teor", well_data.get("Фактический режим Q жид- кости"))
            well_data["Фактический режим ГФ пг"] = dynamic.get("gas_factor", well_data.get("Фактический режим ГФ пг"))
            well_data["P затр"] = dynamic.get("p_zatr", well_data.get("P затр"))
            well_data["Фактический режим Р заб"] = dynamic.get("p_zab", well_data.get("Фактический режим Р заб"))
            well_data["Фактический режим Q нефти"] = dynamic.get("oil_debit", well_data.get("Фактический режим Q нефти"))
        
        probability = catboost_model.predict(well_data)
        wells_list.append({
            "kust": well_data.get("Куст"),
            "n_sk": well_id,
            "q_teor": well_data.get("Фактический режим Q жид- кости"),
            "gas_factor": well_data.get("Фактический режим ГФ пг"),
            "p_u": well_data.get("P затр"),
            "p_zab": well_data.get("Фактический режим Р заб"),
            "temp": well_data.get("Фактический режим Q нефти"),
            "probability": probability
        })
    
    return wells_list

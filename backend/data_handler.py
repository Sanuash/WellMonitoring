# backend/data_handler.py

import pandas as pd
import numpy as np
import os

# Путь к CSV-файлу с данными по скважинам
DATA_PATH = ""
data_df = pd.DataFrame()

def open_data(path):
    # Читаем данные из Excel, пропуская первые 6 строк и используя многоуровневый заголовок
    data = pd.read_excel(path, skiprows=6, header=[0, 1, 2])
    # Удаляем столбцы, в которых менее 70% заполненных значений
    data = data.dropna(axis=1, thresh=0.7 * len(data))
    data.columns = [
        ' '.join([part for part in col if not part.startswith('Unnamed')]).strip()
        for col in data.columns
    ]

    # Фильтрация активных нефтяных скважин
    data = data[
        (data["Месторождение Код"] == 11.0) & 
        (data["Пласт"] == "ПК1-3") & 
        (data["Назначение по проекту"] == "Нефтяные")
    ]
    
    # Удаление константных признаков
    data = data.loc[:, data.nunique() > 1]

    # Признаки типа скважины и системы эксплуатации
    data['is_horis'] = np.where(data['Тип\nскважины'] == 'ГОР', 1, 0)
    data['is_ESP'] = np.where(data['СЭ'] == 'ЭЦН', 1, 0)

    # Списки столбцов на удаление
    to_drop = [
        'Тип насоса', 'ПЭД Марка', 'ГЗУ', 'Тип ГЗУ', 'Дата запуска после КРС', 'Дата остановки',
        'Дата ввода в эксплу-атацию', 'Режим работы УЭЦН Комментарии', 
        'Режим работы УЭЦН Дата установки режима Описание', 'СЭ', 'Тип скважины'
    ]
    to_drop_2 = [
        'Р пл на ВДП', 'Дата запуска', 'Группа фонда', 'Дополнительное оборудование Диаметр',
        'Дополнительное оборудование Глубина спуска', 'Режим работы УЭЦН Режим', 
        'Режим работы УЭЦН Дата установки режима', 'Номинальная производительность', 
        'Номинальный напор', 'Состояние на конец месяца',
        'Сравнение расчетов потенциала dQж при ГРП', 
        'Сравнение расчетов потенциала dQж при ГРП с корр', 'Рзаб (геол огр индив)', 
        'Планируемый режим Q пг', 'ГФ', 'F', 'ГРП JD факт.',
        'Время до псевдоустановившегося режима', 'D э/к', 'D нкт', 'D шт'
    ]
    to_drop_3 = [
        'Расчёт потенциала (Мин. Тех., Нсп(макс) , не ниже ВДП, Рзаб (утв),  огр Рзаб по скв) Р заб',
        'Расчёт потенциала (Мин. Тех., Нсп(макс) , не ниже ВДП, Рзаб (утв),  огр Рзаб по скв) ИДН Q ж',
        'Расчёт потенциала (Мин. Тех., Нсп(макс) , не ниже ВДП, Рзаб (утв),  огр Рзаб по скв) ИДН Q ж  с поправкой на D э/к',
        'Расчёт потенциала (Мин. Тех., Нсп(макс) , не ниже ВДП, Рзаб (утв),  огр Рзаб по скв) ИДН Q н',
        'Расчёт потенциала (Мин. Тех., Нсп(макс) , не ниже ВДП, Рзаб (утв),  огр Рзаб по скв) ИДН Прирост Q н',
        'Расчёт потенциала (Мин. Тех., Нсп(макс) , не ниже ВДП, Рзаб (утв),  огр Рзаб по скв) % прироста Q н',
    ]

    data.columns = data.columns.str.replace(r'\n', ' ', regex=True)
    data = data.drop(columns=(to_drop + to_drop_2 + to_drop_3), errors='ignore')

    # Преобразование object -> float
    for col in data.select_dtypes(include='object').columns:
        data[col] = pd.to_numeric(data[col], errors='coerce')

    # Разности по времени
    data['P пл разность'] = data.groupby("№ скв")['Р пл'].diff().fillna(0)
    data['Qтеор разность'] = data.groupby("№ скв")['Qтеор'].diff().fillna(0)

    # Удаление скважин без номера
    data = data[~data["№ скв"].isna()]
    
    # Заполнение пропусков медианой по скважине
    data.iloc[:, 1:] = data.groupby("№ скв").transform(lambda x: x.fillna(x.median()))
    data = data.dropna()

    # Удаление выбросов по КВЧ
    data = data[data['Содер-жание мех-примесей (КВЧ)'] < 2000]

    # Удаление высоко коррелирующих признаков
    high_corelated_features = [
        'КН', 'Удл', 'Плот-ть раствора глушения', 
        'Расчёт геологического потенциала ИДН Прирост Q н',
        'Расчёт геологического потенциала ИДН Q ж',
        'Сравнение расчетов потенциала dQж при ИДН с корр',
        'Расчёт геологического потенциала ИДН Q ж  с поправкой на D э/к',
        'Удл (Нсп)', 'Сравнение расчетов потенциала dQж при ИДН',
        'Р на приёме', 'Qтеор', 'Сравнение расчетов потенциала dQн при ИДН',
        'Qr характеристический дебит жидкости', 'К пр'
    ]
    data = data.drop(columns=high_corelated_features, errors='ignore')

    # Новые признаки
    data["подвижность жидкости"] = data["k"] / data["В-ть жидкости"]
    data["фильтрационное сопротивление"] = (data["Фактический режим Р заб"] - data["Р лин"]) / data["Фактический режим Q жид- кости"]

    return data

# При старте приложения не пытаемся загружать данные, если DATA_PATH пустой или файл не существует.
if DATA_PATH and os.path.exists(DATA_PATH):
    try:
        data_df = open_data(DATA_PATH)
    except Exception as e:
        raise Exception(f"Ошибка чтения файла {DATA_PATH}: {e}")
else:
    data_df = pd.DataFrame()


def get_all_wells():
    """
    Возвращает копию DataFrame со всеми данными.
    """
    return data_df.copy()

def get_well_by_id(well_id: int):
    wells_df = get_all_wells()
    row = wells_df[wells_df["№ скв"] == well_id]
    if row.empty:
        return None
    return row.to_dict(orient="records")[0]

def reload_data():
    """
    Перезагружает данные из файла по пути DATA_PATH и обновляет глобальную переменную data_df.
    """
    global data_df
    if DATA_PATH and os.path.exists(DATA_PATH):
        try:
            data_df = open_data(DATA_PATH)
        except Exception as e:
            raise Exception("Ошибка при перезагрузке данных: " + str(e))
    else:
        data_df = pd.DataFrame()

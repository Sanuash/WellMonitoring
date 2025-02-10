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
    # Объединяем уровни заголовков в один, пропуская элементы, начинающиеся с "Unnamed"
    data.columns = [
        ' '.join([part for part in col if not part.startswith('Unnamed')]).strip()
        for col in data.columns
    ]
    # Фильтрация строк по ряду условий
    data = data[
        (data["Месторождение Код"].notna()) &
        (data['Месторождение Код'] == 11.0) &
        (data["Пласт"] == "ПК1-3") &
        (data['Назначение по проекту'] == "Нефтяные")
    ]
    # Оставляем только те столбцы, где количество уникальных значений > 1
    data = data.loc[:, data.nunique() > 1]
    # Добавляем булевые столбцы на основе условий
    data['is_horis'] = np.where(data['Тип\nскважины'] == 'ГОР', 1, 0)
    data['is_ESP'] = np.where(data['СЭ'] == 'ЭЦН', 1, 0)

    # Списки столбцов, которые требуется удалить
    to_drop = [
        'Тип насоса', 'ПЭД Марка', 'ГЗУ', 'Тип ГЗУ', 'Дата запуска после КРС', 
        'Дата остановки', 'Дата ввода в эксплу-атацию', 'Режим работы УЭЦН Комментарии', 
        'Режим работы УЭЦН Дата установки режима Описание', 'СЭ', 'Тип скважины'
    ]
    to_drop_2 = [
        'Р пл на ВДП', 'Дата запуска', 'Группа фонда', 'Дополнительное оборудование Диаметр', 
        'Дополнительное оборудование Глубина спуска', 'Режим работы УЭЦН Режим', 
        'Режим работы УЭЦН Дата установки режима', 'Номинальная производительность', 
        'Номинальный напор', 'Номинальный напор', 'Состояние на конец месяца',
        'Сравнение расчетов потенциала dQж при ГРП', 'Сравнение расчетов потенциала dQж при ГРП с корр',
        'Рзаб (геол огр индив)', 'Планируемый режим Q пг', 'ГФ', 'F', 'ГРП JD факт.',
        'Время до псевдоустановившегося режима', 'D э/к', 'D нкт', 'D шт', 
        'Содер-жание мех-примесей (КВЧ)'
    ]

    # Убираем символы переноса строки из заголовков
    data.columns = data.columns.str.replace(r'\n', ' ', regex=True)
    # Заменяем все, что не является цифрой, на пустую строку.
    # Добавляем infer_objects для сохранения прежнего поведения даункастинга.
    data = data.replace(r'[^0-9]', '', regex=True).infer_objects(copy=False)
    # Преобразуем все значения в числовой формат (при ошибке ставим NaN)
    data = data.apply(pd.to_numeric, errors='coerce')
    
    data = data.apply(pd.to_numeric, errors='coerce')

    well_column = "№ скв"
    # Группируем по скважинам и заполняем пропуски медианой по группе.
    # Если в группе нет значащих значений, оставляем без изменений, чтобы избежать предупреждения "Mean of empty slice".
    data.iloc[:, 1:] = data.groupby(well_column).transform(
        lambda x: x.fillna(x.median()) if x.count().all() > 0 else x
    )

    # Удаляем столбцы, указанные в списках
    data = data.drop(columns=(to_drop + to_drop_2))
    # Удаляем оставшиеся строки с пропусками
    data = data.dropna()

    # Вычисляем разности по группам (по скважинам) для столбцов "Р пл" и "Qтеор"
    data['P пл разность'] = data.groupby(well_column)['Р пл'].diff().fillna(0)
    data['Qтеор разность'] = data.groupby(well_column)['Qтеор'].diff().fillna(0)

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
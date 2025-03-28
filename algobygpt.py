import sqlite3
import os

def load_data(components_folder='components'):
    data = {}
    for db_file in os.listdir(components_folder):
        if db_file.endswith('.db'):
            component_type = db_file.split('.')[0]  # Извлекаем имя типа из имени файла
            db_path = os.path.join(components_folder, db_file)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Загружаем элементы
            cursor.execute("SELECT * FROM items")
            items = cursor.fetchall()

            # Загружаем характеристики
            cursor.execute("SELECT * FROM specifications")
            specs = cursor.fetchall()

            data[component_type] = {
                "items": items,
                "specifications": specs
            }

            conn.close()
    return data

components_data = load_data()
for component, data in components_data.items():
    print(f"{component.capitalize()}:")
    print("Items:", len(data["items"]))
    print("Specifications:", len(data["specifications"]))
    print("-" * 50)
print("Данные загружены:", components_data.keys())


def select_components(budget, weights, components_data):
    build = {}
    for component, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
        max_price = int(budget) * weight
        if component not in components_data:
            print(f"Данные для {component} не найдены!")
            continue
        print(f"Бюджет для {component}: {max_price}")


        # Поиск ближайшего по цене элемента
        items = components_data[component]["items"]
        closest_item = None
        closest_diff = float('inf')
        min_price_item = None
        min_price = float('inf')

        for item in items:
            item_id, manufacturer, model, href, price, image = item
            price_diff = abs(price - max_price)

            # Сохраняем элемент с минимальной ценой
            if price < min_price:
                min_price = price
                min_price_item = item

            # Проверяем совместимость временной сборки
            temp_build = build.copy()
            temp_build[component] = {
                "id": item_id,
                "manufacturer": manufacturer,
                "model": model,
                "href": href,
                "price": price,
                "image": image,
            }
            if (
                price <= max_price
                and price_diff < closest_diff
                and check_compatibility(temp_build, components_data)
            ):
                closest_item = item
                closest_diff = price_diff

        if closest_item:
            build[component] = {
                "id": closest_item[0],
                "manufacturer": closest_item[1],
                "model": closest_item[2],
                "href": closest_item[3],
                "price": closest_item[4],
                "image": closest_item[5],
            }
        else:
            print(f"Не удалось подобрать совместимый компонент для {component}!")

    return build

def select_ram_modules(mb_specs, ram_items, required_count):
    """
    Подбирает 2 или 4 модуля оперативной памяти в зависимости от требуемого количества.
    - mb_specs: спецификации материнской платы.
    - ram_items: список модулей оперативной памяти (из таблицы items).
    - required_count: требуемое количество модулей (2 или 4).
    """
    # Извлекаем количество слотов из спецификаций материнской платы
    slot_count = 0
    for mb_key, mb_value in mb_specs.items():
        if "память" in mb_key.lower() and "x" in mb_value:
            slot_count = int(mb_value.split("x")[0])  # Извлекаем количество слотов
            break

    if slot_count < required_count:
        print(f"Недостаточно слотов для {required_count} модулей: {slot_count} доступно.")
        return []

    # Выбираем модули, совместимые по типу памяти
    compatible_ram = []
    for ram_item in ram_items:
        _, _, ram_model, _, price, _ = ram_item
        for mem_type in ["DDR5", "DDR4", "DDR3", "DDR2"]:
            if mem_type in ram_model.upper():  # Совпадение типа памяти
                compatible_ram.append((ram_item, mem_type, price))

    # Проверяем, можно ли выбрать 2 или 4 модуля
    compatible_ram.sort(key=lambda x: x[2])  # Сортируем по цене
    if len(compatible_ram) >= required_count:
        selected_ram = compatible_ram[:required_count]  # Выбираем нужное количество
        return [ram[0] for ram in selected_ram]  # Возвращаем только модули

    print(f"Недостаточно совместимых модулей для {required_count} планок.")
    return []

def memory_compatible(mb_memory_value, ram_items):
    """
    Проверяет совместимость типов памяти между материнской платой и оперативной памятью.
    - mb_memory_value: строка, содержащая тип памяти материнской платы (например, "2x DDR4").
    - ram_items: список модулей оперативной памяти (из таблицы items).
    """
    # Извлекаем тип памяти из строки материнской платы
    mb_memory_type = None
    for mem_type in ["DDR5", "DDR4", "DDR3", "DDR2"]:
        if mem_type in mb_memory_value.upper():
            mb_memory_type = mem_type
            break

    if not mb_memory_type:
        return False  # Тип памяти на материнской плате не указан

    # Сопоставляем тип памяти оперативной памяти из модели
    for ram_item in ram_items:
        _, _, ram_model, _, _, _ = ram_item  # Извлекаем модель оперативной памяти
        for mem_type in ["DDR5", "DDR4", "DDR3", "DDR2"]:
            if mem_type in ram_model.upper():
                ram_memory_type = mem_type
                # Проверяем совместимость (новый тип памяти поддерживает старые)
                if mem_type_compatible(mb_memory_type, ram_memory_type):
                    return True

    return False


# Функция проверки иерархии типов памяти
def mem_type_compatible(mb_type, ram_type):
    """
    Определяет, совместимы ли типы памяти, учитывая, что более новые типы поддерживают более старые.
    """
    memory_hierarchy = ["DDR2", "DDR3", "DDR4", "DDR5"]  # От старого к новому
    return memory_hierarchy.index(mb_type) >= memory_hierarchy.index(ram_type)
# Правила совместимости
COMPATIBILITY_RULES = {
    "materinskie-platy": {
        "processory": lambda mb_specs, cpu_specs: any(
            "сокет" in mb_key.lower() and mb_value in cpu_value
            for mb_key, mb_value in mb_specs.items()
            for cpu_key, cpu_value in cpu_specs.items()
        ),
        "videokarty": lambda mb_specs, gpu_specs: any(
            "слоты" in mb_key.lower() and gpu_value in mb_value
            for mb_key, mb_value in mb_specs.items()
            for gpu_key, gpu_value in gpu_specs.items()
        ),
        "moduli-pamyati": lambda mb_specs, ram_items: (
            select_ram_modules(mb_specs, ram_items, required_count=2) or 
            select_ram_modules(mb_specs, ram_items, required_count=4)
        ),
        "ssd-nakopiteli": lambda mb_specs, ssd_specs: any(
            "разъемы" in mb_key.lower() and ssd_value in mb_value
            for mb_key, mb_value in mb_specs.items()
            for ssd_key, ssd_value in ssd_specs.items()
        ),
        "zhestkie-diski": lambda mb_specs, hdd_specs: any(
            "разъемы" in mb_key.lower() and hdd_value in mb_value
            for mb_key, mb_value in mb_specs.items()
            for hdd_key, hdd_value in hdd_specs.items()
        ),
    },
    "bloki-pitaniya": {
        "videokarty": lambda psu_specs, gpu_specs: any(
            "разъемы" in psu_key.lower() and "питание" in psu_value.lower() and "мощность" in psu_key.lower()
            and int(psu_value.split()[0]) >= int(gpu_specs.get("рекомендуемая мощность", 0))
            for psu_key, psu_value in psu_specs.items()
        ),
        "materinskie-platy": lambda psu_specs, mb_specs: any(
            "разъемы" in psu_key.lower() and "mb" in psu_value.lower()
            for psu_key, psu_value in psu_specs.items()
        ),
    },
    "videokarty": {
        "materinskie-platy": lambda gpu_specs, mb_specs: any(
            "слоты" in mb_key.lower() and gpu_value in mb_value
            for mb_key, mb_value in mb_specs.items()
            for gpu_key, gpu_value in gpu_specs.items()
        ),
        "bloki-pitaniya": lambda gpu_specs, psu_specs: any(
            "питание" in gpu_key.lower() and gpu_value in psu_specs.get("разъемы", "")
            for gpu_key, gpu_value in gpu_specs.items()
        ),
    },
    "moduli-pamyati": {
        "materinskie-platy": lambda ram_specs, mb_specs: memory_compatible(
            mb_specs.get("память", ""), [ram_specs]
        ),
    },
    "ssd-nakopiteli": {
        "materinskie-platy": lambda ssd_specs, mb_specs: any(
            "разъемы" in mb_key.lower() and ssd_value in mb_value
            for mb_key, mb_value in mb_specs.items()
            for ssd_key, ssd_value in ssd_specs.items()
        ),
    },
    "zhestkie-diski": {
        "materinskie-platy": lambda hdd_specs, mb_specs: any(
            "разъемы" in mb_key.lower() and hdd_value in mb_value
            for mb_key, mb_value in mb_specs.items()
            for hdd_key, hdd_value in hdd_specs.items()
        ),
    },
}

# Описание правил:
# 1. Материнская плата (materinskie-platy):
#    - Совместимость сокета с процессором.
#    - Совместимость слотов PCI-E для видеокарты.
#    - Совместимость разъемов SATA и M.2 для SSD и HDD.
#    - Совместимость типа и количества слотов памяти для ОЗУ.
#
# 2. Блок питания (bloki-pitaniya):
#    - Совместимость разъемов питания для материнской платы и видеокарты.
#    - Достаточная мощность для видеокарты и других компонентов.
#
# 3. Видеокарта (videokarty):
#    - Совместимость с разъемами PCI-E материнской платы.
#    - Совместимость с разъемами питания блока питания.
#
# 4. Оперативная память (moduli-pamyati):
#    - Совместимость типа памяти (DDR4, DDR5) с материнской платой.
#    - Соответствие количества модулей доступным слотам на материнской плате.
#
# 5. SSD и HDD (ssd-nakopiteli, zhestkie-diski):
#    - Совместимость разъемов SATA или M.2 с материнской платой.
#    - Поддержка интерфейса SATA III или NVMe на материнской плате.

# Основной алгоритм сборки учитывает все правила, проверяя каждую пару компонентов на совместимость.


def fetch_specifications(component_id, component_type, components_data):
    """
    Возвращает спецификации компонента в виде словаря.
    """
    specs = [
        (spec[1].lower(), spec[2].lower())
        for spec in components_data[component_type]["specifications"]
        if spec[0] == component_id
    ]
    return dict(specs)


def check_compatibility(build, components_data):
    """
    Проверяет совместимость компонентов сборки.
    """
    for component_type, details in build.items():
        component_id = details["id"]
        specs = fetch_specifications(component_id, component_type, components_data)

        for other_type, other_details in build.items():
            if component_type == other_type:
                continue

            other_id = other_details["id"]
            other_specs = fetch_specifications(other_id, other_type, components_data)

            # Применяем правила совместимости
            if component_type in COMPATIBILITY_RULES and other_type in COMPATIBILITY_RULES[component_type]:
                is_compatible = COMPATIBILITY_RULES[component_type][other_type](specs, other_specs)
                if not is_compatible:
                    print(f"Несовместимость: {component_type} с {other_type}")
                    return False

    return True


def calculate_weights(selected_goals, base_weights, goal_weights):
    """
    Вычисляет итоговые коэффициенты для всех компонентов на основе целей пользователя.
    """
    # Копируем базовые коэффициенты
    combined_weights = base_weights.copy()

    # Объединяем коэффициенты выбранных целей
    for goal in selected_goals:
        goal = goal.strip()  # Убираем лишние пробелы
        if goal in goal_weights:
            for component, weight in goal_weights[goal].items():
                combined_weights[component] = max(combined_weights.get(component, 0), weight)

    # Нормализуем коэффициенты, чтобы их сумма была равна 1
    total_weight = sum(combined_weights.values())
    if total_weight > 0:
        for component in combined_weights:
            combined_weights[component] /= total_weight

    return combined_weights


def main():
    # Базовые коэффициенты
    base_weights = {
        "processory": 0.2,
        "videokarty": 0.2,
        "materinskie-platy": 0.18,
        "moduli-pamyati": 0.05,
        "ssd-nakopiteli": 0.05,
        "bloki-pitaniya": 0.15
    }

    goal_weights = {
        "Gaming": {
            "processory": 0.2,
            "videokarty": 0.5,
            "materinskie-platy": 0.1,
            "moduli-pamyati": 0.2
        },
        "Office Work": {
            "processory": 0.3,
            "videokarty": 0.1,
            "materinskie-platy": 0.2,
            "moduli-pamyati": 0.3,
            "ssd-nakopiteli": 0.1
        },
        "Streaming": {
            "processory": 0.4,
            "videokarty": 0.3,
            "materinskie-platy": 0.1,
            "moduli-pamyati": 0.2
        },
        "Video Editing": {
            "processory": 0.35,
            "videokarty": 0.3,
            "materinskie-platy": 0.1,
            "moduli-pamyati": 0.15,
            "ssd-nakopiteli": 0.1
        },
        "3D Rendering": {
            "processory": 0.4,
            "videokarty": 0.4,
            "materinskie-platy": 0.1,
            "moduli-pamyati": 0.1
        },
        "Home Theater PC": {
            "processory": 0.25,
            "videokarty": 0.25,
            "materinskie-platy": 0.2,
            "moduli-pamyati": 0.2,
            "ssd-nakopiteli": 0.1
        },
        "Budget Build": {
            "processory": 0.2,
            "videokarty": 0.2,
            "materinskie-platy": 0.2,
            "moduli-pamyati": 0.2,
            "ssd-nakopiteli": 0.1,
            "bloki-pitaniya": 0.1
        },
        "Workstation": {
            "processory": 0.35,
            "videokarty": 0.25,
            "materinskie-platy": 0.15,
            "moduli-pamyati": 0.2,
            "ssd-nakopiteli": 0.05
        },
        "Casual Use": {
            "processory": 0.3,
            "videokarty": 0.1,
            "materinskie-platy": 0.25,
            "moduli-pamyati": 0.25,
            "ssd-nakopiteli": 0.1
        }
}


    budget = float(input("Введите бюджет на ПК: "))
    selected_goals = input("Выберите цели (через запятую): ").split(',')

    # Расчёт коэффициентов
    weights = calculate_weights(selected_goals, base_weights, goal_weights)
    print("Коэффициенты:", weights)

    # Подбор компонентов
    build = select_components(budget, weights, components_data)
    print("Предварительная сборка:", build)

    # Проверка совместимости
    if check_compatibility(build, components_data):
        print("Сборка совместима!")
    else:
        print("Сборка несовместима.")

main()
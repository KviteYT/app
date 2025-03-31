from flask import Flask, request, jsonify, render_template
import os
import sqlite3

app = Flask(__name__)

# Load data from database
def load_data(components_folder='components'):
    data = {}
    for db_file in os.listdir(components_folder):
        if db_file.endswith('.db'):
            component_type = db_file.split('.')[0]
            db_path = os.path.join(components_folder, db_file)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM items")
            items = cursor.fetchall()

            cursor.execute("SELECT * FROM specifications")
            specs = cursor.fetchall()

            data[component_type] = {
                "items": items,
                "specifications": specs
            }

            conn.close()
    return data

components_data = load_data()

@app.route('/')
def index():
    return render_template('index.html')

# Количество страниц с вопросами
TOTAL_PAGES = 5  

@app.route('/<int:num>')
def questions(num):
    if num < 1 or num > TOTAL_PAGES:
        return "Страница не найдена", 404
    
    return render_template(f'{num}.html', num=num, total_pages=TOTAL_PAGES)

@app.route('/build', methods=['POST'])
def build_pc():
    budget = float(request.json.get('budget', 0))  # Преобразуем бюджет в float
    selected_goals = request.json.get('goals', [])

    # Base and goal weights
    base_weights = {
        "processory": 0.2,
        "videokarty": 0.2,
        "materinskie-platy": 0.18,
        "moduli-pamyati": 0.05,
        "zhestkie-diski": 0.15,
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
            "processory": 0.4,
            "videokarty": 0.3,
            "materinskie-platy": 0.15,
            "moduli-pamyati": 0.15
        }
    }

    def calculate_weights(selected_goals, base_weights, goal_weights):
        combined_weights = base_weights.copy()
        for goal in selected_goals:
            if goal in goal_weights:
                for component, weight in goal_weights[goal].items():
                    combined_weights[component] = max(combined_weights.get(component, 0), weight)
        total_weight = sum(combined_weights.values())
        if total_weight > 0:
            for component in combined_weights:
                combined_weights[component] /= total_weight
        return combined_weights

    weights = calculate_weights(selected_goals, base_weights, goal_weights)

    def safe_check(func):
        def wrapper(*args, **kwargs):
            # Проверяем, что все аргументы существуют и не равны None
            if any(arg is None or not isinstance(arg, dict) or not arg for arg in args):
                return False
            return func(*args, **kwargs)
        return wrapper


    # Определение правил совместимости
    COMPATIBILITY_RULES = {
        "materinskie-platy": {
            "processory": safe_check(lambda mb_specs, cpu_specs: (
                cpu_specs.get("Сокет", "").strip().lower() == mb_specs.get("Сокет", "").strip().lower()
            )),
            "moduli-pamyati": safe_check(lambda mb_specs, ram_specs: (
                ram_specs.get("Объем", "").strip().lower() in mb_specs.get("Сокет", "").split(";")[0].strip().lower()
                and int(ram_specs.get("frequency", 0)) <= int(mb_specs.get("max_memory_frequency", 0))
            )),
            "videokarty": safe_check(lambda mb_specs, gpu_specs: (
                "pci-e" in mb_specs.get("слоты", "").lower() and
                any(version in mb_specs.get("слоты", "").lower() for version in ["3.0", "4.0"])
            )),
        },
        "bloki-pitaniya": {
            "videokarty": safe_check(lambda psu_specs, gpu_specs: int(psu_specs.get("power", 0)) >= int(gpu_specs.get("recommended_power", 0))),
            #"materinskie-platy": safe_check(lambda psu_specs, mb_specs: "24-pin" in psu_specs.get("connectors", "")),
        },
        "videokarty": {
            "materinskie-platy": safe_check(lambda gpu_specs, mb_specs: "PCI-E" in mb_specs.get("expansion_slots", "")),
            "bloki-pitaniya": safe_check(lambda gpu_specs, psu_specs: gpu_specs.get("power_connector") in psu_specs.get("connectors", "")),
        },
        "moduli-pamyati": {
            #"materinskie-platy": safe_check(lambda ram_specs, mb_specs: ram_specs.get("type") in mb_specs.get("supported_memory_types", "")),
        }
    }

    def fetch_specifications(component_id, component_type, components_data):
        specs = [
            (spec[1].lower(), spec[2].lower())
            for spec in components_data.get(component_type, {}).get("specifications", [])
            if spec[0] == component_id
        ]
        return dict(specs) if specs else {}

    # Обновленная функция select_components
    def select_components(budget, weights, components_data):
        build = {}
        errors = []  # Список ошибок

        for component, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
            max_price = budget * weight
            #print(f"Подбираем компонент: {component}, с бюджетом: {max_price}")  # Диагностика

            if component not in components_data:
                errors.append(f"Данные для {component} не найдены!")
                continue

            items = components_data[component]["items"]
            closest_item = None
            closest_diff = float('inf')

            for item in items:
                item_id, manufacturer, model, href, price, image = item
                #print(f"Проверяем {component} {model} с ценой {price}")  # Диагностика

                price_diff = abs(price - max_price)

                # Проверка совместимости временной сборки
                temp_build = build.copy()
                temp_build[component] = {
                    "id": item_id,
                    "manufacturer": manufacturer,
                    "model": model,
                    "href": href,
                    "price": price,
                    "image": image,
                }

                # Проверяем совместимость со всеми уже выбранными компонентами
                compatible = True
                for other_component, details in temp_build.items():
                    if other_component == component:
                        continue

                    # Получаем спецификации
                    other_specs = fetch_specifications(details["id"], other_component, components_data)
                    specs = fetch_specifications(item_id, component, components_data)

                    #print(f"Сравниваем {component} с {other_component}")  # Диагностика
                    #print(f"{component} спецификации: {specs}")  # Диагностика
                    #print(f"{other_component} спецификации: {other_specs}")  # Диагностика

                    # Применяем правила совместимости
                    if (
                        other_component in COMPATIBILITY_RULES.get(component, {}) and
                        not COMPATIBILITY_RULES[component][other_component](specs, other_specs)
                    ):
                        compatible = False
                        if not COMPATIBILITY_RULES[component][other_component](specs, other_specs):
                            print(f"Несовместимость {component} с {other_component}:")
                            print(f"{component} спецификации: {specs}")
                            print(f"{other_component} спецификации: {other_specs}")
                        break

                if compatible and price <= max_price and price_diff < closest_diff:
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
                errors.append(f"Не удалось найти подходящий компонент для {component}. Пожалуйста, измените бюджет или цели.")

        print(f"Сборка завершена: {build}")  # Диагностика
        print(f"Ошибки: {errors}")  # Диагностика
        return {"components": build, "errors": errors}

    build = select_components(budget, weights, components_data)
    return jsonify(build)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Render автоматически задает PORT
    app.run(host="0.0.0.0", port=port)
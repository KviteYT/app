from flask import Flask, render_template, request, jsonify
import json

app = Flask(__name__)

# Загружаем данные о комплектующих из JSON файла
with open("components.json", "r", encoding="utf-8") as f:
    components = json.load(f)

# Список возможных применений для компьютера
applications = ["Игры", "Работа", "Программирование", "Видеомонтаж", "3D моделирование"]

# Список возможных уровней производительности
performance_levels = ["Низкий", "Средний", "Высокий", "Максимальный"]

# Функция для проверки совместимости комплектующих
def is_compatible(selected_components):
    # Проверка совместимости процессора, материнской платы и оперативной памяти
    cpu_socket = selected_components["cpu"]["socket"]
    motherboard_socket = selected_components["motherboard"]["socket"]
    if cpu_socket != motherboard_socket:
        return False

    # Проверка совместимости материнской платы и видеокарты
    motherboard_pci_e = selected_components["motherboard"]["pci_e"]
    gpu_pci_e = selected_components["gpu"]["pci_e"]
    if motherboard_pci_e != gpu_pci_e:
        return False

    # Проверка совместимости материнской платы и блока питания
    motherboard_power_connector = selected_components["motherboard"]["power_connector"]
    psu_connectors = selected_components["psu"]["connectors"]
    if motherboard_power_connector not in psu_connectors:
        return False

    return True

# Функция для подбора комплектующих
def select_components(budget, application, performance_level):
    selected_components = {}
    remaining_budget = budget

    # Процессор
    for cpu in components["cpu"]:
        if cpu["application"] == application and cpu["performance_level"] == performance_level and cpu["price"] <= remaining_budget:
            selected_components["cpu"] = cpu
            remaining_budget -= cpu["price"]
            break

    # Обработка случая, когда процессор не был найден
    if "cpu" not in selected_components:
        selected_components["cpu"] = {"name": "Процессор не найден", "price": 0, "socket": "N/A"}  # Добавлен ключ "socket"
    
    # Материнская плата
    for motherboard in components["motherboard"]:
        if motherboard["socket"] == selected_components["cpu"]["socket"] and motherboard["price"] <= remaining_budget:
            selected_components["motherboard"] = motherboard
            remaining_budget -= motherboard["price"]
            break  # Выходим из цикла, если материнская плата найдена

    # Обработка случая, когда материнская плата не была найдена
    if "motherboard" not in selected_components:
        selected_components["motherboard"] = {"name": "Материнская плата не найдена", "price": 0, "socket": "N/A", "power_connector": "N/A", "pci_e": "N/A"}  # Добавлен ключ "pci_e"] = {"name": "Материнская плата не найдена", "price": 0, "socket": "N/A", "power_connector": "N/A"}  # Добавлен ключ "socket"

    # Оперативная память
    for ram in components["ram"]:
        if ram["performance_level"] == performance_level and ram["price"] <= remaining_budget:
            selected_components["ram"] = ram
            remaining_budget -= ram["price"]
            break

    # Видеокарта
    for gpu in components["gpu"]:
        if gpu["application"] == application and gpu["performance_level"] == performance_level and gpu["price"] <= remaining_budget:
            selected_components["gpu"] = gpu
            remaining_budget -= gpu["price"]
            break  # Выходим из цикла, если видеокарта найдена

    # Обработка случая, когда видеокарта не была найдена
    if "gpu" not in selected_components:
        selected_components["gpu"] = {"name": "Видеокарта не найдена", "price": 0, "pci_e": "N/A"}  # Добавлен ключ "pci_e"

    # Хранилище
    for storage in components["storage"]:
        if storage["application"] == application and storage["performance_level"] == performance_level and storage["price"] <= remaining_budget:
            selected_components["storage"] = storage
            remaining_budget -= storage["price"]
            break

    # Блок питания
    for psu in components["psu"]:
        if psu["power_connector"] == selected_components["motherboard"]["power_connector"] and psu["price"] <= remaining_budget:
            selected_components["psu"] = psu
            remaining_budget -= psu["price"]
            break
    
    # Обработка случая, когда видеокарта не была найдена
    if "gpu" not in selected_components:
        selected_components["gpu"] = {"name": "Видеокарта не найдена", "price": 0}

    return selected_components

# Главная страница
@app.route("/")
def index():
    return render_template("index.html", applications=applications, performance_levels=performance_levels)

# Обработка формы
@app.route("/select", methods=["POST"])
def select():
    budget = int(request.form["budget"])
    application = request.form["application"]
    performance_level = request.form["performance_level"]

    selected_components = select_components(budget, application, performance_level)

    if is_compatible(selected_components):
        return jsonify(selected_components)
    else:
        return jsonify({"error": "Несовместимые комплектующие"})

if __name__ == "__main__":
    app.run(debug=True)
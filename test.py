from selenium import webdriver
from bs4 import BeautifulSoup
from requests import get
from time import sleep
import sqlite3
import re


def main(curl):
    def parc():
        TIMER = 25
        names = []
        hrefs = []
        models = []
        prices = []
        images = []

        driver = webdriver.Chrome()
        driver.get(url=f'https://www.citilink.ru/catalog/{curl}/?p=1')
        sleep(TIMER)
        content = BeautifulSoup(driver.page_source, "html.parser")
        pages = int(content.find_all(
            "div", {"class": "app-catalog-1ck5rca ero1s990"})[-1].text)
        # pages = 1

        for page in range(1, pages + 1):
            driver.get(url=f'https://www.citilink.ru/catalog/{curl}/?p={page}')
            sleep(TIMER)
            content = BeautifulSoup(driver.page_source, "html.parser").find(
                'div', {'class': "ehanbgo0 app-catalog-1w7tb29 e1loosed0"})
            for name in content.find_all("a", {"class": "app-catalog-9gnskf e1259i3g0"}):
                names.append(name.text)
                hrefs.append(name.get('href'))
            for model1 in content.find_all("ul", {"class": "app-catalog-14f68kq e4qu3683"}):
                models_inner = []
                for model in model1.find_all("li", {"class": "app-catalog-12y5psc e4qu3682"}):
                    models_inner.append(model.text)
                models.append(models_inner)
            for price in content.find_all("span", {"class": "e1j9birj0 e106ikdt0 app-catalog-p2oaao e1gjr6xo0"}):
                prices.append(price.text)
            for img in [img for img in content.find_all("img", {'class': 'ekkbt9g0 app-catalog-15kpwh2 e1fcwjnh0'}) + content.find_all(
                "img", {'class': 'emd6ru10 app-catalog-1ljntpj e1fcwjnh0 is-selected'})]:
                images.append(img.get('src'))
        driver.close()
        driver.quit()
        print(len(images), len(hrefs), len(models), len(prices), len(images))
        return names, hrefs, models, prices, images

    def load_data(names, hrefs, models, prices, images):
        """Загружает данные процессоров в базу данных SQLite, обрабатывая различные ошибки."""
        conn = sqlite3.connect(f'components\\{curl}.db')
        cursor = conn.cursor()

        # Удаляем существующие таблицы (если они есть)
        cursor.execute("DROP TABLE IF EXISTS processors")
        cursor.execute("DROP TABLE IF EXISTS specifications")

        try:
            # Создание таблиц (убедитесь, что типы данных соответствуют вашим данным)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processors (
                    processor_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    manufacturer TEXT,
                    model TEXT,
                    package_type TEXT,
                    href TEXT,
                    price INTEGER,
                    image TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS specifications (
                    spec_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    processor_id INTEGER,
                    key TEXT,
                    value TEXT,
                    FOREIGN KEY (processor_id) REFERENCES processors(processor_id)
                )
            ''')
            conn.commit()

            for i, name in enumerate(names):
                try:
                    # Обработка потенциально отсутствующих данных
                    price_str = prices[i] if i < len(prices) else None
                    image = images[i] if i < len(images) else None
                    href = hrefs[i] if i < len(hrefs) else None

                    # Разбор информации о процессоре (добавьте обработку ошибок, если нужно)
                    match = re.match(r'Процессор (.*?) (.*?), (.*)', name)
                    if match:
                        manufacturer = match.group(1).strip()
                        model = match.group(2).strip()
                        package_type = match.group(3).strip()
                    else:
                        print(
                            f"Не удалось разобрать информацию о процессоре: {name}")
                        continue

                    # Обработка цены - удаляем все нецифровые символы
                    price = int(re.sub(r'\D', '', price_str)
                                ) if price_str else None

                    cursor.execute("""
                        INSERT INTO processors (manufacturer, model, package_type, href, price, image) 
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (manufacturer, model, package_type, href, price, image))
                    processor_id = cursor.lastrowid

                    # Обработка характеристик
                    if models and i < len(models):
                        for spec in models[i]:
                            key_value = re.split(r'\xa0', spec, 1)
                            key = key_value[0].strip()
                            value = key_value[1].strip() if len(
                                key_value) > 1 else ''
                            cursor.execute("""
                                INSERT INTO specifications (processor_id, key, value) 
                                VALUES (?, ?, ?)
                            """, (processor_id, key, value))

                except sqlite3.IntegrityError as e:
                    print(
                        f"Ошибка целостности данных для процессора {name}: {e}")
                except ValueError as e:
                    print(
                        f"Ошибка преобразования данных для процессора {name}: {e}")
                except IndexError as e:
                    print(f"Ошибка индексации для процессора {name}: {e}")
                except Exception as e:
                    print(
                        f"Произошла неизвестная ошибка для процессора {name}: {e}")
                    import traceback
                    traceback.print_exc()

            conn.commit()
        except sqlite3.Error as e:
            print(f"Ошибка базы данных: {e}")
        finally:
            conn.close()
    names, hrefs, models, prices, images = parc()
    load_data(names, hrefs, models, prices, images)

# ... (ваш код парсинга) ...
main('materinskie-platy')

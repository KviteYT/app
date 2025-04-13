from selenium import webdriver
from bs4 import BeautifulSoup
from requests import get
from time import sleep
import sqlite3
import re


def main(curl):
    def parc():
        TIMER = 1
        names = []
        hrefs = []
        models = []
        prices = []
        images = []

        driver = webdriver.Chrome()
        driver.get(
            url=f'https://www.citilink.ru/catalog/{curl}/?view_type=list&sorting=price_asc&p=1')
        sleep(TIMER)
        content = BeautifulSoup(driver.page_source, "html.parser")
        pages = int(content.find_all(
            "div", {"class": "app-catalog-10181fg-ElementWrapper--ElementWrapper evbl9mj0"})[-1].text)
        print(pages)

        for page in range(1, pages + 1):
            driver.get(
                url=f'https://www.citilink.ru/catalog/{curl}/?view_type=list&sorting=price_asc&p={page}')
            sleep(TIMER)
            content = BeautifulSoup(driver.page_source, "html.parser").find(
                'div', {'class': "e13x19s60 app-catalog-1bvrslt-StyledGridItem--StyledGridItem-composeBreakpointsStyles--arrayOfStylesByBreakpoints-composeBreakpointsStyles--arrayOfStylesByBreakpoints-GridItem--WrappedGridItem e1uawgvp0"})
            for name in content.find_all("a", {"class": "app-catalog-1g0fl7h-Anchor--Anchor-Anchor--StyledAnchor ejir1360"}):
                names.append(name.text)
                hrefs.append(name.get('href'))
            for model1 in content.find_all("ul", {"class": "app-catalog-1u2u8dc-components--Properties-composeBreakpointsStyles--arrayOfStylesByBreakpoints-getTypographyStyles--getTypographyStyles ekqg32y0"}):
                models_inner = []
                for model in model1.find_all("li", {"class": "app-catalog-5kkfdq-components--PropertiesItem ekqg32y1"}):
                    models_inner.append(model.text)
                models.append(models_inner)
            for price in content.find_all("span", {"class": "e4ahr150 e1a7a4n70 app-catalog-1dno20p-StyledTypography--getTypographyStyle-composeBreakpointsStyles--arrayOfStylesByBreakpoints-StyledText--getTextStyle-Text--StyledTextComponent-MainPriceNumber--StyledMainPriceNumber ez8h4tf0"}):
                prices.append(price.text)
            for img in [img for img in content.find_all("img", {'class': 'eikooao0 app-catalog-1uk1s5v-Img--StyledImg-Img--StyledImg-StyledImage ed4p12j0 is-selected'})]:
                images.append(img.get('src'))
        driver.close()
        driver.quit()
        print(len(images), len(hrefs), len(models), len(prices), len(images))
        return names, hrefs, models, prices, images

    def load_data(names, hrefs, models, prices, images):
        """Загружает данные в базу данных SQLite, обрабатывая различные ошибки."""
        conn = sqlite3.connect(f'components\\{curl}.db')
        cursor = conn.cursor()

        # Удаляем существующие таблицы (если они есть)
        cursor.execute("DROP TABLE IF EXISTS items")
        cursor.execute("DROP TABLE IF EXISTS specifications")

        try:
            # Создание таблиц (убедитесь, что типы данных соответствуют вашим данным)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    manufacturer TEXT,
                    model TEXT,
                    href TEXT,
                    price INTEGER,
                    image TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS specifications (
                    id INTEGER,
                    key TEXT,
                    value TEXT,
                    FOREIGN KEY (id) REFERENCES шеуьы(id)
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
                    name = name.replace('SSD', 'ССД', 1)
                    match = re.match(r'(\b[а-яА-Я]+\b\s*)+(.*?) (.*)', name)
                    if match:
                        manufacturer = match.group(2).strip()
                        model = match.group(3).strip()
                    else:
                        print(
                            f"Не удалось разобрать информацию о {name}")
                        continue

                    # Обработка цены - удаляем все нецифровые символы
                    price = int(re.sub(r'\D', '', price_str)
                                ) if price_str else None

                    cursor.execute("""
                        INSERT INTO items (manufacturer, model, href, price, image) 
                        VALUES (?, ?, ?, ?, ?)
                    """, (manufacturer, model, href, price, image))
                    id = cursor.lastrowid

                    # Обработка характеристик
                    if models and i < len(models):
                        for spec in models[i]:
                            key_value = re.split(r'\xa0', spec, 1)
                            key = key_value[0].strip()
                            value = key_value[1].strip() if len(
                                key_value) > 1 else ''
                            cursor.execute("""
                                INSERT INTO specifications (id, key, value) 
                                VALUES (?, ?, ?)
                            """, (id, key, value))

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
# main('processory')
# main('materinskie-platy')
# main('moduli-pamyati')
# main('bloki-pitaniya')
# main('videokarty')
# main('zhestkie-diski')
# main('ssd-nakopiteli')
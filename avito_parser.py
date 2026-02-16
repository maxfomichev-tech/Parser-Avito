from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import re

def setup_driver():
    """Настройка Chrome с маскировкой"""
    options = Options()
    
    options.add_argument("--incognito")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=options)
    
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        '''
    })
    
    return driver

def human_like_delay(min_sec=1, max_sec=3):
    time.sleep(random.uniform(min_sec, max_sec))

def scroll_like_human(driver):
    for i in range(3):
        driver.execute_script(f"window.scrollBy(0, {random.randint(300, 700)});")
        human_like_delay(0.5, 1.5)

def check_for_captcha(driver):
    """Умная проверка на капчу - ищем элементы капчи, а не просто текст"""
    try:
        # Проверяем наличие элементов капчи
        captcha_selectors = [
            "[data-marker='captcha']",
            ".captcha",
            "#captcha",
            "[class*='captcha']",
            "[id*='captcha']",
            "iframe[src*='captcha']",
            "img[src*='captcha']",
            "[data-testid='captcha']"
        ]
        
        for selector in captcha_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements and any(el.is_displayed() for el in elements):
                return True
        
        # Проверяем URL на редирект капчи
        current_url = driver.current_url
        if any(x in current_url for x in ['captcha', 'check', 'verify', 'secure']):
            return True
            
        # Проверяем title страницы
        title = driver.title.lower()
        if any(x in title for x in ['капча', 'captcha', 'проверка', 'подтвердите']):
            return True
            
        return False
        
    except:
        return False

def parse_avito_selenium(search_query, max_items=20):
    driver = None
    try:
        print("🚀 Запускаем Chrome...")
        driver = setup_driver()
        
        print("⏳ Заходим на Авито...")
        driver.get("https://www.avito.ru/")
        human_like_delay(3, 5)
        
        # Ищем поисковую строку
        search_input = None
        selectors = [
            "[data-marker='search-form/suggest/input']",
            "[data-marker='search-form/suggest']",
            "input[type='search']",
            "input[placeholder*='Найти']",
            "input[placeholder*='Поиск']",
            "[name='q']",
            "input[data-marker*='search']"
        ]
        
        for selector in selectors:
            try:
                search_input = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                print(f"✅ Найдено поле ввода")
                break
            except:
                continue
        
        if not search_input:
            print("❌ Не удалось найти поле поиска")
            driver.save_screenshot("error_no_input.png")
            return None
        
        # Кликаем на поле ввода
        try:
            search_input.click()
        except:
            driver.execute_script("arguments[0].click();", search_input)
        
        human_like_delay(0.3, 0.6)
        
        # Вводим запрос по буквам
        print(f"⌨️  Вводим запрос: {search_query}")
        for char in search_query:
            search_input.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
        
        human_like_delay(0.5, 1)
        
        # Отправляем поиск
        print("⏳ Отправляем поиск...")
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            actions = ActionChains(driver)
            actions.move_to_element(search_input).send_keys(Keys.RETURN).perform()
        except:
            driver.execute_script("""
                var event = new KeyboardEvent('keydown', {
                    key: 'Enter',
                    code: 'Enter',
                    keyCode: 13,
                    which: 13,
                    bubbles: true
                });
                arguments[0].dispatchEvent(event);
            """, search_input)
        
        # Ждем загрузки результатов
        human_like_delay(4, 6)
        
        # Проверяем капчу через элементы, а не текст
        if check_for_captcha(driver):
            print("⚠️  Обнаружена капча!")
            input("Реши капчу в браузере и нажми Enter...")
        
        current_url = driver.current_url
        print(f"🌐 URL: {current_url}")
        
        # Скроллим для подгрузки
        scroll_like_human(driver)
        human_like_delay(2, 3)
        
        # Получаем HTML
        html = driver.page_source
        
        # Парсим
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.find_all('div', attrs={'data-marker': 'item'})
        
        if not items:
            items = soup.find_all('div', class_=lambda x: x and 'iva-item' in x if x else False)
        
        print(f"📦 Найдено: {len(items)} объявлений")
        
        results = []
        for item in items[:max_items]:
            try:
                title_elem = item.find('h3', attrs={'itemprop': 'name'}) or \
                           item.find('a', attrs={'data-marker': 'item-title'}) or \
                           item.find('a', class_=lambda x: x and 'title' in x if x else False)
                title = title_elem.get_text(strip=True) if title_elem else 'Нет названия'
                
                price_elem = item.find('meta', attrs={'itemprop': 'price'}) or \
                           item.find('span', attrs={'data-marker': 'item-price'}) or \
                           item.find('span', class_=lambda x: x and 'price' in x if x else False)
                
                if price_elem and price_elem.get('content'):
                    price = price_elem['content']
                elif price_elem:
                    price = price_elem.get_text(strip=True).replace('\xa0', ' ')
                else:
                    price = 'Цена не указана'
                
                link_elem = item.find('a', href=True)
                if link_elem:
                    href = link_elem['href']
                    link = f'https://www.avito.ru{href}' if href.startswith('/') else href
                else:
                    link = 'Нет ссылки'
                
                results.append({
                    'Название': title,
                    'Цена': price,
                    'Ссылка': link
                })
            except Exception:
                continue
        
        if not results:
            print("❌ Не удалось спарсить")
            return None
        
        df = pd.DataFrame(results)
        output_file = f'avito_{search_query.replace(" ", "_")[:20]}.xlsx'
        df.to_excel(output_file, index=False, engine='openpyxl')
        
        print(f"\n✅ Сохранено {len(results)} объявлений в: {output_file}")
        print(df.head().to_string())
        return df
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        if driver:
            driver.save_screenshot("error.png")
        return None
        
    finally:
        if driver:
            print("\n🛑 Закрываем браузер...")
            driver.quit()

if __name__ == "__main__":
    query = input("Введите поисковый запрос: ")
    parse_avito_selenium(query)
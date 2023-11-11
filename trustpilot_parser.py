from datetime import datetime
import requests
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials


# Путь к файлу сервисного аккаунта и необходимые разрешения
SERVICE_ACCOUNT_FILE = '/Users/sultankhan/Desktop/Тестовое/enhanced-oasis-404712-78a90a673727.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Аутентификация и создание сервиса для работы с Google Sheets
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)

# ID таблицы и диапазон, в который будут добавляться данные
SAMPLE_SPREADSHEET_ID = '1XR956JqX8dW2eNdt48jlT8DW_3G1pyVsvErkGiUGm0w'
SAMPLE_RANGE_NAME = 'Data!A2:I'


# Получаем текущую дату и время
current_time = datetime.now()

# Преобразуем в строку (например, в формате 'YYYY-MM-DD HH:MM:SS')
time_string = current_time.strftime('%Y-%m-%d %H:%M:%S')

def get_company_links(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    company_links = []
    for a_tag in soup.find_all('a', {'class': 'link_internal__7XN06'}):
        href = a_tag.get('href')
        if href and '/review/' in href:
            full_url = 'https://www.trustpilot.com' + href
            company_links.append(full_url)


    return company_links

all_links = []
for page in range(1, 10):  # Для страниц с 1 по 9
    page_url = f'https://www.trustpilot.com/categories/search_engine?page={page}'
    all_links.extend(get_company_links(page_url))

all_links = list(set(all_links))  # Удаление дубликатов из списка

# Вывод списка без дубликатов
#counter = 1
#for link in all_links:
#    print(f"{counter}. {link}")
#    counter += 1

def parse_company_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Инициализация значений по умолчанию
    total_rating = 'Нет данных'
    total_reviews = 'Нет данных'
    star_ratings = {i: 'Нет данных' for i in range(1, 6)}

    # Парсинг общего рейтинга
    rating_element = soup.find('h2', {'class': 'typography_heading-m__T_L_X'})
    if rating_element and rating_element.find('span'):
        total_rating = rating_element.find('span').text

    # Парсинг общего количества отзывов
    reviews_element = soup.find('p', {'data-reviews-count-typography': 'true'})
    if reviews_element:
        total_reviews = reviews_element.text.split()[0].replace(',', '')


    # Парсинг процентного соотношения оценок по звездам
    star_labels = soup.find_all('label', {'class': 'styles_row__wvn4i'})
    for label in star_labels:
        star_percentage = label.find('p', {'class': 'styles_percentageCell__cHAnb'})
        if star_percentage:
            star_value = label.get('data-star-rating')
            if star_value in ['one', 'two', 'three', 'four', 'five']:
                star_index = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5}[star_value]
                star_ratings[star_index] = star_percentage.text.strip('%')

    return {
        "url": url,
        "total_rating": total_rating,
        "total_reviews": total_reviews,
        "star_ratings": star_ratings
    }

company_data = []
for link in all_links:
    try:
        data = parse_company_page(link)
        company_data.append(data)
        print(data)  # Вывод информации о каждой компании
    except Exception as e:
        print(f"Ошибка при обработке {link}: {e}")

# Запись данных в таблицу
def write_to_sheet(company_data):
    values = [[
        time_string,
        data['url'],
        data['total_rating'],
        data['total_reviews'],
        data['star_ratings'][1] if 1 in data['star_ratings'] else '0%',
        data['star_ratings'][2] if 2 in data['star_ratings'] else '0%',
        data['star_ratings'][3] if 3 in data['star_ratings'] else '0%',
        data['star_ratings'][4] if 4 in data['star_ratings'] else '0%',
        data['star_ratings'][5] if 5 in data['star_ratings'] else '0%'
    ] for data in company_data]
    body = {'values': values}
    result = service.spreadsheets().values().append(
        spreadsheetId=SAMPLE_SPREADSHEET_ID,
        range=SAMPLE_RANGE_NAME,
        valueInputOption='USER_ENTERED',
        body=body).execute()
    print('{0} cells appended.'.format(result.get('updates').get('updatedCells')))

# Главная функция
def main():
    all_links = get_company_links('https://www.trustpilot.com/categories/search_engine')
    company_data = [parse_company_page(link) for link in all_links]
    write_to_sheet(company_data)

# Запуск главной функции
if __name__ == '__main__':
    main()



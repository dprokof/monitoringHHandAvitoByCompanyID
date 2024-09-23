import time
import datetime

import gspread
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By

from multiprocessing import Pool


def create_driver():
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    # options.add_argument('--disable-extensions')
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36")
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=options)

    return driver


def get_data_avito(vacancy_url):
    gc = gspread.service_account(filename='../monitoringHHandAvitoByCompanyID/key.json')
    driver = create_driver()
    driver.get(vacancy_url)
    time.sleep(1.5)
    data = []
    ### Дата и время запроса
    current_date = datetime.datetime.now().strftime('%d-%m-%Y')
    dt = datetime.datetime.now()
    current_time = f"{dt.hour}:{dt.minute}"
    ###
    vacancy_id = driver.find_element(by=By.XPATH,
                                     value='//*[@id="app"]/div/div[3]/div[1]/div/div[2]/div[3]/div/div[1]/div[2]/div[4]/div/article/p/span[1]').text
    vacancy_published = driver.find_element(by=By.XPATH,
                                            value='//*[@id="app"]/div/div[3]/div[1]/div/div[2]/div[3]/div/div[1]/div[2]/div[4]/div/article/p/span[2]').text
    vacancy_total_view = driver.find_element(by=By.XPATH,
                                             value='//*[@id="app"]/div/div[3]/div[1]/div/div[2]/div[3]/div/div[1]/div[2]/div[4]/div/article/p/span[3]/span[1]').text
    vacancy_today_view = driver.find_element(by=By.XPATH,
                                             value='//*[@id="app"]/div/div[3]/div[1]/div/div[2]/div[3]/div/div[1]/div[2]/div[4]/div/article/p/span[3]/span[2]').text
    vacancy_name = driver.find_element(by=By.XPATH,
                                       value='/html/body/div[1]/div/div[3]/div[1]/div/div[2]/div[3]/div/div[1]/div[1]/div/div[1]/h1').text
    vacancy_place = driver.find_element(by=By.XPATH,
                                        value='/html/body/div[1]/div/div[3]/div[1]/div/div[2]/div[3]/div/div[1]/div[2]/div[2]/div/div[1]/div[1]/div/span').text
    vacancy_salary = driver.find_element(by=By.XPATH,
                                         value='/html/body/div[1]/div/div[3]/div[1]/div/div[2]/div[3]/div/div[2]/div[1]/div/div/div[1]/div/div[1]/div/div/div/span/span/span[1]').text

    ### create dataframe
    data.append(current_date)
    data.append(current_time)
    data.append(vacancy_id)
    data.append(vacancy_name)
    data.append(vacancy_salary)
    data.append(vacancy_url)
    data.append(vacancy_place)
    data.append(company_name_avito)
    data.append(company_id_avito)
    data.append(vacancy_published)
    data.append(vacancy_total_view)
    data.append(vacancy_today_view)

    ### push data

    wks = gc.open("Вакансии").get_worksheet(4)
    wks.append_row(data)
    time.sleep(0.5)
    driver.quit()




def search_in_avito(company_id):
    driver = create_driver()
    driver.get(f'https://www.avito.ru/brands/{company_id}/items/all/vakansii')
    global company_name_avito

    company_name_avito = driver.find_element(by=By.XPATH, value='/html/body/div[1]/div/div[4]/div[1]/div/div/div[1]/div/section[1]/div/a/div[2]/h1').text

    global company_id_avito

    company_id_avito = company_id
    """
        Прокрутка страницы. Вычисляем высотку, скроллим вниз и смотрим, как изменилась высота.
        Скроллим пока высота не станет статичной
    """
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        # Прокрутка вниз
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # Пауза, пока загрузится страница.
        time.sleep(2)
        # Вычисляем новую высоту прокрутки и сравниваем с последней высотой прокрутки.
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    cards = driver.find_elements(by=By.CLASS_NAME, value='iva-item-root-_lk9K')
    urls = []
    for card in cards:
        vacancy_url = card.find_element(by=By.TAG_NAME, value='a').get_attribute('href')
        urls.append(vacancy_url)

    return urls



def search_in_hh(company_id):
    gc = gspread.service_account(filename='../monitoringHHandAvitoByCompanyID/key.json')
    vacancies_info = requests.get(f'https://api.hh.ru/vacancies?employer_id={company_id}', params={'per_page':'100'}).json()
    if vacancies_info['found'] == 0:
        print('На данный момент у компании активных вакансий!')
    else:
        pages = vacancies_info['pages']
        for page in range(pages + 1):
            vacancies_info = requests.get(f'https://api.hh.ru/vacancies?employer_id={company_id}', params={'per_page':'100', 'page': {page}}).json()
            for vacancy in vacancies_info['items']:
                data = []
                current_date = datetime.datetime.now().strftime('%d-%m-%Y')
                dt = datetime.datetime.now()
                current_time = f"{dt.hour}:{dt.minute}"
                vacancy_id = vacancy['id']
                vacancy_name = vacancy['name']
                if vacancy['salary'] is None:
                    vacancy_salary_from = "Не указано"
                    vacancy_salary_to = "Не указано"
                else:
                    vacancy_salary_from = vacancy['salary']['from']
                    vacancy_salary_to = vacancy['salary']['to']
                vacancy_url = vacancy['alternate_url']
                vacancy_area = vacancy['area']['name']
                employer_name = vacancy['employer']['name']
                employer_id = vacancy['employer']['id']
                vacancy_experience = vacancy['experience']['name']
                vacancy_published = vacancy['published_at']
                vacancy_published = datetime.datetime.strptime(vacancy_published, "%Y-%m-%dT%H:%M:%S%z")
                vacancy_published = vacancy_published.strftime('%Y-%m-%d %H:%M')

                #create dataframe
                data.append(current_date)
                data.append(current_time)
                data.append(vacancy_id)
                data.append(vacancy_name)
                data.append(vacancy_salary_from)
                data.append(vacancy_salary_to)
                data.append(vacancy_url)
                data.append(vacancy_area)
                data.append(employer_name)
                data.append(employer_id)
                data.append(vacancy_experience)
                data.append(vacancy_published)

                #push to google sheets
                wks = gc.open("Вакансии").get_worksheet(3)
                wks.append_row(data)
                time.sleep(0.5)


if __name__ == "__main__":
    place = int(input('Выберите площадку для поиска\n'
                      '1 - HH.ru\n'
                      '2 - Avito\n'
                      'Введите: '))
    company_id = input('Введите ID компании\n'
                       'Если компаний несколько - введите через пробел: ')
    if place == 1:
        company_id = company_id.split()
        p = Pool(processes=5)
        p.map(search_in_hh, company_id)
        print('Готово')

    else:
        company_id = company_id.split()
        p = Pool(processes=5)
        urls = p.map(search_in_avito, company_id)
        urls = [item for sublist in urls for item in sublist]

        p.map(get_data_avito, urls)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import re
import json
import time
import traceback
from pprint import pprint
from config import main_page


def overwriting():
    with open('data_files/temp_timetable.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    with open('data_files/timetable.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False)


def sec_block_format(string):
    date_pattern = r'\d{2}.\d{2}.\d{4}'
    type_pattern = r'\([ЛПРек]{2,3}\)'
    p_group_pattern = r'\d П\.Гр\.'

    date = re.findall(date_pattern, string)
    lesson_type = 0 if not re.findall(type_pattern, string) else re.findall(type_pattern, string)[0][1:-1]
    p_group = 0 if not re.findall(p_group_pattern, string) else re.findall(p_group_pattern, string)[0]

    return date, lesson_type, p_group


def fill_lesson(module):
    time_block = module[0].text

    info_block = module[1].text
    lesson_name = info_block.split('\n')[0]
    date, lesson_type, p_group = sec_block_format(info_block)

    place_block = module[2].text.split('\n')  # кабинет и корпус
    cabinet = place_block[0]
    building = place_block[1][1:-1]
    if 'Талалихина' in building:
        building = f'Талалихина корпус {building[-1]}'

    teacher = 0 if not module[3].text else module[3].text.split('\n')

    lesson = {"name": lesson_name,
              "time": time_block,
              "date": date,
              "type": lesson_type,
              "cabinet": cabinet,
              "building": building,
              "p_group": p_group,
              "teacher": teacher}
    return lesson


def fill_special_lesson(block):
    date_info = block[0].text

    date = re.findall(r'\d{2}.\d{2}.\d{4}', date_info)
    date[0] = date[0][0:2] + '.' + date[0][3:5] + '.' + date[0][6:]

    day_name = date_info.split('\n')[-1].strip()
    day_name = day_name[0].upper() + day_name[1:]

    time_block = block[1].text

    lesson_name = block[2].text.split('\n')[0]

    place_block = block[3].text.split('\n')  # кабинет и корпус
    cabinet = place_block[0]
    building = place_block[1][1:-1]
    if 'Талалихина' in building:
        building = f'Талалихина корпус {building[-1]}'

    lesson = {"name": lesson_name,
              "time": time_block,
              "date": date,
              "type": 0,
              "cabinet": cabinet,
              "building": building,
              "p_group": 0,
              "teacher": 0}
    return day_name, lesson


def parsing(module, check_test=None):
    week = {}
    group_name = module.find_element(By.TAG_NAME, 'p').text
    group_name = group_name[16:(group_name.find('Направление') - 1)].lower()

    day_list = module.find_elements(By.TAG_NAME, 'h2')  # находим все заголовки
    day_lessons = module.find_elements(By.CLASS_NAME, 'table-responsive')  # находим все отдельные таблицы
    for i in range(len(day_list)):
        day = []
        day_name = day_list[i].text

        lesson_line = day_lessons[i].find_elements(By.TAG_NAME, 'tr')
        for line in range(1, len(lesson_line)):
            block = lesson_line[line].find_elements(By.TAG_NAME, 'td')
            day.append(fill_lesson(block))

        week[day_name] = day

    if len(day_list) < len(day_lessons):
        lesson_line = day_lessons[-1].find_elements(By.TAG_NAME, 'tr')
        for line in range(1, len(lesson_line)):
            block = lesson_line[line].find_elements(By.TAG_NAME, 'td')
            if len(block) == 4:
                continue
            day_name, lesson = fill_special_lesson(block)

            if day_name in week.keys():
                day = week[day_name]
                day.append(lesson)
            else:
                week[day_name] = [lesson]
    if check_test:
        pprint(week)
        return
    with open('data_files/temp_timetable.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    data[group_name] = week
    with open('data_files/temp_timetable.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False)
    return


def go_to_links(links, driver):
    url = 'https://mgupp.ru/obuchayushchimsya/raspisanie/GetShedule.php?MyRes='
    for i in links:
        driver.get(url + i)  # переход на страницу расписания группы

        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "content-tab1")))
        timetable = driver.find_element(By.ID, "content-tab1")  # взять расписание
        text = timetable.text

        if not text:
            continue

        parsing(timetable)
        print(text[16:(text.find('Направление') - 1)])  # логи
    return


def get_links(site):
    service = Service(executable_path=ChromeDriverManager().install())
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_prefs = {}
    chrome_options.experimental_options["prefs"] = chrome_prefs
    chrome_prefs["profile.default_content_settings"] = {"images": 2}
    driver = webdriver.Chrome(options=chrome_options, service=service)

    try:
        driver.get(site)  # открытие сайта
        print('get site')

        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, 'panel')))
        institute = driver.find_elements(By.CLASS_NAME, 'panel')  # найти все раскрывающиеся вкладки

        for i in range(0, len(institute), 2):  # открытие вкладок
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(institute[i]))
            institute[i].click()
        print('open tabs')
        time.sleep(3)

        groups = driver.find_elements(By.CLASS_NAME, "GroupConteiner")
        group_link = []
        for group in groups:
            group_link.append(group.get_attribute("value"))

        print(len(group_link))

        go_to_links(group_link, driver)
    except Exception as expt:
        print(expt)
        print(traceback.format_exc())
    finally:
        driver.quit()  # закрыть драйвер


def test():
    service = Service(executable_path=ChromeDriverManager().install())
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_prefs = {}
    chrome_options.experimental_options["prefs"] = chrome_prefs
    chrome_prefs["profile.default_content_settings"] = {"images": 2}
    driver = webdriver.Chrome(options=chrome_options, service=service)
    try:
        site = 'https://mgupp.ru/obuchayushchimsya/raspisanie/GetShedule.php?MyRes=0x8' \
               '0F1000C299AE95F11EACE56F24DAE31_0x80F1000C299AE95F11EAF106441DF5BF_0x80C4000C299AE95511E6FFDE22A08A7D'
        driver.get(site)

        timetable = driver.find_element(By.ID, "content-tab1")
        parsing(timetable, check_test=True)
    except Exception as expt:
        print(expt)
        print(traceback.format_exc())
    finally:
        driver.quit()
    return


if __name__ == '__main__':
    while True:
        try:
            start = time.time()

            get_links(main_page)
            overwriting()

            end = time.time()
            print('-' * 50 + f'\n{((end - start) // 60): 0} мин {((end - start) % 60): 0} сек\n' + '-' * 50)

            sleep_time = (23 * 60 + 40) * 60  # 23:45 in sec
            time.sleep(sleep_time)
        except Exception as e:
            print(e)
            print(traceback.format_exc())
# test()

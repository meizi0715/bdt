import os
import re
import smtplib
import time
from collections import defaultdict
from email.mime.text import MIMEText
import jpholiday
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.chrome.options import Options
from datetime import datetime, timedelta

def select_facility(code1: str, code2: str, code3: str, driver: WebDriver):
    # code1:バトミントン（体育施設用 or 公民館等）
    # code2+code3:体育施設用 or 公民館

    #
    # 打开网页
    driver.get(os.getenv("TARGET_LINK"))
    WebDriverWait(driver, 10).until(
        ec.frame_to_be_available_and_switch_to_it((By.NAME, "MainFrame")))  # 等待 frame 加载并切换进去

    #
    # 目的
    button = WebDriverWait(driver, 10).until(
        ec.element_to_be_clickable((By.XPATH, '//input[@type="image" and @alt="目的"]'))
    )
    button.click()

    #
    # バトミントン（体育施設用 or 公民館等）
    xpath1 = f'//input[@type="checkbox" and @name="chk_bunrui1_{code1}"]'
    checkbox = WebDriverWait(driver, 10).until(
        ec.element_to_be_clickable((By.XPATH, xpath1))
    )
    checkbox.click()

    #
    # 所在地を指定せずに検索
    button = WebDriverWait(driver, 10).until(
        ec.element_to_be_clickable((By.XPATH, '//input[@type="image" and @alt="所在地を指定せずに検索"]'))
    )
    button.click()

    #
    # センター / 公民館
    xpath = f"//input[@type='image' and contains(@onclick, \"cmdYoyaku_click('{code2}','{code3}')\")]"
    button = WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, xpath))
    )
    driver.execute_script("arguments[0].click();", button)

    #
    # 2週間表示
    radio = WebDriverWait(driver, 10).until(
        ec.element_to_be_clickable((By.XPATH, '//input[@type="radio" and @name="disp_mode"]'))
    )
    radio.click()

    #
    # 弹窗
    WebDriverWait(driver, 10).until(ec.alert_is_present())  # 等待弹窗出现
    alert = Alert(driver)  # 切换到弹窗
    alert.accept()
    time.sleep(4)

#
# 判断是否是周末或祝日
def is_weekend_or_holiday(date: datetime.date) -> bool:
    if date.weekday() >= 5:  # 5=土曜, 6=日曜
        return True
    if jpholiday.is_holiday(date):  # 祝日
        return True
    return False

def get_date_time(date_to_times, driver, old_html):

    # 等待图标表格加载完成
    WebDriverWait(driver, 15).until(
        lambda d: d.find_element(By.CLASS_NAME, "clsKoma").get_attribute("innerHTML") != old_html
    )

    # ✅ 缓存所有日期 <th id="Day_XXX"> 元素
    day_map = {}
    for th in driver.find_elements(By.XPATH, '//th[starts-with(@id, "Day_")]'):
        day_id = th.get_attribute("id").replace("Day_", "")
        day_text = th.text.strip()
        day_map[day_id] = day_text

    # 获取所有可预约图标
    icons = driver.find_elements(By.XPATH, '//a[contains(@href, "komaClicked")]/img[@alt="予約可能" and @src="../image/s_empty.gif"]')

    for icon in icons:
        parent_a = icon.find_element(By.XPATH, "./..")
        href = parent_a.get_attribute("href")

        match = re.search(r'komaClicked\((\d+),(\d+),(\d+)\)', href)
        if not match:
            continue

        day_idx, row, col = match.groups()

        # ✅ 使用缓存获取日期文本
        date_text = day_map.get(day_idx)
        if not date_text:
            continue

        # 判断是否为周末或祝日
        holiday = ""
        match = re.search(r"(\d{1,2})月(\d{1,2})日", date_text)
        if match:
            month = int(match.group(1))
            day = int(match.group(2))
            date_to_check = datetime(2025, month, day).date()
            if is_weekend_or_holiday(date_to_check):
                holiday = "X"

        # 映射时间段
        time = ""
        if row == '0' and holiday == "X":
            time = '09:00～11:00'
        elif row == '1' and holiday == "X":
            time = '11:00～13:00'
        elif row == '2' and holiday == "X":
            time = '13:00～15:00'
        elif row == '3' and holiday == "X":
            time = '15:00～17:00'
        elif row == '4' and holiday == "X":
            time = '17:00～19:00'
        elif row == '5':
            time = '19:00～21:00'

        if time:
            date_to_times[date_text].append(time)

#
# 读取可预约时间段函数封装
def get_avalinfo(centername, body_lines, driver, old_html):

    date_to_times = defaultdict(list)
    get_date_time(date_to_times, driver, old_html) #現在～未来2週間
    
    #
    # 翌週表示    
    icon_area = driver.find_element(By.CLASS_NAME, "clsKoma")
    old_html = icon_area.get_attribute("innerHTML") # 旧表单
    button = WebDriverWait(driver, 10).until(
        ec.element_to_be_clickable((By.XPATH, '//img[@class="clsNone" and @alt="翌週表示"]'))
    )
    button.click()
    get_date_time(date_to_times, driver, old_html) #未来2週間～4週間

    #
    # 前週表示
    icon_area = driver.find_element(By.CLASS_NAME, "clsKoma")
    old_html = icon_area.get_attribute("innerHTML")
    button = WebDriverWait(driver, 10).until(
        ec.element_to_be_clickable((By.XPATH, '//img[@class="clsNone" and @alt="前週表示"]'))
    )
    button.click()

    # 等待图标表格加载完成
    WebDriverWait(driver, 10).until(
        lambda d: d.find_element(By.CLASS_NAME, "clsKoma").get_attribute("innerHTML") != old_html
    )
    
    # 结果添加
    if not date_to_times:
        body_lines.append("\n【{centername}】・なし".format(centername=centername))
    else:
        #
        # メール本文追加
        body_lines.append("\n【{centername}】".format(centername=centername))
        for date, times in date_to_times.items():
            line = f"・{date} - " + "、".join(times)
            body_lines.append(line)

def send_mail(body_lines):
    #
    # メール本文挨拶開始
    header_lines = []
    header_lines.append("ご担当者様\n")
    header_lines.append("お疲れ様です。")
    header_lines.append("掲題の件につきまして、本日より4週間先まで川口市各施設バトミントン予約可能時間帯を送ります。")
    header_lines.append("※対象時間帯：平日の19:00~21:00、祝日/週末の終日※")

    #
    # メール本文挨拶終了
    footer_lines = []
    footer_lines.append("\nご希望の時間帯がございましたら、お早めにご予約ください。")
    footer_lines.append("どうぞよろしくお願いいたします。")

    #
    # 构造邮件内容
    email_body = "\n".join(header_lines + body_lines + footer_lines)
    msg = MIMEText(email_body, "plain", "utf-8")

    today = datetime.now()
    msg["Subject"] = f"バトミントン予約可能時間帯({today.strftime('%m/%d')})"
    msg["From"] = os.getenv("EMAIL_FROM")
    msg["To"] = os.getenv("EMAIL_TO")
    
    #
    # 发送邮件
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(os.getenv("EMAIL_FROM"), os.getenv("EMAIL_PASS"))  # 推荐使用应用专用密码
        server.send_message(msg)

#
# 初始化浏览器
def init_driver(headless=True):
    options = Options()
    if headless:
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)

#
# 古いファイル取得
def find_previous_file(file_new, max_attempts:int):
    basename = os.path.basename(file_new)  # 例如 "202510101530.txt"
    dirname = os.path.dirname(file_new)

    # 去掉扩展名，提取时间戳
    timestamp_str = os.path.splitext(basename)[0]  # "202510101530"
    dt_format = "%Y%m%d%H%M"

    try:
        dt = datetime.strptime(timestamp_str, dt_format)
    except ValueError:
        raise ValueError(f"文件名格式错误: {timestamp_str}")

    # 向前找最多 max_attempts 次，每次减 10 分钟
    for i in range(1, max_attempts + 1):
        dt_prev = dt - timedelta(minutes=10 * i)
        candidate_name = dt_prev.strftime(dt_format)  # 不加 .txt
        file_old = os.path.join(dirname, candidate_name).replace("\\", "/") + ".txt"
        if os.path.exists(file_old):
            return file_old
    return None





import time
from datetime import datetime, timedelta
from selenium.webdriver.support.select import Select
from define import select_facility, get_avalinfo, send_mail, init_driver, find_previous_file
from data import CommunityCenter, SportsCenter
import os
from zoneinfo import ZoneInfo
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

#
# 処理開始
start = datetime.now(ZoneInfo("UTC")).astimezone(ZoneInfo("Asia/Tokyo"))
print(f"{start.strftime('%H:%M:%S')} - 処理開始")

#
# メール本文
body_lines = []

#
# バドミントン（公民館等）→　青木東公民館
driver = init_driver(headless=True) # 初始化浏览器
for i, (code2, code3, name) in enumerate(CommunityCenter):

    if i != 0:
        start1 = datetime.now(ZoneInfo("UTC")).astimezone(ZoneInfo("Asia/Tokyo"))  # 処理開始時間    
    
    if i == 0:
        select_facility('110140',code2,code3,driver) # 110140:青木東公民館
        start1 = datetime.now(ZoneInfo("UTC")).astimezone(ZoneInfo("Asia/Tokyo"))  # 処理開始時間
        old_html = "" # 旧表单
        get_avalinfo(name,body_lines,driver,old_html) # 001030

    elif name == "中央ふれあい館":
    
        # 旧表单
        table = driver.find_element(By.CLASS_NAME, "clsKoma")
        old_html = table.get_attribute("innerHTML")
        
        # 选择下一个设施
        wait = WebDriverWait(driver, 5)
        select_element = wait.until(EC.presence_of_element_located(("name", "lst_kaikan")))
        select = Select(select_element)
        select.select_by_value(code2)

        # 等待图标表格加载完成
        WebDriverWait(driver, 10).until(
            lambda d: d.find_element(By.CLASS_NAME, "clsKoma").get_attribute("innerHTML") != old_html
        )
        
        # 旧表单
        table = driver.find_element(By.CLASS_NAME, "clsKoma")
        old_html = table.get_attribute("innerHTML")
        
        # 选择ホール1
        wait = WebDriverWait(driver, 5)
        select_element = wait.until(EC.presence_of_element_located(("name", "lst_shisetu")))
        select = Select(select_element)
        select.select_by_value("151")  # 选择「ホール1」
        get_avalinfo(name+"ホール1",body_lines,driver,old_html)

        # 旧表单
        table = driver.find_element(By.CLASS_NAME, "clsKoma")
        old_html = table.get_attribute("innerHTML")
        
        # 选择ホール2
        wait = WebDriverWait(driver, 5)
        select_element = wait.until(EC.presence_of_element_located(("name", "lst_shisetu")))
        select = Select(select_element)
        select.select_by_value("161")  # 选择「ホール1」
        get_avalinfo(name+"ホール1",body_lines,driver,old_html)
        
    else:
        # 旧表单
        table = driver.find_element(By.CLASS_NAME, "clsKoma")
        old_html = table.get_attribute("innerHTML")

        # 选择下一个设施
        wait = WebDriverWait(driver, 5)
        select_element = wait.until(EC.presence_of_element_located(("name", "lst_kaikan")))
        select = Select(select_element)
        select.select_by_value(code2)
        get_avalinfo(name,body_lines,driver,old_html)

    end1 = datetime.now(ZoneInfo('Asia/Tokyo'))
    print(f"{start1.strftime('%H:%M:%S')} - {name} 　※処理時間：{int((end1 - start1).total_seconds())}秒")  

#
# 关闭浏览器
driver.quit()

#
# バドミントン（体育施設用）→　体育武道センター
driver = init_driver(headless=True) # 初始化浏览器
for i, (code2, code3, name) in enumerate(SportsCenter):

    if i != 0:
        start1 = datetime.now(ZoneInfo("UTC")).astimezone(ZoneInfo("Asia/Tokyo"))  # 処理開始時間    
    
    if i == 0:
        select_facility('003060',code2,code3,driver)  # 003060： バドミントン（体育施設用） 
        start1 = datetime.now(ZoneInfo("UTC")).astimezone(ZoneInfo("Asia/Tokyo"))  # 処理開始時間      
        old_html = ""  # 旧表单
        get_avalinfo(name, body_lines,driver,old_html)
    
    elif name == "芝スポーツセンター":
    
        # 旧表单
        table = driver.find_element(By.CLASS_NAME, "clsKoma")
        old_html = table.get_attribute("innerHTML")
        
        # 选择下一个设施
        wait = WebDriverWait(driver, 5)
        select_element = wait.until(EC.presence_of_element_located(("name", "lst_kaikan")))
        select = Select(select_element)
        select.select_by_value(code2)

        # 等待图标表格加载完成
        WebDriverWait(driver, 10).until(
            lambda d: d.find_element(By.CLASS_NAME, "clsKoma").get_attribute("innerHTML") != old_html
        )
        
        # 旧表单
        table = driver.find_element(By.CLASS_NAME, "clsKoma")
        old_html = table.get_attribute("innerHTML")
        
        # 选择「体育館」
        wait = WebDriverWait(driver, 5)
        select_element = wait.until(EC.presence_of_element_located(("name", "lst_shisetu")))
        select = Select(select_element)
        select.select_by_value("010")  # 选择「体育館」
        get_avalinfo(name+"ホール1",body_lines,driver,old_html)

    # else:
    #     現時点なし

    end1 = datetime.now(ZoneInfo('Asia/Tokyo'))
    print(f"{start1.strftime('%H:%M:%S')} - {name} 　※処理時間：{int((end1 - start1).total_seconds())}秒")  

#
# ファイル保存
rounded = start.replace(minute=(start.minute // 10) * 10, second=0, microsecond=0)
previous = rounded - timedelta(minutes=10)
time_now = rounded.strftime("%Y%m%d%H%M")   # 例202509302110
# time_old = previous.strftime("%Y%m%d%H%M")  # 例202509302100

folder = "output"
os.makedirs(folder, exist_ok=True)

file_new = f"{folder}/{time_now}.txt"
now_jst = datetime.now(ZoneInfo('Asia/Tokyo')).strftime('%H:%M:%S')
print(f"{now_jst} - ファイル保存 {file_new}")
with open(file_new, "w", encoding="utf-8") as f:
    for line in body_lines:
        f.write(line + "\n")

# if start.hour == 6 and start.minute <= 10: # 朝一からの場合、旧ファイル取得
#     time_old = time_old[:-4] + "0300"
#     file = f"{time_old}.txt"
# else:
#     file = f"{time_now}.txt"

# 获取 output 文件夹中所有 txt 文件
files = sorted(os.listdir("output"))
now_jst = datetime.now(ZoneInfo('Asia/Tokyo')).strftime('%H:%M:%S')
if len(files) >= 2:
    file_old = os.path.join("output", files[-2])
    file_new = os.path.join("output", files[-1])    
    with open(file_old, "r", encoding="utf-8") as f1, open(file_new, "r", encoding="utf-8") as f2:
        if f1.read() != f2.read():
            now_jst = datetime.now(ZoneInfo('Asia/Tokyo')).strftime('%H:%M:%S')
            print(f"{now_jst} - ファイル比較\n           新 {file_new}\n           旧 {file_old}\n           ★差異あり★、メール送信")
            send_mail(body_lines)
        else:
            print(f"{now_jst} - ファイル比較\n           新 {file_new}\n           旧 {file_old}\n           ★差異なし★、送信不要")
else:
    print(f"{now_jst} - 旧ファイル存在なし、メール送信")
    send_mail(body_lines)

if start.minute <= 10:
    while len(files) > 6:
        file_delete = files[-7]
        now_jst = datetime.now(ZoneInfo('Asia/Tokyo')).strftime('%H:%M:%S')
        try:        
            print(f"{now_jst} - ファイル削除 {file_delete}")
            os.remove(os.path.join(folder, files[-7])) # 删除旧文件
            files = sorted(os.listdir("output"))
        except Exception as e:            
            print(f"{now_jst} - ⚠️ 删除失败: {file_delete}，原因: {type(e).__name__}: {e}")
            break

#
# 処理終了
end = datetime.now(ZoneInfo("UTC")).astimezone(ZoneInfo("Asia/Tokyo"))
duration_sec = int((end - start).total_seconds())
minutes, seconds = divmod(duration_sec, 60)
if minutes == 0:
    print(f"{end.strftime('%H:%M:%S')} - 処理終了　※処理時間：{seconds}秒")
else:
    print(f"{end.strftime('%H:%M:%S')} - 処理終了　※処理時間：{minutes}分{seconds}秒")


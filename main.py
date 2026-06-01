
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.chrome.options import Options
# import time
# import csv

# options = Options()
# # options.add_argument("--start-maximized")
# # options.add_argument("--disable-gpu")
# # options.add_argument("--no-sandbox")
# # options.add_argument("--disable-dev-shm-usage")

# extension_path1 = r"E:\PYTHON\WEB-AUTOMATION\selenium\mydream\mydreamsseotools Ex 01"
# extension_path2 = r"E:\PYTHON\WEB-AUTOMATION\selenium\mydream\mydreamsseotools Ex 02"
# options.add_argument(f"--load-extension={extension_path1},{extension_path2}")

#                     #    manually giving extensions to access moz
# driver = webdriver.Chrome(options=options)
# wait = WebDriverWait(driver, 20)

# # credentials to access mydreamsseotooletc
# email = "falakshair6191@gmail.com"
# password = "falakshair6191@gmail.com"
# keyword = "bb simon"

# driver.get("https://app.mydreamsseotools.com/member")
# # Instead of clicking:
# # driver.execute_script("window.location.href='https://session.mydreamsseotools.com/moz/moz.php'")


# # 2. Login
# wait.until(EC.presence_of_element_located((By.ID, "amember-login"))).send_keys(email)
# driver.find_element(By.ID, "amember-pass").send_keys(password)
# driver.find_element(By.XPATH, "//input[@type='submit' and @value='Login']").click()

# #   clicking on moz
# moz_link = wait.until(EC.element_to_be_clickable(
#     (By.XPATH, "//a[@id='resource-link-page-1' and @title='Moz']")))
# moz_link.click()
# time.sleep(8)

# # accessing moz tool to scrape
# moz_button = WebDriverWait(driver, 10).until(
#     EC.element_to_be_clickable((By.XPATH, "//a[contains(@onclick, 'moz.php') and contains(text(), 'Access moz')]"))
# )
# moz_button.click()
# # driver.switch_to.window(driver.window_handles[-1])


# # driver.get("https://analytics.moz.com/pro/keyword-explorer")
# time.sleep(50)




#                             # after accessing moz  searching keyword to scrape
# # search_keyword = WebDriverWait(driver, 10).until(
# #     EC.presence_of_element_located((By.XPATH, "//input[@aria-invalid='false' and @name='query']"))
# # )
# # search_keyword.clear()
# # search_keyword.send_keys("bb simon")
# # # search_keyword.Keys.RETURN
# # search_keyword.submit()

#         #  optional
# # 4. Switch to the new window/
# # tab
# # time.sleep(3)



# # # 7. Extract data (example: table rows)
# # results = driver.find_elements(By.XPATH, "//table//tr")

# # data = []
# # for row in results:
# #     cols = row.find_elements(By.TAG_NAME, "td")
# #     if cols:
# #         data.append([col.text for col in cols])

# # # 8. Save to CSV
# # with open("moz_results.csv", "w", newline="", encoding="utf-8") as f:
# #     writer = csv.writer(f)
# #     writer.writerows(data)

# # print("✅ Data saved to moz_results.csv")

# # Optional: Close browser
# # driver.quit()



from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import csv
import pickle

options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--disable-infobars")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
extension_path1 = r"E:\PYTHON\WEB-AUTOMATION\selenium\mydream\mydreamsseotools Ex 01"
extension_path2 = r"E:\PYTHON\WEB-AUTOMATION\selenium\mydream\mydreamsseotools Ex 02"
options.add_argument(f"--load-extension={extension_path1},{extension_path2}")
# Optional: Use headless mode
options.add_argument("--headless")

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 20)

# ---------------- Login Credentials ----------------
email = "falakshair6191@gmail.com"
password = "falakshair6191@gmail.com"
keyword = "bb simon"

# ---------------- Step 1: Login ----------------
driver.get("https://app.mydreamsseotools.com/member")

wait.until(EC.presence_of_element_located((By.ID, "amember-login"))).send_keys(email)
driver.find_element(By.ID, "amember-pass").send_keys(password)
driver.find_element(By.XPATH, "//input[@type='submit' and @value='Login']").click()

# ---------------- Step 2: Open Moz Tool ----------------
moz_link = wait.until(EC.element_to_be_clickable(
    (By.XPATH, "//a[@id='resource-link-page-1' and @title='Moz']")))
moz_link.click()
time.sleep(3)

access_button = wait.until(EC.element_to_be_clickable(
    (By.XPATH, "//a[contains(@onclick, 'moz.php') and contains(text(), 'Access moz')]")))
access_button.click()

# ---------------- Step 3: Switch to Moz Tab ----------------
WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > 1)
driver.switch_to.window(driver.window_handles[-1])

# Wait for Moz page to fully load
WebDriverWait(driver, 30).until(EC.presence_of_element_located(
    (By.XPATH, "//input[@placeholder='Enter a keyword or phrase']")))

# ---------------- Step 4: Search Keyword ----------------
search_input = driver.find_element(By.XPATH, "//input[@placeholder='Enter a keyword or phrase']")
search_input.clear()
search_input.send_keys(keyword)
search_input.submit()

# ---------------- Step 5: Wait for Results ----------------
WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//table")))

# ---------------- Step 6: Scrape Table Data ----------------
rows = driver.find_elements(By.XPATH, "//table//tr")
data = []

for row in rows:
    cols = row.find_elements(By.TAG_NAME, "td")
    if cols:
        data.append([col.text for col in cols])

# ---------------- Step 7: Save to CSV ----------------
with open("moz_results.csv", "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Keyword", "Monthly Volume", "Difficulty", "CTR", "Priority"])  # Adjust columns as needed
    writer.writerows(data)

print("✅ Data saved to moz_results.csv")

# ---------------- Done ----------------
driver.quit()





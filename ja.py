# from selenium import webdriver
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# import time

# email_address="bisharchh@gmail.com"
# password="miakhalifA$2004"

# chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument("--ignore-certificate-errors")
# driver = webdriver.Chrome(options=chrome_options)

# driver.get("https://www.google.com")  pandas and numpy

# search = driver.find_element(By.NAME, "q")
# search.send_keys("Gmail")
# search.send_keys(Keys.RETURN)
# time.sleep(2) 

# gmail_link = WebDriverWait(driver, 10).until(
#         EC.presence_of_element_located((By.CLASS_NAME,'qLRx3b')))
# gmail_link.click()

# time.sleep(2)
# buttonofsign = WebDriverWait(driver, 10).until(
#     EC.presence_of_element_located((By.CLASS_NAME, "button--mobile"))
# )
# time.sleep(2)
# buttonofsign.click()

# writing_gmail = WebDriverWait(driver, 10).until(
#     EC.presence_of_element_located((By.XPATH, '//*[@id="identifierId"]')))
# writing_gmail.send_keys(email_address)

# clicking_next = WebDriverWait(driver, 10).until(
#     EC.presence_of_element_located((By.XPATH,
#                                         '//*[@id="identifierNext"]/div/button/span')))
# clicking_next.click()
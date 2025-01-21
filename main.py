from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time



driver = webdriver.Chrome()  
driver.get("https://www.google.com")

search = driver.find_element(By.NAME, "q")
search.send_keys("Gmail")
search.send_keys(Keys.RETURN)
time.sleep(2) 

gmail_link = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME,'qLRx3b tjvcx GvPZzd cHaqb')))
gmail_link.click()

compose=WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME,'T-I T-I-KE L3')))
time.sleep(2)
compose.click()






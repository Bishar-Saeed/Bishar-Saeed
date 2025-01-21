'https://mail.google.com/mail/u/0/#advanced-search/to=Mark%40mg.markfirthonline.com&query=in%3Asent&isrefinement=true&todisplay=Mark%40mg.markfirthonline.com?compose=new'
'https://mail.google.com/mail/u/0/#advanced-search/to=Mark%40mg.markfirthonline.com%2Cabuzarmehdi4433%40gmail.com&query=in%3Asent&isrefinement=true&todisplay=Mark%40mg.markfirthonline.com%2CAbuzar+Mehdi?compose=new'

import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Set your credentials and details
email_address = "bisharchh@gmail.com"
password = "miakhalifA$2004"
recipient_email = "abuzarmehdi4433@gmail.com"
subject = "Automated Email"
message_body = "This is a test email sent using Selenium."

# Set up the WebDriver (Assuming Chrome)
driver = webdriver.Chrome()  # Use the correct path if WebDriver isn't in your PATH

try:
    # Open Gmail
    driver.get("https://mail.google.com/mail/u/0/#inbox")
    time.sleep(2)
    data = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="identifierId"]')))
    data.send_keys(email_address)
    data = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH,
                                        '//*[@id="identifierNext"]/div/button/span')))
    data.click()
    time.sleep(2)

    data = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="password"]/div[1]/div/div[1]/input')))
    data.send_keys(password)
    data = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH,
                                        '//*[@id="passwordNext"]/div/button/span')))
    data.click()
    time.sleep(5)
    data = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH,
                                        '/html/body/div[20]/div[2]/div[3]/button[2]')))
    data.click()
    driver.get("https://mail.google.com/mail/u/0/#advanced-search/to=abuzarmehdi4433%40gmail.com&query=in%3Asent&isrefinement=true&todisplay=abuzarmehdi4433%40gmail.com?compose=new")
    time.sleep(2)
    # '''''''''''''''''''''''''''''''''''''''''''''''
    
    data = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.ID,
                                        ':6b')))

    data.send_keys(subject)
    print('pass2')

    data = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH,
                                        '//*[@id=":3g"]')))
    data.send_keys(message_body)

    time.sleep(200)
finally:
    driver.quit()
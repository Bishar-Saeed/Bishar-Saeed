'https://mail.google.com/mail/u/0/#advanced-search/to=Mark%40mg.markfirthonline.com&query=in%3Asent&isrefinement=true&todisplay=Mark%40mg.markfirthonline.com?compose=new'
'https://mail.google.com/mail/u/0/#advanced-search/to=Mark%40mg.markfirthonline.com%2Cabuzarmehdi4433%40gmail.com&query=in%3Asent&isrefinement=true&todisplay=Mark%40mg.markfirthonline.com%2CAbuzar+Mehdi?compose=new'

import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Set your credentials and details
email_address = "muhammadbishar512@gmail.com"
password = "CHAUDHARYY"
recipient_email = "abuzarmehdi4433@gmail.com"
subject = "Automated Email"
message_body = "This is a test email sent using Selenium."

# options = Options()
# options.binary_location = r"G:\selenium\chrome-win\chrome.exe" 
driver = webdriver.Chrome(executable_path=r"G\selenium\chromedriver-win64\chromedriver.exe")
try:
    driver.get("https://mail.google.com/mail/u/0/#inbox")
    time.sleep(2)
    data = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="identifierId"]')))
    data.send_keys(email_address)
    data = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH,
                                        '//*[@id="identifierNext"]/div/button/span')))
    data.click()
    time.sleep(300)

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
    # '''''''''''''''''''''''''''''''''''''''''''''''      CHANGED  
    
    data = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH,
                                        ":11k")))
    data.send_keys(recipient_email)
    
    data = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.ID,
                                        ':om')))
    data.send_keys(subject)
    print('pass2')

    data = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID,":nc")))
    data.send_keys(message_body)

    
    data = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID,
                                        ":ow")))
    data.click()
    time.sleep(200)
finally:
    driver.quit()
    
    
    
    #  recipient_email id=:11k ,:13a  subject=:om=id     body=:nc=id    clickonsend=:ow =id
    
    


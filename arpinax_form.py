# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.support.ui import Select
# import time



# driver=webdriver.Chrome()
# driver.get("https://selenium-python.readthedocs.io/")
# driver.implicitly_wait(10)
# element=driver.find_element(By.CLASS_NAME,"reference")
# element.click()

# WebDriverWait(driver,30).until(
#     EC.text_to_be_present_in_element(
#         (By.CLASS_NAME,"progress-label"),         #ELEMENT FILTRATION
#         'Complete!'                               #EXPECTED TEXT
#     )
# )


                                  #   FORM AUTOMATING
# driver=webdriver.Chrome()
# driver.get("https://www.google.com/")

# search=driver.find_element(By.ID,"APjFqb")
# search.send_keys("arpinax")
# search.send_keys(Keys.RETURN)

# arpinax_open=driver.find_element(By.CLASS_NAME,"LC20lb")
# arpinax_open.click()

# contact_form_arpinax=driver.find_element(By.LINK_TEXT,"Contact Us")
# contact_form_arpinax.click()

# name= driver.find_element(By.ID,"wpforms-6540-field_0")
# email= driver.find_element(By.ID,"wpforms-6540-field_1")
# contact_number= driver.find_element(By.ID,"wpforms-6540-field_4")
# message= driver.find_element(By.ID,"wpforms-6540-field_2")
# choose_topic= driver.find_element(By.CLASS_NAME,"search_terms")
# marketing_click=driver.find_element(By.ID,"choices--wpforms-6540-field_3-item-choice-2")
# click_true= driver.find_element(By.NAME,"wpforms[fields][5][]")
# submit=driver.find_element(By.CLASS_NAME,"wpforms-submit")


# name.send_keys("MUHAMMAD BISHAR")
# email.send_keys("bisharchh@gmail.com")
# contact_number.send_keys("03143023821")
# message.send_keys("GREAT WORK")
# choose_topic.click()
# marketing_click.click()
# click_true.click()
# submit.click()

# time.sleep(100)


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
import time


driver = webdriver.Chrome()
driver.get("https://www.google.com/")
search = WebDriverWait(driver, 10).until(
    EC.visibility_of_element_located((By.ID, "APjFqb"))
)
search.send_keys("arpinax")
search.send_keys(Keys.RETURN)


arpinax_open = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.CLASS_NAME, "LC20lb"))
)
arpinax_open.click()


contact_form_arpinax = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.LINK_TEXT, "Contact Us"))
)
contact_form_arpinax.click()


name = WebDriverWait(driver, 10).until(
    EC.visibility_of_element_located((By.ID, "wpforms-6540-field_0"))
)

email = WebDriverWait(driver, 10).until(
    EC.visibility_of_element_located((By.ID, "wpforms-6540-field_1"))
)

contact_number = WebDriverWait(driver, 10).until(
    EC.visibility_of_element_located((By.ID, "wpforms-6540-field_4"))
)

message = WebDriverWait(driver, 10).until(
    EC.visibility_of_element_located((By.ID, "wpforms-6540-field_2"))
)

choose_topic = WebDriverWait(driver, 10).until(
    EC.visibility_of_element_located((By.CLASS_NAME, "choices__inner"))
)

option_click = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.ID, "choices--wpforms-6540-field_3-item-choice-2"))
)
2
click_true = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.NAME, "wpforms[fields][5][]"))
)

submit=WebDriverWait(driver,10).until(
    EC.element_to_be_clickable((By.CLASS_NAME, "wpforms-submit"))
)

name.send_keys("MUHAMMAD BISHAR")
email.send_keys("bisharchh@gmail.com")
contact_number.send_keys("03143023821")
message.send_keys("GREAT WORK")

choose_topic.click()
option_click.click()
click_true.click()

submit.click()
time.sleep(100)


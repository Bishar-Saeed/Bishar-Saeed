from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import csv


driver=webdriver.Chrome()

driver.get("https://www.google.com/")
search=driver.find_element(By.NAME,"q")
search.send_keys("amazon")
search.submit()

seller_data = []

click_website=WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.CLASS_NAME,"CCgQ5"))
)
click_website.click()

                                                      
searching=WebDriverWait(driver,10).until(
    EC.element_to_be_clickable((By.ID,"twotabsearchtextbox"))
)
searching.send_keys("waterbottle")
searching.submit()


changing_delivery_location=driver.find_element(By.ID,"nav-global-location-popover-link")
changing_delivery_location.click()

country_dropdown = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.ID, "GLUXCountryListDropdown"))
)
country_dropdown.click()


option = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH,"//a[@id='GLUXCountryList_219']"))  
)
option.click()
time.sleep(4)

done_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.NAME,"glowDoneButton"))  
)
done_button.click()
time.sleep(3)

# for specific image
product_image =driver.find_element(By.XPATH, "//img[@class='s-image' and contains(@src, '61OPIEsAXaL._AC_UL320_') and contains(@alt, 'IRON °FLASK Camping & Hiking Hydration Flask')]")
# products = driver.find_elements(By.XPATH, '//a[@class="a-link-normal s-no-outline"]')
product_image.click()

# use the get href and xpath
bottle_page_url = driver.current_url
print(f"bottle Page URL {bottle_page_url}")


get_seller_name=driver.find_element(By.ID,"sellerProfileTriggerId")
seller_name=get_seller_name.text
print(f"THIS WATERBOTTLE IS SOLD BY {seller_name}....")


clicking_on_sold_by_info=WebDriverWait(driver,10).until(
    EC.element_to_be_clickable((By.ID,"sellerProfileTriggerId"))
)
clicking_on_sold_by_info.click()


with open("laptop_infromation.csv", mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["URL","SOLD_BY","BUSINESS INFO","BUSINESS_ADDRESS"])  
        writer.writerow([bottle_page_url,seller_name])
        
# business_name = driver.find_element(By.XPATH, "//span[contains(text(), 'Business Name:')]/following-sibling::span")
# print(f"BUSINESS INFO{business_name.text}")

# try:
#     # Try to find the business address
#     address_elements = driver.find_elements(By.XPATH, "//span[contains(text(), 'Business Address:')]/following-sibling::div//span")
#     business_address = "\n".join([address.text for address in address_elements])
# except Exception as e:
#     print(f"Business Address not found: {e}")
       
 






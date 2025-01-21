# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# import time
# import csv

# driver = webdriver.Chrome()

# driver.get("https://www.google.com/")
# search = driver.find_element(By.NAME, "q")
# search.send_keys("amazon")
# search.submit()

# click_website = WebDriverWait(driver, 10).until(
#     EC.element_to_be_clickable((By.CLASS_NAME, "CCgQ5"))
# )
# click_website.click()

# searching = WebDriverWait(driver, 10).until(
#     EC.element_to_be_clickable((By.ID, "twotabsearchtextbox"))
# )
# searching.send_keys("waterbottle")
# searching.submit()

# changing_delivery_location = driver.find_element(By.ID, "nav-global-location-popover-link")
# changing_delivery_location.click()

# country_dropdown = WebDriverWait(driver, 10).until(
#     EC.element_to_be_clickable((By.ID, "GLUXCountryListDropdown"))
# )
# country_dropdown.click()

# option = WebDriverWait(driver, 10).until(
#     EC.element_to_be_clickable((By.XPATH, "//a[@id='GLUXCountryList_219']"))
# )
# option.click()
# time.sleep(4)

# done_button = WebDriverWait(driver, 10).until(
#     EC.element_to_be_clickable((By.NAME, "glowDoneButton"))
# )
# done_button.click()
# time.sleep(3)

# with open("amazonn_product_data.csv", "w", newline="") as file:
#     writer = csv.writer(file)
#     writer.writerow(["PRODUCT_URL", "SOLD_BY", "BUSINESS_NAME", "BUSINESS_ADDRESS"])

#     for page in range(1, 10):  
#         products = driver.find_elements(By.XPATH, '//a[@class="a-link-normal s-no-outline"]')
#         for product in products:
#             product_url = product.get_attribute("href")
        
#             driver.execute_script("window.open(arguments[0]);", product_url)
#             driver.switch_to.window(driver.window_handles[1])

#             try:
#                 try:
#                     sold_by_element = WebDriverWait(driver, 10).until(
#                         EC.presence_of_element_located((By.XPATH, "//a[@id='sellerProfileTriggerId']"))
#                     )
#                     sold_by = sold_by_element.text
#                     if "Amazon.com" in sold_by:
#                         print(f"Skipping product Sold by Amazon: {product_url}")
#                     else:
#                         sold_by_element.click()
                                                        
#                         try:
#                           business_name = driver.find_element(By.XPATH, "//span[contains(text(), 'Business Name:')]/following-sibling::span")
#                           nameofbusiness=business_name.text
#                         except Exception as e:
#                           print(f"Business Name not found: {e}")
                           
#                         # try:
#                         #   address_elements = driver.find_elements(By.XPATH, "//span[contains(text(), 'Business Address:')]/following-sibling::div//span")
#                         #   business_address = "\n".join([address.text for address in address_elements])
#                         # except Exception as e:
#                         #   print(f"Business Address not found: {e}") 
                           
                         
#                         writer.writerow([product_url, sold_by, nameofbusiness])
#                 except:
#                     sold_by_text_element = WebDriverWait(driver, 10).until(
#                         EC.presence_of_element_located((By.XPATH, "//span[contains(@class, 'a-size-small offer-display-feature-text-message')]"))
#                     )
#                     sold_by = sold_by_text_element.text
                    
#                     if "Amazon" in sold_by:
#                         print(f"Skipping product Sold by Amazon: {product_url}")
#                     else:               
#                         business_name = sold_by
#                         business_address = "N/A"
#                         writer.writerow([product_url, sold_by, business_name,business_address])

#             finally:
#                 driver.close()
#                 driver.switch_to.window(driver.window_handles[0])

#         try:
#             next_button = driver.find_element(By.XPATH, '//a[contains(@class, "s-pagination-next")]')
#             next_button.click()
#             time.sleep(2)
#         except:
#             print("No more pages to navigate.")
#             break

# driver.quit()
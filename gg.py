from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv


driver = webdriver.Chrome()
driver.get("https://www.amazon.com/")
searching = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.ID, "twotabsearchtextbox"))
)
searching.send_keys("waterbottle")
searching.submit()

changing_delivery_location = driver.find_element(By.ID, "nav-global-location-popover-link")
changing_delivery_location.click()
country_dropdown = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.ID, "GLUXCountryListDropdown"))
)
country_dropdown.click()
option = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//a[@id='GLUXCountryList_219']"))
)
option.click()
time.sleep(4)
done_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.NAME, "glowDoneButton"))
)
done_button.click()
time.sleep(3)

with open("AMAZON_PRODUCTS_DETAILS.csv", "w", newline="") as file, open("AMAZON_PRODUCTS_URLS.csv", "w", newline="") as url_file:
    writer = csv.writer(file)
    writer.writerow(["PRODUCT_URL", "SOLD_BY", "BUSINESS_NAME", "BUSINESS_ADDRESS"])
    url_writer = csv.writer(url_file)
    url_writer.writerow(["PRODUCTS_URL'S"])


    for page in range(1,2):
        products = driver.find_elements(By.XPATH, '//a[@class="a-link-normal s-no-outline"]')

        for product in products:
            product_url = product.get_attribute("href")
        
            driver.execute_script("window.open(arguments[0]);", product_url)
            driver.switch_to.window(driver.window_handles[1])

            try:
                merchant_info = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "a-size-small offer-display-feature-text-message"))
                )
                sold_by_text = merchant_info.text

                if "Amazon.com" in sold_by_text:
                    print(f"Skipping Amazon-listed product: {product_url}")
                else:
                    print(f"Scraping third-party seller info for: {product_url}")
                    
                    try:
                        seller_trigger = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, "//a[@id='sellerProfileTriggerId']"))
                        )
                        seller_trigger.click()

                        try:
                            business_name = driver.find_element(By.XPATH, "//span[contains(text(), 'Business Name:')]/following-sibling::span")
                            nameofbusiness = business_name.text
                        except Exception as e:
                            print(f"Business Name not found: {e}")
                        
                        addresses = []
                        address_divs = driver.find_elements(By.CSS_SELECTOR, 'div.a-row.a-spacing-none.indent-left')
                        for address_div in address_divs:
                            address = address_div.find_element(By.TAG_NAME, 'span').text
                            addresses.append(address)
                        
                        url_writer.writerow([product_url])
                        writer.writerow([sold_by, nameofbusiness, addresses])

                    except Exception as e:
                        print(f"Error retrieving business info: OR There is no Seller Profile to Click and grab data {e}")

            finally:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])

        try:
            next_button = driver.find_element(By.XPATH, '//a[contains(@class, "s-pagination-next")]')
            next_button.click()
            time.sleep(2)
        except:
            print("No more pages to navigate.")
            break

driver.quit()

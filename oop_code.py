from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv

class ScrapingAmazon:
    def __init__(self):
        self.driver = webdriver.Chrome()
        self.url_file = open("urls.csv", "w", newline="", encoding="utf-8")
        self.sold_by_file = open("sold_by.csv", "w", newline="", encoding="utf-8")

        self.business_name_file = open("business_name.csv", "w", newline="", encoding="utf-8")
        self.business_address_file = open("business_address.csv", "w", newline="", encoding="utf-8")
        
        self.url_writer = csv.writer(self.url_file)
        self.sold_by_writer = csv.writer(self.sold_by_file)
        self.business_name_writer = csv.writer(self.business_name_file)
        self.business_address_writer = csv.writer(self.business_address_file)
        
        self.setup_csv_files()
        
    def setup_csv_files(self):
        self.url_writer.writerow(["PRODUCT_URL"])
        self.sold_by_writer.writerow(["SOLD_BY"])
        self.business_name_writer.writerow(["BUSINESS_NAME"])
        self.business_address_writer.writerow(["BUSINESS_ADDRESS"])
    
    def search_amazon(self):
        self.driver.get("https://www.google.com/")
        search = self.driver.find_element(By.NAME, "q")
        search.send_keys("amazon")
        search.submit()

        click_website = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "CCgQ5"))
        )
        click_website.click()

        searching = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "twotabsearchtextbox"))
        )
        searching.send_keys("laptop")
        searching.submit()
    
    def set_delivery_location(self):
        changing_delivery_location = self.driver.find_element(By.ID, "nav-global-location-popover-link")
        changing_delivery_location.click()

        country_dropdown = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "GLUXCountryListDropdown"))
        )
        country_dropdown.click()

        option = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='GLUXCountryList_219']"))
        )
        option.click()
        time.sleep(4)

        done_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.NAME, "glowDoneButton"))
        )
        done_button.click()
        time.sleep(3)

    def scrape_products(self):
        for page in range(1, 10):  
            products = self.driver.find_elements(By.XPATH, '//a[@class="a-link-normal s-no-outline"]')
            for product in products:
                product_url = product.get_attribute("href")
                self.driver.execute_script("window.open(arguments[0]);", product_url)
                self.driver.switch_to.window(self.driver.window_handles[1])
                try:
                    self.process_product(product_url)
                finally:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])

            try:
                next_button = self.driver.find_element(By.XPATH, '//a[contains(@class, "s-pagination-next")]')
                next_button.click()
                time.sleep(2)
            except:
                print("No more pages to navigate.")
                break

    def process_product(self, product_url):
        try:
            sold_by_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[@id='sellerProfileTriggerId']"))
            )
            sold_by = sold_by_element.text

            if "Amazon.com" in sold_by:
                print(f"Skipping product listed by Amazon: {product_url}")
            else:
                sold_by_element.click()
                self.extract_and_save_product_details(product_url, sold_by)
        except:
            pass

    def extract_and_save_product_details(self, product_url, sold_by):
        try:
            business_name = self.driver.find_element(By.XPATH, "//span[contains(text(), 'Business Name:')]/following-sibling::span").text
        except Exception as e:
            print(f"Business Name not found: {e}")
            business_name = "N/A"

        try:
            addresses = []
            address_divs = self.driver.find_elements(By.CSS_SELECTOR, 'div.a-row.a-spacing-none.indent-left')
            for address_div in address_divs:
                address = address_div.find_element(By.TAG_NAME, 'span').text.strip()
                addresses.append(address)
            address_text = ", ".join(addresses)
        except Exception as e:
            print(f"Business Address not found: {e}")
            address_text = "N/A"

        self.url_writer.writerow([product_url])
        self.sold_by_writer.writerow([sold_by]) 
        self.business_name_writer.writerow([business_name])  
        self.business_address_writer.writerow([address_text])

if __name__ == "__main__":
    scraping = ScrapingAmazon()
    scraping.search_amazon()
    scraping.set_delivery_location()
    scraping.scrape_products()
    scraping.close_files_and_quit()

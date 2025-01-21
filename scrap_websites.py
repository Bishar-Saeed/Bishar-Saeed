

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
import os


output_dir = "scraped_data"
os.makedirs(output_dir, exist_ok=True)

driver = webdriver.Chrome()
driver.get("https://www.google.com")

search_box = driver.find_element(By.NAME, "q")
search_box.send_keys("solar panels")
search_box.submit()                                                         
time.sleep(3)

for i in range(3): 
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//a/h3"))
        )
        results = driver.find_elements(By.XPATH, "//a/h3")
        print(f"Found {len(results)} results.")

        if len(results) > i:
            result = results[i]
            link = result.find_element(By.XPATH, "..").get_attribute("href")
            print("URL:", link)

            for attempt in range(3):  
                try: 
                    result.click()
                    break  
                except Exception as e:
                    print(f"Attempt {attempt + 1}: Element not interactable. Retrying...")
                    time.sleep(2)  
            time.sleep(5)  
            
            
            h1_tags = driver.find_elements(By.TAG_NAME, "h1")
            h2_tags = driver.find_elements(By.TAG_NAME, "h2")
            h3_tags = driver.find_elements(By.TAG_NAME, "h3")
            print(f"Found {len(h1_tags)} h1 tags, {len(h2_tags)} h2 tags, {len(h3_tags)} h3 tags.")

            h1_filename = os.path.join(output_dir, f"h1_website_{i+1}.csv")
            with open(h1_filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["H1 Text", "URL"])  
                for h1 in h1_tags:
                    writer.writerow([h1.text, link])  

            print(f"H1 data saved to {h1_filename}.")

            h2_filename = os.path.join(output_dir, f"h2_website_{i+1}.csv")
            with open(h2_filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["H2 Text", "URL"])  
                for h2 in h2_tags:
                    writer.writerow([h2.text, link])  

            print(f"H2 data saved to {h2_filename}.")

            h3_filename = os.path.join(output_dir, f"h3_website_{i+1}.csv")
            with open(h3_filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["H3 Text", "URL"])  
                for h3 in h3_tags:
                    writer.writerow([h3.text, link])  

            print(f"H3 data saved to {h3_filename}.")
        else:
            print("No more results found.")
            break


        driver.back()
        time.sleep(3)
    except Exception as e:
        print("Error occurred:", e)
        break


driver.quit()
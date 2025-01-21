from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import csv


driver = webdriver.Chrome()
driver.get("https://www.google.com")

search_box = driver.find_element(By.NAME, "q")
search_box.send_keys("uk websites")
search_box.submit()
time.sleep(3)  


results = driver.find_elements(By.XPATH, "//a/h3")  

if len(results) >= 3:
    results = results[:3]
else:
    print(f"Found only {len(results)} results.")


scraped_data = []

for result in results:
    # parent_link = result.find_element(By.XPATH, "..")  
    # parent_link.click()  
    result.click()
    time.sleep(5)  

    try:
        heading = driver.find_element(By.TAG_NAME, "h1").text
        paragraph = driver.find_element(By.TAG_NAME, "p").text
        url=driver.find_element_
        print("Heading:", heading)
        print("Paragraph:", paragraph)

        scraped_data.append([heading, paragraph])
        
    except Exception as e:
        print("Error occurred while scraping:", e)
        scraped_data.append(["Error", "Error"])  

    driver.back()
    time.sleep(3)  
    
with open('scraped_data.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(["Heading", "Paragraph"])  
    writer.writerows(scraped_data)  

    print("Data saved to CSV file.")
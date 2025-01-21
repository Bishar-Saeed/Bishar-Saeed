# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# import time
# import csv

# driver = webdriver.Chrome()
# driver.get("https://www.google.com")

# search_box = driver.find_element(By.NAME, "q")
# search_box.send_keys("uk websites")
# search_box.submit()
# time.sleep(3)

# scraped_data = []

# for i in range(3): 
    
#     WebDriverWait(driver, 10).until(
#         EC.presence_of_all_elements_located((By.XPATH, "//a/h3"))
#     )
    
#     results = driver.find_elements(By.XPATH, "//a/h3")

#     if len(results) > i:
#         result = results[i]

#         link = result.find_element(By.XPATH, "..").get_attribute("href")
#         print("URL:", link)
        
#         result.click()
#         time.sleep(5) 

#         try:
#             heading = driver.find_element(By.TAG_NAME, "h1").text
#             paragraph = driver.find_element(By.TAG_NAME, "p").text

#             print("Heading:", heading)
#             print("Paragraph:", paragraph)

#             scraped_data.append([heading, paragraph, link])
            
#         except Exception as e:
#             print("Error occurred while scraping:", e)
#             scraped_data.append(["Error", "Error", link])

       
#         driver.back()
#         time.sleep(3)
#     else:
#         print("No more results found.")
#         break

# with open('scraped_data.csv', mode='w', newline='', encoding='utf-8') as file:
#     writer = csv.writer(file)
#     writer.writerow(["Heading", "Paragraph", "URL"])  
#     writer.writerows(scraped_data)

#     print("Data saved to CSV file.")

 
# print all the heading and paragraphs on website

# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# import time
# import csv

# driver = webdriver.Chrome()
# driver.get("https://www.google.com")

# search_box = driver.find_element(By.NAME, "q")
# search_box.send_keys("uk websites")
# search_box.submit()
# time.sleep(3)

# scraped_data = []

# for i in range(3): 
#     WebDriverWait(driver, 10).until(
#         EC.presence_of_all_elements_located((By.XPATH, "//a/h3"))
#     )
    
#     results = driver.find_elements(By.XPATH, "//a/h3")

#     if len(results) > i:
#         result = results[i]
#         link = result.find_element(By.XPATH, "..").get_attribute("href")
#         print("URL:", link)
        
#         result.click()
#         time.sleep(5) 

#         try:
            
#             headings = driver.find_elements(By.TAG_NAME, "h1") + driver.find_elements(By.TAG_NAME, "h2") + driver.find_elements(By.TAG_NAME, "h3")
#             paragraphs = driver.find_elements(By.TAG_NAME, "p")

           
#             for heading in headings:
#                 heading_text = heading.text
#                 for paragraph in paragraphs:
#                     paragraph_text = paragraph.text
#                     print("Heading:", heading_text)
#                     print("Paragraph:", paragraph_text)
#                     scraped_data.append([heading_text, paragraph_text, link])

#         except Exception as e:
#             print("Error occurred while scraping:", e)
#             scraped_data.append(["Error", "Error", link])

#         driver.back()
#         time.sleep(3)
#     else:
#         print("No more results found.")
#         break

# with open('scraped_data.csv', mode='w', newline='', encoding='utf-8') as file:
#     writer = csv.writer(file)
#     writer.writerow(["Heading", "Paragraph", "URL"])  
#     writer.writerows(scraped_data)

#     print("Data saved to CSV file.")

# driver.quit()



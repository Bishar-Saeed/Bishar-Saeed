
import csv, time, subprocess, os, shutil, requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from urllib.parse import urlparse

# CONFIG
CAPSOLVER_API_KEY = 'CAP-D7EF953C80E855ECDF9E3894E9997F3627CE80E7CE55986607175965994034DA'
SITE_KEY = '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI'
DA_THRESHOLD = int(input("Enter DA:"))
MIN_DOMAIN_AGE_YEARS = int(input('Enter Domain Age :'))
GOOGLE_PAGES = int(input('Enter NO of Google page scrapped: '))
TARGET_URL = 'https://dapacheckerpro.com/free-bulk-domain-age-checker/'

# Create results folder
os.makedirs("results", exist_ok=True)

# Set up final combined output file
final_output = "results/final_output.csv"
if os.path.exists(final_output):
    os.remove(final_output)
with open(final_output, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Keyword", "DA", "#", "Domain", "Domain Age", "Creation Date", "Expiration Date", "IP Address", "Registrar", "Last Updated"])

# Load keywords
with open("keywords.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    next(reader)
    keywords = [row[0].strip() for row in reader if row]

# Setup browser options
options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-infobars")
options.add_argument("--disable-extensions")
options.add_argument("--disable-popup-blocking")
options.add_argument("--disable-default-apps")
options.add_argument("--no-first-run")
options.add_argument("--disable-notifications")
options.add_argument("--disable-gpu")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
options.add_argument("--start-maximized")
options.binary_location = "./chrome-win/chrome.exe"

for keyword in keywords:
    print(f"Processing: {keyword}")
    safe_keyword = keyword.replace(" ", "_").replace("/", "_").replace("\\", "_")

    google_csv = f"results/google_results_{safe_keyword}.csv"
    da_csv = f"results/da_results_{safe_keyword}.csv"
    domain_age_csv = f"results/domain_age_{safe_keyword}.csv"

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    try:
        # Step 1: Google search
        driver.get("https://www.google.com")
        time.sleep(2)
        search = driver.find_element(By.NAME, "q")
        search.send_keys(keyword)
        search.send_keys(Keys.RETURN)
        time.sleep(2)

        all_urls = []
        for page_num in range(1, GOOGLE_PAGES + 1):
            print(f" Google Page {page_num}")
            links = driver.find_elements(By.XPATH, "//a[h3]")
            for link in links:
                href = link.get_attribute("href")
                if href:
                    all_urls.append(href)

            if page_num < GOOGLE_PAGES:
                try:
                    page_link = driver.find_element(By.XPATH, f"//a[@aria-label='Page {page_num + 1}']")
                    driver.execute_script("arguments[0].click();", page_link)
                except:
                    try:
                        next_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "pnnext")))
                        next_btn.click()
                    except:
                        break

        with open(google_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["URL"])
            for url in all_urls:
                writer.writerow([url])

        # Step 2: Clean and check DA
        print(" Checking Domain Authority...")
        blocked = ["instagram.com", "facebook.com", "tiktok.com", "twitter.com", "linkedin.com"]
        cleaned_domains = []
        for raw in all_urls:
            parsed = urlparse(raw)
            domain = parsed.netloc.lower().replace("www.", "")
            if any(block in domain for block in blocked):
                continue
            cleaned_domains.append(domain)

        qualified_domains = []
        domain_to_da = {} 
        with open(da_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["URL", "DA"])
            for domain in cleaned_domains:
                try:
                    driver.get("https://dapacheckerpro.com/bulk-da-pa-checker/")
                    time.sleep(4)
                    input_area = wait.until(EC.presence_of_element_located((By.ID, "urls-input")))
                    input_area.clear()
                    input_area.send_keys(domain)
                    check_button = driver.find_element(By.ID, "urls-submit")
                    driver.execute_script("arguments[0].scrollIntoView();", check_button)
                    driver.execute_script("arguments[0].click();", check_button)
                    time.sleep(10)
                    da_elem = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "domain-score")))
                    da_value = int(da_elem.text.strip())
                    if da_value >= DA_THRESHOLD:
                        writer.writerow([domain, da_value])
                        qualified_domains.append(domain)
                        domain_to_da[domain]=da_value
                except:
                    continue

        # Step 3: Domain Age
        print("   Solving CAPTCHA...")
        driver.get(TARGET_URL)
        input_box = wait.until(EC.presence_of_element_located((By.ID, "domains")))
        input_box.send_keys("\n".join(qualified_domains))
        time.sleep(1)

        task_payload = {
            'clientKey': CAPSOLVER_API_KEY,
            'task': {
                # 'type': 'ReCaptchaV2Task',
                'type': 'HCaptchaTask',
                'websiteURL': TARGET_URL,
                'websiteKey': SITE_KEY
            }
        }
        response = requests.post("https://api.capsolver.com/createTask", json=task_payload).json()
        task_id = response.get("taskId")
        solution = None
        for _ in range(20):
            time.sleep(5)
            result = requests.post("https://api.capsolver.com/getTaskResult", json={"clientKey": CAPSOLVER_API_KEY, "taskId": task_id}).json()
            if result.get("status") == "ready":
                solution = result["solution"]["gRecaptchaResponse"]
                break

        if not solution:
            print("   CAPTCHA not solved")
            continue

        js = f"""
        document.querySelectorAll('iframe[src*="recaptcha"]').forEach(e => e.remove());
        document.querySelectorAll('.g-recaptcha').forEach(e => e.remove());
        var old = document.getElementById('g-recaptcha-response');
        if (old) old.remove();
        var input = document.createElement('input');
        input.type = 'hidden';
        input.id = 'g-recaptcha-response';
        input.name = 'g-recaptcha-response';
        input.value = '{solution}';
        document.body.appendChild(input);
        input.dispatchEvent(new Event('change', {{ bubbles: true }}));
        """
        driver.execute_script(js)
        time.sleep(2)

        check_btn = wait.until(EC.element_to_be_clickable((By.ID, "checkDomains")))
        driver.execute_script("arguments[0].scrollIntoView();", check_btn)
        driver.execute_script("arguments[0].click();", check_btn)
        time.sleep(10)

        print("Scraping results...")
        table = wait.until(EC.presence_of_element_located((By.ID, "resultsTable")))
        for _ in range(10):
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", table)
            time.sleep(1)

        rows = driver.find_elements(By.CSS_SELECTOR, "#resultsTable tbody tr")
        with open(domain_age_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["#", "Domain", "Domain Age", "Creation Date", "Expiration Date", "IP Address", "Registrar", "Last Updated"])
            for row in rows:
                try:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    age = int(cols[2].text.strip().split()[0])
                    if age < MIN_DOMAIN_AGE_YEARS:
                        writer.writerow([c.text.strip() for c in cols])
                except:
                    continue

        # Append to final_output.csv
        with open(domain_age_csv, "r", encoding="utf-8") as src:
            reader = csv.reader(src)
            next(reader)
            with open(final_output, "a", newline="", encoding="utf-8") as dest:
                writer = csv.writer(dest)
                for row in reader:
                    domain = row[1].strip().lower()
                    da = domain_to_da.get(domain, "")
                    writer.writerow([keyword, da] + row)
        print(f" Done: {keyword}")
        
        os.remove(da_csv)
        os.remove(google_csv)
        os.remove(domain_age_csv)
    except Exception as e:
        print(f" Error with {keyword}: {e}")
        os.remove(da_csv)
        os.remove(google_csv)
        os.remove(domain_age_csv)
    finally:
        driver.quit()

print(f"All done. Combined file: {final_output}")



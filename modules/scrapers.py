import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from modules.utils import get_random_user_agent
import time
import requests
from bs4 import BeautifulSoup
from .logger import logger

def map_grade(raw_grade):
    proper_grade = ''
    if raw_grade=='used':
        proper_grade = 'nearmint'
    elif raw_grade=='cib':
        proper_grade = 'psa_7'
    elif raw_grade=='new':
        proper_grade = 'psa_8'
    elif raw_grade=='graded':
        proper_grade = 'psa_9'
    elif raw_grade=='boxonly':
        proper_grade = 'bgs_9_half'
    elif raw_grade=='manualonly':
        proper_grade = 'psa_10'

    return proper_grade

# used to join with google trends data (monthly dates)
def convert_timestamps(data):
    converted = {}
    for key, values in data.items():
        # Create a list of dictionaries with formatted date and price
        converted[key] = [{'date': pd.to_datetime(ts[0], unit='ms').strftime('%m-%y'), 'price': ts[1]} for ts in values]
    return converted

def top_50_set_scraper(set_name):
    url = f'https://www.pricecharting.com/console/pokemon-{set_name}?sort=highest-price&model-number=&exclude-variants=true&show-images=true&in-collection='

    response = requests.get(url)    # Use Beautiful Soup to parse the page source
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all Pokémon names and numbers
    product_data = []
    for title in soup.find_all('td', class_='title'):
        link = title.find('a')
        if link:
            # Get the product_name name and number from the link text
            product_name = link.text.strip().lower()
            data = {}
            logger.info(f"found product name: {product_name}")

            keywords = [" box", "build", "battle deck","collection", "blister", "bundle", " tin", "booster pack"]
            # if sealed product
            if any(keyword in product_name for keyword in keywords):                
                data["product_name"]=product_name.replace("#", "")
                data["poke_no"]=""
                data["product_type"]="sealed"
            elif '#' in product_name:
                data["product_name"]=product_name.split('#')[0].rstrip() # i.e. Squirtle #151
                data["poke_no"]=product_name.split('#')[1].strip()
                data["product_type"]="card"
            else:
                data["product_name"]=product_name
                data["poke_no"]=""
                data["product_type"]="other"
            
            # put "-" inbetween words, remove any trailing "-"
            data["product_name"]=data["product_name"].replace(" ", "-").replace("?", "").rstrip('-')
            product_data.append(data)

    for data in product_data:
        logger.info(data)

    logger.info(f'{set_name}: total products scraped={len(product_data)}')
    return product_data

def setup_driver(mode):
    logger.info("setup_driver(): choosing random agent")
    user_agent = get_random_user_agent()
    chrome_options = Options()
    
    if mode == "headless":
        logger.info("setup_driver(): running in headless mode")
        chrome_options.add_argument("--headless")    
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument(f"--user-agent={user_agent}")

    chrome_options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=chrome_options)
   
    if driver is None:
        logger.error("\nsetup_driver(): driver initialization failed")
    else:
        logger.info("\nsetup_driver(): initialized driver")        

    return driver

def price_scraper(poke_object, mode="headless"):
    driver=setup_driver(mode)
    url = f'https://www.pricecharting.com/game/pokemon-{poke_object.set_name}/{poke_object.name}-{poke_object.num}'
    
    if poke_object.product_type=='sealed':
        url = f'https://www.pricecharting.com/game/pokemon-{poke_object.set_name}/{poke_object.name}'
        logger.info(f"price_scraper(): sealed product has url= {url}")

    try:
        logger.info(f"price_scraper(): getting url: {url}")
        driver.get(url)
        time.sleep(5)  # Wait for the page to load
        
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        logger.info(f"price_scraper(): got soup.head.title: {str(soup.head.title)}")

        chart_data = driver.execute_script("return VGPC.chart_data;")
        converted_data = convert_timestamps(chart_data)
        
        result = []

        if poke_object.product_type=="sealed":
            nm_data = converted_data["used"]
            for entry in nm_data:
                entry['grade']='nearmint'
                entry['poke_name']=poke_object.name
                entry['poke_no']=poke_object.num
                entry["set_name"]=poke_object.set_name
                entry["product_type"]="sealed"
                entry["set_year"] = poke_object.set_year
                entry["set_month"] = poke_object.set_month
                result.append(entry)

        else:        
            for grade, price_arr in converted_data.items():
                for entry in price_arr:                    
                    fmt_grade = map_grade(grade)
                    entry['grade']=fmt_grade
                    entry['poke_name']=poke_object.name
                    entry['poke_no']=poke_object.num
                    entry["set_name"]=poke_object.set_name
                    entry["product_type"]="card"
                    entry["set_year"] = poke_object.set_year
                    entry["set_month"] = poke_object.set_month
                    result.append(entry)
        
        df = pd.DataFrame(result)
        df['execution_datetime'] = pd.Timestamp.now()
        logger.info(f"price_scraper() df of shape {df.shape}:\n{df.head(5)}")
        return df
    
    except Exception as e:
        logger.error(f"price_scraper(): An error occurred: {e} for poke_object.name {poke_object.name}")

    finally:
        driver.quit()  # Make sure to close the browser
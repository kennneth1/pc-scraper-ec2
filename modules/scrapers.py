import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

import time
import requests
from bs4 import BeautifulSoup

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
            print(f"found product name: {product_name}")

            keywords = [" box", "build", "collection", "blister", "bundle", " tin", "booster pack"]
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
            data["product_name"]=data["product_name"].replace(" ", "-").rstrip('-')
            product_data.append(data)

    for data in product_data:
        print(data)

    print(f'{set_name}: total products scraped={len(product_data)}')
    return product_data

def full_set_scraper(set_name):
    driver = webdriver.Chrome()
    url = f'https://www.pricecharting.com/console/pokemon-{set_name}?sort=highest-price&model-number=&exclude-variants=true&show-images=true&in-collection='

    driver.get(url)

    # Scroll down to load more items
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # down to the bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait for new content to load
        time.sleep(2)  # Adjust the sleep time as necessary

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break  # Exit the loop if no new content is loaded
        last_height = new_height

    # After loading all items, get the page source
    page_source = driver.page_source

    # Close the WebDriver
    driver.quit()

    # Use Beautiful Soup to parse the page source
    soup = BeautifulSoup(page_source, 'html.parser')

    # Find all Pokémon names and numbers
    product_data = []
    for title in soup.find_all('td', class_='title'):
        link = title.find('a')
        if link:
            # Get the product_name name and number from the link text
            product_name = link.text.strip().lower()
            data = {}
            print(f"found product name: {product_name}")

            keywords = [" box", "collection", "blister", "bundle", "build and battle", " tin", "booster pack"]
            # if sealed product
            if any(keyword in product_name for keyword in keywords):                
                data["product_name"]=product_name.replace("#", "")
                data["poke_no"]=""
                data["product_type"]="sealed"
                data["product_name"]=product_name
                data["poke_no"]=""
                data["product_type"]="sealed"
            elif '#' in product_name:
                data["product_name"]=product_name.split('#')[0].rstrip() # i.e. Squirtle #151
                data["poke_no"]=product_name.split('#')[1].strip()
                data["product_type"]="card"
            elif 'energy' in product_name:
                data["product_name"]=product_name
                data["poke_no"]=""
                data["product_type"]="card"
            else:
                data["product_name"]=product_name
                data["poke_no"]=""
                data["product_type"]="other"

            product_data.append(data)

    for data in product_data:
        print(data)

    print(f'{set_name}: total products scraped={len(product_data)}')
    return product_data

def price_scraper(set_name, poke_name, poke_no, prod_type, set_year, set_month):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode

    # Initialize the Chrome driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    url = f'https://www.pricecharting.com/game/pokemon-{set_name}/{poke_name}-{poke_no}'
    
    if prod_type=='sealed':
        url = f'https://www.pricecharting.com/game/pokemon-{set_name}/{poke_name}'
        print(f"sealed product has url: {url}")

    try:
        print(f"price_scraper getting url: {url}")
        driver.get(url)
        time.sleep(5)  # Wait for the page to load
        
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        print("got soup.head.title:", soup.head.title)

        chart_data = driver.execute_script("return VGPC.chart_data;")
        converted_data = convert_timestamps(chart_data)
        
        result = []

        if prod_type=="sealed":
            nm_data = converted_data["used"]
            for entry in nm_data:
                entry['grade']='nearmint'
                entry['poke_name']=poke_name
                entry['poke_no']=poke_no
                entry["set_name"]=set_name
                entry["product_type"]="sealed"
                entry["set_year"] = set_year
                entry["set_month"] = set_month
                result.append(entry)

        else:        
            for grade, price_arr in converted_data.items():
                for entry in price_arr:                    
                    fmt_grade = map_grade(grade)
                    entry['grade']=fmt_grade
                    entry['poke_name']=poke_name
                    entry['poke_no']=poke_no
                    entry["set_name"]=set_name
                    entry["product_type"]="card"
                    entry["set_year"] = set_year
                    entry["set_month"] = set_month
                    result.append(entry)
        
        print("converting to df")
        df = pd.DataFrame(result)
        df['execution_datetime'] = pd.Timestamp.now()
        print("df of shape", df.shape, df.head(5))
        return df
    
    except Exception as e:
        # maybe return empty df, does concat later effected by this exceptions? 
        # Handle the exception
        print(f"An error occurred: {e}")

    finally:
        driver.quit()  # Make sure to close the browser
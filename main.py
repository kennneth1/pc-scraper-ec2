from modules.scrapers import price_scraper, top_50_set_scraper
from modules.cloud import write_csv_to_s3, read_json_from_s3, shutdown_instance
from modules.poke_object import PokeObject
from modules.logger import logger

import pandas as pd
from datetime import datetime


def main():        
    dataframes = []
    logger.info("getting config.json from s3")
    data = read_json_from_s3("configs-pc-psa", "config.json")
    logger.info("got config.json:", str(data)[:99], "...\n")

    print(f"scraping {len(data)} sets")
    set_count=0
    # scrape each set for top 50 products
    for sets, dict in data.items():
        set_name = sets
        if set_name == "champions-path":
            print("reformatting champions path set name to scarlet-&-violet-151")
            set_name = "champion%27s-path"
        if set_name == "151":
            print("reformatting 151 set name to scarlet-&-violet-151")
            set_name = "scarlet-&-violet-151"
        set_year = dict["set_year"]
        set_month = dict["set_month"]
        logger.info(f"scraping set {set_name}: {set_count} of {len(data)}")

        count=0
        # returns up to 50 top expensive products in set
        products = top_50_set_scraper(set_name)

        # scrape historical data for each product (50 products per set, 30 set~, 1500 drivers and scrapes)
        for product in products:
            name = product["product_name"]
            if "." in name:
                name = name.replace(".", "")
                logger.info(". found in pokemon name, reformatting as", name)
        
            num = product["poke_no"]
            product_type = product["product_type"]
            
            logger.info(f"({count}/{len(products)}) scraping {name} #{num} from set: {set_name} - {set_year}")
            poke_object = PokeObject(set_name, name, num, product_type, set_year, set_month)
            df = price_scraper(poke_object, mode="headless")
            dataframes.append(df)           
            count+=1
        set_count+=1

        logger.info("products added to dataframes:", len(dataframes))

    logger.info("concat all dfs")
    # Concatenate all DataFrames in the list into a single DataFrame
    final_df = pd.concat(dataframes, ignore_index=True)

    now = datetime.now()
    formatted_date = now.strftime("%Y-%m-%d")

    #write to s3 bucket as csv
    bucket = "pricecharting-scraper-outputs"
    file_path = f"{formatted_date}/pc.csv"
    logger.info("saving to S3, final_df of shape:", final_df.shape, final_df.head(5))
    write_csv_to_s3(final_df, bucket, file_path, aws_access_key_id=None, aws_secret_access_key=None)
    logger.info("successfully wrote pc.csv to s3")
    shutdown_instance()

if __name__ == "__main__":
    main()
from modules.scrapers import price_scraper, top_50_set_scraper
from modules.cloud import write_csv_to_s3, read_json_from_s3
from modules.poke_object import PokeObject

import pandas as pd
from datetime import datetime


def main():
    dataframes = []
    print("getting config.json from s3")
    data = read_json_from_s3("configs-pc-psa", "config.json")
    print("got config.json:", str(data)[:99], "...\n")

    print(f"scraping {len(data)} sets")
    set_count=0
    # scrape each set for top 50 products
    for sets, dict in data.items():
        set_name = sets
        if set_name == "champions-path":
            set_name = "champion%27s-path"
        set_year = dict["set_year"]
        set_month = dict["set_month"]
        print(f"scraping set {set_name}: {set_count} of {len(data)}")

        count=0
        # returns up to 50 top expensive products in set
        products = top_50_set_scraper(set_name)

        # scrape historical data for each product (50 products per set, 30 set~, 1500 drivers and scrapes)
        for product in products:
            name = product["product_name"]
            num = product["poke_no"]
            product_type = product["product_type"]
            
            print(f"({count}/{len(products)}) scraping {name} #{num} from set: {set_name} - {set_year}")
            poke_object = PokeObject(set_name, name, num, product_type, set_year, set_month)
            df = price_scraper(poke_object, mode="headless")
            dataframes.append(df)           
            count+=1
        set_count+=1

        print("products added to dataframes:", len(dataframes))

    print("concat all dfs")
    # Concatenate all DataFrames in the list into a single DataFrame
    final_df = pd.concat(dataframes, ignore_index=True)

    now = datetime.now()
    formatted_date = now.strftime("%Y-%m-%d")

    #write to s3 bucket as csv
    bucket = "pricecharting-scraper-outputs/"
    file_path = f"{formatted_date}/pc.csv"
    print("saving to S3, final_df of shape:", final_df.shape, final_df.head(5))
    write_csv_to_s3(final_df, bucket, file_path, aws_access_key_id=None, aws_secret_access_key=None)
    print("successfully wrote pc.csv to s3")

if __name__ == "__main__":
    main()
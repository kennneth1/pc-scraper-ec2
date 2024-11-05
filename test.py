from modules.scrapers import top_50_set_scraper
from modules.poke_object import PokeObject
from modules.logger import logger
from modules.scrapers import price_scraper

class test():
    def __init__(self):
        # to test one set"
        self.set_name = "evolutions" 
        self.set_year = "2016"
        self.set_month = "2"
        # to test one pokemon with price_scraper
        self.poke_obj= PokeObject("evolutions", "hitmonchan", "62",
                                 "card", "2016", "2")
        self.mode="headless"

    def test_top_50_set_scraper(self):
        products = top_50_set_scraper(self.set_name)[12:] # get first 10
        self.products = products

    def test_price_scraper(self):
        df = price_scraper(self.poke_obj, mode=self.mode)
        print("test_price_scraper():", df.info())
        return df
    
    def test_loop_set(self, products):
        count=0
        # scrape historical data for each product (50 products per set, 30 set~, 1500 drivers and scrapes)
        for product in self.products:
            name = product["product_name"]
            num = product["poke_no"]
            product_type = product["product_type"]
            
            logger.info(f"({count}/{len(products)}) scraping {name} #{num} from set: {self.set_name} - {self.set_year}")
            poke_object = PokeObject(self.set_name, name, num, product_type, self.set_year, self.set_month)
            df = price_scraper(poke_object, mode=self.mode)
            print(f"test_loop_set() iters: {count}", poke_object.name, "\ndf info:", df.info())
            count+=1
    
if __name__ == "__main__":
    session = test()
    #generate products to self.products
    session.test_top_50_set_scraper()
    session.test_loop_set(session.products)

    #session.test_price_scraper()


    print("tests complete")
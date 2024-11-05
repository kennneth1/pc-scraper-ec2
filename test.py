from modules.scrapers import top_50_set_scraper
from modules.poke_object import PokeObject

class test():
    def __init__(self):
        self.set_name = "evolutions" 
        self.poke_obj= PokeObject("evolutions", "hitmonchan", "62"
                                 "card", "2016", "2")

    def test_top_50_set_scraper(self):
        top_50_set_scraper(self.set_name)
    
if __name__ == "__main__":
    session = test()
    test.test_top_50_set_scraper()
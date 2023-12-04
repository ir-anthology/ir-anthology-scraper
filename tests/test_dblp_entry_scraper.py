from json import load
import unittest

from scripts.dblp_entry_scraper import DBLPEntryScraper
from scripts.dblp_logger import DBLPLogger


class TestDBLPscraper(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        logger = DBLPLogger("")
        logger.log = lambda x: x
        cls.dblp_entry_scraper = DBLPEntryScraper(venuetype="conf", output_directory="tests/output", dblp_logger=logger)

        # SIGIR 1971 test resources
        with open("tests/resources/sigir_1971_dblp.json") as file:
            cls.sigir_1971_dblp_json = load(file)

        # mocked test resources (for bibkey suffix handling)
        with open("tests/resources/mocked_dblp.json") as file:
            cls.mocked_dblp_json = load(file)
    
    def test_scrape_entries_with_year(self):
        entries_sigir_1971 = self.dblp_entry_scraper.scrape_entries("sigir", 1971)
        self.assertEqual([entry["info"] for entry in entries_sigir_1971],
                         [entry["info"] for entry in self.sigir_1971_dblp_json])

        entries_sigir_1975 = self.dblp_entry_scraper.scrape_entries("sigir", 1975)
        self.assertEqual([entry["info"] for entry in entries_sigir_1975],
                         [])        

    def test_scrape_entry_batch(self):
        year = 1971
        payload = {"q": (("streamid:conf/" + "sigir" + ":") +
                         ("year" + ":" + (str(year) + ":") if year else "")),
                   "format": "json",
                   "h": "5",
                   "f": "3"}
        entry_batch = self.dblp_entry_scraper._scrape_entry_batch(payload)
        self.assertEqual([entry["info"] for entry in entry_batch],
                         [entry["info"] for entry in self.sigir_1971_dblp_json[3:8]])
                                                       
        
if __name__ == "__main__":
    unittest.main()


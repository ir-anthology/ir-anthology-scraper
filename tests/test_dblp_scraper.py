from scripts.dblp_scraper import DBLPscraper
from json import load
import unittest


class TestDBLPscraper(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        cls.scraped_entries = []
        cls.scraper = DBLPscraper()
        cls.scraper.logger = lambda x: x
        with open("tests/resources/hits_dblp_api_sigir_1971.json") as file:
            cls.hits_dblp_api_sigir_1971 = load(file)
        with open("tests/resources/hits_dblp_api_sigir_1971_entry_3_to_7.json") as file:
            cls.hits_dblp_api_sigir_1971_entry_3_to_7 = load(file)
        with open("tests/resources/PotthastGBBBFKN21.json") as file:
            cls.entry_PotthastGBBBFKN21 = load(file)
        with open("tests/resources/PotthastGBBBFKN21.bib") as file:
            cls.bibtex_PotthastGBBBFKN21 = "".join(file.readlines())

    def test_scrape_conference(self):
        print("\n\n >>> TO DO - FIX ME <<<\n")

    def test_scrape_conference_with_year(self):
        entries_sigir_1971 = self.scraper.scrape_conference("sigir", 1971)
        self.assertEqual(entries_sigir_1971, self.hits_dblp_api_sigir_1971)

        entries_sigir_1975 = self.scraper.scrape_conference("sigir", 1975)
        self.assertEqual(entries_sigir_1975, [])

    def test_scrape_conference_batch(self):
        year = 1971
        payload = {"q": (("streamid:conf/" + "sigir" + ":") +
                         ("year" + ":" + (str(year) + ":") if year else "")),
                   "format": "json",
                   "h": "5",
                   "f": "3"}
        entry_batch = self.scraper._scrape_conference_batch(payload)
        self.assertEqual(entry_batch, self.hits_dblp_api_sigir_1971_entry_3_to_7)

    def test_strats(self):
        mocked_entries = [{"info":{"year":"2000"}},
                          {"info":{"year":"2000"}},
                          {"info":{"year":"2000"}},
                          {"info":{"year":"2005"}},
                          {"info":{"year":"2010"}}]
        stats = self.scraper.stats(mocked_entries)
        self.assertEqual(stats, {"2000": 3, "2005": 1, "2010": 1})

    def test_scrape_bibtex(self):     
        bibtex_string_scraped = self.scraper.scrape_bibtex(self.entry_PotthastGBBBFKN21)
        self.assertEqual(bibtex_string_scraped, self.bibtex_PotthastGBBBFKN21 + "\n\n")


if __name__ == "__main__":
    unittest.main()


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
        with open("tests/resources/PotthastGBBBFKN21_dblp.json") as file:
            cls.PotthastGBBBFKN21_dblp_json = load(file)
        with open("tests/resources/PotthastGBBBFKN21_dblp.bib") as file:
            cls.PotthastGBBBFKN21_dblp_bibtex = "".join(file.readlines())
        with open("tests/resources/PotthastGBBBFKN21_ir_anthology.bib") as file:
            cls.PotthastGBBBFKN21_ir_anthology_bibtex = "".join(file.readlines())

    def test_scrape_conference(self):
        self.skipTest("TO DO (FIX ME)")

    def test_scrape_conference_with_year(self):
        entries_sigir_1971 = self.scraper.scrape_conference("sigir", 1971)
        self.assertEqual([entry["info"] for entry in entries_sigir_1971],
                         [entry["info"] for entry in self.hits_dblp_api_sigir_1971])

        entries_sigir_1975 = self.scraper.scrape_conference("sigir", 1975)
        self.assertEqual([entry["info"] for entry in entries_sigir_1975],
                         [])

    def test_scrape_conference_batch(self):
        year = 1971
        payload = {"q": (("streamid:conf/" + "sigir" + ":") +
                         ("year" + ":" + (str(year) + ":") if year else "")),
                   "format": "json",
                   "h": "5",
                   "f": "3"}
        entry_batch = self.scraper._scrape_conference_batch(payload)
        self.assertEqual([entry["info"] for entry in entry_batch],
                         [entry["info"] for entry in self.hits_dblp_api_sigir_1971[3:8]])

    def test_strats(self):
        mocked_entries = [{"info":{"year":"2000"}},
                          {"info":{"year":"2000"}},
                          {"info":{"year":"2000"}},
                          {"info":{"year":"2005"}},
                          {"info":{"year":"2010"}}]
        stats = self.scraper.stats(mocked_entries)
        self.assertEqual(stats, {"2000": 3, "2005": 1, "2010": 1})

    def test_scrape_bibtex(self):     
        bibtex_string_scraped = self.scraper.scrape_bibtex(self.PotthastGBBBFKN21_dblp_json)
        self.assertEqual(bibtex_string_scraped, self.PotthastGBBBFKN21_dblp_bibtex)

    def test_amend_bibtex(self):
        bibtex_string_edited = self.scraper.amend_bibtex(self.PotthastGBBBFKN21_dblp_json, self.PotthastGBBBFKN21_dblp_bibtex)
        self.assertEqual(bibtex_string_edited, self.PotthastGBBBFKN21_ir_anthology_bibtex)

    def test_get_personids_string_from_entry(self):
        self.assertEqual(self.scraper._get_personids_string_from_entry(self.PotthastGBBBFKN21_dblp_json),
                         ("87/6573 and " +
                          "67/6306-2 and " +
                          "195/5852 and " +
                          "262/5952 and " +
                          "234/7521 and " +
                          "256/9118 and " +
                          "186/7380 and " +
                          "118/5294 and " +
                          "59/10289 and " +
                          "69/4806-1 and " +
                          "95/1130"))

    def test_get_bibkey_from_entry(self):
        self.assertEqual(self.scraper._get_bibkey_from_entry(self.PotthastGBBBFKN21_dblp_json),
                         "sigir-potthast-2021")
    

    def test_get_sourceid_from_bibtex_line(self):
        bibtex_line = "@inproceedings{DBLP:conf/sigir/PotthastGBBBFKN21,"
        self.assertEqual(self.scraper._get_sourceid_from_bibtex_line(bibtex_line), "DBLP:conf/sigir/PotthastGBBBFKN21")


if __name__ == "__main__":
    unittest.main()


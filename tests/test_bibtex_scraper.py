from os import makedirs
from scripts.dblp.bibtex_scraper import BibtexScraper
from json import load
import unittest

from scripts.logger import Logger


class TestBibtexScraper(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        logger = Logger("")
        logger.log = lambda x: x
        makedirs("tests/output")
        cls.dblp_bibtex_scraper = BibtexScraper(venuetype="conf",
                                                logger=logger,
                                                output_directory="tests/output", 
                                                bibtex_cache_filepath=None,
                                                bibtex_padding="\n\n\n")

        # Potthast 2021 test resources
        with open("tests/resources/PotthastGBBBFKN21_dblp.json") as file:
            cls.PotthastGBBBFKN21_dblp_json = load(file)
        with open("tests/resources/PotthastGBBBFKN21_dblp.bib") as file:
            cls.PotthastGBBBFKN21_dblp_bibtex = "".join(file.readlines()).split("\n\n\n\n")

    def test_scrape_bibtex(self):     
        bibtex_string_scraped = self.dblp_bibtex_scraper.scrape_bibtex(self.PotthastGBBBFKN21_dblp_json[0])
        self.assertEqual(bibtex_string_scraped.strip(), self.PotthastGBBBFKN21_dblp_bibtex[0].strip())
                                                       
        
if __name__ == "__main__":
    unittest.main()


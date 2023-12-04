import json
from os.path import exists, sep
from time import sleep

from utils.utils import get


class BibtexScraper:
    """
    Scrape bibtex from dblp.

    Attributes:
        venuetype: "conf" for conference or "journals" for journals.
        output_directory: The output directory for the scraping process.
        logger: The logger used.
        bibtex_cache_filepath: The path to the file of previously scraped bibtex.
        bibtex_cache: The cache of previously scraped bibtex.
    """

    def __init__(self, venuetype, logger, output_directory, bibtex_cache_filepath, bibtex_padding):
        self.logger = logger
        self.bibtex_padding = bibtex_padding
        self.venuetype = venuetype
        self.bibtex_cache_filepath = bibtex_cache_filepath if bibtex_cache_filepath else output_directory + sep + "dblp_bibtex_cache.txt"
        self.bibtex_cache = self._load_bibtex_cache(self.bibtex_cache_filepath)

    def _load_bibtex_cache(self, bibtex_cache_filepath):
        """
        Load bibtex cache from file.
        
        Args:
            bibtex_cache_filepath: Path to bibtex cache file.
        Returns:
            A dictionary of dblp URLs keys and dblp bibtex strings.
        """
        bibtex_cache = {}
        if bibtex_cache_filepath and exists(bibtex_cache_filepath):
            with open(bibtex_cache_filepath) as file:
                for line in file:
                    url, bibtex = json.loads(line)
                    bibtex_cache[url] = bibtex
        return bibtex_cache

    def scrape_bibtex(self, entry):
        """
        Scrape the bibtex for a given entry from dblp.

        Calls to the API require minimum of 3 second courtesy delay to avoid ERROR 429.

        Args:
            entry: An entry-as-dictionary as provided by the dblp API.
        Returns:
            A bibtex string with three linebreaks added as padding to the end.
        """
        try:
            return self.bibtex_cache[entry["info"]["url"]].strip() + self.bibtex_padding
        except KeyError:
            response = get(self.logger, entry["info"]["url"] + ".bib")
            bibtex = response.text.strip() + self.bibtex_padding
            if self.bibtex_cache_filepath:
                with open(self.bibtex_cache_filepath, "a") as file:
                    file.write(json.dumps([entry["info"]["url"],bibtex]) + "\n")
            sleep(3)
            return bibtex


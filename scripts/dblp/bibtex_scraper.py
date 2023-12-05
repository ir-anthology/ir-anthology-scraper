import json
from os.path import exists, sep
from time import sleep

from utils.utils import get


class BibtexScraper:
    """
    Scrape bibtex from dblp.

    Attributes:
        venuetype: "conf" for conference or "journals" for journals.
        logger: The logger used.
        output_directory: The output directory for the purpose of storing bibtex cache.
        bibtex_cache_filepath: The path to the file of previously scraped bibtex.
        bibtex_cache: The cache of previously scraped bibtex.
        bibtex_padding: Padding between bibtex entries; usually '\n\n\n'.
    """

    def __init__(self, venuetype, logger, output_directory, bibtex_cache_filepath, bibtex_padding):
        self.venuetype = venuetype
        self.logger = logger
        self.output_directory = output_directory 
        self.bibtex_cache_filepath = bibtex_cache_filepath
        self.bibtex_cache = {}
        self._load_bibtex_cache()
        self.bibtex_padding = bibtex_padding

    def _load_bibtex_cache(self):
        """
        Load bibtex cache from file.
        """
        if self.bibtex_cache_filepath and exists(self.bibtex_cache_filepath):
            with open(self.bibtex_cache_filepath) as file:
                for line in file:
                    url, bibtex = json.loads(line)
                    self.bibtex_cache[url] = bibtex
        else:
            
            self.bibtex_cache_filepath = self.output_directory + sep + "dblp_bibtex_cache.txt"
            if exists(self.bibtex_cache_filepath):
                check = input("Bibtex cache file found (" + self.bibtex_cache_filepath + "). Load? [y/n] ")
                if check == "y":
                    self._load_bibtex_cache()
                else:
                    check == input("Bibtex will be appended to existing cache file. Are you sure? [y/n] ")
                    if check == "y":
                        print("Bibtex will be appended to cache - manually check for duplicate!")
                    else:
                        print("Loading existing bibtex cache file.")
                        self._load_bibtex_cache()

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


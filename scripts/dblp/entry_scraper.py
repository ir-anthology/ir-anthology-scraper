import json
from os.path import sep
from time import sleep

from utils.utils import get


class EntryScraper:
    """
    Scrape entries from dblp using the dblp API.

    Attributes:
        venuetype: "conf" for conference or "journals" for journals.
        logger: The logger used.
        api_endpoint: The dblp API endpoint URL.
    """

    def __init__(self, venuetype, logger):
        self.venuetype = venuetype  
        self.logger = logger
        self.api_endpoint = "https://dblp.org/search/publ/api"

    def scrape_entries(self, venue, year):
        """
        Scrape all papers published at a given venue and in a given year from dblp.

        Calls to the API require minimum of 3 second courtesy delay to avoid ERROR 429.
        
        Args:
            venue: Name of the venue for which entries shall be scraped.
            year: Year for which entries shall be scraped (optional).
        Returns:
            A list of entries as dictionaries representing publications of venue and year provided.
        """
        
        self.logger.log("\nScraping venue " + venue + " " + str(year) + ".")
        
        payload = {"q": ("streamid:" + self.venuetype + sep + venue + ":" +
                         "year" + ":" + str(year)),
                   "format": "json",
                   "h": "1000",
                   "f": "0"}
        
        entry_list = []
        
        while len(entry_list) % 1000 == 0 and not (len(entry_list) == 0 and payload["f"] != "0"):
            sleep(3)
            entry_list += self._scrape_entry_batch(payload)
            self.logger.log(str(len(entry_list)) + " entries scraped from dblp API.")
            payload["f"] = str(int(payload["f"]) + 1000)
            
        return [entry for entry in entry_list if entry["info"]["key"].startswith(self.venuetype + sep + venue)]

    def _scrape_entry_batch(self, payload):
        """
        Helper function to scrape specific batch of papers
        published at a given venue and in a given year.
        
        Args:
            payload: Dictionary of query parameters.
        Returns:
            A list of dictionary entries representing
            publications of venue provided.
        """
        
        response = get(self.logger, self.api_endpoint, payload)
        try:
            data = json.loads(response.text)
        except json.decoder.JSONDecodeError:
            self.logger.log(response.text)
        hits = data["result"]["hits"].get("hit", [])
        return hits
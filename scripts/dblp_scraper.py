import requests
import json
import bibtexparser
from pprint import pprint
from time import sleep

class DBLPscraper:

    def __init__(self):
        self.api_endpoint = "https://dblp.org/search/publ/api"
        self.logger = print
        self.bibtex_padding = "\n\n\n"

    def scrape_conference(self, conference, year):
        """
        Scrape all papers published at a given conference (and in a given year).

        Calls to API require minimum of 3 second courtesy delay to avoid ERROR 429.
        
        Args:
            conference: Name of the conference for which entries shall be scraped.
            year: Year for which entries shall be scraped (optional).

        Returns:
            A list of dictionary entries representing publications of conference provided.
        """
        payload = {"q": ("streamid:conf/" + conference + ":" +
                         "year" + ":" + str(year)),
                   "format": "json",
                   "h": "1000",
                   "f": "0"}
        
        entries = []
        
        while len(entries) % 1000 == 0 and not (len(entries) == 0 and payload["f"] != "0"):
            self.logger("Scraping entries " + str(len(entries) + 1) + "...")
            sleep(3)
            entries += self._scrape_conference_batch(payload)
            self.logger("... to " + str(len(entries)))
            payload["f"] = str(int(payload["f"]) + 1000)
            
        return entries

    def _scrape_conference_batch(self, payload):
        """
        Helper function to scrape specific batch of papers published at a given conference (and in a given year).
        
        Args:
            payload: Dictionary of query parameters.

        Returns:
            A list of dictionary entries representing publications of conference provided.
        """
        
        response = self._get(self.api_endpoint, payload)
        try:
            data = json.loads(response.text)
        except json.decoder.JSONDecodeError:
            self.logger(response.text)
        hits = data["result"]["hits"].get("hit", [])
        return hits

    def _get(self, url, parameters = {}):
        response = requests.get(url, parameters)
        delay = 10
        while response.status_code == 429:
            if delay > 60:
                raise TimeoutError("Scrape aborted due to repeated status code 429.")
            else:
                self.logger("Server responded with 429 (Too Many Requests); waiting " + str(delay) + " seconds...")
                sleep(delay)
            response = requests.get(self.api_endpoint, params = payload)
            delay += 10
        return response

    def stats(self, entries):
        """
        Provide entry count by year.

        Args:
            entries: The scraped entries to analyse.

        Returns:
            A dictionary of year-count key-value pairs.
        """
        return {year:[e['info']['year'] for e in entries].count(year) for year in sorted(set([e['info']['year'] for e in entries]))}

    def scrape_bibtex(self, entry):
        """
        Scrape the bibtex for a given entry from dblp.

        Args:
            entry: An entry-as-dictionary as provided by the dblp API.

        Returns:
            A bibtex string with two linebreaks added as padding to the end.
        """
        url = entry["info"]["url"] + ".bib"
        response = self._get(url)
        return response.text.strip() + self.bibtex_padding

    def amend_bibtex(self, entry, bibtex):
        bibtex_lines = bibtex.strip().split("\n")
        first_bibtex_line = bibtex_lines[0]
        bibkey = self._get_bibkey_from_entry(entry)
        authorid_string = self._get_authorid_string_from_entry(entry)
        dblp_bibkey = self._get_dblp_bibkey_from_entry(entry)
        return "\n".join([first_bibtex_line[:first_bibtex_line.find("{")] +  "{" + bibkey + ","] +
                         bibtex_lines[1:-2] + [bibtex_lines[-2] + ","] +
                         ["  dblpbibkey   = " + "{" + dblp_bibkey + "}" + ",",
                          "  authorid     = " + "{" + authorid_string + "}",
                          "}" + self.bibtex_padding])

    def _get_bibkey_from_entry(self, entry):
        def get_last_name_of_first_author(list_or_dict):
            if type(list_or_dict) == list:
                first_author = list_or_dict[0]["text"]
            if type(list_or_dict) == dict:
                first_author = list_or_dict["text"]
            return ("".join([c for c in first_author if (c.isalpha() or c == " ")])).strip().split(" ")[-1]
        return (entry["info"].get("venue", "novenue").lower() + "-" +
                entry["info"]["year"] + "-" +
                get_last_name_of_first_author(entry["info"].get("authors", {"author":{"@pid":"noauthorid","text":"noauthorname"}})["author"]).lower())

    def _get_authorid_string_from_entry(self, entry):
        def get_pids_of_authors(list_or_dict):
            if type(list_or_dict) == list:
                return [author["@pid"] for author in list_or_dict]
            if type(list_or_dict) == dict:
                return [list_or_dict["@pid"]]
        return " and ".join(get_pids_of_authors(
            entry["info"].get("authors", {"author":{"@pid":"noauthorid","text":"noauthorname"}})["author"]))

    def _get_dblp_bibkey_from_entry(self, entry):
        return "DBLP" + ":" + entry["info"]["key"]
        

if __name__ == "__main__":
    scraper = DBLPscraper()


    with open("../tests/resources/hits_dblp_api_sigir_1971_entry_3_to_7.json") as file:
        entry_batch = json.load(file)

    pprint(entry_batch)

    input("CHECK")

    entries_sigir = scraper.scrape_conference("sigir")

    stats = scraper.stats(entries_sigir)

    pprint(stats)

    for year in stats:
        print(year)
        entries_sigir_year = scraper.scrape_conference("sigir", year)
        
        ids_entries_sigir_full_reduced_year = set([e["@id"] for e in entries_sigir if e["info"]["year"] == year])
        ids_entries_sigir_year = set([e["@id"] for e in entries_sigir_year])

        missing_from_year = ids_entries_sigir_full_reduced_year.difference(ids_entries_sigir_year)
        missing_from_full = ids_entries_sigir_year.difference(ids_entries_sigir_full_reduced_year)

        print("Missing from year:", missing_from_year)
        for ID in missing_from_year:
            for entry in entries_sigir:
                if entry["@id"] == ID:
                    pprint(entry)

        print("Missing from full:", missing_from_full)
        for ID in missing_from_full:
            for entry in entries_sigir_year:
                if entry["@id"] == ID:
                    pprint(entry)
        print("="*50)


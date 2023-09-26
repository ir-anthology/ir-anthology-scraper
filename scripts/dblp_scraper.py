import requests
import json
import bibtexparser
from pprint import pprint
from time import sleep
from unicodedata import normalize

class DBLPscraper:

    def __init__(self):
        self.api_endpoint = "https://dblp.org/search/publ/api"
        self.logger = print
        self.bibtex_padding = "\n\n\n"
        self.suffixes = "abcdefghijklmnopqrstuvxyz"

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
        
        entry_list = []
        
        while len(entry_list) % 1000 == 0 and not (len(entry_list) == 0 and payload["f"] != "0"):
            self.logger("Scraping entries " + str(len(entry_list) + 1) + "...")
            sleep(3)
            entry_list += self._scrape_conference_batch(payload)
            self.logger("... to " + str(len(entry_list)))
            payload["f"] = str(int(payload["f"]) + 1000)
            
        return entry_list

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

    def stats(self, entry_list):
        """
        Provide entry count by year.

        Args:
            entry_list: The scraped entries to analyse.

        Returns:
            A dictionary of year-count key-value pairs.
        """
        return {year:[e['info']['year'] for e in entry_list].count(year) for year in sorted(set([e['info']['year'] for e in entry_list]))}

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

    def generate_bibtex_string(self, entry_list, bibtex_list):
        authors = []
        editorid_string = ""
        for entry in entry_list:
            authors.append(self._get_last_name_of_first_author_from_entry(entry))
            if entry["info"]["type"] == "Editorship":
                editorid_string = self._get_authorid_string_from_entry(entry)
        author_suffixes = self._calculate_author_suffixes(authors)
        return "".join([self._amend_bibtex(entry, bibtex, author_suffix, editorid_string)
                        for entry,bibtex,author_suffix in zip(entry_list, bibtex_list, author_suffixes)])

    def _calculate_author_suffixes(self, authors):
        def calculte_suffix_indices(author_count):
            if author_count < 27:
                return [author_count]
            else:
                result = [0,0]
                for _ in range(author_count, 0, -1):
                    if result[-1] == 26:
                        if result[-2] == 26:
                            result.append(0)
                        else:
                            result[-2] += 1
                            result[-1] = 0
                    result[-1] += 1
                return result
        def generate_suffix(count):
            suffixes = " abcdefghijklmnopqrstuvwxyz"
            return "".join(suffixes[suffix_index].strip() for suffix_index in calculte_suffix_indices(count))
    
        author_counts = {author:0 for author in set(authors)}
        author_suffixes = []
        for author in authors:
            author_suffixes.append(generate_suffix(author_counts[author]))
            author_counts[author] += 1
        return author_suffixes

    def _amend_bibtex(self, entry, bibtex, author_suffix, editorid_string):
        bibtex = bibtex.replace("\n                  ", " ")
        bibtex_lines = bibtex.strip().split("\n")

        dblp_bibkey = self._get_dblp_bibkey_from_entry(entry)
        ir_anthology_bibkey = self._get_ir_anthology_bibkey_from_entry(entry) + (("-" + author_suffix) if author_suffix else "")
        authorid_string = self._get_authorid_string_from_entry(entry)
        
        return ("\n".join([bibtex_lines[0].replace(dblp_bibkey, ir_anthology_bibkey)] +
                          bibtex_lines[1:-2] + [bibtex_lines[-2] + ","]) +
                "\n" +
                (("  dblpbibkey   = " + "{" + dblp_bibkey + "}") + ("," if authorid_string or editorid_string else "") + "\n") +
                (("  authorid     = " + "{" + authorid_string + "}" + ("," if editorid_string else "") + "\n") if authorid_string else "") +
                (("  editorid     = " + "{" + editorid_string + "}" + "\n") if editorid_string else "" + "\n") +
                "}" + self.bibtex_padding)

    def _get_authorid_string_from_entry(self, entry):
        def get_pids_of_authors(list_or_dict_or_string):
            if type(list_or_dict_or_string) == list:
                return [author["@pid"] for author in list_or_dict_or_string]
            if type(list_or_dict_or_string) == dict:
                return [list_or_dict_or_string["@pid"]]
            if type(list_or_dict_or_string) == str:
                return [""]
        return " and ".join(get_pids_of_authors(entry["info"].get("authors", {"author":""})["author"]))

    def _get_dblp_bibkey_from_entry(self, entry):
        return "DBLP" + ":" + entry["info"]["key"]
    
    def _get_ir_anthology_bibkey_from_entry(self, entry):
        last_name_of_first_author = self._get_last_name_of_first_author_from_entry(entry)
        return "-".join([entry["info"].get("venue", entry["info"].get("key").split("/")[1]).lower(), entry["info"]["year"]] +
                        ([last_name_of_first_author] if last_name_of_first_author else []))                

    def _get_last_name_of_first_author_from_entry(self, entry):
        authors = entry["info"].get("authors", {"author":""})["author"]
        if type(authors) == list:
            first_author = authors[0]["text"]
        if type(authors) == dict:
            first_author = authors["text"]
        if type(authors) == str:
            first_author = authors
        return self._convert_to_ascii(("".join([c for c in first_author if (c.isalpha() or c == " ")])).strip().lower()).split(" ")[-1]

    def _convert_to_ascii(self, string):
        return normalize("NFD",string).encode("ASCII","ignore").decode("ASCII")

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


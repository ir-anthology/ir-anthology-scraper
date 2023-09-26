import requests
import json
from time import sleep
from unicodedata import normalize

class DBLPscraper:

    def __init__(self):
        self.api_endpoint = "https://dblp.org/search/publ/api"
        self.logger = print
        self.bibtex_padding = "\n\n\n"

    def scrape_conference(self, conference, year):
        """
        Scrape all papers published at a given conference and in a given year from dblp.

        Calls to the API require minimum of 3 second courtesy delay to avoid ERROR 429.
        
        Args:
            conference: Name of the conference for which entries shall be scraped.
            year: Year for which entries shall be scraped (optional).

        Returns:
            A list of entries as dictionaries representing publications of conference and year provided.
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
        Helper function to scrape specific batch of papers
        published at a given conference and in a given year.
        
        Args:
            payload: Dictionary of query parameters.

        Returns:
            A list of dictionary entries representing
            publications of conference provided.
        """
        
        response = self._get(self.api_endpoint, payload)
        try:
            data = json.loads(response.text)
        except json.decoder.JSONDecodeError:
            self.logger(response.text)
        hits = data["result"]["hits"].get("hit", [])
        return hits

    def _get(self, url, parameters = {}):
        """
        Wrapper function for GET request. If the server responds with Error 429,
        the request is repeated after a delay starting at 10 seconds and incrementing
        by 10 seconds until the delay is greater than 60 seconds, at which point this
        function throws a TimeoutError.

        Args:
            url: The API endpoint of dblp.
            parameters: Dictionary of query parameters (optional).

        Returns:
            The API response of dblp to the request.

        Throws:
            TimeoutError if server responds with Error 429 and delay has increased to 60 seconds.
        """
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
            entry_list: A list of entries-as-dictionaries to analyse.

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
            A bibtex string with three linebreaks added as padding to the end.
        """
        url = entry["info"]["url"] + ".bib"
        response = self._get(url)
        return response.text.strip() + self.bibtex_padding

    def generate_bibtex_string(self, entry_list, bibtex_list):
        """
        Generate a string of bibtex entries from a list of entries as provided by the
        dblp API and a list of bibtex string as provided and scraped from the dblp website.

        Args:
            entry_list: List of entries-as-dictionaries.
            bibtex_list: List of bibtex string.
        Returns:
            A string of bibtex entries which have been formatted:
                - IR-Anthology bibkey [CONFERENCE]-[YEAR]-[ASCII-LAST-NAME-OF-FIRST-AUTHOR](-[index])
                - dblpbibkey field added
                - authorid field added
                - editorid field added
        """
        ir_anthology_bibkeys = []
        editorid_string = ""
        for entry in entry_list:
            ir_anthology_bibkeys.append(self._get_ir_anthology_bibkey_from_entry(entry))
            if entry["info"]["type"] == "Editorship":
                editorid_string = self._get_authorid_string_from_entry(entry)
        ir_anthology_bibkeys = self._append_suffixes_to_bibkeys(ir_anthology_bibkeys)
        return "".join([self._amend_bibtex(entry, bibtex, ir_anthology_bibkey, editorid_string)
                        for entry,bibtex,ir_anthology_bibkey in zip(entry_list, bibtex_list, ir_anthology_bibkeys)])

    def _append_suffixes_to_bibkeys(self, ir_anthology_bibkeys):
        """
        Appends deduplication suffixes to a list of bibkeys (-a, -b, ... , -y, -z, -aa, -ab, ...).
        First entry of a given bibkey receives no suffix.

        Args:
            ir_anthology_bibkeys: List of bibkeys
        Returns:
            List of bibkeys with deduplication suffixes added where applicable.
        """
        def calculte_suffix_indices(ir_anthology_bibkey_count):
            if ir_anthology_bibkey_count < 27:
                return [ir_anthology_bibkey_count]
            else:
                result = [0,0]
                for _ in range(ir_anthology_bibkey_count, 0, -1):
                    if result[-1] == 26:
                        if result[-2] == 26:
                            result.append(0)
                        else:
                            result[-2] += 1
                            result[-1] = 0
                    result[-1] += 1
                return result
        def generate_suffix(ir_anthology_bibkey_count):
            suffixes = " abcdefghijklmnopqrstuvwxyz"
            return "".join(suffixes[suffix_index].strip() for suffix_index in calculte_suffix_indices(ir_anthology_bibkey_count))
    
        ir_anthology_bibkey_counts = {ir_anthology_bibkey:0 for ir_anthology_bibkey in set(ir_anthology_bibkeys)}
        
        ir_anthology_bibkey_suffixes = []
        for ir_anthology_bibkey in ir_anthology_bibkeys:
            ir_anthology_bibkey_suffixes.append(generate_suffix(ir_anthology_bibkey_counts[ir_anthology_bibkey]))
            ir_anthology_bibkey_counts[ir_anthology_bibkey] += 1
        return [ir_anthology_bibkey + (("-" + ir_anthology_bibkey_suffix) if ir_anthology_bibkey_suffix else "")
                for ir_anthology_bibkey, ir_anthology_bibkey_suffix in zip(ir_anthology_bibkeys, ir_anthology_bibkey_suffixes)]

    def _amend_bibtex(self, entry, bibtex, ir_anthology_bibkey, editorid_string):
        bibtex = bibtex.replace("\n                  ", " ")
        bibtex_lines = bibtex.strip().split("\n")

        dblp_bibkey = self._get_dblp_bibkey_from_entry(entry)
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
        ir_anthology_bibkeys = entry["info"].get("authors", {"author":""})["author"]
        if type(ir_anthology_bibkeys) == list:
            first_author = ir_anthology_bibkeys[0]["text"]
        if type(ir_anthology_bibkeys) == dict:
            first_author = ir_anthology_bibkeys["text"]
        if type(ir_anthology_bibkeys) == str:
            first_author = ir_anthology_bibkeys
        return self._convert_to_ascii(("".join([c for c in first_author if (c.isalpha() or c == " ")])).strip().lower()).split(" ")[-1]

    def _convert_to_ascii(self, string):
        return normalize("NFD",string).encode("ASCII","ignore").decode("ASCII")


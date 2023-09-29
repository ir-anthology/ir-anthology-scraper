import requests
import json
from time import sleep
from copy import deepcopy
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
        self.logger("Scraping conference " + conference + " " + str(year) + ".")
        
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
                self.logger("Server responded with 429 (Too Many Requests); waiting " + 
                            str(delay) + " seconds...")
                sleep(delay)
            response = requests.get(url, params = parameters)
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
        return {year:[entry['info']['year'] for entry in entry_list].count(year)
                for year in sorted(set([e['info']['year'] for e in entry_list]))}

    def scrape_bibtex(self, entry):
        """
        Scrape the bibtex for a given entry from dblp.

        Calls to the API require minimum of 3 second courtesy delay to avoid ERROR 429.

        Args:
            entry: An entry-as-dictionary as provided by the dblp API.
        Returns:
            A bibtex string with three linebreaks added as padding to the end.
        """
        url = entry["info"]["url"] + ".bib"
        self.logger("Scraping bibtex of entry " + entry["info"]["title"] + 
                    " (" + entry["info"]["url"] + ")...")
        response = self._get(url)
        sleep(3)
        return response.text.strip() + self.bibtex_padding

    def generate_bibtex_string(self, entry_list, bibtex_list):
        """
        Generate a string of bibtex entries from a list of entries as provided by the
        dblp API and a list of bibtex string as provided and scraped from the dblp website.

        entry_list is deep-copied to avoid overwriting of original entry_list object.

        Args:
            entry_list: List of entries-as-dictionaries.
            bibtex_list: List of bibtex string.
        Returns:
            A string of bibtex entries which have been formatted. For details see _amend_bibtex.
        """
        entry_list = deepcopy(entry_list)
        ir_anthology_bibkeys = []
        editors_json = None
        editorid_string = ""
        for entry, bibtex in zip(entry_list, bibtex_list):
            if entry["info"]["type"] == "Editorship":
                editors_json = entry["info"]["authors"]
                editorid_string = self._get_authorid_string_from_entry(entry)
        if editors_json:
            for entry in entry_list:
                if "authors" not in entry["info"]:
                    entry["info"]["authors"] = deepcopy(editors_json)
        for entry in entry_list:
            ir_anthology_bibkeys.append(self._get_ir_anthology_bibkey_from_entry(entry))
        ir_anthology_bibkeys = self._append_suffixes_to_bibkeys(ir_anthology_bibkeys)
        return "".join([self._amend_bibtex(entry, bibtex, ir_anthology_bibkey, editorid_string)
                        for entry,bibtex,ir_anthology_bibkey in zip(entry_list, 
                                                                    bibtex_list, 
                                                                    ir_anthology_bibkeys)])

    def _append_suffixes_to_bibkeys(self, ir_anthology_bibkeys):
        """
        Appends deduplication suffixes to a list of bibkeys.
        First entry of a given bibkey receives no suffixm,
        second entry ends in -2, third ends in -3, and so on.

        Args:
            ir_anthology_bibkeys: List of bibkeys.
        Returns:
            List of bibkeys with deduplication suffixes added where applicable.
        """    
        ir_anthology_bibkey_counts = {}
        
        ir_anthology_bibkeys_with_suffixes = []
        for ir_anthology_bibkey in ir_anthology_bibkeys:
            if ir_anthology_bibkey not in ir_anthology_bibkey_counts:
                ir_anthology_bibkeys_with_suffixes.append(ir_anthology_bibkey)
                ir_anthology_bibkey_counts[ir_anthology_bibkey] = 2
            else:
                ir_anthology_bibkeys_with_suffixes.append(ir_anthology_bibkey + "-" + str(ir_anthology_bibkey_counts[ir_anthology_bibkey]))
                ir_anthology_bibkey_counts[ir_anthology_bibkey] += 1
        return ir_anthology_bibkeys_with_suffixes

    def _amend_bibtex(self, entry, bibtex, ir_anthology_bibkey, editorid_string):
        """
        Amend bibtex as provided by dblp by:
            - replaying dblp bibkey IR-Anthology bibkey
              ([CONFERENCE]-[YEAR]-[ASCII-LAST-NAME-OF-FIRST-AUTHOR](-[index]))
            - adding dblpbibkey field and value
            - adding venue field and venue
            - adding authorid field and value
            - adding editorid field and value

        Args:
            entry: Entry-as-dictionary as provided by the dblp API.
            bibtex: Bibtex string as provided by the dblp website.
            ir_anthology_bibkey: IR-Anthology bibkey as generated from list of entries.
            editorid_string: Editor-ID string of conference at which this entry appeared.
        Returns:
            Bibtex string amended for IR-Anthology.
        """
        bibtex = bibtex.replace("\n                  ", " ")
        bibtex_lines = bibtex.strip().split("\n")
        if entry["info"]["type"] != "Editorship":
            bibtex_lines = self._add_author_line_to_bibtex_lines(bibtex_lines)

        dblp_bibkey = self._get_dblp_bibkey_from_entry(entry)
        venue_string = self._get_venue_string_from_entry(entry)
        authorid_string = self._get_authorid_string_from_entry(entry)
        
        return ("\n".join([bibtex_lines[0].replace(dblp_bibkey, ir_anthology_bibkey)] +
                          bibtex_lines[1:-2] + [bibtex_lines[-2] + ","]) +
                "\n" +
                
                ("  dblpbibkey   = " + "{" + dblp_bibkey + "}" + 
                 ("," if authorid_string or editorid_string or venue_string else "") + "\n") +
                
                (("  venue        = " + "{" + venue_string + "}" +
                  ("," if authorid_string or editorid_string else "") + "\n")
                 if venue_string else "") +
                
                (("  authorid     = " + "{" + authorid_string + "}" +
                  ("," if editorid_string else "") + "\n")
                 if authorid_string and entry["info"]["type"] != "Editorship" else "") +
                
                (("  editorid     = " + "{" + editorid_string + "}" + "\n") 
                 if editorid_string else "") +
                "}" + self.bibtex_padding)

    def _add_author_line_to_bibtex_lines(self, bibtex_lines):
        """
        Add author to bibtex if missing and bibentry type is not 'proceedings'.

        Args:
            bibtex_lines: The bibtex split into lines.
        Returns:
            The bibtex lines provided with author line added as second element,
            if applicable.
        """
        editor_line = ""
        author_line = ""
        for line in bibtex_lines:
            if line.strip().startswith("editor "):
                editor_line = line
            if line.strip().startswith("author "):
                author_line = line
        if editor_line and not author_line:
            bibtex_lines.insert(1, editor_line.replace("editor ", "author "))
        return bibtex_lines

    def _get_authorid_string_from_entry(self, entry):
        """
        Generate author ID string from entry with the format
        [ID-OF-FIRST-AUTHOR] and [ID-OF-SECOND-AUTHOR] and ...

        Args:
            entry: Entry-as-dictionary as provided by the dblp API.
        Returns:
            String of author IDs, separated by " and ".
        """
        authors = entry["info"].get("authors", {"author":""})["author"]
        if type(authors) is list:
            person_ids = [author["@pid"] for author in authors]
        if type(authors) is dict:
            person_ids = [authors["@pid"]]
        if type(authors) is str:
            person_ids = []
        return " and ".join(person_ids)

    def _get_venue_string_from_entry(self, entry):
        """
        Generate venue string from entry with the format
        [FIRST-VENUE] and [SECOND-AUTHOR] and ...

        Args:
            entry: Entry-as-dictionary as provided by the dblp API.
        Returns:
            String of venues, separated by " and ".
        """
        venues = entry["info"].get("venue", [])
        if type(venues) is str:
            venues = [venues]
        return " and ".join(venues)

    def _get_dblp_bibkey_from_entry(self, entry):
        """
        Generate dblp bibkey string string from entry as used in the bibtex
        as provided by the dblp website. As entry as provided by the dblp API
        does not contain the full dblp bibkey, "DBLP:" is prefixed.        

        Args:
            entry: Entry-as-dictionary as provided by the dblp API.
        Returns:
            String representation of the dblp bibkey of this entry.
        """
        return "DBLP" + ":" + entry["info"]["key"]
    
    def _get_ir_anthology_bibkey_from_entry(self, entry):
        """
        Generate IR-Anthology bibkey from entry with the format
        [CONFERENCE]-[YEAR]-[ASCII-LAST-NAME-OF-FIRST-AUTHOR](-[index]

        Args:
            entry: Entry-as-dictionary as provided by the dblp API.
        Returns:
            String representation of the IR-Anthology bibkey of this entry.
        """
        last_name_of_first_author = self._get_last_name_of_first_author_from_entry(entry)
        return "-".join([entry["info"].get("key").split("/")[1].lower(),
                         entry["info"]["year"]] +
                        ([last_name_of_first_author] if (last_name_of_first_author and
                                                         entry["info"]["type"] != "Editorship")
                         else []))                

    def _get_last_name_of_first_author_from_entry(self, entry):
        """
        Get last name of first author of entry (ASCII formatted).

        Args:
            entry: Entry-as-dictionary as provided by the dblp API.
        Returns:
            String representing the last name of the first author.
        """
        authors = entry["info"].get("authors", {"author":""})["author"]
        if type(authors) is list:
            first_author = authors[0]["text"]
        if type(authors) is dict:
            first_author = authors["text"]
        if type(authors) is str:
            first_author = authors
        return self._convert_to_ascii(("".join([c for c in first_author if (c.isalpha() or c == " ")]))
                                      .strip()
                                      .lower()).split(" ")[-1]

    def _convert_to_ascii(self, string):
        """
        Format string to ASCII.

        Args:
            entry: A string.
        Returns:
            ASCII-formatted version of the input string.
        """
        return normalize("NFD",string).encode("ASCII","ignore").decode("ASCII")


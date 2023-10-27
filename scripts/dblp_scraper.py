import requests
import json
from os.path import exists
from os import makedirs
from time import sleep
from copy import deepcopy
from unicodedata import normalize
from datetime import datetime
from re import search


class DBLPscraper:

    def __init__(self, output_directory):
        self.api_endpoint = "https://dblp.org/search/publ/api"
        self.logger = self.log
        self.bibtex_padding = "\n\n\n"
        now = datetime.now()
        with open("scripts/character_map.json") as file:
            self.character_map = json.load(file)
        self.output_directory = output_directory
        self.logger(str(now.year) + "-" + str(now.month) + "-" + (str(now.day).rjust(2,"0")) + " " +
                    str(now.hour) + ":" + str(now.minute) + ":" + (str(now.second).rjust(2,"0")))

    def log(self, message):
        if not exists(self.output_directory):
            makedirs(self.output_directory)
        with open(self.output_directory + "/" + "log.txt", "a") as file:
            file.write(message + "\n")

    def scrape_venue(self, venuetype, venue, year):
        """
        Scrape all papers published at a given venue and in a given year from dblp.

        Calls to the API require minimum of 3 second courtesy delay to avoid ERROR 429.
        
        Args:
            venuetype: Type of venue, either 'conf' or 'journals'.
            venue: Name of the venue for which entries shall be scraped.
            year: Year for which entries shall be scraped (optional).
        Returns:
            A list of entries as dictionaries representing publications of venue and year provided.
        """
        if venuetype not in ["conf", "journals"]:
            raise ValueError("Invalid venue type ('conf' or 'journals').")
        self.logger("\nScraping venue " + venue + " " + str(year) + ".")
        
        payload = {"q": ("streamid:" + venuetype + "/" + venue + ":" +
                         "year" + ":" + str(year)),
                   "format": "json",
                   "h": "1000",
                   "f": "0"}
        
        entry_list = []
        
        while len(entry_list) % 1000 == 0 and not (len(entry_list) == 0 and payload["f"] != "0"):
            sleep(3)
            entry_list += self._scrape_venue_batch(payload)
            self.logger(str(len(entry_list)) + " entries scraped from dblp API.")
            payload["f"] = str(int(payload["f"]) + 1000)
            
        return [entry for entry in entry_list if entry["info"]["key"].startswith(venuetype + "/" + venue)]

    def _scrape_venue_batch(self, payload):
        """
        Helper function to scrape specific batch of papers
        published at a given venue and in a given year.
        
        Args:
            payload: Dictionary of query parameters.
        Returns:
            A list of dictionary entries representing
            publications of venue provided.
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
        #self.logger("Scraping bibtex of entry " + entry["info"]["title"] + 
        #            " (" + entry["info"]["url"] + ")...")
        response = self._get(url)
        sleep(3)
        return response.text.strip() + self.bibtex_padding

    def generate_bibtex_string(self, entry_list, bibtex_list, venuetype):
        """
        Generate a string of bibtex entries from a list of entries as provided by the
        dblp API and a list of bibtex string as provided and scraped from the dblp website.

        entry_list is deep-copied to avoid overwriting of original entry_list object.

        Args:
            entry_list: List of entries-as-dictionaries.
            bibtex_list: List of bibtex string.
            venuetype: Type of venue, either 'conf' or 'journals'.
        Returns:
            A string of bibtex entries which have been formatted.
        """
        entry_list = deepcopy(entry_list)
        bibtex_lines_list = [bibtex.replace("\n                  ", " ").strip().split("\n") for bibtex in bibtex_list]

        editor_map = {}
        # GET EDITOR STRING AND MATCH WITH EDITOR ID STRING AND PERSONS JSON
        for entry, bibtex_lines in zip(entry_list, bibtex_lines_list):
            if entry["info"]["type"] == "Editorship":
                for bibtex_line in bibtex_lines:
                    if bibtex_line.strip().startswith("editor"):
                        match = search("{.*}", bibtex_line)
                        if match:
                            editor = bibtex_line[match.start():match.end()]
                            editor_map[editor] = {"editorid_string":"{" + self._get_personid_string_from_entry(entry) + "}",
                                                  "persons":entry["info"]["authors"]}
        if editor_map == {}:
            self.logger("No editors found.")
        dblp_bibkeys = []
        
        # ADD DBLPBIBKEY, VENUE AND (WHERE APPLICABLE) AUTHOR, EDITOR, AUTHORID AND EDITORID TO BIBTEX
        for entry, bibtex_lines in zip(entry_list, bibtex_lines_list):

            dblp_bibkey = self._get_dblp_bibkey_from_entry(entry)
            bibtex_lines.insert(-1, "  dblpbibkey   = " + "{" + dblp_bibkey + "}")
            dblp_bibkeys.append(dblp_bibkey)
            
            venue_string = self._get_venue_string_from_entry(entry)
            if venue_string:
                bibtex_lines.insert(-1, "  venue        = " + "{" + venue_string + "}")

            editorship = entry["info"]["type"] == "Editorship"

            author = False
            author_string = ""
            authorid = False
            authorid_string = ""
            editor = False
            editor_string = ""
            editorid = False
            editorid_string = ""

            # GET AUTHOR AND EDITOR STRING FROM BIBTEX
            for bibtex_line in bibtex_lines:
                if bibtex_line.strip().startswith("author"):
                    match = search("{.*}", bibtex_line)
                    author_string = bibtex_line[match.start():match.end()]
                    author = True
                if bibtex_line.strip().startswith("editor"):
                    match = search("{.*}", bibtex_line)
                    editor_string = bibtex_line[match.start():match.end()]
                    editor = True

            # SET EDITOR AND EDITOR ID STRING
            if editor:
                if editor_string in editor_map:
                    editorid_string = editor_map[editor_string]["editorid_string"]
                    editorid = True
                else:
                    editorid_string = "{ERROR: NO EDITORID}"
                    self.logger("No editorid for entry " + venue_string + " " + entry["info"]["year"] + " " + entry["info"]["url"] + ".html?view=bibtex")
            else:
                editor_string = "{ERROR: NO EDITORS}"
                self.logger("No editor for entry " + venue_string + " " + entry["info"]["year"] + " " + entry["info"]["url"] + ".html?view=bibtex")
                editorid_string = "{ERROR: NO EDITORID}"
                self.logger("No editorid for entry " + venue_string + " " + entry["info"]["year"] + " " + entry["info"]["url"] + ".html?view=bibtex")

            # SET AUTHOR AND AUTHOR ID STRING
            if author:
                authorid_string = "{" + self._get_personid_string_from_entry(entry) + "}"
                authorid = True
            else:
                if not editorship:
                    if editor:
                        author_string = editor_string
                        if editorid:
                            authorid_string = editorid_string
                            authorid = True
                        else:
                            authorid_string = "{ERROR: NO EDITORID}"
                            self.logger("No authorid for entry " + venue_string + " " + entry["info"]["year"] + " " + entry["info"]["url"] + ".html?view=bibtex")
                    else:
                        author_string = "{ERROR: NO EDITORS}"
                        self.logger("No author for entry " + venue_string + " " + entry["info"]["year"] + " " + entry["info"]["url"] + ".html?view=bibtex")
                        authorid_string = "{ERROR: NO EDITORID}"
                        self.logger("No authorid for entry " + venue_string + " " + entry["info"]["year"] + " " + entry["info"]["url"] + ".html?view=bibtex")

            # HANDLE PERSON DATA IN JSON
            if editorship:
                if "authors" in entry["info"]: del entry["info"]["authors"]
            else:
                if "authors" not in entry["info"]:
                    if editor and editor_string in editor_map:
                        entry["info"]["authors"] = editor_map[editor_string]["persons"]
                    else:
                        self.logger("No persons for entry " + venue_string + " " + entry["info"]["year"] + " " +
                                    entry["info"]["url"] + ".html?view=bibtex. Trying to obtain persons from bibtex instead.")
                        if editor:
                            entry["info"]["authors"] = {"author":[{"@pid":"PERSONIDERROR",
                                                                    "text":author_text.strip()}
                                                                    for author_text in editor_string[1:-1].split(" and ")]}
                        else:
                            self.logger("Unable to get persons from bibtex for entry " + venue_string + " " + entry["info"]["year"] + " " +
                                        entry["info"]["url"] + ".html?view=bibtex")
                            entry["info"]["authors"] = {"author":[{"@pid":"PERSONIDERROR",
                                                                   "text":"PERSONTEXTERROR"}]} 

            if not editor and editor_string:
                bibtex_lines.insert(2 if author else 1,
                                    "  editor       = " + editor_string)
                editor = True
            if not author and author_string:
                bibtex_lines.insert( 1,
                                    "  author       = " + author_string)
                author = True
            if author: 
                bibtex_lines.insert(-1,
                                    "  authorid     = " + authorid_string)
            if editor:
                bibtex_lines.insert(-1,
                                    "  editorid     = " + editorid_string)

        # GENERATE IR-ANTHOLOGY BIBKEYS
        ir_anthology_bibkeys = self._append_suffixes_to_bibkeys([self._get_ir_anthology_bibkey_from_entry(entry, venuetype) for entry in entry_list])

        # REPLACE DBLP BIBKEY WITH IR-ANTHOLOGY BIBKEYS
        for bibtex_lines, dblp_bibkey, ir_anthology_bibkey in zip(bibtex_lines_list, dblp_bibkeys, ir_anthology_bibkeys):
            bibtex_lines[0] = bibtex_lines[0].replace(dblp_bibkey, ir_anthology_bibkey)

        # CONCATENATE
        return "".join([self._join_bibtex_lines(bibtex_lines) for bibtex_lines in bibtex_lines_list])
    
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

    def _join_bibtex_lines(self, bibtex_lines):
        """
        Concatenates a list of bibtex lines to a bibentry.

        Args:
            bibtex_lines: List of bibtex lines.
        Returns:
            A bibtex entry.
        """
        STRING = bibtex_lines[0]
        for line in bibtex_lines[1:-2]:
            STRING += ("\n" + line + ("," if not line.endswith(",") else "")) if line else ""
        STRING += ("\n" + bibtex_lines[-2]) if bibtex_lines[-2] else ""
        STRING += "\n" + bibtex_lines[-1] + self.bibtex_padding
        return STRING

    def _get_personid_string_from_entry(self, entry):
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
    
    def _get_ir_anthology_bibkey_from_entry(self, entry, venuetype):
        """
        Generate IR-Anthology bibkey from entry with the format
        [VENUE]-[YEAR]-[ASCII-LAST-NAME-OF-FIRST-AUTHOR](-[index]

        Args:
            entry: Entry-as-dictionary as provided by the dblp API.
            venuetype: Type of venue, either 'conf' or 'journals'.
        Returns:
            String representation of the IR-Anthology bibkey of this entry.
        """
        last_name_of_first_author = self._get_last_name_of_first_author_from_entry(entry)
        return "-".join([{"conf":"conf","journals":"jrnl"}[venuetype],
                         entry["info"].get("key").split("/")[1].lower(),
                         entry["info"]["year"]] +
                        ([last_name_of_first_author] if last_name_of_first_author else []))                

    def _get_last_name_of_first_author_from_entry(self, entry):
        """
        Get last name of first author of entry (ASCII formatted).

        Args:
            entry: Entry-as-dictionary as provided by the dblp API.
        Returns:
            String representing the last name of the first author.
        """
        #self.logger(str(entry))
        authors = entry["info"].get("authors", {"author":""})["author"]
        if type(authors) is list:
            first_author = authors[0]["text"]
        if type(authors) is dict:
            first_author = authors["text"]
        if type(authors) is str:
            first_author = authors
        return self._convert_name("".join([c for c in first_author if (c.isalpha() or c == " ")])
                                  .strip()
                                  .split(" ")[-1]
                                  .lower())

    def _convert_name(self, string):
        def normalize_to_ascii(character):
            return normalize("NFD",character).encode("ASCII","ignore").decode("ASCII")
        """
        Format string to ASCII.

        Args:
            entry: A string.
        Returns:
            ASCII-formatted version of the input string.
        """
        return "".join([self.character_map.get(character, normalize_to_ascii(character)) for character in string])


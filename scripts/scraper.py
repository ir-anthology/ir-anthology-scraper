from copy import deepcopy
from csv import writer
from json import dump
from re import search
from os.path import exists, sep
from os import makedirs
import traceback

from tqdm import tqdm
from scripts.dblp.bibtex_scraper import BibtexScraper
from scripts.dblp.entry_scraper import EntryScraper
from scripts.logger import Logger

from utils.utils import convert_string_to_ascii

class Scraper:
    """
    Scraper to wrap the dblp entry and bibtex scraper and generate bibtex strings from
    entries and their respective bibtex strings.

    Attributes:
        venuetype: "conf" for conference or "journals" for journals.
        output_directory: The root directory for the output, automatically set
                          to the output_directory/venuetype as provided.
        logger: The logger used.
        bibtex_padding: Padding between bibtex entries; set to '\n\n\n'.
        dblp_entry_scraper: The scraper to scrape dblp entries.
        dblp_bibtex_scraper: The scraper to scrape dblp bibtex.
    """

    def __init__(self, venuetype, output_directory, bibtex_cache_filepath):
        if venuetype not in ["conf", "journals"]:
            raise ValueError("Invalid venue type ('conf' or 'journals').")
        else:
            self.venuetype = venuetype
        self.output_directory = output_directory + sep + venuetype
        self.logger = Logger(self.output_directory)
        if not exists(self.output_directory):
            makedirs(self.output_directory)
        self.bibtex_padding = "\n\n\n"
        self.dblp_entry_scraper = EntryScraper(venuetype, self.logger)
        self.dblp_bibtex_scraper = BibtexScraper(venuetype, self.logger, self.output_directory, bibtex_cache_filepath, self.bibtex_padding)

    def scrape_entries_and_bibtex(self, venue, year):
        """
        Scrape entries and bibtex for venue and year from dblp.

        Args:
            venue: The name of the venue, e.g. 'sigir'.
            year: The year of the conference or journal, e.g. 1971.
        Returns:
            A touple of entry and bibtex lists.        
        """
        print("Scraping bibtex entries of " + venue + " " + str(year) + "...")
        fails = {}
        try:
            entry_list = self.dblp_entry_scraper.scrape_entries(venue, year)
            with open(self.logger.logger_directory + sep + "dblp_json_results.csv", "a") as file:
                csv_writer = writer(file, delimiter=",")
                csv_writer.writerow([venue, year, len(entry_list)])
            if entry_list != []:
                bibtex_list = [self.dblp_bibtex_scraper.scrape_bibtex(entry) for entry in tqdm(entry_list, total=len(entry_list))]
                return entry_list, bibtex_list
            else:
                return [], []
        except:
            self.logger.log(traceback.format_exc())
            with open(self.logger.logger_directory + sep + "failed.json", "w") as file:
                if venue not in fails:
                    fails[venue] = []
                fails[venue].append(year)
                dump({"venuetype":self.venuetype,"venues":fails}, file)
                return [], []
        
    def generate_bibtex_string(self, entry_list, bibtex_list):
        """
        Generate a string of bibtex entries from a list of entries as provided by the
        dblp API and a list of bibtex string as provided and scraped from the dblp website.

        entry_list is deep-copied to avoid overwriting of original entry_list object.

        Args:
            entry_list: List of entries-as-dictionaries.
            bibtex_list: List of bibtex string.
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
            self.dblp_logger.log("No editors found.")
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
                    self.dblp_logger.log("No editorid for entry " + venue_string + " " + entry["info"]["year"] + " " + entry["info"]["url"] + ".html?view=bibtex")
            else:
                editor_string = "{ERROR: NO EDITORS}"
                self.dblp_logger.log("No editor for entry " + venue_string + " " + entry["info"]["year"] + " " + entry["info"]["url"] + ".html?view=bibtex")
                editorid_string = "{ERROR: NO EDITORID}"
                self.dblp_logger.log("No editorid for entry " + venue_string + " " + entry["info"]["year"] + " " + entry["info"]["url"] + ".html?view=bibtex")

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
                            self.dblp_logger.log("No authorid for entry " + venue_string + " " + entry["info"]["year"] + " " + entry["info"]["url"] + ".html?view=bibtex")
                    else:
                        author_string = "{ERROR: NO EDITORS}"
                        self.dblp_logger.log("No author for entry " + venue_string + " " + entry["info"]["year"] + " " + entry["info"]["url"] + ".html?view=bibtex")
                        authorid_string = "{ERROR: NO EDITORID}"
                        self.dblp_logger.log("No authorid for entry " + venue_string + " " + entry["info"]["year"] + " " + entry["info"]["url"] + ".html?view=bibtex")

            # HANDLE PERSON DATA IN JSON
            if editorship:
                if "authors" in entry["info"]: del entry["info"]["authors"]
            else:
                if "authors" not in entry["info"]:
                    if editor and editor_string in editor_map:
                        entry["info"]["authors"] = editor_map[editor_string]["persons"]
                    else:
                        self.dblp_logger.log("No persons for entry " + venue_string + " " + entry["info"]["year"] + " " +
                                        entry["info"]["url"] + ".html?view=bibtex. Trying to obtain persons from bibtex instead.")
                        if editor:
                            entry["info"]["authors"] = {"author":[{"@pid":"PERSONIDERROR",
                                                                    "text":author_text.strip()}
                                                                    for author_text in editor_string[1:-1].split(" and ")]}
                        else:
                            self.dblp_logger.log("Unable to get persons from bibtex for entry " + venue_string + " " + entry["info"]["year"] + " " +
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
        ir_anthology_bibkeys = self._append_suffixes_to_bibkeys([self._get_ir_anthology_bibkey_from_entry(entry) for entry in entry_list])

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
    
    def _get_ir_anthology_bibkey_from_entry(self, entry):
        """
        Generate IR-Anthology bibkey from entry with the format
        [VENUE]-[YEAR]-[ASCII-LAST-NAME-OF-FIRST-AUTHOR](-[index]

        Args:
            entry: Entry-as-dictionary as provided by the dblp API.
        Returns:
            String representation of the IR-Anthology bibkey of this entry.
        """
        last_name_of_first_author = self._get_last_name_of_first_author_from_entry(entry)
        return "-".join([{"conf":"conf","journals":"jrnl"}[self.venuetype],
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
        return convert_string_to_ascii("".join([c for c in first_author if (c.isalpha() or c == " ")])
                            .strip()
                            .split(" ")[-1]
                            .lower())
from scripts.dblp_scraper import DBLPscraper
from json import load
from copy import deepcopy
import unittest


class TestDBLPscraper(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        cls.scraper = DBLPscraper()
        cls.scraper.logger = lambda x: x

        # Potthast 2021 test resources
        with open("tests/resources/PotthastGBBBFKN21_dblp.json") as file:
            cls.PotthastGBBBFKN21_dblp_json = load(file)
        with open("tests/resources/PotthastGBBBFKN21_dblp.bib") as file:
            cls.PotthastGBBBFKN21_dblp_bibtex = "".join(file.readlines())
        with open("tests/resources/PotthastGBBBFKN21_ir_anthology.bib") as file:
            cls.PotthastGBBBFKN21_ir_anthology_bibtex = "".join(file.readlines())
        with open("tests/resources/PotthastGBBBFKN21_ir_anthology_noauthorid.bib") as file:
            cls.PotthastGBBBFKN21_ir_anthology_bibtex_noauthorid = "".join(file.readlines())
        with open("tests/resources/PotthastGBBBFKN21_ir_anthology_noeditorid.bib") as file:
            cls.PotthastGBBBFKN21_ir_anthology_bibtex_noeditorid = "".join(file.readlines())
        with open("tests/resources/PotthastGBBBFKN21_ir_anthology_noeditorid_noauthorid.bib") as file:
            cls.PotthastGBBBFKN21_ir_anthology_bibtex_noeditorid_noauthorid = "".join(file.readlines())

        # SIGIR 1971 test resources
        with open("tests/resources/sigir_1971_dblp.json") as file:
            cls.sigir_1971_dblp_json = load(file)
        with open("tests/resources/sigir_1971_dblp.bib") as file:
            cls.sigir_1971_dblp_bibtex = "".join(file.readlines()).split("\n\n\n\n")
        with open("tests/resources/sigir_1971_ir_anthology.bib") as file:
            cls.sigir_1971_ir_anthology_bibtex = "".join(file.readlines())

        # mocked test resources (for bibkey suffix handling)
        with open("tests/resources/mocked_dblp.json") as file:
            cls.mocked_dblp_json = load(file)
        with open("tests/resources/mocked_dblp.bib") as file:
            cls.mocked_dblp_bibtex = "".join(file.readlines()).split("\n\n\n\n")
        with open("tests/resources/mocked_ir_anthology.bib") as file:
            cls.mocked_ir_anthology_bibtex = "".join(file.readlines())

    def test_scrape_conference_with_year(self):
        entries_sigir_1971 = self.scraper.scrape_conference("sigir", 1971)
        self.assertEqual([entry["info"] for entry in entries_sigir_1971],
                         [entry["info"] for entry in self.sigir_1971_dblp_json])

        entries_sigir_1975 = self.scraper.scrape_conference("sigir", 1975)
        self.assertEqual([entry["info"] for entry in entries_sigir_1975],
                         [])        

    def test_scrape_conference_batch(self):
        year = 1971
        payload = {"q": (("streamid:conf/" + "sigir" + ":") +
                         ("year" + ":" + (str(year) + ":") if year else "")),
                   "format": "json",
                   "h": "5",
                   "f": "3"}
        entry_batch = self.scraper._scrape_conference_batch(payload)
        self.assertEqual([entry["info"] for entry in entry_batch],
                         [entry["info"] for entry in self.sigir_1971_dblp_json[3:8]])

    def test_scrape_bibtex(self):     
        bibtex_string_scraped = self.scraper.scrape_bibtex(self.PotthastGBBBFKN21_dblp_json[0])
        self.assertEqual(bibtex_string_scraped, self.PotthastGBBBFKN21_dblp_bibtex)

    def test_stats(self):
        mocked_entries = [{"info":{"year":"2000"}},
                          {"info":{"year":"2000"}},
                          {"info":{"year":"2000"}},
                          {"info":{"year":"2005"}},
                          {"info":{"year":"2010"}}]
        stats = self.scraper.stats(mocked_entries)
        self.assertEqual(stats, {"2000": 3, "2005": 1, "2010": 1})

    def test_calculate_author_suffixes(self):
        self.assertEqual(self.scraper._append_suffixes_to_bibkeys
                         (["author1","author2","author1","author1","author1","author2"]),
                         ["author1","author2","author1-2","author1-3","author1-4","author2-2"])

    def test_amend_bibtex(self):
        editorid_string = "38/2451-1 and 04/4087 and s/TorstenSuel and c/PabloCastells and 40/5446 and 18/6321"
        bibtex_string_edited = self.scraper._amend_bibtex(self.PotthastGBBBFKN21_dblp_json[0],
                                                          self.PotthastGBBBFKN21_dblp_bibtex,
                                                          "sigir-2021-potthast",
                                                          editorid_string)
        self.assertEqual(bibtex_string_edited, self.PotthastGBBBFKN21_ir_anthology_bibtex)

        json_without_author = deepcopy(self.PotthastGBBBFKN21_dblp_json[0])
        del json_without_author["info"]["authors"]
        
        # no author id
        bibtex_string_edited = self.scraper._amend_bibtex(json_without_author,
                                                          self.PotthastGBBBFKN21_dblp_bibtex,
                                                          "sigir-2021-potthast",
                                                          editorid_string)
        self.assertEqual(bibtex_string_edited, self.PotthastGBBBFKN21_ir_anthology_bibtex_noauthorid)

        # no editor id
        bibtex_string_edited = self.scraper._amend_bibtex(self.PotthastGBBBFKN21_dblp_json[0],
                                                          self.PotthastGBBBFKN21_dblp_bibtex,
                                                          "sigir-2021-potthast",
                                                          "")
        self.assertEqual(bibtex_string_edited, self.PotthastGBBBFKN21_ir_anthology_bibtex_noeditorid)

        # no editor id and no author id
        bibtex_string_edited = self.scraper._amend_bibtex(json_without_author,
                                                          self.PotthastGBBBFKN21_dblp_bibtex,
                                                          "sigir-2021-potthast",
                                                          "")
        self.assertEqual(bibtex_string_edited, self.PotthastGBBBFKN21_ir_anthology_bibtex_noeditorid_noauthorid)

    def test_add_author_line_to_bibtex_lines(self):
        bibtex_lines_without_author = ["@inproceedings{DBLP:conf/test/T23,",
                                       "  editor       = {Jack Doe},",
                                       "  authorid     = {9},",
                                       "  editorid     = {9}",
                                       "}"]

        bibtex_lines_with_author = ["@inproceedings{DBLP:conf/test/T23,",
                                    "  author       = {Jack Doe},",
                                    "  editor       = {Jack Doe},",
                                    "  authorid     = {9},",
                                    "  editorid     = {9}",
                                    "}"]
        self.assertEqual(self.scraper._add_author_line_to_bibtex_lines(bibtex_lines_without_author), bibtex_lines_with_author)
        

    def test_get_authorid_string_from_entry(self):
        self.assertEqual(self.scraper._get_authorid_string_from_entry(self.PotthastGBBBFKN21_dblp_json[0]),
                         ("87/6573 and " +
                          "67/6306-2 and " +
                          "195/5852 and " +
                          "262/5952 and " +
                          "234/7521 and " +
                          "256/9118 and " +
                          "186/7380 and " +
                          "118/5294 and " +
                          "59/10289 and " +
                          "69/4806-1 and " +
                          "95/1130"))

    def test_get_venue_string_from_entry(self):
        mocked_entry = {"info":{"venue":["venue1", "venue2"]}}
        self.assertEqual(self.scraper._get_venue_string_from_entry(mocked_entry), "venue1 and venue2")
        mocked_entry = {"info":{"venue":"venue"}}
        self.assertEqual(self.scraper._get_venue_string_from_entry(mocked_entry), "venue")
        mocked_entry = {"info":{}}
        self.assertEqual(self.scraper._get_venue_string_from_entry(mocked_entry), "")

    def test_get_ir_anthology_bibkey_from_entry(self):
        self.assertEqual(self.scraper._get_ir_anthology_bibkey_from_entry(self.PotthastGBBBFKN21_dblp_json[0]),
                         "sigir-2021-potthast")

    def test_get_dblp_bibkey_from_entry(self):
        self.assertEqual(self.scraper._get_dblp_bibkey_from_entry(self.PotthastGBBBFKN21_dblp_json[0]),
                         "DBLP:conf/sigir/PotthastGBBBFKN21")

    def test_generate_bibtex_string(self):
        
        generated_bibtex_string = self.scraper.generate_bibtex_string(self.sigir_1971_dblp_json,
                                                                      self.sigir_1971_dblp_bibtex)
        self.assertEqual(generated_bibtex_string, self.sigir_1971_ir_anthology_bibtex)

        generated_bibtex_string = self.scraper.generate_bibtex_string(self.mocked_dblp_json,
                                                                      self.mocked_dblp_bibtex)
        self.assertEqual(generated_bibtex_string, self.mocked_ir_anthology_bibtex)

    def test_convert_to_ascii(self):
        with_diacritics    = "áàâǎőȍãȧạṳăȃāașçę"
        without_diacritics = "aaaaooaaauaaaasce"
        self.assertEqual(self.scraper._convert_to_ascii(with_diacritics), without_diacritics)
                                                       
        
if __name__ == "__main__":
    unittest.main()


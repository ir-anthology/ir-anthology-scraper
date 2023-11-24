from datetime import datetime
from pprint import pprint
from re import sub
import fitz
import bibtexparser
from glob import glob
from os.path import dirname, exists, sep
from os import makedirs
from utils.utils import normalize_to_ascii

class PDFextractor:

    def __init__(self, proceedings_directory):
        self.proceedings_directories = sorted(glob(proceedings_directory + sep + "*" + sep + "*"))
        now = datetime.now()
        self.start = ((str(now.year)) + "-" + (str(now.month).rjust(2,"0")) + "-" + (str(now.day).rjust(2,"0")) + "_" +
                      (str(now.hour).rjust(2,"0")) + "-" + (str(now.minute).rjust(2,"0")))
        
        self.log_directory = "extraction_logs"
        if not exists(self.log_directory): makedirs(self.log_directory)
        self.log_file = self.log_directory + sep + self.start + ".txt"

    def bibliography(self, entry):
        bibkey, title, authors, doi, pages = (entry["ID"], 
                                              entry["title"], 
                                              entry.get("author", None),
                                              entry.get("doi", None), 
                                              entry.get("pages"))
        first_page = self.get_first_page(pages)
        page_count = self.get_page_count(pages)
        if self.get_first_page(pages) != None and self.get_page_count(pages) != None and authors:
            return (bibkey, 
                    title,
                    self.convert_title_to_filename(title),
                    [self.normalize_name_to_ascii(author.split(" ")[-1]) for author in authors.split(" and ")],
                    doi,
                    first_page,
                    page_count)
        else:
            return None

    def extract(self, venue, year, test):
        proceedings_pdf_filepaths = sorted(glob("../sources/proceedings-by-venue" + sep + 
                                                venue + sep + year + sep + 
                                                venue + "-" + year + "-" + "proceedings" + "*.pdf"))
        bibfile_path = ("../conf" + sep +
                        venue + sep + year + sep + 
                        "conf" + "-" + venue + "-" + year + ".bib")
            
        if not exists(bibfile_path):
            return 0,0
        
        with open(bibfile_path) as bibfile:
            entries = [item for item in 
                       [self.bibliography(entry) for entry in bibtexparser.load(bibfile).entries] if item]

        entries_found_by_doi = {}
        entries_found_by_title = {}

        for proceeding_pdf_filepath in proceedings_pdf_filepaths:
            proceedings_offset_filepath = proceeding_pdf_filepath[:-3] + "txt"
            if not exists(proceedings_offset_filepath):
                with open(self.log_file) as logfile:
                    logfile.write("Proceedings file " + proceeding_pdf_filepath + " without offset file. Setting offset to 0.")
                    offset = 0
            else:
                with open(proceedings_offset_filepath) as txt:
                    offset = int(txt.readline().strip())
            with fitz.open(proceeding_pdf_filepath) as pdf:
                for page_number, page in enumerate(pdf.pages()):
                    page_text = page.get_text().replace("\n", " ")
                    page_text_preprocessed = sub(" +", " ", page_text.lower()).replace("ﬁ","fi")

                    for bibkey, title, title_as_filename, authors, doi, first_page, pages in entries:
                        authors_lowered = [author.lower() for author in authors]
                        if bibkey not in entries_found_by_doi and bibkey not in entries_found_by_title:
                            if doi:
                                doi = doi.replace("\\", "")
                            if (title.lower() in page_text_preprocessed and
                                doi and doi in page_text):
                                entries_found_by_doi[bibkey] = [doi,
                                                                proceeding_pdf_filepath, 
                                                                page_number, page_number+pages]
                            elif (title.lower() in page_text_preprocessed and
                                  "abstract" in page_text_preprocessed and
                                  False not in [author_lowered in page_text_preprocessed for author_lowered in authors_lowered] and
                                  page_number > first_page + offset - 10):
                                entries_found_by_title[bibkey] = [title_as_filename,
                                                                  proceeding_pdf_filepath, 
                                                                  page_number, page_number+pages]
                                
        for entries_found, output_directory in [[entries_found_by_doi,
                                                 "../sources/papers-by-venue-extracted-by-doi" + ("-test-2" if test else "")],
                                                [entries_found_by_title,
                                                 "../sources/papers-by-venue-extracted-by-title" + ("-test-2" if test else "")]]:
            for bibkey, values in entries_found.items():
                doi_or_title_as_pathname, proceeding_pdf_filepath, from_page, to_page = values
                with fitz.open(proceeding_pdf_filepath) as pdf:
                    paper = fitz.open()
                    paper.insert_pdf(pdf, from_page=from_page, to_page=to_page)
                    filepath = (output_directory + sep + 
                                venue + sep + year + sep + 
                                doi_or_title_as_pathname + ".pdf")
                    if not exists(dirname(filepath)):
                        makedirs(dirname(filepath))
                    paper.save(filepath)

        return len(entries_found_by_doi), len(entries_found_by_title)

    def run(self, test):
        paper_count = [0, 0]

        for proceedings_directory in self.proceedings_directories:
            venue, year = proceedings_directory.split("/")[-2:]
            paper_count = [i+j for i,j in zip(paper_count, self.extract(venue, year, test))]
            with open(self.log_file, "a") as file:
                file.write(proceedings_directory + " " + venue + " " + str(year) + "\n")

        with open(self.log_file, "a") as file:
            file.write(str(paper_count))

    def get_page_count(self, pages):
        if not pages:
            return None
        pages_split = pages.split("--")
        try:
            if len(pages_split) == 1:
                return 0
            else:
                return int(pages_split[1]) - int(pages_split[0])
        except ValueError:
            return 0
        
    def get_first_page(self, pages):
        if not pages:
            return None
        try:
            return int(pages.split("--")[0])
        except ValueError:
            return None
        
    def normalize_name_to_ascii(self, string):
        return "".join([normalize_to_ascii(character) for character in string])
        
    def normalize_title_to_ascii(self, string):
        """
        Format string to ASCII.

        Args:
            entry: A string.
        Returns:
            ASCII-formatted version of the input string.
        """
        return "".join([normalize_to_ascii(character) for character in string if character.isalpha() or character == " "])

    def convert_title_to_filename(self, title):
        return self.normalize_title_to_ascii(title).replace(" ", "_").lower()


if __name__ == "__main__":

    pdf_extractor = PDFextractor("../sources/proceedings-by-venue")
    pdf_extractor.run(test = True)

    

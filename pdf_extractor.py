import csv
from datetime import datetime
from re import sub
from time import sleep
import fitz
import bibtexparser
from glob import glob
from os.path import dirname, exists, sep
from os import makedirs, system
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
                                              entry.get("author", []),
                                              entry.get("doi", None), 
                                              entry.get("pages"))
        title_as_filename = self.convert_title_to_filename(title)
        last_names_of_authors = [self.normalize_name_to_ascii(author.split(" ")[-1]) for author in authors.split(" and ")]
        page_count = self.get_page_count(pages)
        if self.get_page_count(pages) != None:
            return (bibkey, title, title_as_filename, authors, last_names_of_authors, doi, page_count)
        else:
            return None
        
    def check_page(self, page_text, title, authors, doi):
        system("clear")
        print(self.blue("TITLE: " + title))
        print(self.green("AUTHORS: " + ", ".join([author for author in authors])))
        print(self.yellow("DOI: " + (doi if doi else "-")))
        print()
        edited_page_text = sub(title.replace(" ", "[ \n]"), self.blue(title), page_text)
        if doi:
            edited_page_text = edited_page_text.replace(doi, self.yellow(doi))
        for author in authors:
            edited_page_text = edited_page_text.replace(author, self.green(author))
        edited_page_text = edited_page_text.replace("Introduction", self.red("Introduction"))
        edited_page_text = edited_page_text.replace("Abstract", self.red("Abstract"))
        print(edited_page_text.strip())
        print()
        check = None
        while check not in ["y", "n", "i"]:
            check = input("Enter 'y' if correct; enter 'n' if wrong paper; enter 'i' if table of content, reference page, etc to skip page. ")
        return check

    def yellow(self, string):
        return "\033[1;33m" + string + "\033[1;m"

    def green(self, string):
        return "\033[1;32m" + string + "\033[1;m"

    def red(self, string):
        return "\033[1;31m" + string + "\033[1;m"

    def blue(self, string):
        return "\033[1;34m" + string + "\033[1;m"

    def extract(self, venue, year, test):
        print(venue, year)
        sleep(1)
        system("clear")
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
            by_doi_filepath = proceeding_pdf_filepath.replace(".pdf", "_found_by_doi.csv")
            if exists(by_doi_filepath):
                with open(by_doi_filepath) as by_doi_file:
                    csv_reader = csv.reader(by_doi_file, delimiter=",")
                    for bibkey, title, title_as_filename, authors, doi, proceeding_pdf_filepath, from_page, to_page in csv_reader:
                        entries_found_by_doi[bibkey] = [doi, proceeding_pdf_filepath, int(from_page), int(to_page)]
            by_title_filepath = proceeding_pdf_filepath.replace(".pdf", "_found_by_title.csv")
            if exists(by_title_filepath):
                with open(by_title_filepath) as by_title_file:
                    csv_reader = csv.reader(by_title_file, delimiter=",")
                    for bibkey, title, title_as_filename, authors, doi, proceeding_pdf_filepath, from_page, to_page in csv_reader:
                        entries_found_by_title[bibkey] = [title_as_filename, proceeding_pdf_filepath, int(from_page), int(to_page)]
            with fitz.open(proceeding_pdf_filepath) as pdf:
                for page_number, page in enumerate(pdf.pages()):
                    page_text = page.get_text()
                    page_text_no_linebreaks = page_text.replace("\n", " ")
                    page_text_preprocessed = sub(" +", " ", page_text_no_linebreaks.lower()).replace("ﬁ","fi")

                    #print("PAGE NUMBER:", page_number)
                    for bibkey, title, title_as_filename, authors, last_names_of_authors, doi, page_count in entries:
                        last_names_of_authors_lowered = [last_name_of_author.lower() for last_name_of_author in last_names_of_authors]
                        if bibkey not in entries_found_by_doi and bibkey not in entries_found_by_title:
                            if doi:
                                doi = doi.replace("\\", "")
                            if (title.lower() in page_text_preprocessed and
                                doi and doi in page_text_no_linebreaks):
                                self.check_page(page_text, title, last_names_of_authors, doi)
                                check = self.check_page(page_text, title, last_names_of_authors, doi)
                                if check == "y":
                                    entries_found_by_doi[bibkey] = [doi,
                                                                    proceeding_pdf_filepath, 
                                                                    page_number, page_number+page_count]
                                    with open(by_doi_filepath, "a") as by_doi_file:
                                        csv_writer = csv.writer(by_doi_file, delimiter=",")
                                        #bibkey, title, title_as_filename, authors, last_names_of_authors, doi, page_count
                                        csv_writer.writerow([bibkey, title, title_as_filename, authors, doi, proceeding_pdf_filepath, page_number, page_number+page_count])
                                else:
                                    break
                            elif (title.lower() in page_text_preprocessed and
                                  False not in [last_name_of_author_lowered in page_text_preprocessed 
                                                for last_name_of_author_lowered in last_names_of_authors_lowered]):
                                check = self.check_page(page_text, title, last_names_of_authors, doi)
                                if check == "y":
                                    entries_found_by_title[bibkey] = [title_as_filename,
                                                                      proceeding_pdf_filepath, 
                                                                      page_number, page_number+page_count]
                                    with open(by_title_filepath, "a") as by_title_file:
                                        csv_writer = csv.writer(by_title_file, delimiter=",")
                                        csv_writer.writerow([bibkey, title, title_as_filename, authors, doi, proceeding_pdf_filepath, page_number, page_number+page_count])
                                else:
                                    break
                                
        for entries_found, output_directory in [[entries_found_by_doi,
                                                 "../sources/papers-by-venue-extracted-by-doi" + ("-test-4" if test else "")],
                                                [entries_found_by_title,
                                                 "../sources/papers-by-venue-extracted-by-title" + ("-test-4" if test else "")]]:
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
                    if not exists(filepath):
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
    #pdf_extractor.run(test = True)

    

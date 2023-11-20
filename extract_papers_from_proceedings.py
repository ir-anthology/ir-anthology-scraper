from pprint import pprint
from re import sub
import fitz
import bibtexparser
from glob import glob
from os.path import dirname, exists, sep
from os import makedirs
from utils.utils import normalize_to_ascii

def get_page_count(pages):
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
    
def get_first_page(pages):
    if not pages:
        return None
    try:
        return int(pages.split("--")[0])
    except ValueError:
        return None
    
def normalize_name_to_ascii(string):
    return "".join([normalize_to_ascii(character) for character in string])
    
def normalize_title_to_ascii(string):
    """
    Format string to ASCII.

    Args:
        entry: A string.
    Returns:
        ASCII-formatted version of the input string.
    """
    return "".join([normalize_to_ascii(character) for character in string if character.isalpha() or character == " "])

def convert_title_to_filename(title):
     return normalize_title_to_ascii(title).replace(" ", "_").lower()

def extract(venue, year):
    proceedings_pdf_filepaths = glob("../sources/proceedings-by-venue" + sep + 
                                     venue + sep + year + sep + 
                                     venue + "-" + year + "-" + "proceedings" + "*.pdf")
    bibfile_path = ("../conf" + sep +
                    venue + sep + year + sep + 
                    "conf" + "-" + venue + "-" + year + ".bib")
           
    if not exists(bibfile_path):
        return 0,0
    
    with open(bibfile_path) as bibfile:
        entries = [(entry["ID"],
                    entry["title"],
                    entry.get("author", None),
                    entry.get("doi", None), 
                    entry.get("pages")) 
                    for entry in bibtexparser.load(bibfile).entries]

    entries = [(bibkey,
                title,
                [normalize_name_to_ascii(author.split(" ")[-1]) for author in authors.split(" and ")],
                convert_title_to_filename(title),
                doi,
                get_first_page(pages),
                get_page_count(pages))
                for bibkey, title, authors, doi, pages in entries if get_first_page(pages) != None and get_page_count(pages) != None and authors]
    
    #for entry in entries:
    #    print(entry)
    #    input()
    entries_found_by_doi = {}
    entries_found_by_title = {}

    for proceeding_pdf_filepath in proceedings_pdf_filepaths:
        with fitz.open(proceeding_pdf_filepath) as pdf:
            for page_number, page in enumerate(pdf.pages()):
                page_text = page.get_text().replace("\n", " ")
                page_text_preprocessed = sub(" +", " ", page_text.lower()).replace("ﬁ","fi")

                for bibkey, title, authors, title_as_filename, doi, first_page, pages in entries:
                    authors_lowered = [author.lower() for author in authors]
                    if bibkey not in entries_found_by_doi and bibkey not in entries_found_by_title:
                        if doi:
                            doi = doi.replace("\\", "")
                        if (title.lower() in page_text_preprocessed and
                            doi and doi in page_text):
                            entries_found_by_doi[bibkey] = [title, doi,
                                                            proceeding_pdf_filepath, 
                                                            page_number, page_number+pages]
                        elif (title.lower() in page_text_preprocessed and
                              False not in [author_lowered in page_text_preprocessed for author_lowered in authors_lowered] and
                              not page_number <= first_page):
                            entries_found_by_title[bibkey] = [title_as_filename, doi,
                                                              proceeding_pdf_filepath, 
                                                              page_number, page_number+pages]

    for bibkey, values in entries_found_by_doi.items():
        title, doi, proceeding_pdf_filepath, from_page, to_page = values
        with fitz.open(proceeding_pdf_filepath) as pdf:
            paper = fitz.open()
            paper.insert_pdf(pdf, from_page=from_page, to_page=to_page)
            filepath = ("../sources/papers-by-venue-extracted-by-doi-test" + sep + 
                        venue + sep + year + sep + 
                        doi + ".pdf")
            if not exists(dirname(filepath)):
                makedirs(dirname(filepath))
            paper.save(filepath)

    for bibkey, values in entries_found_by_title.items():
        title_as_filename, doi, proceeding_pdf_filepath, from_page, to_page = values
        with fitz.open(proceeding_pdf_filepath) as pdf:
            paper = fitz.open()
            paper.insert_pdf(pdf, from_page=from_page, to_page=to_page)
            filepath = ("../sources/papers-by-venue-extracted-by-title-test" + sep + 
                        venue + sep + year + sep + 
                        title_as_filename + ".pdf")
            if not exists(dirname(filepath)):
                makedirs(dirname(filepath))
            paper.save(filepath)

    return len(entries_found_by_doi), len(entries_found_by_title)


if __name__ == "__main__":

    with open("log.txt", "w") as file:
        pass

    proceedings_directories = sorted(glob("../sources/proceedings-by-venue/*/*"))

    paper_count = [0, 0]

    for proceedings_directory in proceedings_directories:
        venue, year = proceedings_directory.split("/")[-2:]
        paper_count = [i+j for i,j in zip(paper_count, extract(venue, year))]
        with open("log.txt", "a") as file:
            file.write(proceedings_directory + " " + venue + " " + str(year) + "\n")

    with open("log.txt", "a") as file:
        file.write(str(paper_count))

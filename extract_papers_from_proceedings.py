import fitz
import bibtexparser
from glob import glob
from os.path import dirname, exists, sep
from os import makedirs
from utils.utils import normalize_to_ascii

def get_page_count(pages):
    if not pages:
        return 0
    pages_split = pages.split("--")
    try:
        if len(pages_split) == 1:
            return 1
        else:
            return int(pages_split[1]) - int(pages_split[0])
    except ValueError:
        return 0
    
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
                    entry.get("doi", None), 
                    entry.get("pages")) 
                    for entry in bibtexparser.load(bibfile).entries]

    entries = [(bibkey,
                title,
                convert_title_to_filename(title),
                doi,
                get_page_count(pages))
                for bibkey, title, doi, pages in entries if get_page_count(pages)]
    
    print(entries)
    entries_found_by_doi = []
    entries_found_by_title = []

    for proceeding_pdf_filepath in proceedings_pdf_filepaths:
        with fitz.open(proceeding_pdf_filepath) as pdf:
            for page_number, page in enumerate(pdf.pages()):
                page_text = page.get_text().replace("\n", " ")
                page_text_lowered = page_text.lower()
                for bibkey, title, title_as_filename, doi, pages in entries:
                    if doi:
                        doi = doi.replace("\\", "")
                    if doi and doi in page_text and title.lower() in page_text_lowered:
                        entries_found_by_doi.append([bibkey, title, doi,
                                                     proceeding_pdf_filepath, page_number, page_number+pages])
                    elif page_text_lowered.startswith(title.lower()) and "Abstract" in page_text:
                         entries_found_by_title.append([bibkey, title_as_filename, doi,
                                                        proceeding_pdf_filepath, page_number, page_number+pages])

    for bibkey, title, doi, proceeding_pdf_filepath, from_page, to_page in entries_found_by_doi:
        with fitz.open(proceeding_pdf_filepath) as pdf:
            paper = fitz.open()
            paper.insert_pdf(pdf, from_page=from_page, to_page=to_page)
            filepath = ("../sources/papers-by-venue-extracted-by-doi" + sep + 
                        venue + sep + year + sep + 
                        doi + ".pdf")
            if not exists(dirname(filepath)):
                makedirs(dirname(filepath))
            paper.save(filepath)

    for bibkey, title_as_filename, doi, proceeding_pdf_filepath, from_page, to_page in entries_found_by_title:
        with fitz.open(proceeding_pdf_filepath) as pdf:
            paper = fitz.open()
            paper.insert_pdf(pdf, from_page=from_page, to_page=to_page)
            filepath = ("../sources/papers-by-venue-extracted-by-title" + sep + 
                        venue + sep + year + sep + 
                        title_as_filename + ".pdf")
            if not exists(dirname(filepath)):
                makedirs(dirname(filepath))
            paper.save(filepath)

    return len(entries_found_by_doi), len(entries_found_by_title)


if __name__ == "__main__":

    proceedings_directories = sorted(glob("../sources/proceedings-by-venue/adcs/2022"))

    paper_count = [0, 0]

    for proceedings_directory in proceedings_directories:
        venue, year = proceedings_directory.split("/")[-2:]
        print(proceedings_directory, venue, year)
        paper_count = [i+j for i,j in zip(paper_count, extract(venue, year))]

    print(paper_count)

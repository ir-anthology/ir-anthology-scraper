import bibtexparser
from datetime import datetime
from shutil import copyfile
from glob import glob
from json import loads
from os.path import dirname, exists, sep
from os import makedirs
from csv import reader, writer
from matplotlib import pyplot as plt
from tqdm import tqdm

from utils.utils import normalize_to_ascii


def normalize_name_to_ascii(string):
    ascii_string = "".join([normalize_to_ascii(character) for character in string])
    return "".join([character for character in ascii_string if character in "abcdefghijklmnopqrstuvwxyz"])

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

def generate_overview(result_csv_filepath):
    overview = {}

    with open(result_csv_filepath) as file:
        csvreader = reader(file, delimiter = ",")
        for row in csvreader:
            venue, year, bibkey, title, doi, sources = row
            if doi:
                if venue not in overview:
                    overview[venue] = {}
                if year not in overview[venue]:
                    overview[venue][year] = [0,0]
                overview[venue][year][1] += 1
                if sources != []:
                    overview[venue][year][0] += 1

    with open(result_csv_filepath.replace(".csv", "_doi_pdf_ratio.csv"), "w") as file:
        csvwriter = writer(file, delimiter = ",")
        for venue in overview:
            for year in overview[venue]:
                csvwriter.writerow([venue, year, overview[venue][year][0], overview[venue][year][1]])

def write_years_not_found_by_dois(years_of_entries_not_found_by_doi, output_directory, venuetype):
    with open(output_directory + sep + "years_of_entries_not_found_by_doi_" + venuetype + ".txt", "w") as file:
        for year in sorted(years_of_entries_not_found_by_doi.keys()):
            file.write(str(year) + "," + str(years_of_entries_not_found_by_doi[year]) + "\n")

def plot_years_not_found_by_dois(years_of_entries_not_found_by_doi, output_directory, venuetype):
    years = list(range(1960,2024))
    plt.figure().set_figwidth(12)
    plt.xticks(years, rotation='vertical')
    plt.title(venuetype.title() + " - Entries not Found by DOI")
    plt.bar(years, [years_of_entries_not_found_by_doi.get(year, 0) for year in years])
    plt.savefig(output_directory + sep + "years_of_entries_not_found_by_doi_" + venuetype + ".jpg")

USE_TITLE = False
DRY_RUN = True
OVERWRITE_EXISTING = False

now = datetime.now()
start = (str(now.year) + "-" + (str(now.month).rjust(2,"0")) + "-" + (str(now.day).rjust(2,"0")) + "_" +
         (str(now.hour).rjust(2,"0")) + "-" + (str(now.minute).rjust(2,"0")))
output_directory = "copy_logs" + sep + start
if not exists(output_directory): makedirs(output_directory)

for venuetype in ["conf","jrnl"]:

    result_txt_filename = "copy_pdfs_" + start + "_" + venuetype + ".txt"
    result_csv_filename = "copy_pdfs_" + start + "_" + venuetype + ".csv"
    result_csv_filename_missing = "copy_pdfs_" + start + "_" + venuetype + "_missing.csv"
    error_cvs_filename = "copy_pdfs_" + start + "_" + venuetype + "_error.csv"

    bibfile_paths = sorted(glob("../" + venuetype + "/*/*/*.bib"))

    wcsp15_doi_path_mapping = {}
    with open("resources/wcsp15-doi-path-mapping.txt") as file:
        for line in file:
            doi,path = loads(line)
            wcsp15_doi_path_mapping[doi] = path

    wcsp15_title_path_mapping = {}
    with open("resources/wcsp15-longtitle-path-mapping.txt") as file:
        for line in file:
            title_lowered,path,author,year = loads(line)
            wcsp15_title_path_mapping[title_lowered.lower()] = {"path":path,
                                                        "author":author,
                                                        "year":year}

    entry_count = 0
    doi_count = 0
    pdf_count = 0
    source_count = {}
    years_of_entries_not_found_by_doi = {}

    # CSV FORMAT: VENUE, YEAR, BIBKEY, DOI, acm50years, papers-by-venue, proceedings-by-venue, wlgc, wcsp15 (using doi), (wcsp15 (using title))

    for bibfile_path in tqdm(bibfile_paths, total=len(bibfile_paths)):
        with open(bibfile_path) as bibfile:
                
            entries = bibtexparser.load(bibfile).entries
            
            for entry in entries:
                
                if entry["ENTRYTYPE"] == "proceedings":
                    continue

                entry_count += 1

                bibkey = entry["ID"].split("-", 3)
                title_lowered = entry["title"].lower()
                title_as_filename = convert_title_to_filename(entry["title"])
                author = normalize_name_to_ascii(entry["author"].strip().split(" and ")[0].strip().split(" ")[-1]) if "author" in entry else None
                doi = entry.get("doi", None)
                if doi:
                    doi = doi.replace("\\", "")
                venue = bibkey[1]
                year = int(bibkey[2])
                
                pdf_dst_path = dirname(bibfile_path) + sep + entry["ID"] + ".pdf"
                pdf_src_paths = {}
                
                if doi:
                    doi_count += 1

                    pdf_src_paths = {"acm50years": {"path": "../sources/acm50yrs/papers-by-doi/" + doi + ".pdf",
                                                    "flag": False},
                                     "papers-by-venue": {"path": "../sources/papers-by-venue/" + venue + "/" + str(year) + "/" + doi + ".pdf",
                                                         "flag": False},
                                     "papers-by-venue-extracted-by-doi": {"path": "../sources/papers-by-venue-extracted-by-doi/" + 
                                                                          venue + "/" + str(year) + "/" + doi + ".pdf",
                                                                          "flag": False},
                                     "papers-by-venue-extracted-by-title": {"path": "../sources/papers-by-venue-extracted-by-title/" + 
                                                                            venue + "/" + str(year) + "/" + title_as_filename + ".pdf",
                                                                            "flag": False},                                     
                                     "wlgc": {"path": "../sources/wlgc/papers-by-doi/" + doi + ".pdf",
                                              "flag": False},
                                     "wcsp15 (using doi)": {"path": ("../sources/" + wcsp15_doi_path_mapping[doi]) 
                                                            if doi in wcsp15_doi_path_mapping else None,
                                                            "flag": False}
                                     }

                    for source in pdf_src_paths:
                        if pdf_src_paths[source]["path"] and exists(pdf_src_paths[source]["path"]):
                            pdf_src_paths[source]["flag"] = True
                            if OVERWRITE_EXISTING or not exists(pdf_dst_path):
                                if not DRY_RUN:
                                    copyfile(pdf_src_paths[source]["path"], pdf_dst_path)

                if True not in [pdf_src_paths[source]["flag"] for source in pdf_src_paths]:

                    if year not in years_of_entries_not_found_by_doi:
                        years_of_entries_not_found_by_doi[year] = 0
                    years_of_entries_not_found_by_doi[year] += 1

                    if title_lowered in wcsp15_title_path_mapping:
                        
                        pdf_src_path_wcsp_per_title = "../sources/" + wcsp15_title_path_mapping[title_lowered]["path"]
                        wscp_author = normalize_name_to_ascii(wcsp15_title_path_mapping[title_lowered]["author"])
                        wscp_year = int(wcsp15_title_path_mapping[title_lowered]["year"])
                    
                        if USE_TITLE and exists(pdf_src_path_wcsp_per_title):
                            if (author == wscp_author and
                                year == wscp_year):
                                pdf_src_paths["wcsp15 (using title)"] = {"path": pdf_src_path_wcsp_per_title,
                                                                         "flag": True}
                                if OVERWRITE_EXISTING or not exists(pdf_dst_path):
                                    if not DRY_RUN:
                                        copyfile(pdf_src_path_wcsp_per_title, pdf_dst_path)
                            else:
                                with open(output_directory + sep + error_cvs_filename, "a") as error_csv_file:
                                    csv_writer = writer(error_csv_file, delimiter=",")
                                    csv_writer.writerow([entry["ID"], title_lowered, author, wscp_author, year, wscp_year])

                if True in [pdf_src_paths[source]["flag"] for source in pdf_src_paths]:
                    pdf_count += 1
                    for source in pdf_src_paths:
                        if pdf_src_paths[source]["flag"]:
                            if source not in source_count:
                                source_count[source] = 0
                            source_count[source] += 1
                else:
                    if doi:
                        with open(output_directory + sep + "dois_of_missing_pdfs.txt", "a") as file:
                            file.write(venue + "," + str(year) + "," + doi + "\n")

                with open(output_directory + sep + result_csv_filename, "a") as result_csv_file:
                    csv_writer = writer(result_csv_file, delimiter=",")
                    sources = [source for source in pdf_src_paths if pdf_src_paths[source]["flag"]]
                    csv_writer.writerow([venue, year, entry["ID"], entry["title"], entry.get("doi", "n/a"), sources])

                if True not in [pdf_src_paths[source]["flag"] for source in pdf_src_paths]:
                    with open(output_directory + sep + result_csv_filename_missing, "a") as result_csv_file:
                        csv_writer = writer(result_csv_file, delimiter=",")
                        csv_writer.writerow([doi if doi else "n/a", entry["title"], entry["author"], entry["ID"] + ".pdf", ("https://www.doi.org/" + doi) if doi else "n/a"])
                                   
    with open(output_directory + sep + result_txt_filename, "w") as logfile:
        logfile.write("Entries: " + str(entry_count) + "\n")
        logfile.write("with DOI: " + str(doi_count) + "\n")
        logfile.write("with PDF: " + str(pdf_count) + "\n")
        for source,count in source_count.items():
            logfile.write(source + ": " + str(count) + "\n")

    #generate_overview(output_directory + sep + result_csv_filename)
    write_years_not_found_by_dois(years_of_entries_not_found_by_doi, output_directory, venuetype)
    plot_years_not_found_by_dois(years_of_entries_not_found_by_doi, output_directory, venuetype)
        

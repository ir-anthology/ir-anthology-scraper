from unicodedata import normalize
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


def normalize_to_ascii(string):
    ascii_string = "".join([normalize("NFD",character).encode("ASCII","ignore").decode("ASCII") for character in string])
    return "".join([character for character in ascii_string if character in "abcdefghijklmnopqrstuvwxyz"])

def generate_overview(result_csv_filepath):
    overview = {}

    with open(result_csv_filepath) as file:
        csvreader = reader(file, delimiter = ",")
        for row in csvreader:
            if len(row) == 11:
                venue, year, bibkey, title, doi, s1, s2, s3, s4, s5, s6 = row
            else:
                venue, year, bibkey, title, doi, s1, s2, s3, s4, s5 = row
            if doi:
                if venue not in overview:
                    overview[venue] = {}
                if year not in overview[venue]:
                    overview[venue][year] = [0,0]
                overview[venue][year][1] += 1
                if set([s1, s2, s3, s4, s5, s6] if len(row) == 11 else [s1, s2, s3, s4, s5]) != {"-"}:
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

    bibfilepaths = sorted(glob("../" + venuetype + "/*/*/*.bib"))

    wcsp15_doi_path_mapping = {}
    with open("resources/wcsp15-doi-path-mapping.txt") as file:
        for line in file:
            doi,path = loads(line)
            wcsp15_doi_path_mapping[doi] = path

    wcsp15_title_path_mapping = {}
    with open("resources/wcsp15-longtitle-path-mapping.txt") as file:
        for line in file:
            title,path,author,year = loads(line)
            wcsp15_title_path_mapping[title.lower()] = [path, author, year]

    entry_count = 0
    doi_count = 0
    pdf_count = 0
    source_count = {}
    years_of_entries_not_found_by_doi = {}

    # CSV FORMAT: VENUE, YEAR, BIBKEY, DOI, acm50years, papers-by-venue, proceedings-by-venue, wlgc, wcsp15 (using doi), (wcsp15 (using title))

    for bibfilepath in tqdm(bibfilepaths, total=len(bibfilepaths)):
        with open(bibfilepath) as bibfile:
                
            entries = bibtexparser.load(bibfile).entries
            
            for entry in entries:
                
                if entry["ENTRYTYPE"] == "proceedings":
                    continue

                entry_count += 1

                bibkey = entry["ID"].split("-", 3)
                title = entry["title"].lower()
                author = normalize_to_ascii(entry["author"].strip().split(" and ")[0].strip().split(" ")[-1]) if "author" in entry else None
                doi = entry.get("doi", None)
                if doi:
                    doi = doi.replace("\\", "")
                venue = bibkey[1]
                year = int(bibkey[2])
                
                pdf_dst_path = dirname(bibfilepath) + sep + entry["ID"] + ".pdf"
                pdf_src_paths = {}
                
                if doi:
                    doi_count += 1

                    pdf_src_paths = {"acm50years": {"path": "../sources/acm50yrs/papers-by-doi/" + doi + ".pdf",
                                                    "flag": False},
                                     "papers-by-venue": {"path": "../sources/papers-by-venue/" + venue + "/" + str(year) + "/" + doi + ".pdf",
                                                         "flag": False},
                                     "proceedings-by-venue": {"path": "../sources/proceedings-by-venue/" + venue + "/" + str(year) + "/" + doi + ".pdf",
                                                              "flag": False},
                                     "wlgc": {"path": "../sources/wlgc/papers-by-doi/" + doi + ".pdf",
                                              "flag": False},
                                     "wcsp15 (using doi)": {"path": ("../sources/" + wcsp15_doi_path_mapping[doi]) if doi in wcsp15_doi_path_mapping else None,
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

                    if title in wcsp15_title_path_mapping:
                        
                        wscp_author = normalize_to_ascii(wcsp15_title_path_mapping[title][1])
                        wscp_year = int(wcsp15_title_path_mapping[title][2])
                    
                        pdf_src_path_wcsp_per_title = "../sources/" + wcsp15_title_path_mapping[title][0]

                        if USE_TITLE and exists(pdf_src_path_wcsp_per_title):
                            if (author == wscp_author and
                                year == wscp_year):
                                pdf_src_paths["wcsp15 (using title if no doi)"] = {"path": pdf_src_path_wcsp_per_title,
                                                                                   "flag": True}
                                if OVERWRITE_EXISTING or not exists(pdf_dst_path):
                                    if not DRY_RUN:
                                        copyfile(pdf_src_path_wcsp_per_title, pdf_dst_path)
                            else:
                                with open(output_directory + sep + error_cvs_filename, "a") as error_csv_file:
                                    csv_writer = writer(error_csv_file, delimiter=",")
                                    csv_writer.writerow([entry["ID"], title, author, wscp_author, year, wscp_year])

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
                    csv_writer.writerow([venue, year, entry["ID"], entry["title"], entry.get("doi", "n/a")] +
                                        ([source if pdf_src_paths[source]["flag"] else "-" for source in pdf_src_paths] if pdf_src_paths else ["-"]*(6 if USE_TITLE else 5)))

                if not exists(pdf_dst_path):
                    with open(output_directory + sep + result_csv_filename_missing, "a") as result_csv_file:
                        csv_writer = writer(result_csv_file, delimiter=",")
                        csv_writer.writerow([doi if doi else "n/a", entry["title"], entry["author"], entry["ID"] + ".pdf", ("https://www.doi.org/" + doi) if doi else "n/a"])
                                   
    with open(output_directory + sep + result_txt_filename, "w") as logfile:
        logfile.write("Entries: " + str(entry_count) + "\n")
        logfile.write("with DOI: " + str(doi_count) + "\n")
        logfile.write("with PDF: " + str(pdf_count) + "\n")
        for source,count in source_count.items():
            logfile.write(source + ": " + str(count) + "\n")

    generate_overview(output_directory + sep + result_csv_filename)
    write_years_not_found_by_dois(years_of_entries_not_found_by_doi, output_directory, venuetype)
    plot_years_not_found_by_dois(years_of_entries_not_found_by_doi, output_directory, venuetype)
        

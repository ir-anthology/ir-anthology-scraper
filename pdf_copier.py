from pprint import pprint
import bibtexparser
from datetime import datetime
from shutil import copyfile
from glob import glob
from json import loads, dump
from os.path import dirname, exists, sep
from os import makedirs
from csv import writer
from matplotlib import pyplot as plt
from tqdm import tqdm

from utils.utils import normalize_to_ascii

class PDFcopier:

    def __init__(self, use_title, dry_run, overwrite_existing):
        self.use_title = use_title
        self.dry_run = dry_run
        self.overwrite_existing = overwrite_existing

        now = datetime.now()
        self.start = ((str(now.year)) + "-" + (str(now.month).rjust(2,"0")) + "-" + (str(now.day).rjust(2,"0")) + "_" +
                      (str(now.hour).rjust(2,"0")) + "-" + (str(now.minute).rjust(2,"0")))
        
        self.output_directory = "copy_logs" + sep + self.start
        if not exists(self.output_directory): makedirs(self.output_directory)

        self.wcsp15_doi_path_mapping = {}
        with open("resources/wcsp15-doi-path-mapping.txt") as file:
            for line in file:
                doi,path = loads(line)
                self.wcsp15_doi_path_mapping[doi] = path

        self.wcsp15_title_path_mapping = {}
        with open("resources/wcsp15-longtitle-path-mapping.txt") as file:
            for line in file:
                title_lowered,path,first_author,year = loads(line)
                self.wcsp15_title_path_mapping[title_lowered.lower()] = {"path":path,
                                                                         "first_author":first_author,
                                                                         "year":year}
                
    def sources(self, title, first_author, doi, venue, year):
        def check_path(path):
            if exists(path):
                return path
            else:
                return None

        title_lowered = title.lower()  
        title_as_filename = self.convert_title_to_filename(title)

        if title_lowered in self.wcsp15_title_path_mapping:
            pdf_src_path_wcsp_per_title = "../sources/" + self.wcsp15_title_path_mapping[title_lowered]["path"]
            wscp_first_author = self.normalize_name_to_ascii(self.wcsp15_title_path_mapping[title_lowered]["first_author"])
            wscp_year = int(self.wcsp15_title_path_mapping[title_lowered]["year"])

        return {"by_doi": {"acm50years": check_path("../sources/acm50yrs/papers-by-doi/" + doi + ".pdf") if doi else None,
                           "papers-by-venue": check_path("../sources/papers-by-venue/" + venue + "/" + str(year) + "/" + doi + ".pdf") if doi else None,
                           "papers-by-venue-extracted-by-doi": check_path("../sources/papers-by-venue-extracted-by-doi/" + venue + "/" + str(year) + "/" + doi + ".pdf") if doi else None,
                           "wlgc": check_path("../sources/wlgc/papers-by-doi/" + doi + ".pdf") if doi else None,
                           "wcsp15 (using doi)": check_path("../sources/" + self.wcsp15_doi_path_mapping[doi]) if doi and doi in self.wcsp15_doi_path_mapping else None},
                "by_title": {"papers-by-venue-extracted-by-title": check_path("../sources/papers-by-venue-extracted-by-title/" + venue + "/" + str(year) + "/" + title_as_filename + ".pdf") if self.use_title else None,
                             "wcsp15 (using title)": check_path(pdf_src_path_wcsp_per_title) if self.use_title and title_lowered in self.wcsp15_title_path_mapping and first_author == wscp_first_author and year == wscp_year else None}
                }
    
    def bibliography(self, entry):
        bibkey = entry["ID"]
        bibkey_split = bibkey.split("-", 3)
        title = entry["title"]
        first_author = self.normalize_name_to_ascii(entry["author"].strip().split(" and ")[0].strip().split(" ")[-1]) if "author" in entry else None
        doi = entry.get("doi", None)
        if doi:
            doi = doi.replace("\\", "")
        venue = bibkey_split[1]
        year = int(bibkey_split[2])
        return bibkey, title, first_author, doi, venue, year
                
    def run(self, venuetype):
        bibfile_paths = sorted(glob("../" + venuetype + "/*/*/*.bib"))
        results_txt_filename = "copy_pdfs_" + self.start + "_" + venuetype + ".txt"
        results_csv_filename = "copy_pdfs_" + self.start + "_" + venuetype + ".csv"
        missing_csv_filename = "copy_pdfs_" + self.start + "_" + venuetype + "_missing.csv"
        #error_cvs_filename = "copy_pdfs_" + self.start + "_" + venuetype + "_error.csv"
    
        entry_count = 0
        doi_count = 0
        pdf_count = 0
        source_count = {}
        years_of_entries_not_found_by_doi = {}
        pdf_ratio_per_venue_and_year = {}

        # CSV FORMAT: VENUE, YEAR, BIBKEY, DOI, SOURCES
        results = []
        missing = []

        duplicates = {}

        for bibfile_path in tqdm(bibfile_paths, total=len(bibfile_paths)):
            with open(bibfile_path) as bibfile:
                    
                entries = bibtexparser.load(bibfile).entries
                
                for entry in entries:
                    
                    if entry["ENTRYTYPE"] == "proceedings":
                        continue

                    entry_count += 1

                    bibkey, title, first_author, doi, venue, year = self.bibliography(entry)
                    doi_count += 1 if doi else 0

                    if venue not in pdf_ratio_per_venue_and_year:
                        pdf_ratio_per_venue_and_year[venue] = {}
                    if year not in pdf_ratio_per_venue_and_year[venue]:
                        pdf_ratio_per_venue_and_year[venue][year] = [0,0]
                    pdf_ratio_per_venue_and_year[venue][year][1] += 1
                    
                    pdf_dst_path = dirname(bibfile_path) + sep + entry["ID"] + ".pdf"
                    pdf_src_paths = self.sources(title, first_author, doi, venue, year)

                    if pdf_src_paths["by_title"]["papers-by-venue-extracted-by-title"]:
                        if title not in duplicates:
                            duplicates[title] = []
                        duplicates[title].append(entry) 
                    
                    for source_path in pdf_src_paths["by_doi"]:
                        if not self.dry_run:
                            if pdf_src_paths["by_doi"][source_path]:
                                if self.overwrite_existing or not exists(pdf_dst_path):
                                    copyfile(pdf_src_paths["by_doi"][source_path], pdf_dst_path)
                                    break
                    else:
                        if year not in years_of_entries_not_found_by_doi:
                            years_of_entries_not_found_by_doi[year] = 0
                        years_of_entries_not_found_by_doi[year] += 1              
                        
                        for source_path in pdf_src_paths["by_title"]:
                            if not self.dry_run:
                                if pdf_src_paths["by_title"][source_path]:
                                    if self.overwrite_existing or not exists(pdf_dst_path):
                                        copyfile(pdf_src_paths["by_title"][source_path], pdf_dst_path)
                                        break
                                    #with open(self.output_directory + sep + self.error_cvs_filename, "a") as error_csv_file:
                                    #    csv_writer = writer(error_csv_file, delimiter=",")
                                    #    csv_writer.writerow([entry["ID"], title_lowered, author, wscp_author, year, wscp_year])

                    if set(pdf_src_paths["by_doi"].values()).union(set(pdf_src_paths["by_title"].values())) != {None}:                                                
                        pdf_count += 1
                        pdf_ratio_per_venue_and_year[venue][year][0] += 1
                    else:
                        missing.append([venue, year, bibkey, title, doi, entry["author"]])
                    
                    for source_type in pdf_src_paths:
                        for source_path in pdf_src_paths[source_type]:
                            if pdf_src_paths[source_type][source_path]:
                                if source_path not in source_count:
                                    source_count[source_path] = 0
                                source_count[source_path] += 1

                    sources = ([source for source in pdf_src_paths["by_doi"] if pdf_src_paths["by_doi"][source]] +
                               [source for source in pdf_src_paths["by_title"] if pdf_src_paths["by_title"][source]])
                    results.append([venue, year, bibkey, title, doi, sources])

        # sort entries missing PDF decending by ratio of PDF coverage for venue and year
        missing.sort(key=lambda result: pdf_ratio_per_venue_and_year[result[0]][result[1]][0]/pdf_ratio_per_venue_and_year[result[0]][result[1]][1], reverse=True)

        # write missing entries to file
        with open(self.output_directory + sep + missing_csv_filename, "a") as result_csv_file:
            csv_writer = writer(result_csv_file, delimiter=",")
            for venue, year, bibkey, title, doi, author in missing:
                csv_writer.writerow([doi if doi else "n/a", title, author, bibkey + ".pdf", ("https://www.doi.org/" + doi) if doi else "n/a"])

        # write results to file
        with open(self.output_directory + sep + results_csv_filename, "a") as result_csv_file:
            csv_writer = writer(result_csv_file, delimiter=",")
            for venue, year, bibkey, title, doi, sources in results:
                csv_writer.writerow([venue, year, bibkey, title, doi if doi else "n/a", sources])

        # write overview
        with open(self.output_directory + sep + results_txt_filename, "w") as logfile:
            logfile.write("Entries: " + str(entry_count) + "\n")
            logfile.write("with DOI: " + str(doi_count) + "\n")
            logfile.write("with PDF: " + str(pdf_count) + "\n")
            for source_path,count in source_count.items():
                logfile.write(source_path + ": " + str(count) + "\n")

        with open("duplicates" + "_" + venuetype + ".json", "w") as file:
            dump({title:duplicates[title] for title in duplicates if len(duplicates[title]) > 1}, file)

        self.generate_pdf_ratio_overview(pdf_ratio_per_venue_and_year, venuetype)
        self.write_years_not_found_by_dois(years_of_entries_not_found_by_doi, venuetype)
        self.plot_years_not_found_by_dois(years_of_entries_not_found_by_doi, venuetype)

    def normalize_name_to_ascii(self, string):
        ascii_string = "".join([normalize_to_ascii(character) for character in string])
        return "".join([character for character in ascii_string if character in "abcdefghijklmnopqrstuvwxyz"])

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

    def generate_pdf_ratio_overview(self, pdf_ratio_per_venue_and_year, venuetype):
        pdf_ratio_filename = self.output_directory + sep + "copy_pdfs_" + self.start + "_" + venuetype + "_pdf_ratio.csv"
        with open(pdf_ratio_filename, "w") as file:
            csvwriter = writer(file, delimiter = ",")
            for venue in pdf_ratio_per_venue_and_year:
                for year in pdf_ratio_per_venue_and_year[venue]:
                    csvwriter.writerow([venue, year, pdf_ratio_per_venue_and_year[venue][year][0], pdf_ratio_per_venue_and_year[venue][year][1]])

    def write_years_not_found_by_dois(self, years_of_entries_not_found_by_doi, venuetype):
        with open(self.output_directory + sep + "years_of_entries_not_found_by_doi_" + venuetype + ".txt", "w") as file:
            for year in sorted(years_of_entries_not_found_by_doi.keys()):
                file.write(str(year) + "," + str(years_of_entries_not_found_by_doi[year]) + "\n")

    def plot_years_not_found_by_dois(self, years_of_entries_not_found_by_doi, venuetype):
        years = list(range(1960,2024))
        plt.figure().set_figwidth(12)
        plt.xticks(years, rotation='vertical')
        plt.title(venuetype.title() + " - Entries not Found by DOI")
        plt.bar(years, [years_of_entries_not_found_by_doi.get(year, 0) for year in years])
        plt.savefig(self.output_directory + sep + "years_of_entries_not_found_by_doi_" + venuetype + ".jpg")

pdf_copier = PDFcopier(use_title=True, dry_run=True, overwrite_existing=False)

for venuetype in ["conf","jrnl"]:
    pdf_copier.run(venuetype)   

    
        

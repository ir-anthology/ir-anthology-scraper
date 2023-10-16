from scripts.dblp_scraper import DBLPscraper
from os.path import dirname, exists, sep
from os import makedirs
from json import dump, dumps, loads, load
from tqdm import tqdm
from csv import writer
import traceback

def write_bibtex_string_to_file(bibtex_string, output_filepath):
    with open(output_filepath, "w") as file:
        file.write(bibtex_string)


if __name__ == "__main__":

    scraper = DBLPscraper("failed")

    with open(scraper.output_directory + sep + "config.json") as file:
        config = load(file)
        
    fails = {}

    bibtex_cache_filepath = scraper.output_directory + sep + "dblp_bibtex_cache.txt"
    
    bibtex_dump = {}
    if exists(bibtex_cache_filepath):
        with open(bibtex_cache_filepath) as file:
            for line in file:
                url, bibtex = loads(line)
                bibtex_dump[url] = bibtex

    for conference, years in config.items():

        for year in years:

            try:
                print("Scraping bibtex entries of " + conference + " " + str(year) + "...")
                entry_list = scraper.scrape_conference(conference, year)
                with open(scraper.output_directory + sep + "dblp_json_results.csv", "a") as file:
                    csv_writer = writer(file, delimiter=",")
                    csv_writer.writerow([conference, year, len(entry_list)])

                if entry_list != []:
                    bibtex_list = []
                    for entry in tqdm(entry_list, total=len(entry_list)):
                        try:
                            bibtex_list.append(bibtex_dump[entry["info"]["url"]])
                        except KeyError:
                            bibtex = scraper.scrape_bibtex(entry)
                            with open(bibtex_cache_filepath, "a") as file:
                                file.write(dumps([entry["info"]["url"],bibtex]) + "\n")
                            bibtex_list.append(bibtex)
                    bibtex_string = scraper.generate_bibtex_string(entry_list, bibtex_list)

                    conference_year_directory = scraper.output_directory + sep + conference + sep + str(year)

                    if not exists(conference_year_directory):
                        makedirs(conference_year_directory)
                    write_bibtex_string_to_file(bibtex_string, conference_year_directory + sep + conference + "-" + str(year) + ".bib")

            except:
                scraper.log(traceback.format_exc())
                with open(scraper.output_directory + sep + "failed.json", "w") as file:
                    if conference not in fails:
                        fails[conference] = []
                    fails[conference].append(year)
                    dump(fails, file)

        scraper.log("="*100)

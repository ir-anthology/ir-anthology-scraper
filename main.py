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

    for venue_type_directory in ["conf","jrnl"]:

        scraper = DBLPscraper("output/" + venue_type_directory)

        with open("output/" + venue_type_directory + "/config.json") as file:
            config = load(file)
            
        fails = {}

        bibtex_cache_filepath = scraper.output_directory + sep + "dblp_bibtex_cache.txt"
        
        bibtex_dump = {}
        if exists(bibtex_cache_filepath):
            with open(bibtex_cache_filepath) as file:
                for line in file:
                    url, bibtex = loads(line)
                    bibtex_dump[url] = bibtex

        for venue, years in config["venues"].items():

            for year in years:

                try:
                    print("Scraping bibtex entries of " + venue + " " + str(year) + "...")
                    entry_list = scraper.scrape_venue(config["venuetype"], venue, year)
                    with open(scraper.output_directory + sep + "dblp_json_results.csv", "a") as file:
                        csv_writer = writer(file, delimiter=",")
                        csv_writer.writerow([venue, year, len(entry_list)])

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
                        bibtex_string = scraper.generate_bibtex_string(entry_list, bibtex_list, config["venuetype"])

                        conference_year_directory = scraper.output_directory + sep + venue + sep + str(year)

                        if not exists(conference_year_directory):
                            makedirs(conference_year_directory)
                        write_bibtex_string_to_file(bibtex_string,
                                                    conference_year_directory + sep + venue_type_directory + "-" + venue + "-" + str(year) + ".bib")

                except:
                    scraper.log(traceback.format_exc())
                    with open(scraper.output_directory + sep + "failed.json", "w") as file:
                        if venue not in fails:
                            fails[venue] = []
                        fails[venue].append(year)
                        dump({"venuetype":config["venuetype"],"venues":fails}, file)

            scraper.log("="*100)

from scripts.dblp_scraper import DBLPscraper
from os.path import exists, sep
from os import makedirs
from shutil import copyfile
from json import dump, load
from tqdm import tqdm
import traceback


if __name__ == "__main__":

    OUTPUT_DIRECTORY = "output"
    CONFIG_FILEPATH = "config.json"
    BIBTEX_CACHE_FILEPATH = "output/conf/dblp_bibtex_cache.txt"

    with open(CONFIG_FILEPATH) as file:
        config = load(file)

    VENUETYPE = config["venuetype"]

    scraper = DBLPscraper(VENUETYPE, OUTPUT_DIRECTORY, BIBTEX_CACHE_FILEPATH)

    copyfile(CONFIG_FILEPATH, scraper.logger_directory + sep + "config.json")
        
    fails = {}

    for venue, years in config["venues"].items():

        for year in years:

            try:
                print("Scraping bibtex entries of " + venue + " " + str(year) + "...")
                entry_list = scraper.scrape_venue(venue, year)

                if entry_list != []:
                    bibtex_list = [scraper.scrape_bibtex(entry) for entry in tqdm(entry_list, total=len(entry_list))]
                    bibtex_string = scraper.generate_bibtex_string(entry_list, bibtex_list)

                    venue_year_directory = scraper.output_directory + sep + venue + sep + str(year)
                    bib_filepath = venue_year_directory + sep + VENUETYPE + "-" + venue + "-" + str(year) + ".bib"

                    if not exists(venue_year_directory):
                        makedirs(venue_year_directory)
                    if exists(bib_filepath):
                        print("Bibtex file for venue " + venue + " and year " + str(year) + " already exists!")
                    else:
                        with open(bib_filepath, "w") as file:
                            file.write(bibtex_string)

            except:
                scraper.log(traceback.format_exc())
                with open(scraper.output_directory + sep + "failed.json", "w") as file:
                    if venue not in fails:
                        fails[venue] = []
                    fails[venue].append(year)
                    dump({"venuetype":VENUETYPE,"venues":fails}, file)

        scraper.log("="*100)

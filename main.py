from argparse import ArgumentParser
from scripts.dblp_scraper import DBLPscraper
from os.path import dirname, exists, sep
from os import makedirs
from json import load
import traceback

def write_bibtex_string_to_file(bibtex_string, output_filepath):
    with open(output_filepath, "w") as file:
        file.write(bibtex_string)


if __name__ == "__main__":

    argument_parser = ArgumentParser()

    argument_parser.add_argument("-c", "--conference",
                                 help="The conference to scrape.")
    argument_parser.add_argument("-y", "--year",
                                 help="The year of the conference to scrape.")
    argument_parser.add_argument("-o", "--output",
                                 help="The path to the output directory.")
    argument_parser.add_argument("--config",
                                 default=None,
                                 help="The path to the config file.")

    args = vars(argument_parser.parse_args())

    if args["config"]:
        with open(args["config"]) as file:
            config = load(file)
        conferences = config["conferences"]
        years = config["years"]
        output_directory = config["output"]

    else:
        conferences = [args["conference"]]
        years = [args["year"]]
        output_directory = args["output"]
        
    scraper = DBLPscraper()

    for conference, year in zip(conferences, years):

        try:
            entry_list = scraper.scrape_conference(conference, year)
            bibtex_list = [scraper.scrape_bibtex(entry) for entry in entry_list]
            bibtex_string = scraper.generate_bibtex_string(entry_list, bibtex_list)

            while True:

                output_filepath = output_directory + sep + conference + "-" + year + ".bib"
            
                if exists(output_filepath):
                    overwrite_check = input("Output file already exists. Overwrite? [Y|n] (Press ENTER to input alternative output path.) ")
                    if overwrite_check == "Y":
                        write_bibtex_string_to_file(bibtex_string, output_filepath)
                        break
                    elif overwrite_check == "n":
                        print("Export aborted.")
                        break
                    elif overwrite_check == "":
                        output_filepath = input("Please enter output filepath: ")
                else:
                    if not exists(output_directory):
                        makedirs(output_directory)
                    write_bibtex_string_to_file(bibtex_string, output_filepath)
                    break
        except:
            scraper.log(traceback.format_exc())

    scraper.log("="*100)

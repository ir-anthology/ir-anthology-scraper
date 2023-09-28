from argparse import ArgumentParser
from scripts.dblp_scraper import DBLPscraper
from os.path import dirname, exists
from os import makedirs


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
                                 help="The path to the output file.")
    argument_parser.add_argument("-m", "--max",
                                 default=None,
                                 help="Maximum number of entries to scrape (defaults to all).")

    args = vars(argument_parser.parse_args())

    conference = args["conference"]
    year = args["year"]
    output_filepath = args["output"]
    output_directory = dirname(output_filepath)
    max_entries = args["max"]
    scraper = DBLPscraper()

    
    entry_list = scraper.scrape_conference(conference, year)[:int(max_entries)] if max_entries else scraper.scrape_conference(conference, year)
    bibtex_list = [scraper.scrape_bibtex(entry) for entry in entry_list]
    bibtex_string = scraper.generate_bibtex_string(entry_list, bibtex_list)

    while True:
    
        if exists(output_filepath):
            overwrite_check = input("Output file already exists. Overwrite? [Y|n] (Press ENTER to input alternative output path.) ")
            if overwrite_check == "Y":
                write_bibtex_string_to_file(bibtex_string, output_filepath)
                break
            elif overwrite_check == "n":
                print("Export aborted.")
                break
            elif overwrite_check == "":
                output_filepath = input("Please enter output path: ")
        else:
            if output_directory and not exists(output_directory):
                makedirs(output_directory)
            write_bibtex_string_to_file(bibtex_string, output_filepath)
            break

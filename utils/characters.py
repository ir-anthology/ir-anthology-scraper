from scripts.dblp_scraper import DBLPscraper
from json import load

if __name__ == "__main__":

    with open("config.json") as file:
        config = load(file)
        
    scraper = DBLPscraper("output")
    
    characters = set()
    abc = set([character for character in "abcdefghijklmnopqrstuvwxyz"])

    for conference, years in config.items():

        for year in years:

            for entry in scraper.scrape_conference(conference, year):
                authors = entry["info"].get("authors", {"author":""})["author"]
                if type(authors) is list:
                    first_author = authors[0]["text"]
                if type(authors) is dict:
                    first_author = authors["text"]
                if type(authors) is str:
                    first_author = authors
                lastname = "".join([c for c in first_author if (c.isalpha() or c == " ")]).strip().lower().split(" ")[-1]
                for character in lastname.lower():
                    if character not in abc:
                        if character not in characters:
                            print(lastname)
                            characters.add(character)
                            with open("characters.txt", "a") as file:
                                file.write(character + "\n")
    with open("characters.txt", "a") as file:
        file.write("="*50)
    


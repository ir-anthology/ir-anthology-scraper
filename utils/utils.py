from time import sleep
from unicodedata import normalize
from requests import get as GET

def normalize_to_ascii(character):
    return normalize("NFD",character).encode("ASCII","ignore").decode("ASCII")

def convert_string_to_ascii(string):
    """
    Format string to ASCII, excluding the following exceptions:

    ä -> ae
    ö -> oe
    ü -> ue
    ß -> ss

    Args:
        string: A string.
    Returns:
        ASCII-formatted version of the input string.
    """
    return "".join([{"ä":"ae","ö":"oe","ü":"ue","ß":"ss"}.get(character, normalize_to_ascii(character)) for character in string])

def get(logger, url, parameters = {}):
        """
        Wrapper function for GET request. If the server responds with Error 429,
        the request is repeated after a delay starting at 10 seconds and incrementing
        by 10 seconds until the delay is greater than 60 seconds, at which point this
        function throws a TimeoutError.

        Args:
            url: The url of the API endpoint.
            parameters: Dictionary of query parameters (optional).
        Returns:
            The API response to the request.
        Throws:
            TimeoutError if server responds with Error 429 and delay has increased to 60 seconds.
        """
        response = GET(url, parameters)
        delay = 10
        while response.status_code == 429:
            if delay > 60:
                raise TimeoutError("Scrape aborted due to repeated status code 429.")
            else:
                logger("Server responded with 429 (Too Many Requests); waiting " + 
                       str(delay) + " seconds...")
                sleep(delay)
            response = GET(url, parameters)
            delay += 10
        return response

def stats(entry_list):
    """
    Provide entry count by year.

    Args:
        entry_list: A list of entries-as-dictionaries to analyse.
    Returns:
        A dictionary of year-count key-value pairs.
    """
    return {year:[entry['info']['year'] for entry in entry_list].count(year)
            for year in sorted(set([e['info']['year'] for e in entry_list]))}

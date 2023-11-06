from unicodedata import normalize

def normalize_to_ascii(character):
    return normalize("NFD",character).encode("ASCII","ignore").decode("ASCII")

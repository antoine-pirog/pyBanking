import json
from importlib import resources

class Hasher(dict):
    # https://stackoverflow.com/a/3405143/190597
    def __missing__(self, key):
        value = self[key] = type(self)()
        return value

with resources.files("pyBanking.resources").joinpath("categories.json").open("r") as f:
    try:
        secrets = Hasher(json.load(f))
    except FileNotFoundError:
        print("WARNING: secrets.json not found, using empty secrets.")
        secrets = Hasher({})



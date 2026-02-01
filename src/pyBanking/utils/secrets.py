import json
from importlib import resources

class Hasher(dict):
    # https://stackoverflow.com/a/3405143/190597
    def __missing__(self, key):
        value = self[key] = type(self)()
        return value
try:
    with resources.files("pyBanking").joinpath("secrets.json").open("r") as f:
        secrets = Hasher(json.load(f))
except FileNotFoundError:
    print("WARNING: secrets.json not found, using empty secrets and dummy database.")
    secrets = Hasher({"db_path" : "data/dummy_database.db"})



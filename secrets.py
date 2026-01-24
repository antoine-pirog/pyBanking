import json

class Hasher(dict):
    # https://stackoverflow.com/a/3405143/190597
    def __missing__(self, key):
        value = self[key] = type(self)()
        return value

try:
    secrets = Hasher(json.load(open('secrets.json')))
except FileNotFoundError:
    print("WARNING: secrets.json not found, using empty secrets.")
    secrets = Hasher({})



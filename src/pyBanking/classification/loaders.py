import json
from importlib import resources
from pyBanking.utils.secrets import secrets

def load_categories():
    with resources.files("pyBanking.resources").joinpath("categories.json").open("r", encoding='utf-8') as f:
        categories = json.load(f)["categories"]
    return categories

def load_classifiers():
    with resources.files("pyBanking.resources").joinpath("classifiers.json").open("r", encoding='utf-8') as f:
        classifiers = json.load(f)
    classifiers = {**classifiers, **secrets["classifiers"]}
    return classifiers
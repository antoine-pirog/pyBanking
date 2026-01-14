import re
import json

with open("classifiers.json", encoding='utf-8') as f:
    CLASSIFIERS = json.load(f)

with open("categories.json", encoding='utf-8') as f:
    CATEGORIES = json.load(f)["categories"]

def get_category_name(subcategory_id):
    main_category_id = subcategory_id // 100
    for category in CATEGORIES:
        if category["id"] == main_category_id:
            break
    for subcategory in category["subcategories"]:
        if subcategory["id"] == subcategory_id:
            return (category["name"], subcategory["name"])

def classify(label):
    for classifier in CLASSIFIERS:
        if re.compile(classifier, re.IGNORECASE).match(label):
            return CLASSIFIERS[classifier]
    return 601

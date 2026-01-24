import re
import json
from pdf_utils import regex_ignore_chars
from common import DbTransaction

from secrets import secrets

with open("classifiers.json", encoding='utf-8') as f:
    CLASSIFIERS = json.load(f)
    CLASSIFIERS = {**CLASSIFIERS, **secrets["classifiers"]}

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
        # if re.compile(classifier, re.IGNORECASE).match(label):
        #     return get_category_by_id(CLASSIFIERS[classifier])
        if regex_ignore_chars(pattern=classifier, text=label, flags=re.IGNORECASE):
            return get_category_by_id(CLASSIFIERS[classifier])
    return get_category_by_id(601)  # Uncategorized

def get_category_by_id(subcategory_id):
    for category in CATEGORIES:
        for subcategory in category["subcategories"]:
            if subcategory["id"] == subcategory_id:
                return (category, subcategory)

def categorize_expenses(db_rows):
    expenses_by_category = {}
    expenses_by_subcategory = {}
    for row in db_rows:
        transaction = DbTransaction(row)
        if transaction.amount >= 0:
            # Not an expense
            continue
        if transaction.category not in expenses_by_category:
            expenses_by_category[transaction.category] = 0
        if transaction.subcategory not in expenses_by_subcategory:
            expenses_by_subcategory[transaction.subcategory] = 0
        expenses_by_category[transaction.category]       += transaction.amount
        expenses_by_subcategory[transaction.subcategory] += transaction.amount
    return expenses_by_category, expenses_by_subcategory

import re
import json
from pyBanking.utils.pdf_utils import regex_ignore_chars
from pyBanking.utils.common import DbTransaction
from pyBanking.classification import loaders

CATEGORIES  = loaders.load_categories()
CLASSIFIERS = loaders.load_classifiers()

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
        if regex_ignore_chars(pattern=classifier, text=label, flags=re.IGNORECASE):
            return get_category_by_id(CLASSIFIERS[classifier])
    return get_category_by_id(601)  # Uncategorized

def get_category_by_id(subcategory_id):
    for category in CATEGORIES:
        for subcategory in category["subcategories"]:
            if subcategory["id"] == subcategory_id:
                return (category, subcategory)

def categorize_expenses(db_rows):
    expenses_total = 0
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
        expenses_total                                   += transaction.amount
        expenses_by_category[transaction.category]       += transaction.amount
        expenses_by_subcategory[transaction.subcategory] += transaction.amount
    return expenses_total, expenses_by_category, expenses_by_subcategory

def categorize_revenues(db_rows):
    revenues_total = 0
    revenues_by_category = {}
    revenues_by_subcategory = {}
    for row in db_rows:
        transaction = DbTransaction(row)
        if transaction.amount <= 0:
            # Not a revenue
            continue
        if transaction.category not in revenues_by_category:
            revenues_by_category[transaction.category] = 0
        if transaction.subcategory not in revenues_by_subcategory:
            revenues_by_subcategory[transaction.subcategory] = 0
        revenues_total                                   += transaction.amount
        revenues_by_category[transaction.category]       += transaction.amount
        revenues_by_subcategory[transaction.subcategory] += transaction.amount
    return revenues_total, revenues_by_category, revenues_by_subcategory

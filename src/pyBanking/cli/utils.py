from pyBanking.utils.common import DbTransaction
from pyBanking.classification import classifier

def _format_row(db_row):
    transaction = DbTransaction(db_row)
    category, subcategory = classifier.get_category_name(transaction.subcategory)
    transaction.label = shorten(transaction.label, 50)
    return f"[[yellow]{transaction.id:>5}[/]] {transaction.date} : {transaction.label:-<50} {transaction.amount:>8.2f} € - [grey50]({transaction.subcategory}) {category} / {subcategory}[/]"

def shorten(string, length=50):
    if len(string) > length:
        string = string[:(length-3)] + "..."
    return string

def input_text(prompt):
    return input(prompt)

def input_int(prompt, retry_message="Must input integer."):
    while True:
        try:
            strvalue = input(prompt)
            if strvalue == "":
                return None
            return int(strvalue)
        except:
            print(retry_message)
            pass

def input_float(prompt, retry_message="Must input float."):
    while True:
        try:
            strvalue = input(prompt)
            if strvalue == "":
                return None
            return float(strvalue)
        except:
            print(retry_message)
            pass

def fix_date(datestr):
    return re.compile(r"(\d{1,2})-(\d{1,2})-(\d{4})").sub(r"\3-\2-\1", datestr)
import pymupdf

import re
import json

from pyBanking.utils.common import Transaction
from pyBanking.utils.pdf_utils import dump_text
from pyBanking.utils.pdf_utils import regex_ignore_chars
from pyBanking.utils.pdf_utils import extract_text_between_tags
from pyBanking.utils.pdf_utils import tofloat
from pyBanking.utils.pdf_utils import reformat

IGNORE_CHARS = set([" ", "\n", "\r"])

def extract_transactions(path_to_file):
    text = load_pdf_statement(path_to_file)
    detail = parse_detailed_listing(text)
    main_ops = parse_main_operations(text)
    transactions = []
    transactions.extend(detail)
    transactions.extend(main_ops)
    return transactions

def load_pdf_statement(path_to_file):
    doc = pymupdf.open(path_to_file)
    doc.authenticate('')
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def parse_file(text):
    overview = parse_accounts_overview(text)
    main_operations = parse_main_operations(text)
    detail = parse_detailed_listing(text)

def parse_tabular_data(text):
    lines = []
    date, label, amount = None, None, None
    STEP_OTHER  = 0
    STEP_DATE   = 1
    STEP_LABEL  = 2
    STEP_AMOUNT = 3
    step = STEP_OTHER
    for line in text.splitlines():
        if (step == STEP_OTHER) or (step == STEP_AMOUNT) :
            if re.compile(r"\d{2}\/\d{2}").match(line.strip()):
                # if date detected : start cycle
                step = STEP_DATE
                date = line.strip()
            else:
                step = STEP_OTHER
        elif step == STEP_DATE :
            # after date, except first label line
            step = STEP_LABEL
            label = line.strip()
        elif step == STEP_LABEL :
            # after a label, expect either another label line or an amount
            if re.compile(r"\d+,\d{2}").match(line.replace(" ", "").strip()):
                # if amount detected, record and commit line
                step = STEP_AMOUNT
                amount = line.strip()
                lines.append((date, label, amount))
            else:
                # otherwise, this is another label line
                step = STEP_LABEL
                label += " " + line.strip()
    return lines

def parse_accounts_overview(text, verbose=False):
    """ Get span of accounts overview """
    pattern_start = "Situation de vos comptes"
    pattern_end   = "Compte Courant Postal"
    
    """ Extract accounts overview """
    overview_raw = extract_text_between_tags(
        text,
        start_tag=pattern_start,
        end_tag=pattern_end,
        ignore_chars=IGNORE_CHARS
    )

    """ Extract table """
    re_table = re.compile(r"(.+?) ([\+\-] ? \d*.*,\d{1,2})")
    table = re_table.findall(overview_raw)

    for i,line in enumerate(table):
        table[i] = (line[0].strip(), tofloat(line[1]))

    if verbose:
        print("Extracted table lines:")
        for line in table:
            print(line)

    return table

def parse_main_operations(text, verbose=False):
    """ Get span of main operations """
    pattern_start = "Compte Courant Postal n. \\d{2} \\d{3} \\d{2}[A-Z] \\d{3}"
    pattern_end   = "Total des op.rations"

    """ Extract main operations """
    operations_raw = extract_text_between_tags(
        text,
        start_tag=pattern_start,
        end_tag=pattern_end,
        ignore_chars=IGNORE_CHARS
    )

    lines = parse_tabular_data(operations_raw)

    """ Extract table """
    table = []
    for line in lines:
        date, label, amount = line
        if re.compile(r"versement.+").match(label.lower()):
            amount = tofloat(amount)
        elif re.compile(r"prelevement.+").match(label.lower()):
            amount = -tofloat(amount)
        elif re.compile(r"virement de.+").match(label.lower()):
            amount = tofloat(amount)
        elif re.compile(r"virement pour.+").match(label.lower()):
            amount = -tofloat(amount)
        elif re.compile(r"virement permanent pour.+").match(label.lower()):
            amount = -tofloat(amount)
        elif re.compile(r"virement instantane a.+").match(label.lower()):
            amount = -tofloat(amount)
        elif re.compile(r"virement emis a.+").match(label.lower()):
            amount = -tofloat(amount)
        elif re.compile(r"cheque n. \d+").match(label.lower()):
            amount = -tofloat(amount)
        elif re.compile(r"remise de cheques .+"):
            amount = tofloat(amount)
        else:
            amount = tofloat(amount)
        table.append(Transaction(
            date=date, 
            label=label, 
            amount=amount)
            )

    """ Update dates """
    dates = [transaction.date for transaction in table]
    dates = update_dates(dates, text)
    for transaction, date in zip(table, dates):
        transaction.date = date

    return table

def parse_detailed_listing(text, verbose=False):
    """ Get span of detailed listing """
    pattern_start = "Carte VISA PREMIER"
    pattern_end   = "Montant pr.lev. sur votre CCP"

    """ Extract detailed listing """
    detail_raw = extract_text_between_tags(
        text,
        start_tag=pattern_start,
        end_tag=pattern_end,
        ignore_chars=IGNORE_CHARS
    )
    
    lines = parse_tabular_data(detail_raw)

    table = []
    for i,line in enumerate(lines):
        date, label, amount = line
        table.append(Transaction(
            date = date, 
            label = label, 
            amount = -tofloat(amount)
            )
        )
    
    """ Update dates """
    dates = [transaction.date for transaction in table]
    dates = update_dates(dates, text)
    for transaction, date in zip(table, dates):
        transaction.date = date

    if verbose:
        print("Extracted table lines:")
        for line in table:
            print(line)
    
    return table

def parse_date_span(text):
    """ Retrieve date span of bank statement """
    """ Especially to retrieve year information, absent from most fields """

    """ Date edited """
    edited_raw = regex_ignore_chars(
        r"Relev. n. \d{1,2} \| \d{2}\/\d{2}\/\d{4}", 
        text, chars=IGNORE_CHARS)[0].text
    edited_found = re.compile(r"\d{2}\/\d{2}\/\d{4}").findall(edited_raw)
    statement_edited = edited_found[0]
    # print("Statement edited :", statement_edited)

    """ Date span of detail section """
    detail_span_raw = regex_ignore_chars(
        r"Vos op.rations  carte . d.bit  diff.r. \(du \d{2}\/\d{2}\/\d{4} au \d{2}\/\d{2}\/\d{4}\)", 
        text, chars=IGNORE_CHARS)[0].text
    detail_dates_found = re.compile(r"\d{2}\/\d{2}\/\d{4}").findall(detail_span_raw)
    detail_span = (detail_dates_found[0], detail_dates_found[1])
    # print("Transaction details span :", detail_span)
    
    return {
        "edited" : statement_edited,
        "detail" : detail_span
    } 


def update_dates(dates, text):
    parsed_dates = parse_date_span(text)
    """ Complement dates with missing year field and return them as yyyy/mm/dd"""
    date_begin, date_end = parsed_dates["detail"]
    # Supports edge cases, e.g. 28/12/2024 & 27/01/2025 : 12/2024 != 01/2025
    lookup = {
        date_begin.split("/")[1] : date_begin.split("/")[2],
        date_end.split("/")[1]   : date_end.split("/")[2],
    }
    """ Append correct year to dates """
    dates_updated = []
    for date in dates:
        if len(date.split("/")) == 3:
            dates_updated.append(date)
        else:
            if date.split("/")[1] in lookup:
                newdate = date + "/" + lookup[date.split("/")[1]]
                dates_updated.append(newdate)
            else:
                newdate = date + "/" + date_begin.split("/")[2]
                dates_updated.append("?" + newdate)

    """ Switch to yyyymmdd format """
    for i,date in enumerate(dates_updated):
        if date.startswith("?"):
            prefix = "?"
            date = date[1:]
        else:
            prefix = ""
        parts = date.split("/")
        date_formatted = f"{prefix}{parts[2]}-{parts[1]}-{parts[0]}"
        dates_updated[i] = date_formatted

    return dates_updated



if __name__ == "__main__":
    # Example usage
    text = load_pdf_statement("dev/sample_bank_statement_LBP.pdf")
    parse_detailed_listing(text, verbose=True)
    parse_main_operations(text, verbose=True)
    parse_accounts_overview(text, verbose=True)
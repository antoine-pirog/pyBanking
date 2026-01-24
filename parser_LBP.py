import PyPDF2 as pdf
import re
import json

from common import Transaction

from pdf_utils import dump_text
from pdf_utils import regex_ignore_chars
from pdf_utils import extract_text_between_tags
from pdf_utils import tofloat
from pdf_utils import reformat

from secrets import secrets

statement_tags = json.load(open('statement_tags.json'))
statement_bank = "LaBanquePostale"
statement_file_version = "V2024"

IGNORE_CHARS = set([" ", "\n", "\r"])
DETAILED_LISTING_RE  = 'detailed_listing_regexes' 
ACCOUNTS_OVERVIEW_RE = 'accounts_overview_regexes'
MAIN_OPERATIONS_RE   = 'main_operations_regexes'

def load_pdf_statement(path_to_file):
    with open(path_to_file, 'rb') as fid:
        reader = pdf.PdfReader(fid)
        reader.decrypt('')
        text = "\n".join(page.extract_text() for page in reader.pages)
    return text

def parse_file(text):
    overview = parse_accounts_overview(text)
    main_operations = parse_main_operations(text)
    detail = parse_detailed_listing(text)

def parse_accounts_overview(text, verbose=False):
    """ Get span of accounts overview """
    pattern_start = statement_tags[statement_bank][ACCOUNTS_OVERVIEW_RE][statement_file_version]['start']
    pattern_end   = statement_tags[statement_bank][ACCOUNTS_OVERVIEW_RE][statement_file_version]['end']
    
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
    pattern_start = statement_tags[statement_bank][MAIN_OPERATIONS_RE][statement_file_version]['start']
    pattern_end   = statement_tags[statement_bank][MAIN_OPERATIONS_RE][statement_file_version]['end']

    """ Extract main operations """
    operations_raw = extract_text_between_tags(
        text,
        start_tag=pattern_start,
        end_tag=pattern_end,
        ignore_chars=IGNORE_CHARS
    )

    """ Preprocess raw text """
    operations_raw = operations_raw.replace('\n', ' ')

    """ Strip unnecessary parts """
    patterns_to_strip = [
        r"IBAN  : .+? BIC :  [A-Z]+"
        r"> D.couvert autoris. au \d{2}\/\d{2}\/\d{4} .+? utilisation effective du d.couvert\.",
        r"D.couvert autoris. au \d{2}\/\d{2}\/\d{4} .+? r.gulariser sous 30 jours\)",
        r"> Avantage FORMULE DE COMPTE .+? sont pas factur.s. \(Seuil  en vigueur  au \d{2}\/\d{2}\/\d{4}\)",
        r"Ancien solde au \d{2}\/\d{2}\/\d{4} \d+,\d{1,2}",
        r"Relev.  n. \d+ .+? \(suite\)",
        r"> Frais et cotisations .+? \d{2}\/\d{2}\/\d{4} .+? \d+,\d{1,2}",
    ]
    for pattern in patterns_to_strip:
        matches_pattern = regex_ignore_chars(pattern, operations_raw, chars=IGNORE_CHARS)
        if matches_pattern:
            # print(f"Matched strip pattern: {pattern}")
            for match_pattern in matches_pattern:
                operations_raw = operations_raw[:match_pattern.start] + operations_raw[match_pattern.end:]

    # dump_text(operations_raw.replace('\n', ' '), destination="dev/main_operations_extracted.txt")

    """ Extract table lines """
    lines = re.compile(r"\d{2}\/\d{2}.*?,\d{1,2}").findall(operations_raw)

    """ Detect special fields and replace them with correct formatting """
    special_fields_patterns = [
        *secrets["main_operations"]["debit_mandates"],
        r"REFERENCE : \S{16}",
        r"CARTE NUMERO \d{3}",
        r"\d{2}\/\d{2}\/\d{4}",
        r"\d{2}\/\d{4}",
    ]

    for i,line in enumerate(lines):
        # print(line)
        for pattern in special_fields_patterns:
            matches_pattern = regex_ignore_chars(pattern, line, chars=IGNORE_CHARS)
            if matches_pattern:
                for match_pattern in matches_pattern[::-1]: # Reverse to not mess up indices
                    original_text = line[match_pattern.start:match_pattern.end]
                    corrected_text = reformat(original_text, pattern, IGNORE_CHARS) + " "
                    line = line[:match_pattern.start] + corrected_text + ";" + line[match_pattern.end:]
        lines[i] = line

    """ Extract table """
    table = []
    for line in lines:
        entry_with_reference = re.compile(r"(\d{2}\/\d{2}) *?(VIREMENT.+?REFERENCE : \d{16}) *?([\d+]? *[\d+]? *\d+,\d{1,2})").search(line)
        entry_generic = re.compile(r"(\d{2}\/\d{2}) *?(.+?) *?([\d+]? *[\d+]? *\d+,\d{1,2})").search(line)
        if entry_with_reference:
            # print(f"Matched entry with reference: {line}")
            entry = entry_with_reference
        else:
            entry = entry_generic
        # print(line)
        if entry:
            matched_date = entry.group(1).strip()
            matched_description = entry.group(2).strip()
            matched_amount = entry.group(3).strip().replace(",", ".")
            if "versement" in matched_description.lower():
                matched_amount = tofloat(matched_amount)
            elif "prelevement" in matched_description.lower():
                matched_amount = -tofloat(matched_amount)
            elif "virement de" in matched_description.lower():
                matched_amount = tofloat(matched_amount)
            elif "virement pour" in matched_description.lower():
                matched_amount = -tofloat(matched_amount)
            elif "virement permanent pour" in matched_description.lower():
                matched_amount = -tofloat(matched_amount)
            else:
                matched_amount = tofloat(matched_amount)
            table.append(Transaction(
                date=matched_date, 
                label=matched_description, 
                amount=matched_amount)
                )

    """ Update dates """
    dates = [transaction.date for transaction in table]
    dates = update_dates(dates, text)
    for transaction, date in zip(table, dates):
        transaction.date = date

    # for line in table:
    #     print(line)

    return table

def parse_detailed_listing(text, verbose=False):
    """ Get span of detailed listing """
    pattern_start = statement_tags[statement_bank][DETAILED_LISTING_RE][statement_file_version]['start']
    pattern_end   = statement_tags[statement_bank][DETAILED_LISTING_RE][statement_file_version]['end']

    """ Extract detailed listing """
    detail_raw = extract_text_between_tags(
        text,
        start_tag=pattern_start,
        end_tag=pattern_end,
        ignore_chars=IGNORE_CHARS
    )

    """ Extract table """
    re_table = re.compile(r"(\d{2}\/\d{2})(.+?)(\d+,\d{1,2})")

    table = re_table.findall(detail_raw)

    for i,line in enumerate(table):
        table[i] = Transaction(
            date=line[0].strip(), 
            label=line[1].strip(), 
            amount=-tofloat(line[2])
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
        date_formatted = f"{prefix}{parts[2]}/{parts[1]}/{parts[0]}"
        dates_updated[i] = date_formatted

    return dates_updated



if __name__ == "__main__":
    # Example usage
    text = load_pdf_statement("dev/sample_bank_statement_LBP.pdf")
    parse_detailed_listing(text, verbose=True)
    parse_main_operations(text, verbose=True)
    parse_accounts_overview(text, verbose=True)
import cmd
import re
import random

import classifier
from common import DbTransaction

messages = [
    "Reconstructing your financial crimes...",
    "Parsing your questionable life choices...",
    "Auditing your past optimism...",
    "Calculating how coffee became a lifestyle...",
    "Summoning the ghosts of purchases past...",
    "Replaying your economic decisions in slow motion...",
    "Analyzing where the money went. Again.",
    "Turning denial into data...",
    "Converting impulse into statistics...",
    "Welcome back to the consequences of your own actions.",
    "Initializing fiscal introspection module...",
    "Loading regret-driven analytics engine...",
    "Compiling spending history...",
    "Optimizing your relationship with reality...",
    "Booting budget-awareness daemon...",
    "Mounting financial truth filesystem...",
    "Running post-mortem on your wallet...",
    "Allocating memory for bad decisions...",
    "Indexing transactions you forgot about...",
    "Starting the accountant you never wanted...",
    "Detecting abnormal caffeine-related expenses...",
    "Estimating your lifetime coffee investment...",
    "Identifying recurring café-based happiness...",
    "Normalizing coffee-to-income ratio...",
    "Coffee spending classified as infrastructure...",
    "Auditing your relationship with baristas...",
    "I promise not to judge. Much.",
    "Your money story is safe with me. Probably.",
    "Let's pretend this is all under control.",
    "I see everything. Especially the late-night purchases.",
    "Trust me, I've seen worse.",
    "Preparing polite disappointment...",
    "Simulating financial responsibility...",
    "Let's call this 'data-driven maturity'.",
    "Sharpening virtual pencil...",
    "Straightening virtual glasses...",
    "Summoning inner accountant...",
    "Balancing sheets and expectations...",
    "Dusting off the ledger of truth...",
    "Opening the book of financial honesty...",
    "You spent money. I have proof.",
    "This will hurt a little.",
    "Spoiler: you bought things.",
    "Numbers don't lie. Unfortunately.",
    "Facing the spreadsheet of destiny...",
    "Reality check loading...",
    "Brace yourself for statistics.",
    "Decrypting wallet activity...",
    "Accessing secure regret vault...",
    "Running financial forensics...",
    "Tracing money packets...",
    "Establishing connection to reality...",
    "Root access granted to your expenses...",
    "Scanning for fiscal anomalies...",
    "Breathe in. Breathe out. It's just numbers.",
    "This is a safe space for bad decisions.",
    "Let the data cleanse you...",
    "Acceptance begins with CSV files.",
    "Today we face the numbers peacefully.",
    "Yes, this is still better than Excel.",
    "You could have used a spreadsheet. You didn't.",
    "Good choice building this tool. You clearly needed it.",
    "This app exists for a reason. You know why.",
    "Future you thanks present you.",
    "Past you apologizes silently.",
    "Rolling for financial awareness... d20 → 3",
    "Achievement unlocked: Budget Curiosity",
    "XP gained: +5 Financial Anxiety",
    "Quest started: Track where the gold went",
    "Inventory check: Mostly receipts",
    "NPC accountant has entered the chat"
]

intro_message = ""
intro_message += f"================================================\n"
intro_message += f"= pyBanking - {random.choice(messages)}\n"
intro_message += f"= Type help for commands.\n"
intro_message += f"================================================\n"

def cmd_lookup(db, command):
    regexes = {
        r"show all" : show_all,
        r"show where +(.+)" : show_where_custom_query,
        r"show categories" : show_categories,
        r"show uncategorized" : show_uncategorized,
        r"show date +between +(\d{1,2}\/\d{1,2}\/\d{4})-(\d{1,2}\/\d{1,2}\/\d{4})" : show_date_between,
        r"show date +before +(\d{1,2}\/\d{1,2}\/\d{4})" : show_date_before,
        r"show date +after +(\d{1,2}\/\d{1,2}\/\d{4})" : show_date_after,
        r"show (\d+)" : show_entry_by_id,
        r"edit (\d+)" : edit_entry_by_id,
        r"search (.+)" : search_text,
    }
    for regex in regexes:
        match = re.compile(regex).match(command)
        if match:
            regexes[regex](db, match.groups())
            continue

class CLI(cmd.Cmd):
    prompt = "> "
    intro = intro_message

    def link_db(self, db):
        self.db = db

    def do_show(self, line):
        """ Shows list of expenses 
            | Supported commands :
            | - show all
            | - show uncategorized
            | - show categories
            | - show date after <dd/mm/yyyy> 
            |   > ex. : show date after 01/01/2024
            | - show date before <dd/mm/yyyy>
            |   > ex. : show date before 01/01/2024
            | - show date between <dd/mm/yyyy-dd/mm/yyyy>
            |   > ex. : show date afte between 01/01/2024-31/12/2025
            | - show where <sql filter>
            |   > ex. : show where amount < -1000
            |   > columns in db are :
            |     - date (str)
            |     - label (str)
            |     - amount (float)
            |     - category (int)
            |     - subcategory (int)
            |     - ignore (int)"""
        cmd_lookup(self.db, f"show {line}")
    
    def do_edit(self, line):
        """ Edits a database entry
            | Syntax : edit <db entry id>
            | > ex. : edit 1801
        """
        cmd_lookup(self.db, f"edit {line}")

    def do_search(self, line):
        """ Searches transaction entries labels for a string
            | Syntax : search <pattern to search>
            | > ex. : search sushi bar
        """
        cmd_lookup(self.db, f"search {line}")

    def do_exit(self, line):
        """Exits the program """
        return True

def _format_row(db_row):
    transaction = DbTransaction(db_row)
    category, subcategory = classifier.get_category_name(transaction.subcategory)
    if len(transaction.label) > 50:
        transaction.label = transaction.label[:47] + "..."
    return f"[{transaction.id:>5}] {transaction.date} : {transaction.label:-<50} {transaction.amount:>8.2f} € - {category} / {subcategory}"

def show_uncategorized(db, args=None):
    print("=================================================")
    print("Uncategorized transactions :")
    uncategorized = db.fetch_uncategorized()
    labels = {} # Keep track of unique labels and number of occurences
    total = 0
    for row in uncategorized:
        transaction = DbTransaction(row)
        id = transaction.id
        date = transaction.date
        label = transaction.label
        amount = transaction.amount
        category = transaction.category
        subcategory = transaction.subcategory
        if label not in labels: 
            labels[label] = {"nbr" : 1, "amount" : amount}
        else: 
            labels[label]["nbr"] += 1
            labels[label]["amount"] += amount
        total += amount
        print(_format_row(row))
    print()
    print(f"({len(uncategorized)} rows total - {len(labels)} unique labels) - {total:.2f} €")
    print()
    print("Regularily occuring labels (ignoring < 3) :")
    for label in sorted([k for k in labels], key=lambda x : -labels[x]["nbr"]):
        if labels[label]["nbr"] > 2:
            print(f"  - {label} (x{labels[label]["nbr"]})")
    print()
    print("Most expensive occuring labels (ignoring < 100 €) :")
    for label in sorted([k for k in labels], key=lambda x : -labels[x]["amount"]):
        if labels[label]["amount"] > 100:
            print(f"  - {label} ({labels[label]["amount"]:.2f} € on {labels[label]["nbr"]} transaction(s))")
    print("=================================================")

def update_uncategorized(db, args=None):
    rows_to_update = db.fetch_uncategorized()
    updated = 0
    for row in rows_to_update:
        transaction = DbTransaction(row)
        id = transaction.id
        date = transaction.date
        label = transaction.label
        amount = transaction.amount
        category = transaction.category
        subcategory = transaction.subcategory

        category, subcategory = classifier.classify(label)
        db.update_row(id, "transactions", "category", category["id"])
        db.update_row(id, "transactions", "subcategory", subcategory["id"])
        if subcategory["id"] != 601:
            updated += 1
    db.commit()
    print(f"{updated} rows updated.")

def show_categories(db, args=None):
    for category in classifier.CATEGORIES:
        print(f"[{category['id']}] {category['name']} ======================")
        for subcategory in category['subcategories']:
            print(f"  - [{subcategory['id']:>3}] {subcategory['name']}")

def show_all(db, args=None):
    rows = db.query(f"SELECT * FROM transactions")
    for row in rows :
        print(_format_row(row))
    print()
    print_categorized_expenses(rows)

def show_where_custom_query(db, args):
    query, = args
    query = re.compile(r"(\d{1,2})\/(\d{1,2})\/(\d{4})").sub(r"\3/\2/\1", query)
    rows = db.query(f"SELECT * FROM transactions WHERE {query}")
    for row in rows :
        print(_format_row(row))
    print()
    print_categorized_expenses(rows)

def print_categorized_expenses(db_rows):
    total_expenses, expenses_by_category, expenses_by_subcategory = classifier.categorize_expenses(db_rows)
    categorized_expenses = {**expenses_by_category, **expenses_by_subcategory}
    print(f"{'TOTAL' + ' ':#<65} {total_expenses:>8.2f} €")
    for category_id in expenses_by_category:
        category, _ = classifier.get_category_name(category_id*100 + 1)
        subtotal = expenses_by_category[category_id]
        print(f"{category + ' ':=<60} {subtotal:>8.2f} € ({100*subtotal/total_expenses:>5.2f}%)")
        for subcategory_id in expenses_by_subcategory:
            if (subcategory_id // 100) == category_id :
                _, subcategory = classifier.get_category_name(subcategory_id)
                subtotal = expenses_by_subcategory[subcategory_id]
                print(f"  - {subcategory + ' ':-<30} {subtotal:>8.2f} € ({100*subtotal/total_expenses:>5.2f}%)")

def show_date_between(db, args):
    date0, date1 = args
    date0 = "/".join(date0.split("/")[::-1])
    date1 = "/".join(date1.split("/")[::-1])
    rows = db.query(f"SELECT * FROM transactions WHERE date >= {date0} AND date <= {date1}")
    rows = [row for row in rows if not row[1].startswith("?")] # Exclude undefined dates
    for row in rows :
        print(_format_row(row))

def show_date_before(db, args):
    date0, = args
    date0 = "/".join(date0.split("/")[::-1])
    rows = db.query(f"SELECT * FROM transactions WHERE date <= {date0}")
    rows = [row for row in rows if not row[1].startswith("?")] # Exclude undefined dates
    for row in rows :
        print(_format_row(row))

def show_date_after(db, args):
    date0, = args
    date0 = "/".join(date0.split("/")[::-1])
    rows = db.query(f"SELECT * FROM transactions WHERE date >= {date0}")
    rows = [row for row in rows if not row[1].startswith("?")] # Exclude undefined dates
    for row in rows :
        print(_format_row(row))

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

def fix_date(datestr):
    return re.compile(r"(\d{1,2})\/(\d{1,2})\/(\d{4})").sub(r"\3/\2/\1", datestr)

def show_entry_by_id(db, args):
    entry_id, = args
    transaction = DbTransaction(db.get_by_id(entry_id))
    print(f"+-------------------------------------------------")
    print(f"| Entry {entry_id} :")
    print(f"|   - label : {transaction.label}")
    print(f"|   - date  : {transaction.date}")
    print(f"|   - amount : {transaction.amount} €")
    print(f"|   - category : {transaction.category}")
    print(f"|   - subcategory : {transaction.subcategory}")
    print(f"|   - ignore : {transaction.ignore}")
    print(f"+-------------------------------------------------")

def edit_entry_by_id(db, args):
    entry_id, = args
    transaction = DbTransaction(db.get_by_id(entry_id))
    show_entry_by_id(db, args)
    print(f"| Leave fields blank to leave unchanged.")
    print( "| New label : ")           ; updated_label       = input_text("| > ").strip()
    print( "| New date : ")            ; updated_date        = input_text("| > ").strip()
    print( "| New amount : ")          ; updated_amount      = input_int("| > ", retry_message="| Must input integer.")
    print( "| New category idx : ")    ; updated_category    = input_int("| > ", retry_message="| Must input integer.")
    print( "| New subcategory idx : ") ; updated_subcategory = input_int("| > ", retry_message="| Must input integer.")
    print( "| New ignore flag : ")     ; updated_ignore      = input_int("| > ", retry_message="| Must input integer.")
    print(f"+-------------------------------------------------")

    updated_label = transaction.label if updated_label == "" else updated_label
    updated_date = transaction.date if updated_date == "" else updated_date
    updated_amount = transaction.amount if updated_amount is None else updated_amount
    updated_category = transaction.category if updated_category is None else updated_category
    updated_subcategory = transaction.subcategory if updated_subcategory is None else updated_subcategory
    updated_ignore = transaction.ignore if updated_ignore is None else updated_ignore

    db.update_row(entry_id, "transactions", "label", '"' + updated_label + '"')
    db.update_row(entry_id, "transactions", "date", '"' + updated_date + '"')
    db.update_row(entry_id, "transactions", "amount", updated_amount)
    db.update_row(entry_id, "transactions", "category", updated_category)
    db.update_row(entry_id, "transactions", "subcategory", updated_subcategory)
    db.update_row(entry_id, "transactions", "ignore", updated_ignore)
    db.commit()

    print("| Edited :")
    print("| " + _format_row(db.get_by_id(entry_id)))
    print(f"+-------------------------------------------------")

def search_text(db, args):
    text, = args
    print(f"+-------------------------------------------------")
    print(f"| Searching pattern '{text}'")
    idx = 1
    matches = []
    while True:
        entry = db.get_by_id(idx)
        if not entry:
            break # end of db reached
        transaction = DbTransaction(entry)
        if text.lower() in transaction.label.lower():
            matches.append(entry)
        idx += 1
    print(f"| {len(matches)} found :")
    for match in matches:
        print("|   " + _format_row(match))
    print(f"+-------------------------------------------------")


import re
from pyBanking.utils.common import DbTransaction
from pyBanking.cli import utils
from pyBanking.classification import classifier

def show_buffered(ctx, args=None):
    for row in ctx.buffered :
        print(utils._format_row(row))
    print()

    print_categorized_expenses(ctx.buffered)
    print()
    print_categorized_revenues(ctx.buffered)

def show_uncategorized(ctx, args=None):
    print("=================================================")
    print("Uncategorized transactions :")
    uncategorized = ctx.db.fetch_uncategorized()
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
        print(utils._format_row(row))
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
    return uncategorized

def update_uncategorized(ctx, args=None):
    rows_to_update = ctx.db.fetch_uncategorized()
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
        ctx.db.update_row(id, "transactions", "category", category["id"])
        ctx.db.update_row(id, "transactions", "subcategory", subcategory["id"])
        if subcategory["id"] != 601:
            updated += 1
    ctx.db.commit()
    print(f"{updated} rows updated.")

def show_categories(ctx, args=None):
    for category in classifier.CATEGORIES:
        print(f"[{category['id']}] {category['name']} ======================")
        for subcategory in category['subcategories']:
            print(f"  - [{subcategory['id']:>3}] {subcategory['name']}")

def show_all(ctx, args=None):
    rows = ctx.db.query(f"SELECT * FROM transactions")
    for row in rows :
        print(utils._format_row(row))
    print()
    print_categorized_expenses(rows)
    print()
    print_categorized_revenues(rows)
    return rows

def show_where_custom_query(ctx, args):
    query, = args
    query = re.compile(r"(\d{1,2})-(\d{1,2})-(\d{4})").sub(r"'\3-\2-\1'", query)
    rows = ctx.db.query(f"SELECT * FROM transactions WHERE {query}")
    for row in rows :
        print(utils._format_row(row))
    print()
    print_categorized_expenses(rows)
    print()
    print_categorized_revenues(rows)
    return rows

def print_categorized_expenses(db_rows):
    total_expenses, expenses_by_category, expenses_by_subcategory = classifier.categorize_expenses(db_rows)
    categorized_expenses = {**expenses_by_category, **expenses_by_subcategory}
    print(f"{'TOTAL EXPENSES' + ' ':#<65} {total_expenses:>8.2f} €")
    for category_id in expenses_by_category:
        category, _ = classifier.get_category_name(category_id*100 + 1)
        subtotal = expenses_by_category[category_id]
        print(f"{category + ' ':=<60} {subtotal:>8.2f} € ({100*subtotal/total_expenses:>5.2f}%)")
        for subcategory_id in expenses_by_subcategory:
            if (subcategory_id // 100) == category_id :
                _, subcategory = classifier.get_category_name(subcategory_id)
                subtotal = expenses_by_subcategory[subcategory_id]
                print(f"  - {subcategory + ' ':-<30} {subtotal:>8.2f} € ({100*subtotal/total_expenses:>5.2f}%)")

def print_categorized_revenues(db_rows):
    total_revenues, revenues_by_category, revenues_by_subcategory = classifier.categorize_revenues(db_rows)
    categorized_revenues = {**revenues_by_category, **revenues_by_subcategory}
    print(f"{'TOTAL REVENUES' + ' ':#<65} {total_revenues:>8.2f} €")
    for category_id in revenues_by_category:
        category, _ = classifier.get_category_name(category_id*100 + 1)
        subtotal = revenues_by_category[category_id]
        print(f"{category + ' ':=<60} {subtotal:>8.2f} € ({100*subtotal/total_revenues:>5.2f}%)")
        for subcategory_id in revenues_by_subcategory:
            if (subcategory_id // 100) == category_id :
                _, subcategory = classifier.get_category_name(subcategory_id)
                subtotal = revenues_by_subcategory[subcategory_id]
                print(f"  - {subcategory + ' ':-<30} {subtotal:>8.2f} € ({100*subtotal/total_revenues:>5.2f}%)")

def show_date_between(ctx, args):
    date0, date1 = args
    date0 = "-".join(date0.split("-")[::-1])
    date1 = "-".join(date1.split("-")[::-1])
    rows = ctx.db.query(f"SELECT * FROM transactions WHERE date >= '{date0}' AND date <= '{date1}'")
    rows = [row for row in rows if not row[1].startswith("?")] # Exclude undefined dates
    for row in rows :
        print(utils._format_row(row))
    print()
    print_categorized_expenses(rows)
    print()
    print_categorized_revenues(rows)
    return rows

def show_date_before(ctx, args):
    date0, = args
    date0 = "-".join(date0.split("-")[::-1])
    rows = ctx.db.query(f"SELECT * FROM transactions WHERE date <= '{date0}'")
    rows = [row for row in rows if not row[1].startswith("?")] # Exclude undefined dates
    for row in rows :
        print(utils._format_row(row))
    print()
    print_categorized_expenses(rows)
    print()
    print_categorized_revenues(rows)
    return rows

def show_date_after(ctx, args):
    date0, = args
    date0 = "-".join(date0.split("-")[::-1])
    rows = ctx.db.query(f"SELECT * FROM transactions WHERE date >= '{date0}'")
    rows = [row for row in rows if not row[1].startswith("?")] # Exclude undefined dates
    for row in rows :
        print(utils._format_row(row))
    print()
    print_categorized_expenses(rows)
    print()
    print_categorized_revenues(rows)
    return rows

def show_month(ctx, args):
    date, = args
    date = date.strip()
    match_mmyyyy = re.compile(r".*(\d{2})-(\d{4}).*").match(date)
    match_yyyymm = re.compile(r".*(\d{4})-(\d{2}).*").match(date)
    if match_mmyyyy:
        month = match_mmyyyy.group(1)
        year  = match_mmyyyy.group(2)
    if match_yyyymm:
        month = match_mmyyyy.group(2)
        year  = match_mmyyyy.group(1)
    buffered = show_where_custom_query(ctx, (f"date >= '{year}-{month}-01' AND date <= '{year}-{month}-31'",))
    return buffered

def show_year(ctx, args):
    year, = args
    year = year.strip()
    buffered = show_where_custom_query(ctx, (f"date >= '{year}-01-01' AND date <= '{year}-12-31'",))
    return buffered

def show_entry_by_id(ctx, args):
    entry_id, = args
    transaction = DbTransaction(ctx.db.get_by_id(entry_id))
    print(f"+-------------------------------------------------")
    print(f"| Entry {entry_id} :")
    print(f"|   - label : {transaction.label}")
    print(f"|   - date  : {transaction.date}")
    print(f"|   - amount : {transaction.amount} €")
    print(f"|   - category : {transaction.category}")
    print(f"|   - subcategory : {transaction.subcategory}")
    print(f"|   - ignore : {transaction.ignore}")
    print(f"+-------------------------------------------------")

def edit_entry_by_id(ctx, args):
    entry_id, = args
    transaction = DbTransaction(ctx.db.get_by_id(entry_id))
    show_entry_by_id(ctx, args)
    print(f"| Leave fields blank to leave unchanged.")
    print( "| New label : ")           ; updated_label       = utils.input_text("| > ").strip()
    print( "| New date : ")            ; updated_date        = utils.input_text("| > ").strip()
    print( "| New amount : ")          ; updated_amount      = utils.input_float("| > ", retry_message="| Must input integer.")
    print( "| New category idx : ")    ; updated_category    = utils.input_int("| > ", retry_message="| Must input integer.")
    print( "| New subcategory idx : ") ; updated_subcategory = utils.input_int("| > ", retry_message="| Must input integer.")
    print( "| New ignore flag : ")     ; updated_ignore      = utils.input_int("| > ", retry_message="| Must input integer.")
    print(f"+-------------------------------------------------")

    updated_label = transaction.label if updated_label == "" else updated_label
    updated_date = transaction.date if updated_date == "" else updated_date
    updated_amount = transaction.amount if updated_amount is None else updated_amount
    updated_category = transaction.category if updated_category is None else updated_category
    updated_subcategory = transaction.subcategory if updated_subcategory is None else updated_subcategory
    updated_ignore = transaction.ignore if updated_ignore is None else updated_ignore

    ctx.db.update_row(entry_id, "transactions", "label", '"' + updated_label + '"')
    ctx.db.update_row(entry_id, "transactions", "date", '"' + updated_date + '"')
    ctx.db.update_row(entry_id, "transactions", "amount", updated_amount)
    ctx.db.update_row(entry_id, "transactions", "category", updated_category)
    ctx.db.update_row(entry_id, "transactions", "subcategory", updated_subcategory)
    ctx.db.update_row(entry_id, "transactions", "ignore", updated_ignore)
    ctx.db.commit()

    print("| Edited :")
    print("| " + utils._format_row(ctx.db.get_by_id(entry_id)))
    print(f"+-------------------------------------------------")

def edit_buffered_entries(ctx, args=None):
    show_buffered(ctx)
    print(f"| Leave fields blank to leave unchanged.")
    print( "| New label : ")           ; updated_label       = utils.input_text("| > ").strip()
    print( "| New date : ")            ; updated_date        = utils.input_text("| > ").strip()
    print( "| New amount : ")          ; updated_amount      = utils.input_float("| > ", retry_message="| Must input integer.")
    print( "| New category idx : ")    ; updated_category    = utils.input_int("| > ", retry_message="| Must input integer.")
    print( "| New subcategory idx : ") ; updated_subcategory = utils.input_int("| > ", retry_message="| Must input integer.")
    print( "| New ignore flag : ")     ; updated_ignore      = utils.input_int("| > ", retry_message="| Must input integer.")
    print(f"+-------------------------------------------------")
    for entry in ctx.buffered:
        transaction = DbTransaction(entry)
        entry_id = transaction.id
        # Handle updates to do
        updated_this_label = transaction.label if updated_label == "" else updated_label
        updated_this_date = transaction.date if updated_date == "" else updated_date
        updated_this_amount = transaction.amount if updated_amount is None else updated_amount
        updated_this_category = transaction.category if updated_category is None else updated_category
        updated_this_subcategory = transaction.subcategory if updated_subcategory is None else updated_subcategory
        updated_this_ignore = transaction.ignore if updated_ignore is None else updated_ignore
        # Update in db
        ctx.db.update_row(entry_id, "transactions", "label", '"' + updated_this_label + '"')
        ctx.db.update_row(entry_id, "transactions", "date", '"' + updated_this_date + '"')
        ctx.db.update_row(entry_id, "transactions", "amount", updated_this_amount)
        ctx.db.update_row(entry_id, "transactions", "category", updated_this_category)
        ctx.db.update_row(entry_id, "transactions", "subcategory", updated_this_subcategory)
        ctx.db.update_row(entry_id, "transactions", "ignore", updated_this_ignore)
    # Commit changes (TODO : ask for confirmation before committing ...)
    ctx.db.commit()

def execute_sql_request(ctx, args):
    request, = args
    ctx.db.raw_execute(request)
    ctx.db.commit()

def search_text(ctx, args):
    text, = args
    print(f"+-------------------------------------------------")
    print(f"| Searching pattern '{text}'")
    idx = 1
    matches = []
    while True:
        entry = ctx.db.get_by_id(idx)
        if not entry:
            break # end of db reached
        transaction = DbTransaction(entry)
        if text.lower() in transaction.label.lower():
            matches.append(entry)
        idx += 1
    print(f"| {len(matches)} found :")
    for match in matches:
        print("|   " + utils._format_row(match))
    print(f"+-------------------------------------------------")
    return matches
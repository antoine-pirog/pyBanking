import re
from pyBanking.utils.common import DbTransaction
from pyBanking.cli import utils
from pyBanking.classification import classifier
from pyBanking.cli.console import console
from pyBanking.cli import colors

def _show_analytics(db_rows, args=None):
    for row in db_rows :
        console.print(utils._format_row(row))
    console.print()
    print_categorized_expenses(db_rows)
    console.print()
    print_categorized_revenues(db_rows)


def show_buffered(ctx, args=None):
    _show_analytics(ctx.buffered, args=args)

def show_uncategorized(ctx, args=None):
    console.print("=================================================")
    console.print("Uncategorized transactions :")
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
        console.print(utils._format_row(row))
    console.print()
    console.print(f"({len(uncategorized)} rows total - {len(labels)} unique labels) - {total:.2f} €")
    console.print()
    console.print("Regularily occuring labels (ignoring < 3) :")
    for label in sorted([k for k in labels], key=lambda x : -labels[x]["nbr"]):
        if labels[label]["nbr"] > 2:
            console.print(f"  - {label} (x{labels[label]["nbr"]})")
    console.print()
    console.print("Most expensive occuring labels (ignoring < 100 €) :")
    for label in sorted([k for k in labels], key=lambda x : -labels[x]["amount"]):
        if labels[label]["amount"] > 100:
            console.print(f"  - {label} ({labels[label]["amount"]:.2f} € on {labels[label]["nbr"]} transaction(s))")
    console.print("=================================================")
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
    console.print(f"{updated} rows updated.")

def show_categories(ctx, args=None):
    for category in classifier.CATEGORIES:
        console.print(f"[{category['id']}] {category['name']} ======================")
        for subcategory in category['subcategories']:
            console.print(f"  - [{subcategory['id']:>3}] {subcategory['name']}")

def show_all(ctx, args=None):
    rows = ctx.db.query(f"SELECT * FROM transactions")
    _show_analytics(rows, args=args)
    return rows

def show_where_custom_query(ctx, args):
    query, = args
    query = re.compile(r"(\d{1,2})-(\d{1,2})-(\d{4})").sub(r"'\3-\2-\1'", query)
    rows = ctx.db.query(f"SELECT * FROM transactions WHERE {query}")
    _show_analytics(rows, args=args)
    return rows

def _print_categorized(db_rows, which):
    if which == "expenses":
        total, amount_by_category, amount_by_subcategory = classifier.categorize_expenses(db_rows)
        title = "TOTAL EXPENSES"
    elif which == "revenues":
        total, amount_by_category, amount_by_subcategory = classifier.categorize_revenues(db_rows)
        title = "TOTAL REVENUES"
    else:
        return
    categorized_transactions = {**amount_by_category, **amount_by_subcategory}
    console.print(f"[bold #00FF00]{title + ' ':#<65} {total:>8.2f} €[/]")
    # Print inline and as bar plot
    Nbars = 100 # width (in characters) of bar plot
    cat_repartition_text = ""
    subcat_repartition_text = ""
    subcat_repartition_text_nosymbol = ""
    for category_id in amount_by_category:
        category, _ = classifier.get_category_properties(category_id*100 + 1)
        subtotal = amount_by_category[category_id]
        percentage = 100*subtotal/total
        legend = f"[#ffffff on {category['color']}]     [/] "
        console.print(f"{legend} [#ffffff]{category['name'] + ' ':=<55} [bold]{subtotal:>8.2f} €[/bold] [i]({percentage:>5.2f}%)[/]")
        for subcategory_id in amount_by_subcategory:
            if (subcategory_id // 100) == category_id :
                _, subcategory = classifier.get_category_properties(subcategory_id)
                subtotal = amount_by_subcategory[subcategory_id]
                percentage = 100*subtotal/total
                color = subcategory["color"] if "color" in subcategory else colors.randomize_hex_color(category['color'])
                symbol = subcategory["name"][0].lower()
                legend = f"  [#ffffff on {color}] {symbol} [/] "
                console.print(f"{legend }   - {subcategory['name'] + ' ':-<30} {subtotal:>8.2f} € [i]({percentage:>5.2f}%)[/i]")
                cat_repartition_text    += f"[#ffffff on {category['color']}]" + (" ".center(round((percentage/100) * Nbars))) + "[/]"
                subcat_repartition_text += f"[#ffffff on {color}]"             + (symbol.center(round((percentage/100) * Nbars))) + "[/]"
                subcat_repartition_text_nosymbol += f"[#ffffff on {color}]"    + (" ".center(round((percentage/100) * Nbars))) + "[/]"
    console.print()
    console.print("-"*Nbars)
    console.print(cat_repartition_text)
    console.print(cat_repartition_text)
    console.print(subcat_repartition_text)
    console.print("-"*Nbars)

def print_categorized_expenses(db_rows):
    _print_categorized(db_rows, which="expenses")

def print_categorized_revenues(db_rows):
    _print_categorized(db_rows, which="revenues")

def show_date_between(ctx, args):
    date0, date1 = args
    date0 = "-".join(date0.split("-")[::-1])
    date1 = "-".join(date1.split("-")[::-1])
    rows = ctx.db.query(f"SELECT * FROM transactions WHERE date >= '{date0}' AND date <= '{date1}'")
    rows = [row for row in rows if not row[1].startswith("?")] # Exclude undefined dates
    _show_analytics(rows, args=args)
    return rows

def show_date_before(ctx, args):
    date0, = args
    date0 = "-".join(date0.split("-")[::-1])
    rows = ctx.db.query(f"SELECT * FROM transactions WHERE date <= '{date0}'")
    rows = [row for row in rows if not row[1].startswith("?")] # Exclude undefined dates
    _show_analytics(rows, args=args)
    return rows

def show_date_after(ctx, args):
    date0, = args
    date0 = "-".join(date0.split("-")[::-1])
    rows = ctx.db.query(f"SELECT * FROM transactions WHERE date >= '{date0}'")
    rows = [row for row in rows if not row[1].startswith("?")] # Exclude undefined dates
    _show_analytics(rows, args=args)
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
    console.print(f"+-------------------------------------------------")
    console.print(f"| Entry {entry_id} :")
    console.print(f"|   - label : {transaction.label}")
    console.print(f"|   - date  : {transaction.date}")
    console.print(f"|   - amount : {transaction.amount} €")
    console.print(f"|   - category : {transaction.category}")
    console.print(f"|   - subcategory : {transaction.subcategory}")
    console.print(f"|   - ignore : {transaction.ignore}")
    console.print(f"+-------------------------------------------------")

def edit_entry_by_id(ctx, args):
    entry_id, = args
    transaction = DbTransaction(ctx.db.get_by_id(entry_id))
    show_entry_by_id(ctx, args)
    console.print(f"| Leave fields blank to leave unchanged.")
    console.print( "| New label : ")           ; updated_label       = utils.input_text("| > ").strip()
    console.print( "| New date : ")            ; updated_date        = utils.input_text("| > ").strip()
    console.print( "| New amount : ")          ; updated_amount      = utils.input_float("| > ", retry_message="| Must input integer.")
    console.print( "| New category idx : ")    ; updated_category    = utils.input_int("| > ", retry_message="| Must input integer.")
    console.print( "| New subcategory idx : ") ; updated_subcategory = utils.input_int("| > ", retry_message="| Must input integer.")
    console.print( "| New ignore flag : ")     ; updated_ignore      = utils.input_int("| > ", retry_message="| Must input integer.")
    console.print(f"+-------------------------------------------------")

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

    console.print("| Edited :")
    console.print("| " + utils._format_row(ctx.db.get_by_id(entry_id)))
    console.print(f"+-------------------------------------------------")

def edit_buffered_entries(ctx, args=None):
    show_buffered(ctx)
    console.print(f"| Leave fields blank to leave unchanged.")
    console.print( "| New label : ")           ; updated_label       = utils.input_text("| > ").strip()
    console.print( "| New date : ")            ; updated_date        = utils.input_text("| > ").strip()
    console.print( "| New amount : ")          ; updated_amount      = utils.input_float("| > ", retry_message="| Must input integer.")
    console.print( "| New category idx : ")    ; updated_category    = utils.input_int("| > ", retry_message="| Must input integer.")
    console.print( "| New subcategory idx : ") ; updated_subcategory = utils.input_int("| > ", retry_message="| Must input integer.")
    console.print( "| New ignore flag : ")     ; updated_ignore      = utils.input_int("| > ", retry_message="| Must input integer.")
    console.print(f"+-------------------------------------------------")
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
    console.print(f"+-------------------------------------------------")
    console.print(f"| Searching pattern '{text}'")
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
    console.print(f"| {len(matches)} found :")
    for match in matches:
        console.print("|   " + utils._format_row(match))
    console.print(f"+-------------------------------------------------")
    return matches
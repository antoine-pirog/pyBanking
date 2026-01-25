import PyPDF2 as pdf
import re
import glob
import argparse
import json

import parser_LBP as statement_parser
import classifier
from database import Database
from common import DbTransaction

from secrets import secrets

if __name__ == "__main__":
    import argparse
    import glob
    import re

    parser = argparse.ArgumentParser(description='Manage and monitor finances and expenses.')
    parser.add_argument('-f', '--files', type=str  , help='Input statement files (pdf)')
    parser.add_argument('-i', '--interactive', action='store_true')
    parser.add_argument('--update-uncategorized', action='store_true')
    parser.add_argument('--show-uncategorized', action='store_true')
    parser.add_argument('--rebuild-database', action='store_true')
    args = parser.parse_args()

    """ Load configuration """
    configuration = json.load(open('config.json'))
    bank_statements_directory = configuration.get("bank_statements_directory", "./pdfs")

    if args.rebuild_database:
        import os
        os.remove("database.db")
    db = Database()

    if args.files:
        statement_files = glob.glob(args.files) 
        """ Populate database """
        for i,f in enumerate(statement_files):
            print(f"Processing statement {i+1}/{len(statement_files)} ...")
            text = statement_parser.load_pdf_statement(f)
            detail = statement_parser.parse_detailed_listing(text)
            main_ops = statement_parser.parse_main_operations(text)

            transactions = []
            transactions.extend(detail)
            transactions.extend(main_ops)

            for transaction in transactions:
                category, subcategory = classifier.classify(transaction.label)
                dbtransaction = DbTransaction((
                    None, # id is auto-incremented
                    transaction.date, 
                    transaction.label, 
                    transaction.amount,
                    category["id"],
                    subcategory["id"],
                    subcategory["ignore"]
                ))
                db.insert(dbtransaction)
    
    if args.update_uncategorized:
        update_uncategorized(db)

    if args.show_uncategorized:
        show_uncategorized(db)
    
    if args.interactive:
        from cli import CLI
        CLI_handle = CLI()
        CLI_handle.link_db(db)
        CLI_handle.cmdloop()

        

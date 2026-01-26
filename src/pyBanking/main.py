import re
import glob
import argparse
import json

from pyBanking.parsing import parser_LBP as statement_parser
from pyBanking.classification import classifier
from pyBanking.database.interface import Database
from pyBanking.utils.common import DbTransaction
from pyBanking.cli.interface import CLI
from pyBanking.cli.functions import update_uncategorized, show_uncategorized
from pyBanking.context import AppContext

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Manage and monitor finances and expenses.')
    parser.add_argument('-f', '--files', type=str  , help='Input statement files (pdf)')
    parser.add_argument('-i', '--interactive', action='store_true')
    parser.add_argument('--update-uncategorized', action='store_true')
    parser.add_argument('--show-uncategorized', action='store_true')
    parser.add_argument('--rebuild-database', action='store_true')
    args = parser.parse_args()

    if args.rebuild_database:
        import os
        os.remove("database.db")
    db = Database()
    ctx = AppContext(db)

    if args.files:
        statement_files = glob.glob(args.files) 
        """ Populate database """
        for i,f in enumerate(statement_files):
            print(f"Processing statement {i+1}/{len(statement_files)} ...")
            transactions = statement_parser.extract_transactions(f)
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
        cupdate_uncategorized(db)

    if args.show_uncategorized:
        cshow_uncategorized(db)
    
    if args.interactive:
        CLI(ctx).cmdloop()

        

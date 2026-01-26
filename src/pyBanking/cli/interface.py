import cmd
import re
import random

from pyBanking.classification import classifier
from pyBanking.utils.common import DbTransaction
from pyBanking.cli.funnies import messages
from pyBanking.cli import functions

intro_message = ""
intro_message += f"================================================\n"
intro_message += f"= pyBanking - {random.choice(messages)}\n"
intro_message += f"= Type help for commands.\n"
intro_message += f"================================================\n"

def cmd_lookup(ctx, command):
    regexes = {
        r"show all" : functions.show_all,
        r"show where +(.+)" : functions.show_where_custom_query,
        r"show categories" : functions.show_categories,
        r"show uncategorized" : functions.show_uncategorized,
        r"show date +between +(\d{1,2}-\d{1,2}-\d{4}):(\d{1,2}-\d{1,2}-\d{4})" : functions.show_date_between,
        r"show date +before +(\d{1,2}-\d{1,2}-\d{4})" : functions.show_date_before,
        r"show date +after +(\d{1,2}-\d{1,2}-\d{4})" : functions.show_date_after,
        r"show month +(\d{1,2}-\d{4})" : functions.show_month,
        r"show month +(\d{4}-\d{1,2})" : functions.show_month,
        r"show year +(\d{4})" : functions.show_year,
        r"show buffered" : functions.show_buffered,
        r"show (\d+)" : functions.show_entry_by_id,
        r"edit buffered" : functions.edit_buffered_entries,
        r"edit (\d+)" : functions.edit_entry_by_id,
        r"search (.+)" : functions.search_text,
        r"sql (.+)" : functions.execute_sql_request,
    }
    buffered = None
    for regex in regexes:
        match = re.compile(regex).match(command)
        if match:
            buffered = regexes[regex](ctx, match.groups())
            continue

    if buffered is not None:
        ctx.buffered = buffered

class CLI(cmd.Cmd):
    def __init__(self, context):
        global intro_message
        super().__init__(self)
        self.prompt = "> "
        self.intro = intro_message
        self.context = context

    def do_show(self, line):
        """ Shows list of expenses 
            | Supported commands :
            | - show all
            | - show uncategorized
            | - show categories
            | - show date after <dd-mm-yyyy> 
            |   > ex. : show date after 01-01-2024
            | - show date before <dd-mm-yyyy>
            |   > ex. : show date before 01-01-2024
            | - show date between <dd-mm-yyyy:dd-mm-yyyy>
            |   > ex. : show date afte between 01-01-2024:31-12-2025
            | - show month <mm-yyyy>
            | - show year <yyyy>
            | - show where <sql filter>
            |   > ex. : show where amount < -1000
            |   > columns in db are :
            |     - date (str)
            |     - label (str)
            |     - amount (float)
            |     - category (int)
            |     - subcategory (int)
            |     - ignore (int)"""
        cmd_lookup(self.context, f"show {line}")
    
    def do_edit(self, line):
        """ Edits a database entry
            | Syntax : edit <db entry id>
            | > ex. : edit 1801
        """
        cmd_lookup(self.context, f"edit {line}")

    def do_search(self, line):
        """ Searches transaction entries labels for a string
            | Syntax : search <pattern to search>
            | > ex. : search sushi bar
        """
        cmd_lookup(self.context, f"search {line}")
    
    def do_sql(self, line):
        """ Executes a SQL request on the database """
        cmd_lookup(self.context, f"sql {line}")

    def do_exit(self, line):
        """Exits the program """
        return True
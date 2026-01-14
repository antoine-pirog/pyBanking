import PyPDF2 as pdf
import re
import glob
import argparse
import json

import parser_LBP as parser
import classifier

if __name__ == "__main__":
    """ Load configuration """
    configuration = json.load(open('config.json'))

    bank_statements_directory = configuration.get("bank_statements_directory", "./pdfs")

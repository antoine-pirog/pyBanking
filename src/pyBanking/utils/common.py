from dataclasses import dataclass

@dataclass
class Transaction:
    date: str
    label: str
    amount: float

@dataclass
class Balance:
    date: str
    label: str
    amount: float

class DbTransaction:
    def __init__(self, db_row):
        id, date, label, amount, category, subcategory, ignore = db_row
        self.id = id
        self.label = label
        self.date = date
        self.amount = amount
        self.category = category
        self.subcategory = subcategory
        self.ignore = ignore
from dataclasses import dataclass

@dataclass
class Transaction:
    date: str # TODO : change to datetime
    description: str
    amount: float

@dataclass
class Balance:
    date: str # TODO : change to datetime
    label: str
    amount: float
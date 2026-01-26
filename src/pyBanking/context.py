class AppContext:
    def __init__(self, db):
        self.db = db
        self.buffered = []
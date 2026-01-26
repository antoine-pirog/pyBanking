import sqlite3

class Database:
    def __init__(self, db_path="data/database.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        
        # Initialise tables
        create_table_query = '''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                label TEXT,
                amount REAL NOT NULL,
                category INTEGER,
                subcategory INTEGER,
                ignore INTEGER DEFAULT 0
            );
            '''
        self.cursor.execute(create_table_query)
        self.commit()

    def close(self):
        if self.conn:
            self.conn.close()

    @property
    def cursor(self):
        return self.conn.cursor()

    def query(self, request, exclude_ignored=False):
        if exclude_ignored:
            request += " AND ignore = 0" if "WHERE" in request else " WHERE ignore = 0"
        print(request)
        return self.conn.execute(request).fetchall()

    def commit(self):
        self.conn.commit()

    def insert(self, transaction):
        self.cursor.execute(
            "INSERT INTO transactions (date, label, amount, category, subcategory, ignore) VALUES (?, ?, ?, ?, ?, ?)",
            (
                transaction.date.replace("/","-"), 
                transaction.label, 
                transaction.amount, 
                transaction.category, 
                transaction.subcategory, 
                transaction.ignore
            )
        )
        self.commit()
    
    def fetch_uncategorized(self):
        return self.conn.execute("SELECT * FROM transactions WHERE subcategory = 601").fetchall()

    def update_row(self, id, table, field, value):
        self.conn.execute(f"UPDATE {table} SET {field} = {value} WHERE id = {id}")
    
    def get_by_id(self, id):
        try :
            return self.conn.execute(f"SELECT * FROM transactions WHERE id = {id}").fetchall()[0]
        except IndexError:
            return None
    
    def raw_execute(self, request):
        self.conn.execute(request)

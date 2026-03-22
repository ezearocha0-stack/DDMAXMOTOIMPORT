import sqlite3
import builtins

db_path = "c:/Users/pc gaming/Desktop/Escritorio/Tareas/AntiGravity/instance/motocicletas.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

schema = {}
for table in tables:
    table_name = table[0]
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    schema[table_name] = [col[1] for col in columns]

for table, cols in schema.items():
    print(f"Table: {table}")
    for col in cols:
        print(f"  - {col}")
    print()

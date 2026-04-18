import sqlite3
import os

db_path = os.path.join(os.getcwd(), 'instance', 'motocicletas.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE productos ADD COLUMN stock INTEGER DEFAULT 0;")
    print("Column 'stock' added successfully.")
except sqlite3.OperationalError as e:
    print(f"OperationalError: {e}")

try:
    cursor.execute("UPDATE productos SET stock = 0 WHERE stock IS NULL;")
    print("Column 'stock' updated successfully.")
except sqlite3.OperationalError as e:
    print(f"OperationalError: {e}")

conn.commit()
conn.close()

import sqlite3

def inspect_db():
    conn = sqlite3.connect("Verdion/veridion.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [r[0] for r in cursor.fetchall()]
    print(f"Total tables: {len(tables)}")
    table_counts = {}
    for t in tables:
        cursor.execute(f"SELECT count(*) FROM {t};")
        cnt = cursor.fetchone()[0]
        table_counts[t] = cnt
        print(f"  {t}: {cnt} rows")
    conn.close()
    return table_counts

if __name__ == "__main__":
    inspect_db()

import sqlite3

conn = sqlite3.connect(r'c:\Users\DIVYANK BHARDWAJ\Desktop\Projects\veridion\Verdion\veridion.db')
c = conn.cursor()
tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print(f"Total tables: {len(tables)}")
print("Tables:", tables)

for t in ['cases', 'agents', 'prediction_markets', 'evidence_bounties', 'audit_records', 'source_documents', 'evidence_passages', 'canonical_decision_records']:
    if t in tables:
        cnt = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {cnt} rows")

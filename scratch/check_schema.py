import sqlite3
conn = sqlite3.connect('stock_tracker.db')
res = conn.execute("SELECT sql FROM sqlite_master WHERE name='users'").fetchone()
if res:
    print(res[0])
else:
    print("Table 'users' not found")
res = conn.execute("PRAGMA table_info(portfolios)").fetchall()
print("\nPortfolios columns:")
for col in res:
    print(col[1])
conn.close()

import sqlite3

conn = sqlite3.connect("adressen.db")
cur = conn.cursor()

cur.execute("CREATE INDEX IF NOT EXISTS idx_plz ON adressen(plz)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_ort ON adressen(ort)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_street ON adressen(street)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_latlon ON adressen(lat, lon)")

conn.commit()
conn.close()

print("Indexes created")

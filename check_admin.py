import sqlite3
conn = sqlite3.connect('instance/lost_found.db')
cursor = conn.cursor()
cursor.execute('SELECT id, username, is_admin FROM users')
for row in cursor.fetchall():
    print(row)
conn.close()

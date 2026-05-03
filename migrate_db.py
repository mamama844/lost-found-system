import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'lost_found.db')

if not os.path.exists(db_path):
    print("数据库文件不存在，请先运行应用创建数据库")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("正在检查并更新数据库结构...")

try:
    cursor.execute("SELECT is_admin FROM users LIMIT 1")
except sqlite3.OperationalError:
    print("添加 is_admin 列...")
    cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")

try:
    cursor.execute("SELECT is_active FROM users LIMIT 1")
except sqlite3.OperationalError:
    print("添加 is_active 列...")
    cursor.execute("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1")

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='forum_posts'")
if not cursor.fetchone():
    print("创建 forum_posts 表...")
    cursor.execute("""
        CREATE TABLE forum_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title VARCHAR(200) NOT NULL,
            content TEXT NOT NULL,
            category VARCHAR(50) DEFAULT '综合讨论',
            views INTEGER DEFAULT 0,
            is_pinned BOOLEAN DEFAULT 0,
            is_locked BOOLEAN DEFAULT 0,
            status VARCHAR(20) DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='forum_replies'")
if not cursor.fetchone():
    print("创建 forum_replies 表...")
    cursor.execute("""
        CREATE TABLE forum_replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            status VARCHAR(20) DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES forum_posts(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

cursor.execute("SELECT id FROM users WHERE username = 'admin'")
admin = cursor.fetchone()
if not admin:
    print("创建管理员账号...")
    from werkzeug.security import generate_password_hash
    password_hash = generate_password_hash('admin123')
    cursor.execute("""
        INSERT INTO users (username, email, password_hash, real_name, is_admin, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ('admin', 'admin@example.com', password_hash, '系统管理员', 1, 1))
    print("管理员账号创建成功:")
    print("  用户名: admin")
    print("  密码: admin123")
else:
    cursor.execute("UPDATE users SET is_admin = 1 WHERE username = 'admin'")
    print("已将 admin 设置为管理员")

conn.commit()
conn.close()

print("\n数据库更新完成！")

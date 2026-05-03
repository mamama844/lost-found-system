import os
import sys
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'lost_found.db')

print(f"数据库路径: {db_path}")

if not os.path.exists(db_path):
    print("数据库文件不存在，将创建新数据库")
else:
    print("开始数据库迁移...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"现有表: {tables}")
    
    def get_columns(table_name):
        cursor.execute(f"PRAGMA table_info({table_name})")
        return [row[1] for row in cursor.fetchall()]
    
    def add_column_if_not_exists(table, column, definition):
        cols = get_columns(table)
        if column not in cols:
            print(f"  添加 {table}.{column}")
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
                conn.commit()
            except Exception as e:
                print(f"    警告: {e}")
                conn.rollback()
    
    if 'users' in tables:
        print("\n更新users表...")
        add_column_if_not_exists('users', 'credit_score', 'INTEGER DEFAULT 100')
        add_column_if_not_exists('users', 'avatar', "VARCHAR(255) DEFAULT 'default_avatar.png'")
    
    if 'lost_items' in tables:
        print("\n更新lost_items表...")
        add_column_if_not_exists('lost_items', 'audit_status', "VARCHAR(20) DEFAULT 'approved'")
        add_column_if_not_exists('lost_items', 'audit_reason', 'VARCHAR(200)')
    
    if 'found_items' in tables:
        print("\n更新found_items表...")
        add_column_if_not_exists('found_items', 'audit_status', "VARCHAR(20) DEFAULT 'approved'")
        add_column_if_not_exists('found_items', 'audit_reason', 'VARCHAR(200)')
    
    if 'categories' in tables:
        print("\n更新categories表...")
        add_column_if_not_exists('categories', 'icon', 'VARCHAR(50)')
        add_column_if_not_exists('categories', 'sort_order', 'INTEGER DEFAULT 0')
        add_column_if_not_exists('categories', 'is_active', 'BOOLEAN DEFAULT 1')
        add_column_if_not_exists('categories', 'created_at', 'DATETIME')
    
    if 'match_records' in tables:
        print("\n更新match_records表...")
        add_column_if_not_exists('match_records', 'text_similarity', 'FLOAT DEFAULT 0.0')
        add_column_if_not_exists('match_records', 'image_similarity', 'FLOAT DEFAULT 0.0')
    
    if 'forum_posts' in tables:
        print("\n更新forum_posts表...")
        add_column_if_not_exists('forum_posts', 'like_count', 'INTEGER DEFAULT 0')
    
    print("\n创建新表...")
    
    if 'post_likes' not in tables:
        print("  创建post_likes表...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS post_likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES forum_posts (id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(post_id, user_id)
            )
        ''')
        conn.commit()
    
    if 'notifications' not in tables:
        print("  创建notifications表...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title VARCHAR(200) NOT NULL,
                content TEXT,
                notification_type VARCHAR(20) DEFAULT 'system',
                related_id INTEGER,
                is_read BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        conn.commit()
    
    if 'system_configs' not in tables:
        print("  创建system_configs表...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key VARCHAR(50) UNIQUE NOT NULL,
                config_value VARCHAR(500),
                description VARCHAR(200),
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
    
    if 'user_logs' not in tables:
        print("  创建user_logs表...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action VARCHAR(50) NOT NULL,
                detail TEXT,
                ip_address VARCHAR(50),
                user_agent VARCHAR(255),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        conn.commit()
    
    print("\n初始化系统配置...")
    default_configs = [
        ('match_threshold', '0.5', '匹配阈值'),
        ('text_weight', '0.4', '文本相似度权重'),
        ('image_weight', '0.3', '图像相似度权重'),
        ('category_weight', '0.3', '类别权重')
    ]
    
    for key, value, desc in default_configs:
        cursor.execute("SELECT id FROM system_configs WHERE config_key = ?", (key,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO system_configs (config_key, config_value, description) VALUES (?, ?, ?)",
                (key, value, desc)
            )
    conn.commit()
    
    conn.close()
    print("\n数据库迁移完成!")

print("\n" + "="*50)
print("新增功能:")
print("="*50)
print("1. 用户信用评分系统 - User.credit_score")
print("2. 物品审核流程 - LostItem/FoundItem.audit_status")
print("3. 分类管理功能 - 管理员可添加/修改/删除分类")
print("4. 匹配参数配置 - 管理员可调节阈值和权重")
print("5. 匹配记录管理 - 管理员可查看所有匹配记录")
print("6. 用户权限分配 - 管理员可设置用户为管理员")
print("7. 修改密码功能 - /change-password")
print("8. 修改个人信息功能 - /edit-profile")
print("9. 站内消息通知系统 - Notification模型")
print("10. 帖子点赞功能 - PostLike模型")
print("11. 用户操作日志 - UserLog模型")
print("="*50)

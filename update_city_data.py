import os
import random
import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'lost_found.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("开始更新测试数据为城市失物招领...")

cursor.execute("DELETE FROM forum_replies")
cursor.execute("DELETE FROM forum_posts")
cursor.execute("DELETE FROM comments")
cursor.execute("DELETE FROM reports")
cursor.execute("DELETE FROM match_records")
cursor.execute("DELETE FROM lost_items")
cursor.execute("DELETE FROM found_items")
cursor.execute("DELETE FROM users WHERE username != 'admin'")
print("已清理旧数据")

users_data = [
    ('liwei', 'liwei@example.com', '李伟', '13900001001'),
    ('wangfang', 'wangfang@example.com', '王芳', '13900001002'),
    ('zhangjie', 'zhangjie@example.com', '张杰', '13900001003'),
    ('chenxiao', 'chenxiao@example.com', '陈晓', '13900001004'),
    ('liuyang', 'liuyang@example.com', '刘洋', '13900001005'),
    ('zhaoxin', 'zhaoxin@example.com', '赵欣', '13900001006'),
    ('sunhao', 'sunhao@example.com', '孙浩', '13900001007'),
    ('zhoumei', 'zhoumei@example.com', '周梅', '13900001008'),
]

print("插入用户数据...")
user_ids = []
for username, email, real_name, phone in users_data:
    password_hash = generate_password_hash('123456')
    created_at = datetime.now() - timedelta(days=random.randint(1, 30))
    cursor.execute("""
        INSERT INTO users (username, email, password_hash, real_name, phone, is_admin, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, 0, 1, ?)
    """, (username, email, password_hash, real_name, phone, created_at))
    user_ids.append(cursor.lastrowid)
    print(f"  创建用户: {username} - {real_name}")

lost_items = [
    ('丢失黑色iPhone 15 Pro', '在地铁站丢失一部黑色iPhone 15 Pro，有透明手机壳，内有重要资料，望好心人归还！', '地铁站'),
    ('丢失棕色皮钱包', '在商场购物时不慎遗失棕色真皮钱包，内有身份证、银行卡和现金，证件名字李伟。', '购物中心'),
    ('丢失钥匙串', '丢失一串钥匙，上面有3把钥匙和一个蓝色钥匙扣，可能在公园附近丢失。', '城市公园'),
    ('丢失身份证', '丢失身份证一张，姓名王芳，可能在银行办理业务时遗失。', '银行'),
    ('丢失黑色双肩包', '在公交车上丢失黑色双肩包，内有笔记本电脑和文件，非常重要！', '公交车'),
    ('丢失近视眼镜', '丢失一副黑框近视眼镜，度数较高，可能在餐厅用餐时遗忘。', '餐厅'),
    ('丢失智能手表', '丢失华为智能手表，黑色表带，健身房锻炼时可能遗落。', '健身房'),
    ('丢失红色折叠伞', '在超市购物后丢失一把红色折叠伞，伞柄有划痕。', '超市'),
]

lost_images = [
    'uploads/lost/屏幕截图 2026-03-31 183351.png',
    'uploads/lost/屏幕截图 2026-03-31 183455.png',
    'uploads/lost/屏幕截图 2026-03-31 183537.png',
    'uploads/lost/屏幕截图 2026-03-31 183613.png',
    'uploads/lost/屏幕截图 2026-03-31 183650.png',
    'uploads/lost/屏幕截图 2026-03-31 183718.png',
    'uploads/lost/屏幕截图 2026-03-31 183743.png',
    'uploads/lost/屏幕截图 2026-03-31 183823.png',
]

print("\n插入寻物启事...")
for i, (title, description, location) in enumerate(lost_items):
    user_id = user_ids[i]
    image_path = lost_images[i]
    category_id = random.randint(1, 7)
    lost_time = datetime.now() - timedelta(days=random.randint(1, 10))
    created_at = datetime.now() - timedelta(days=random.randint(1, 20))
    contact = f"电话: 1390000100{i+1}"
    
    cursor.execute("""
        INSERT INTO lost_items (title, description, category_id, user_id, location, lost_time, image_path, status, contact_info, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'open', ?, ?)
    """, (title, description, category_id, user_id, location, lost_time, image_path, contact, created_at))
    print(f"  发布寻物: {title}")

found_items = [
    ('捡到黑色iPhone手机', '在地铁站捡到一部黑色iPhone手机，有透明手机壳，请失主联系认领。', '地铁站'),
    ('捡到棕色钱包', '在商场休息区捡到棕色钱包一个，内有证件和银行卡，请失主认领。', '购物中心'),
    ('捡到钥匙串', '在公园长椅上捡到一串钥匙，有蓝色钥匙扣，请失主联系。', '城市公园'),
    ('捡到身份证', '在银行门口捡到身份证一张，已交至服务台，请失主前往认领。', '银行'),
    ('捡到黑色双肩包', '在公交车上捡到黑色双肩包，已交至公交总站失物招领处。', '公交总站'),
    ('捡到近视眼镜', '在餐厅餐桌旁捡到黑框眼镜一副，请失主联系认领。', '餐厅'),
    ('捡到智能手表', '在健身房更衣室捡到华为智能手表，请失主联系认领。', '健身房'),
    ('捡到红色折叠伞', '在超市门口捡到红色折叠伞一把，请失主认领。', '超市'),
]

found_images = [
    'uploads/found/屏幕截图 2026-03-31 183430.png',
    'uploads/found/屏幕截图 2026-03-31 183507.png',
    'uploads/found/屏幕截图 2026-03-31 183544.png',
    'uploads/found/屏幕截图 2026-03-31 183620.png',
    'uploads/found/屏幕截图 2026-03-31 183656.png',
    'uploads/found/屏幕截图 2026-03-31 183722.png',
    'uploads/found/屏幕截图 2026-03-31 183748.png',
    'uploads/found/屏幕截图 2026-03-31 183828.png',
]

print("\n插入失物招领...")
for i, (title, description, location) in enumerate(found_items):
    user_id = user_ids[i]
    image_path = found_images[i]
    category_id = random.randint(1, 7)
    found_time = datetime.now() - timedelta(days=random.randint(1, 10))
    created_at = datetime.now() - timedelta(days=random.randint(1, 20))
    contact = f"电话: 1390000100{i+1}"
    
    cursor.execute("""
        INSERT INTO found_items (title, description, category_id, user_id, location, found_time, image_path, status, contact_info, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'open', ?, ?)
    """, (title, description, category_id, user_id, location, found_time, image_path, contact, created_at))
    print(f"  发布招领: {title}")

forum_posts = [
    ('寻物经验分享：如何在城市快速找回丢失物品', '综合讨论', '大家好，分享一下我在城市找回丢失物品的经验。首先，要及时发布寻物启事，其次要多关注失物招领信息，最后可以在社交媒体求助。希望对大家有帮助！'),
    ('防骗指南：警惕冒领行为', '防骗指南', '最近发现有冒领现象，大家在认领物品时一定要核实对方身份，最好能提供物品的详细特征证明是自己的。'),
    ('感谢信：感谢拾金不昧的好心人', '感谢信', '非常感谢在地铁站捡到我钱包的好心人，钱包里的证件补办很麻烦，你的善举让我省了很多麻烦。好人有好报！'),
    ('关于公共场所安全的一些建议', '综合讨论', '建议在地铁站、商场等公共场所增加失物招领服务点，同时大家也要提高安全意识，贵重物品不要离身。'),
    ('寻物经验：丢失身份证怎么办', '寻物经验', '身份证丢失后，第一时间去派出所挂失，然后关注失物招领信息。一般证件都会被好心人交到派出所或服务台。'),
    ('防骗提醒：不要轻信代找服务', '防骗指南', '有人声称可以帮忙找回物品但要收费，这很可能是骗局。官方的失物招领服务是免费的，请大家注意。'),
    ('感谢帮我找回手机的好心人', '感谢信', '在公交车上丢失手机后，以为找不回来了，没想到有好心人捡到后交到了公交总站，非常感谢！'),
    ('城市失物招领系统使用体验', '综合讨论', '这个系统很好用，匹配功能很智能，希望能推广开来，让更多人受益。'),
]

print("\n插入论坛帖子...")
for i, (title, category, content) in enumerate(forum_posts):
    user_id = user_ids[i % len(user_ids)]
    created_at = datetime.now() - timedelta(days=random.randint(1, 20))
    views = random.randint(10, 200)
    
    cursor.execute("""
        INSERT INTO forum_posts (user_id, title, content, category, views, is_pinned, is_locked, status, created_at)
        VALUES (?, ?, ?, ?, ?, 0, 0, 'active', ?)
    """, (user_id, title, content, category, views, created_at))
    post_id = cursor.lastrowid
    
    reply_count = random.randint(1, 5)
    for j in range(reply_count):
        reply_user_id = user_ids[random.randint(0, len(user_ids) - 1)]
        reply_content = random.choice([
            '感谢分享，很有帮助！',
            '学习了，谢谢楼主！',
            '支持一下，希望更多人看到。',
            '我也遇到过类似情况。',
            '建议很好，支持！',
            '顶一个！',
        ])
        reply_created = created_at + timedelta(hours=random.randint(1, 48))
        cursor.execute("""
            INSERT INTO forum_replies (post_id, user_id, content, status, created_at)
            VALUES (?, ?, ?, 'active', ?)
        """, (post_id, reply_user_id, reply_content, reply_created))
    
    print(f"  发布帖子: {title} (回复: {reply_count})")

print("\n插入评论...")
for i in range(10):
    user_id = user_ids[i % len(user_ids)]
    item_type = 'lost' if i < 5 else 'found'
    item_id = i + 1 if item_type == 'lost' else i - 4
    content = random.choice([
        '这个我好像在哪里见过！',
        '是不是在地铁站？',
        '联系我了，谢谢！',
        '特征很像我的，已私信。',
        '希望能早日找回！',
        '已联系认领，感谢！',
    ])
    created_at = datetime.now() - timedelta(days=random.randint(1, 15))
    
    cursor.execute("""
        INSERT INTO comments (user_id, item_type, item_id, content, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, item_type, item_id, content, created_at))
    print(f"  添加评论: {content[:20]}...")

print("\n插入举报记录...")
for i in range(3):
    user_id = user_ids[i]
    item_type = 'lost' if i % 2 == 0 else 'found'
    item_id = i + 1
    reason = random.choice([
        '信息不实',
        '涉嫌诈骗',
        '联系方式无效',
    ])
    description = '测试举报内容'
    status = 'pending'
    created_at = datetime.now() - timedelta(days=random.randint(1, 10))
    
    cursor.execute("""
        INSERT INTO reports (user_id, item_type, item_id, reason, description, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, item_type, item_id, reason, description, status, created_at))
    print(f"  添加举报: {reason}")

conn.commit()
conn.close()

print("\n测试数据更新完成！")
print("=" * 50)
print("用户账号 (密码都是 123456):")
for username, _, real_name, _ in users_data:
    print(f"  {username} - {real_name}")
print("\n管理员账号:")
print("  admin - admin123")

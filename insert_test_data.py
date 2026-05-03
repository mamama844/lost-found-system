import os
import random
import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'lost_found.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("开始插入测试数据...")

users_data = [
    ('zhangsan', 'zhangsan@example.com', '张三', '13800138001'),
    ('lisi', 'lisi@example.com', '李四', '13800138002'),
    ('wangwu', 'wangwu@example.com', '王五', '13800138003'),
    ('zhaoliu', 'zhaoliu@example.com', '赵六', '13800138004'),
    ('sunqi', 'sunqi@example.com', '孙七', '13800138005'),
    ('zhouba', 'zhouba@example.com', '周八', '13800138006'),
    ('wujiu', 'wujiu@example.com', '吴九', '13800138007'),
    ('zhengshi', 'zhengshi@example.com', '郑十', '13800138008'),
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
    print(f"  创建用户: {username}")

lost_titles = [
    '丢失黑色iPhone 14 Pro',
    '丢失校园卡（张三）',
    '丢失蓝色钱包',
    '丢失黑色双肩包',
    '丢失银色眼镜',
    '丢失红色雨伞',
    '丢失机械键盘',
    '丢失运动水杯',
]

lost_locations = ['图书馆一楼', '食堂', '操场', '教学楼A栋', '宿舍楼', '篮球场', '实验楼', '校门口']

found_titles = [
    '捡到黑色iPhone手机',
    '捡到学生证',
    '捡到棕色钱包',
    '捡到黑色背包',
    '捡到银框眼镜',
    '捡到红色折叠伞',
    '捡到机械键盘',
    '捡到保温杯',
]

found_locations = ['图书馆', '食堂门口', '操场跑道', '教学楼大厅', '宿舍楼下', '体育馆', '实验楼走廊', '校门口']

print("\n插入寻物启事...")
for i in range(8):
    user_id = user_ids[i]
    title = lost_titles[i]
    description = f"在{lost_locations[i]}丢失，如有拾获请联系我，必有重谢！"
    location = lost_locations[i]
    category_id = random.randint(1, 7)
    image_path = f"uploads/lost/sample_{i+1}.jpg"
    lost_time = datetime.now() - timedelta(days=random.randint(1, 10))
    created_at = datetime.now() - timedelta(days=random.randint(1, 20))
    
    cursor.execute("""
        INSERT INTO lost_items (title, description, category_id, user_id, location, lost_time, image_path, status, contact_info, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'open', ?, ?)
    """, (title, description, category_id, user_id, location, lost_time, image_path, f"电话: {random.choice(['13800138001', '13800138002', '13800138003'])}", created_at))
    print(f"  发布寻物: {title}")

print("\n插入失物招领...")
for i in range(8):
    user_id = user_ids[i]
    title = found_titles[i]
    description = f"在{found_locations[i]}捡到，请失主联系我认领。"
    location = found_locations[i]
    category_id = random.randint(1, 7)
    image_path = f"uploads/found/sample_{i+1}.jpg"
    found_time = datetime.now() - timedelta(days=random.randint(1, 10))
    created_at = datetime.now() - timedelta(days=random.randint(1, 20))
    
    cursor.execute("""
        INSERT INTO found_items (title, description, category_id, user_id, location, found_time, image_path, status, contact_info, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'open', ?, ?)
    """, (title, description, category_id, user_id, location, found_time, image_path, f"电话: {random.choice(['13800138001', '13800138002', '13800138003'])}", created_at))
    print(f"  发布招领: {title}")

forum_posts = [
    ('寻物经验分享：如何在校园快速找回丢失物品', '综合讨论', '大家好，今天分享一下我在校园找回丢失物品的经验。首先，要及时发布寻物启事，其次要多关注失物招领信息，最后可以加入校园群求助。希望对大家有帮助！'),
    ('防骗指南：警惕冒领行为', '防骗指南', '最近发现有冒领现象，大家在认领物品时一定要核实对方身份，最好能提供物品的详细特征证明是自己的。'),
    ('感谢信：感谢拾金不昧的同学', '感谢信', '非常感谢在图书馆捡到我钱包的同学，钱包里的证件补办很麻烦，你的善举让我省了很多麻烦。好人有好报！'),
    ('关于校园安全的一些建议', '综合讨论', '建议学校在公共场所增加监控设备，同时大家也要提高安全意识，贵重物品不要离身。'),
    ('寻物经验：丢失校园卡怎么办', '寻物经验', '校园卡丢失后，第一时间去卡务中心挂失，然后关注失物招领信息。一般校园卡都会被好心人交到卡务中心。'),
    ('防骗提醒：不要轻信代找服务', '防骗指南', '有人声称可以帮忙找回物品但要收费，这很可能是骗局。官方的失物招领服务是免费的，请大家注意。'),
    ('感谢帮我找回手机的同学', '感谢信', '在操场丢失手机后，以为找不回来了，没想到有好心同学捡到后交到了保卫处，非常感谢！'),
    ('校园失物招领系统使用体验', '综合讨论', '这个系统很好用，匹配功能很智能，希望能推广开来，让更多人受益。'),
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
        '是不是在图书馆？',
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

print("\n测试数据插入完成！")
print("=" * 50)
print("用户账号 (密码都是 123456):")
for username, _, real_name, _ in users_data:
    print(f"  {username} - {real_name}")
print("\n管理员账号:")
print("  admin - admin123")

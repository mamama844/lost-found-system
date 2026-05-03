from app import create_app, db
from app.models.models import User, Category, ForumBoard, SystemConfig, LostItem, FoundItem, MatchRecord, ForumPost, ForumReply, Notification, CreditRecord
from datetime import datetime, timedelta
import random

app = create_app()
with app.app_context():
    db.drop_all()
    db.create_all()
    
    print("正在创建测试数据...")
    
    admin = User(username='admin', email='admin@example.com', phone='13800000000', is_admin=True, is_active=True, credit_score=100, is_verified=True)
    admin.set_password('admin123')
    db.session.add(admin)
    
    users = []
    for i in range(1, 6):
        user = User(
            username=f'user{i}',
            email=f'user{i}@example.com',
            phone=f'1380000000{i}',
            real_name=f'测试用户{i}',
            credit_score=random.randint(60, 100),
            is_verified=True
        )
        user.set_password('123456')
        users.append(user)
        db.session.add(user)
    
    db.session.commit()
    print(f"已创建 {len(users)+1} 个用户")
    
    categories = [
        Category(name='电子产品', description='手机、电脑、平板等电子设备', icon='bi-phone', sort_order=1),
        Category(name='证件卡片', description='身份证、银行卡、学生证等', icon='bi-credit-card', sort_order=2),
        Category(name='钥匙', description='各类钥匙', icon='bi-key', sort_order=3),
        Category(name='包包钱包', description='背包、钱包、手提包等', icon='bi-bag', sort_order=4),
        Category(name='饰品配件', description='手表、项链、眼镜等', icon='bi-gem', sort_order=5),
        Category(name='书籍文具', description='书本、笔记本、文具等', icon='bi-book', sort_order=6),
        Category(name='衣物鞋帽', description='衣服、鞋子、帽子等', icon='bi-bag-check', sort_order=7),
        Category(name='其他物品', description='其他未分类物品', icon='bi-box', sort_order=99),
    ]
    for cat in categories:
        db.session.add(cat)
    db.session.commit()
    print(f"已创建 {len(categories)} 个分类")
    
    boards = [
        ForumBoard(name='综合讨论', description='失物招领相关话题讨论', icon='bi-chat', sort_order=1),
        ForumBoard(name='寻物经验', description='分享寻找失物的经验和技巧', icon='bi-lightbulb', sort_order=2),
        ForumBoard(name='防骗指南', description='防骗知识和案例分享', icon='bi-shield-check', sort_order=3),
        ForumBoard(name='感谢信', description='感谢帮助找回物品的好心人', icon='bi-heart', sort_order=4),
    ]
    for board in boards:
        db.session.add(board)
    db.session.commit()
    print(f"已创建 {len(boards)} 个论坛板块")
    
    configs = [
        SystemConfig(config_key='match_threshold', config_value='0.5', description='匹配阈值'),
        SystemConfig(config_key='text_weight', config_value='0.4', description='文本权重'),
        SystemConfig(config_key='image_weight', config_value='0.3', description='图片权重'),
        SystemConfig(config_key='category_weight', config_value='0.3', description='分类权重'),
        SystemConfig(config_key='mail_enabled', config_value='false', description='是否启用邮件通知'),
        SystemConfig(config_key='sms_enabled', config_value='false', description='是否启用短信通知'),
    ]
    for config in configs:
        db.session.add(config)
    db.session.commit()
    
    lost_items = [
        LostItem(title='iPhone 14 Pro 黑色', description='在图书馆三楼丢失，黑色iPhone 14 Pro，有透明手机壳', category_id=1, user_id=2, location='图书馆三楼', lost_time=datetime.now() - timedelta(days=2), contact_info='13800000001', audit_status='approved', status='open'),
        LostItem(title='身份证 张三', description='丢失身份证，姓名张三', category_id=2, user_id=3, location='食堂', lost_time=datetime.now() - timedelta(days=1), contact_info='13800000002', audit_status='approved', status='open'),
        LostItem(title='宿舍钥匙', description='一串钥匙，有一个蓝色钥匙扣', category_id=3, user_id=4, location='宿舍楼下', lost_time=datetime.now() - timedelta(hours=5), contact_info='13800000003', audit_status='approved', status='open'),
        LostItem(title='黑色双肩包', description='耐克黑色双肩包，内有笔记本', category_id=4, user_id=5, location='操场', lost_time=datetime.now() - timedelta(hours=12), contact_info='13800000004', audit_status='pending', status='open'),
        LostItem(title='银色眼镜', description='近视眼镜，银色金属框架', category_id=5, user_id=2, location='教学楼A201', lost_time=datetime.now() - timedelta(days=3), contact_info='13800000001', audit_status='approved', status='closed'),
    ]
    for item in lost_items:
        db.session.add(item)
    db.session.commit()
    print(f"已创建 {len(lost_items)} 条丢失物品记录")
    
    found_items = [
        FoundItem(title='iPhone 14 Pro 黑色', description='在图书馆三楼捡到黑色iPhone，透明手机壳', category_id=1, user_id=3, location='图书馆三楼', found_time=datetime.now() - timedelta(days=2), contact_info='13800000002', audit_status='approved', status='open'),
        FoundItem(title='身份证', description='捡到一张身份证', category_id=2, user_id=4, location='食堂门口', found_time=datetime.now() - timedelta(days=1), contact_info='13800000003', audit_status='approved', status='open'),
        FoundItem(title='钥匙串', description='捡到一串钥匙，蓝色钥匙扣', category_id=3, user_id=5, location='宿舍楼下', found_time=datetime.now() - timedelta(hours=4), contact_info='13800000004', audit_status='approved', status='open'),
        FoundItem(title='银色框架眼镜', description='捡到一副近视眼镜', category_id=5, user_id=2, location='教学楼', found_time=datetime.now() - timedelta(days=3), contact_info='13800000001', audit_status='approved', status='closed'),
    ]
    for item in found_items:
        db.session.add(item)
    db.session.commit()
    print(f"已创建 {len(found_items)} 条拾获物品记录")
    
    matches = [
        MatchRecord(lost_item_id=1, found_item_id=1, similarity_score=0.85, text_similarity=0.90, image_similarity=0.80, status='pending', lost_confirmed=False, found_confirmed=False, expires_at=datetime.now() + timedelta(hours=72)),
        MatchRecord(lost_item_id=2, found_item_id=2, similarity_score=0.75, text_similarity=0.70, image_similarity=0.80, status='pending', lost_confirmed=True, found_confirmed=False, expires_at=datetime.now() + timedelta(hours=72)),
        MatchRecord(lost_item_id=3, found_item_id=3, similarity_score=0.65, text_similarity=0.60, image_similarity=0.70, status='pending', lost_confirmed=False, found_confirmed=False, expires_at=datetime.now() + timedelta(hours=72)),
        MatchRecord(lost_item_id=5, found_item_id=4, similarity_score=0.90, text_similarity=0.85, image_similarity=0.95, status='confirmed', lost_confirmed=True, found_confirmed=True),
    ]
    for match in matches:
        db.session.add(match)
    db.session.commit()
    print(f"已创建 {len(matches)} 条匹配记录")
    
    posts = [
        ForumPost(user_id=2, title='分享：如何在校园内找回丢失物品', content='大家好，今天分享一下我找回丢失手机的经验...\n\n1. 第一时间到失物招领处登记\n2. 在校园论坛发布寻物启事\n3. 联系保卫处调取监控\n\n希望对大家有帮助！', category='寻物经验', board_id=2, audit_status='approved', status='active', views=156, like_count=12, collect_count=5),
        ForumPost(user_id=3, title='防骗提醒：冒充失物招领的诈骗', content='最近有不法分子冒充失物招领工作人员进行诈骗，请大家注意防范！\n\n1. 正规失物招领不会索要验证码\n2. 不会要求转账\n3. 遇到可疑情况及时报警', category='防骗指南', board_id=3, audit_status='approved', status='active', views=89, like_count=8, collect_count=3),
        ForumPost(user_id=4, title='感谢信：感谢帮我找回钱包的好心人', content='今天我的钱包不小心丢失了，里面有身份证、银行卡等重要证件。\n\n非常感谢捡到我钱包的同学，您的善举让我非常感动！', category='感谢信', board_id=4, audit_status='approved', status='active', views=67, like_count=15, collect_count=2),
        ForumPost(user_id=5, title='新手报到，请问如何使用这个系统？', content='大家好，我是新来的，请问这个系统怎么用？', category='综合讨论', board_id=1, audit_status='pending', status='active', views=23, like_count=1),
    ]
    for post in posts:
        db.session.add(post)
    db.session.commit()
    print(f"已创建 {len(posts)} 条论坛帖子")
    
    replies = [
        ForumReply(post_id=1, user_id=3, content='感谢分享！很有用的经验！', audit_status='approved', status='active'),
        ForumReply(post_id=1, user_id=4, content='学习了，以后丢东西知道怎么做了', audit_status='approved', status='active'),
        ForumReply(post_id=2, user_id=2, content='感谢提醒！大家一定要注意安全', audit_status='approved', status='active'),
        ForumReply(post_id=3, user_id=2, content='好人一生平安！', audit_status='approved', status='active'),
    ]
    for reply in replies:
        db.session.add(reply)
    db.session.commit()
    print(f"已创建 {len(replies)} 条回复")
    
    notifications = [
        Notification(user_id=2, title='物品审核通过', content='您发布的物品"iPhone 14 Pro 黑色"已通过审核', notification_type='audit', is_read=False),
        Notification(user_id=3, title='新的匹配结果', content='您拾获的物品"iPhone 14 Pro 黑色"找到了可能的失主', notification_type='match', is_read=False),
        Notification(user_id=4, title='帖子有新回复', content='有人回复了您的帖子"感谢信：感谢帮我找回钱包的好心人"', notification_type='reply', is_read=True),
    ]
    for notif in notifications:
        db.session.add(notif)
    db.session.commit()
    print(f"已创建 {len(notifications)} 条通知")
    
    credit_records = [
        CreditRecord(user_id=2, change=5, reason='成功找回物品奖励', old_score=95, new_score=100),
        CreditRecord(user_id=3, change=3, reason='发布有效拾获信息', old_score=87, new_score=90),
    ]
    for record in credit_records:
        db.session.add(record)
    db.session.commit()
    print(f"已创建 {len(credit_records)} 条信用记录")
    
    print("\n" + "="*50)
    print("测试数据创建完成！")
    print("="*50)
    print("\n账号信息：")
    print("管理员: admin / admin123")
    print("测试用户: user1~user5 / 123456")
    print("\n启动命令: python run.py")

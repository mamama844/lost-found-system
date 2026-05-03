import os
import sys
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.models import User, LostItem, FoundItem, Category, MatchRecord, ForumPost, ForumReply, PostLike, Notification, Comment

app = create_app()

with app.app_context():
    print("开始添加测试数据...")
    
    # 创建普通用户
    users_data = [
        ('zhangsan', 'zhangsan@qq.com', '张三', '13800138001'),
        ('lisi', 'lisi@qq.com', '李四', '13800138002'),
        ('wangwu', 'wangwu@qq.com', '王五', '13800138003'),
        ('zhaoliu', 'zhaoliu@qq.com', '赵六', '13800138004'),
        ('sunqi', 'sunqi@qq.com', '孙七', '13800138005'),
        ('zhouba', 'zhouba@qq.com', '周八', '13800138006'),
        ('wujiu', 'wujiu@qq.com', '吴九', '13800138007'),
        ('zhengshi', 'zhengshi@qq.com', '郑十', '13800138008'),
    ]
    
    users = []
    for username, email, real_name, phone in users_data:
        if not User.query.filter_by(username=username).first():
            user = User(
                username=username,
                email=email,
                real_name=real_name,
                phone=phone,
                credit_score=random.randint(60, 100)
            )
            user.set_password('123456')
            db.session.add(user)
            users.append(user)
    
    db.session.commit()
    print(f"已创建 {len(users)} 个普通用户")
    
    all_users = User.query.filter(User.username != 'admin').all()
    categories = Category.query.all()
    
    # 丢失物品数据
    lost_items_data = [
        ('黑色iPhone 15手机', '在地铁站丢失一部黑色iPhone 15，有透明手机壳，屏幕左上角有小划痕', '电子产品', '地铁2号线人民广场站', '13800138001'),
        ('棕色钱包', '丢失棕色真皮钱包，内有身份证、银行卡若干', '生活用品', '市中心商场', '13800138002'),
        ('学生证', '丢失XX大学学生证，姓名张三', '证件卡片', '图书馆', '13800138003'),
        ('黑色双肩包', '丢失黑色耐克双肩包，内有笔记本电脑', '生活用品', '公交站台', '13800138004'),
        ('AirPods耳机', '丢失白色AirPods Pro耳机，耳机盒有贴纸', '电子产品', '咖啡店', '13800138005'),
        ('银色手表', '丢失卡西欧银色电子表', '生活用品', '健身房', '13800138006'),
        ('蓝色雨伞', '丢失蓝色折叠雨伞', '生活用品', '超市门口', '13800138007'),
        ('黑色眼镜', '丢失黑色框眼镜，度数300度', '生活用品', '餐厅', '13800138008'),
    ]
    
    lost_items = []
    for title, desc, cat_name, location, contact in lost_items_data:
        cat = next((c for c in categories if c.name == cat_name), categories[-1])
        user = random.choice(all_users)
        item = LostItem(
            title=title,
            description=desc,
            category_id=cat.id,
            user_id=user.id,
            location=location,
            contact_info=contact,
            lost_time=datetime.now() - timedelta(days=random.randint(1, 7)),
            status='open',
            audit_status='approved'
        )
        db.session.add(item)
        lost_items.append(item)
    
    db.session.commit()
    print(f"已创建 {len(lost_items)} 条丢失物品")
    
    # 拾获物品数据
    found_items_data = [
        ('黑色苹果手机', '在地铁站拾获一部黑色苹果手机，有透明壳', '电子产品', '地铁2号线', '13900139001'),
        ('棕色皮钱包', '拾获棕色真皮钱包，请失主联系认领', '生活用品', '市中心商场', '13900139002'),
        ('学生证', '拾获学生证一张', '证件卡片', '图书馆门口', '13900139003'),
        ('黑色背包', '拾获黑色双肩包一个', '生活用品', '公交车上', '13900139004'),
        ('白色无线耳机', '拾获白色无线耳机', '电子产品', '咖啡店', '13900139005'),
        ('银色电子表', '拾获银色手表一块', '生活用品', '健身房', '13900139006'),
        ('蓝色折叠伞', '拾获蓝色雨伞一把', '生活用品', '超市', '13900139007'),
        ('黑色眼镜', '拾获黑色框眼镜一副', '生活用品', '餐厅', '13900139008'),
    ]
    
    found_items = []
    for title, desc, cat_name, location, contact in found_items_data:
        cat = next((c for c in categories if c.name == cat_name), categories[-1])
        user = random.choice(all_users)
        item = FoundItem(
            title=title,
            description=desc,
            category_id=cat.id,
            user_id=user.id,
            location=location,
            contact_info=contact,
            found_time=datetime.now() - timedelta(days=random.randint(1, 7)),
            status='open',
            audit_status='approved'
        )
        db.session.add(item)
        found_items.append(item)
    
    db.session.commit()
    print(f"已创建 {len(found_items)} 条拾获物品")
    
    # 创建匹配记录
    for i, (lost, found) in enumerate(zip(lost_items[:5], found_items[:5])):
        match = MatchRecord(
            lost_item_id=lost.id,
            found_item_id=found.id,
            similarity_score=random.uniform(0.5, 0.95),
            text_similarity=random.uniform(0.4, 0.9),
            image_similarity=random.uniform(0.3, 0.85),
            status=random.choice(['pending', 'confirmed', 'rejected'])
        )
        db.session.add(match)
    
    db.session.commit()
    print("已创建匹配记录")
    
    # 创建论坛帖子
    posts_data = [
        ('分享：我在地铁丢了手机，3天后找回了！', '上周我在地铁上丢了手机，通过这个平台发布信息后，第二天就有人联系我了，真的很感谢！', '感谢信'),
        ('寻物经验分享', '丢失物品后第一时间要做什么？我来分享一下我的经验...', '寻物经验'),
        ('防骗提醒：认领时注意核实身份', '最近有不法分子冒领失物，大家一定要注意核实对方身份...', '防骗指南'),
        ('这个平台真的很有用！', '今天成功找回了我丢失的钱包，感谢平台和拾金不昧的好心人！', '感谢信'),
        ('求助：丢失重要证件怎么办？', '身份证丢了，补办流程是什么？有经验的朋友分享一下...', '综合讨论'),
    ]
    
    for title, content, category in posts_data:
        user = random.choice(all_users)
        post = ForumPost(
            user_id=user.id,
            title=title,
            content=content,
            category=category,
            views=random.randint(50, 500),
            like_count=random.randint(0, 20)
        )
        db.session.add(post)
    
    db.session.commit()
    print("已创建论坛帖子")
    
    # 创建通知
    for user in all_users[:5]:
        notification = Notification(
            user_id=user.id,
            title='系统通知',
            content='欢迎使用城市失物招领系统！发布失物信息后，系统会自动为您匹配。',
            notification_type='system'
        )
        db.session.add(notification)
    
    db.session.commit()
    print("已创建通知消息")
    
    # 创建评论
    for i in range(10):
        comment = Comment(
            user_id=random.choice(all_users).id,
            item_type=random.choice(['lost', 'found']),
            item_id=random.choice(lost_items).id if random.random() > 0.5 else random.choice(found_items).id,
            content=f'这是第{i+1}条测试评论'
        )
        db.session.add(comment)
    
    db.session.commit()
    print("已创建评论")
    
    print("\n" + "="*50)
    print("测试数据添加完成！")
    print("="*50)
    print(f"用户数: {User.query.count()}")
    print(f"丢失物品: {LostItem.query.count()}")
    print(f"拾获物品: {FoundItem.query.count()}")
    print(f"匹配记录: {MatchRecord.query.count()}")
    print(f"论坛帖子: {ForumPost.query.count()}")
    print(f"通知消息: {Notification.query.count()}")
    print(f"评论数: {Comment.query.count()}")
    print("="*50)
    print("\n管理员账号: admin / admin123")
    print("普通用户密码均为: 123456")

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.models import (
    User, Category, LostItem, FoundItem, ForumBoard, ForumPost, ForumReply,
    MatchRecord, Comment, Report, Notification, SystemConfig, UserLog,
    Favorite, PostLike, PostCollection, CreditRecord, SystemBackup, SystemStats,
    ChatMessage
)
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
import random

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()
    print("数据库已重建")

    admin = User(
        username='admin', email='admin@lostfound.com', phone='13800000001',
        password_hash=generate_password_hash('admin123'),
        is_admin=True, is_active=True, is_verified=True, credit_score=100,
        real_name='系统管理员'
    )
    db.session.add(admin)

    users_data = [
        ('张三', 'zhangsan@163.com', '13900001001', '张三丰'),
        ('李四', 'lisi@163.com', '13900001002', '李思远'),
        ('王五', 'wangwu@163.com', '13900001003', '王武强'),
        ('赵六', 'zhaoliu@163.com', '13900001004', '赵柳青'),
        ('陈七', 'chenqi@163.com', '13900001005', '陈琪琪'),
        ('刘八', 'liuba@163.com', '13900001006', '刘宝山'),
        ('孙九', 'sunjiu@163.com', '13900001007', '孙久安'),
        ('周十', 'zhoushi@163.com', '13900001008', '周世杰'),
    ]
    users = [admin]
    for uname, email, phone, rname in users_data:
        u = User(
            username=uname, email=email, phone=phone,
            password_hash=generate_password_hash('123456'),
            is_admin=False, is_active=True, is_verified=True, credit_score=100,
            real_name=rname
        )
        db.session.add(u)
        users.append(u)
    db.session.commit()
    print(f"创建了 {len(users)} 个用户")

    categories_data = [
        ('电子产品', '手机、电脑、平板、耳机等电子设备', 'phone'),
        ('证件卡类', '身份证、学生证、银行卡、门禁卡等', 'card'),
        ('钥匙钱包', '钥匙、钱包、背包、手提包等', 'key'),
        ('衣物配饰', '衣服、鞋子、手表、眼镜、首饰等', 'bag'),
        ('图书文具', '书籍、笔记本、文具、U盘等', 'book'),
        ('宠物', '猫、狗等走失宠物', 'heart'),
        ('其他物品', '不属于以上分类的物品', 'box'),
    ]
    categories = []
    for name, desc, icon in categories_data:
        c = Category(name=name, description=desc, icon=icon, sort_order=len(categories), is_active=True)
        db.session.add(c)
        categories.append(c)
    db.session.commit()
    print(f"创建了 {len(categories)} 个分类")

    boards_data = [
        ('综合讨论', '失物招领相关话题讨论', 'chat'),
        ('寻物经验', '分享寻找丢失物品的经验和技巧', 'lightbulb'),
        ('感谢信', '找回失物后的感谢与分享', 'emoji-smile'),
        ('防骗提醒', '警惕各类诈骗行为，保护自身安全', 'shield-check'),
    ]
    boards = []
    for name, desc, icon in boards_data:
        b = ForumBoard(name=name, description=desc, icon=icon, sort_order=len(boards), is_active=True)
        db.session.add(b)
        boards.append(b)
    db.session.commit()
    print(f"创建了 {len(boards)} 个板块")

    now = datetime.now()

    lost_items_data = [
        ('苹果iPhone15手机丢失', '4月28日下午3点左右，在海淀区中关村大街丢失一部苹果iPhone15手机，黑色，带透明手机壳，锁屏壁纸是猫咪。内有重要照片和通讯录，非常着急！', 1, '北京市海淀区中关村大街', now - timedelta(days=4, hours=3), '13900001001'),
        ('身份证丢失', '5月1日上午在朝阳区大悦城购物时不慎丢失身份证，姓名张三丰，请拾到者联系我，万分感谢！', 2, '北京市朝阳区朝阳大悦城', now - timedelta(days=1, hours=6), '13900001001'),
        ('家门钥匙丢失', '4月30日在西城区金融街附近丢失一串钥匙，共3把，挂有红色小熊钥匙扣，非常着急回家！', 3, '北京市西城区金融街', now - timedelta(days=2), '13900001002'),
        ('黑色双肩包丢失', '5月1日在地铁1号线国贸站到四惠东方向丢失一个黑色双肩包，内有笔记本电脑和重要文件', 4, '北京市地铁1号线国贸站', now - timedelta(days=1), '13900001002'),
        ('金毛犬走失', '4月29日在丰台区丰台公园遛狗时金毛犬走失，名叫"旺财"，3岁公犬，戴红色项圈，非常温顺', 6, '北京市丰台区丰台公园', now - timedelta(days=3), '13900001003'),
        ('华为MatePad平板丢失', '5月2日上午在东城区王府井书店丢失华为MatePad平板电脑，灰色，贴有磨砂膜', 1, '北京市东城区王府井书店', now - timedelta(hours=5), '13900001003'),
        ('学生证丢失', '4月27日在北京大学校园内丢失学生证，姓名李思远，学号2023010002', 2, '北京市海淀区北京大学', now - timedelta(days=5), '13900001004'),
        ('银色手表丢失', '5月1日在朝阳区三里屯太古里丢失一块银色手表，品牌天梭，有划痕', 4, '北京市朝阳区三里屯太古里', now - timedelta(days=1, hours=2), '13900001005'),
    ]
    lost_items = []
    for title, desc, cat_id, loc, lost_time, contact in lost_items_data:
        item = LostItem(
            title=title, description=desc, category_id=cat_id,
            user_id=users[1 + (len(lost_items) % 8)].id,
            location=loc, lost_time=lost_time, contact_info=contact,
            status='open', audit_status='approved', is_deleted=False,
            view_count=len(lost_items) * 15 + 10, created_at=lost_time
        )
        db.session.add(item)
        lost_items.append(item)

    closed_lost = LostItem(
        title='已找回的蓝色钱包', description='3月15日在通州区万达广场丢失蓝色钱包，内有身份证和银行卡，已通过本平台找回！',
        category_id=3, location='北京市通州区万达广场', lost_time=now - timedelta(days=45),
        contact_info='13900001006', user_id=users[6].id,
        status='closed', audit_status='approved', is_deleted=False,
        view_count=88, created_at=now - timedelta(days=45), status_note='已通过平台匹配找回'
    )
    db.session.add(closed_lost)

    db.session.commit()
    print(f"创建了 {len(lost_items)} 条寻物启事")

    found_items_data = [
        ('捡到苹果手机一部', '4月28日下午在海淀区中关村大街捡到一部黑色苹果手机，带透明手机壳，锁屏是猫咪图片，已交到附近派出所', 1, '北京市海淀区中关村大街', now - timedelta(days=4, hours=2), '13900001004'),
        ('捡到身份证一张', '5月1日在朝阳大悦城一楼服务台附近捡到身份证，姓名张三丰', 2, '北京市朝阳区朝阳大悦城', now - timedelta(days=1, hours=5), '13900001005'),
        ('捡到一串钥匙', '4月30日在西城区金融街购物中心门口捡到一串钥匙，3把，红色小熊钥匙扣', 3, '北京市西城区金融街购物中心', now - timedelta(days=2, hours=1), '13900001006'),
        ('捡到黑色双肩包', '5月1日在地铁1号线国贸站捡到黑色双肩包，内有电脑和文件', 4, '北京市地铁1号线国贸站', now - timedelta(days=1, hours=1), '13900001007'),
        ('捡到金毛犬一只', '4月29日在丰台区丰台公园门口发现一只金毛犬，戴红色项圈，非常温顺，暂时寄养在家中', 6, '北京市丰台区丰台公园', now - timedelta(days=3, hours=1), '13900001008'),
        ('捡到银色手表', '5月1日在三里屯太古里捡到一块银色天梭手表，有轻微划痕', 4, '北京市朝阳区三里屯太古里', now - timedelta(days=1, hours=1), '13900001001'),
        ('捡到U盘一个', '5月2日在海淀区五道口地铁站捡到一个金士顿32G U盘', 5, '北京市海淀区五道口地铁站', now - timedelta(hours=3), '13900001002'),
        ('捡到银行卡一张', '4月30日在石景山区万达广场捡到工商银行卡一张', 2, '北京市石景山区万达广场', now - timedelta(days=2, hours=5), '13900001003'),
    ]
    found_items = []
    for title, desc, cat_id, loc, found_time, contact in found_items_data:
        item = FoundItem(
            title=title, description=desc, category_id=cat_id,
            user_id=users[1 + (len(found_items) % 8)].id,
            location=loc, found_time=found_time, contact_info=contact,
            status='open', audit_status='approved', is_deleted=False,
            view_count=len(found_items) * 12 + 8, created_at=found_time
        )
        db.session.add(item)
        found_items.append(item)
    db.session.commit()
    print(f"创建了 {len(found_items)} 条失物招领")

    matches_data = [
        (1, 1, 0.92, 0.88, 0.0, 'confirmed'),
        (2, 2, 0.85, 0.80, 0.0, 'confirmed'),
        (3, 3, 0.78, 0.75, 0.0, 'confirmed'),
        (4, 4, 0.72, 0.68, 0.0, 'pending'),
        (5, 5, 0.88, 0.82, 0.0, 'confirmed'),
        (8, 6, 0.65, 0.60, 0.0, 'pending'),
    ]
    for lost_id, found_id, sim, text_sim, img_sim, status in matches_data:
        m = MatchRecord(
            lost_item_id=lost_items[lost_id-1].id if lost_id <= len(lost_items) else lost_items[0].id,
            found_item_id=found_items[found_id-1].id if found_id <= len(found_items) else found_items[0].id,
            similarity_score=sim, text_similarity=text_sim, image_similarity=img_sim,
            status=status, lost_confirmed=(status=='confirmed'), found_confirmed=(status=='confirmed'),
            created_at=now - timedelta(days=random.randint(0,5))
        )
        db.session.add(m)
    db.session.commit()
    print(f"创建了 {len(matches_data)} 条匹配记录")

    posts_data = [
        ('感谢平台帮我找回了手机！', '真的太感谢这个平台了！我在中关村丢失的手机，第二天就有人发布招领信息，通过智能匹配功能我们联系上了，手机已经拿回来了！强烈推荐大家使用！', '感谢信', 3),
        ('分享：如何提高找回丢失物品的概率', '1. 第一时间发布寻物启事，描述越详细越好\n2. 选择正确的分类，方便系统匹配\n3. 提供准确的丢失时间和地点\n4. 多关注招领信息，主动联系\n5. 保持联系方式畅通', '寻物经验', 2),
        ('警惕！有人冒充拾到者进行诈骗', '最近有人通过平台私信联系失主，要求先转账才归还物品，这是诈骗！请大家在确认物品信息前不要转账，可以通过平台官方匹配功能确认身份。', '防骗提醒', 4),
        ('大家出门一定要保管好随身物品', '最近看到好多寻物启事，提醒大家出门在外一定要注意：\n1. 手机不要放在外口袋\n2. 证件和现金分开存放\n3. 随时检查随身物品\n4. 在公共场所保持警惕', '综合讨论', 1),
        ('感谢好心人送回我的钥匙！', '昨天在西城区金融街丢了钥匙，今天就有好心人联系我了！钥匙虽然不值钱，但回家真的很需要。感谢拾金不昧的好心人，也感谢这个平台！', '感谢信', 3),
        ('地铁上遗失物品怎么办？', '分享一个经验：如果在地铁上遗失物品，可以：\n1. 联系地铁客服热线\n2. 到终点站失物招领处查询\n3. 在本平台发布寻物启事\n4. 关注地铁官方微博的失物信息', '寻物经验', 2),
    ]
    import random
    posts = []
    for title, content, category, board_idx in posts_data:
        p = ForumPost(
            user_id=users[1 + random.randint(0, 7)].id,
            title=title, content=content, category=category,
            board_id=boards[board_idx-1].id if board_idx <= len(boards) else boards[0].id,
            views=random.randint(50, 300), like_count=random.randint(5, 30),
            collect_count=random.randint(2, 15),
            is_pinned=(title.startswith('警惕') or title.startswith('分享：如何')),
            is_locked=False, audit_status='approved', status='active',
            created_at=now - timedelta(days=random.randint(0, 5), hours=random.randint(0, 12))
        )
        db.session.add(p)
        posts.append(p)
    db.session.commit()
    print(f"创建了 {len(posts)} 条论坛帖子")

    for post in posts:
        for j in range(random.randint(1, 3)):
            reply = ForumReply(
                post_id=post.id,
                user_id=users[1 + random.randint(0, 7)].id,
                content=['说得好！', '感谢分享！', '我也遇到过类似的情况', '非常有用的信息，收藏了', '希望更多人看到', '太感谢了！'][random.randint(0, 5)],
                audit_status='approved', status='active',
                created_at=post.created_at + timedelta(hours=random.randint(1, 24))
            )
            db.session.add(reply)
    db.session.commit()
    print("创建了论坛回复")

    for item in lost_items[:4]:
        c = Comment(
            user_id=users[1 + random.randint(0, 7)].id,
            item_type='lost', item_id=item.id,
            content=['帮你顶一下，希望能尽快找回！', '我也在那个地方丢过东西', '建议去附近派出所问问', '关注了，有消息通知你'][random.randint(0, 3)],
            audit_status='approved', is_deleted=False,
            created_at=item.created_at + timedelta(hours=random.randint(1, 12))
        )
        db.session.add(c)
    db.session.commit()
    print("创建了评论")

    r = Report(
        user_id=users[3].id, item_type='lost', item_id=lost_items[0].id,
        reason='信息不实', description='该寻物启事描述的地点和时间有矛盾，疑似虚假信息',
        status='pending', created_at=now - timedelta(hours=2)
    )
    db.session.add(r)
    db.session.commit()
    print("创建了举报记录")

    for u in users[1:4]:
        for item in random.sample(lost_items[:4], min(2, len(lost_items))):
            f = Favorite(user_id=u.id, item_type='lost', item_id=item.id, created_at=now - timedelta(hours=random.randint(1, 24)))
            db.session.add(f)
    db.session.commit()
    print("创建了收藏记录")

    for u in users[1:4]:
        n = Notification(
            user_id=u.id, title='系统通知', content='欢迎使用城市失物招领智能匹配系统！请完善您的个人信息以便更好地使用平台功能。',
            notification_type='system', is_read=False, created_at=now - timedelta(days=random.randint(0, 3))
        )
        db.session.add(n)
    n2 = Notification(
        user_id=users[1].id, title='匹配通知', content='您发布的寻物启事"苹果iPhone15手机丢失"找到了一个潜在匹配，请及时查看！',
        notification_type='match', is_read=True, created_at=now - timedelta(hours=6)
    )
    db.session.add(n2)
    db.session.commit()
    print("创建了通知")

    for u in users:
        log = UserLog(
            user_id=u.id, action='login', detail='用户登录系统',
            ip_address=f'192.168.1.{random.randint(1, 255)}',
            created_at=now - timedelta(hours=random.randint(0, 48))
        )
        db.session.add(log)
    db.session.commit()
    print("创建了操作日志")

    configs = [
        ('site_name', '城市失物招领智能匹配系统', '站点名称'),
        ('site_description', '基于AI智能匹配的失物招领平台', '站点描述'),
        ('contact_email', 'admin@lostfound.com', '联系邮箱'),
        ('default_credit', '100', '注册默认信用分'),
        ('min_credit_publish', '30', '发布最低信用分'),
        ('max_login_attempts', '5', '登录失败锁定次数'),
        ('lock_duration', '60', '锁定时长(分钟)'),
        ('enable_register', 'true', '开放注册'),
        ('enable_auto_match', 'true', '自动匹配'),
    ]
    for key, value, desc in configs:
        c = SystemConfig(config_key=key, config_value=value, description=desc)
        db.session.add(c)
    db.session.commit()
    print("创建了系统配置")

    for i in range(7):
        d = now.date() - timedelta(days=i)
        ss = SystemStats(
            date=d,
            new_users=random.randint(2, 8),
            new_lost_items=random.randint(3, 12),
            new_found_items=random.randint(2, 10),
            new_matches=random.randint(1, 5),
            confirmed_matches=random.randint(0, 3),
            new_posts=random.randint(1, 6),
            new_replies=random.randint(2, 10),
            active_users=random.randint(5, 15),
            created_at=datetime.combine(d, datetime.min.time())
        )
        db.session.add(ss)
    db.session.commit()
    print("创建了统计数据")

    chat_data = [
        (2, 3, '你好，我在西单地铁站捡到一个黑色钱包，是你丢的吗？', 1),
        (3, 2, '是的！我的钱包就是在西单丢的，里面有什么？', 1),
        (2, 3, '里面有身份证、几张银行卡和现金，身份证名字是王五', 1),
        (3, 2, '对对对！就是我的！太感谢你了！', 1),
        (2, 3, '不客气，我们约个时间地点还给你吧', 1),
        (3, 2, '好的，你什么时候方便？我在朝阳区上班', 1),
        (2, 3, '明天中午12点在西单地铁站B口见面可以吗？', 1),
        (3, 2, '没问题，明天见！', 1),
        (4, 5, '你好，我看到你发布了一条iPhone 15的寻物启事', 2),
        (5, 4, '是的，我的手机在国贸丢了，你捡到了吗？', 2),
        (4, 5, '我在国贸商城捡到一部iPhone 15，银色的', 2),
        (5, 4, '就是我的！手机壳是透明硅胶的，背面有一张贴纸', 2),
        (4, 5, '是的，有一张贴纸！那应该就是你的了', 2),
        (5, 4, '太好了！怎么联系你取回来？', 2),
        (4, 5, '我明天在国贸附近，可以约在国贸商城一楼星巴克', 2),
        (5, 4, '好的，明天下午2点见！', 2),
        (6, 7, '你好，请问你丢的钥匙是在望京SOHO吗？', 3),
        (7, 6, '是的！三把钥匙挂在一个小熊挂件上', 3),
        (6, 7, '对的！我捡到了，在望京SOHO T1前台，你可以去取', 3),
        (7, 6, '太感谢了！我明天就去取', 3),
    ]
    for sender_id, receiver_id, content, match_id in chat_data:
        msg = ChatMessage(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            match_id=match_id,
            is_read=True,
            created_at=now - timedelta(minutes=random.randint(10, 1440))
        )
        db.session.add(msg)
    db.session.commit()
    print("创建了聊天记录")

    print("\n所有测试数据创建完成！")
    print(f"用户: {User.query.count()} | 分类: {Category.query.count()} | 寻物: {LostItem.query.count()} | 招领: {FoundItem.query.count()}")
    print(f"帖子: {ForumPost.query.count()} | 匹配: {MatchRecord.query.count()} | 评论: {Comment.query.count()}")
    print(f"通知: {Notification.query.count()} | 日志: {UserLog.query.count()}")

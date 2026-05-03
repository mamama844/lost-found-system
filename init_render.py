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
    db.create_all()
    print("数据库表已创建（如不存在）")
    
    if User.query.filter_by(is_admin=True).first():
        print("数据库已有数据，跳过初始化")
    else:
        print("首次部署，开始初始化示例数据...")
        
        admin = User(
            username='admin', email='admin@lostfound.com', phone='13800000001',
            password_hash=generate_password_hash('admin123'),
            is_admin=True, is_active=True, is_verified=True, credit_score=100,
            real_name='系统管理员'
        )
        db.session.add(admin)
        
        categories_data = [
            {'name': '电子产品', 'icon': 'phone', 'description': '手机、电脑、平板等电子设备'},
            {'name': '证件卡片', 'icon': 'credit-card', 'description': '身份证、学生证、银行卡等'},
            {'name': '钥匙钱包', 'icon': 'key', 'description': '钥匙、钱包、背包等'},
            {'name': '衣物配饰', 'icon': 'bag', 'description': '衣服、鞋子、眼镜、手表等'},
            {'name': '书籍文具', 'icon': 'book', 'description': '课本、笔记、文具等'},
            {'name': '其他物品', 'icon': 'box', 'description': '其他未分类物品'},
        ]
        for cat_data in categories_data:
            cat = Category(name=cat_data['name'], icon=cat_data['icon'], description=cat_data['description'], is_active=True)
            db.session.add(cat)
        db.session.commit()
        
        users_data = [
            {'username': '张三', 'email': 'zhangsan@example.com', 'phone': '13800000002', 'real_name': '张三'},
            {'username': '李四', 'email': 'lisi@example.com', 'phone': '13800000003', 'real_name': '李四'},
            {'username': '王五', 'email': 'wangwu@example.com', 'phone': '13800000004', 'real_name': '王五'},
            {'username': '赵六', 'email': 'zhaoliu@example.com', 'phone': '13800000005', 'real_name': '赵六'},
            {'username': '孙七', 'email': 'sunqi@example.com', 'phone': '13800000006', 'real_name': '孙七'},
        ]
        users = []
        for u in users_data:
            user = User(
                username=u['username'], email=u['email'], phone=u['phone'],
                password_hash=generate_password_hash('123456'),
                is_active=True, is_verified=True, credit_score=100,
                real_name=u['real_name']
            )
            db.session.add(user)
            users.append(user)
        db.session.commit()
        
        cat_electronics = Category.query.filter_by(name='电子产品').first()
        cat_keys = Category.query.filter_by(name='钥匙钱包').first()
        cat_clothes = Category.query.filter_by(name='衣物配饰').first()
        cat_docs = Category.query.filter_by(name='证件卡片').first()
        cat_other = Category.query.filter_by(name='其他物品').first()
        
        lost_items_data = [
            {'title': '丢失黑色钱包', 'description': '在食堂丢失一个黑色皮质钱包，内有身份证和银行卡', 'category': cat_keys, 'user': users[0], 'location': '第一食堂', 'status': 'open'},
            {'title': '丢失iPhone 15手机', 'description': '在图书馆三楼丢失一部iPhone 15黑色手机，带透明手机壳', 'category': cat_electronics, 'user': users[1], 'location': '图书馆三楼', 'status': 'open'},
            {'title': '丢失一串钥匙', 'description': '在教学楼B栋丢失一串钥匙，共5把，带一个蓝色钥匙扣', 'category': cat_keys, 'user': users[2], 'location': '教学楼B栋', 'status': 'open'},
            {'title': '丢失蓝色书包', 'description': '在操场丢失一个蓝色书包，内有课本和笔记本', 'category': cat_other, 'user': users[3], 'location': '操场', 'status': 'open'},
            {'title': '丢失学生证', 'description': '在宿舍楼下丢失学生证，姓名王五', 'category': cat_docs, 'user': users[2], 'location': '宿舍楼', 'status': 'open'},
        ]
        
        lost_items = []
        for item_data in lost_items_data:
            item = LostItem(
                title=item_data['title'], description=item_data['description'],
                category_id=item_data['category'].id, user_id=item_data['user'].id,
                location=item_data['location'], status=item_data['status'],
                audit_status='approved', is_deleted=False,
                contact_info=item_data['user'].phone,
                lost_time=datetime.now() - timedelta(days=random.randint(1, 7)),
                created_at=datetime.now() - timedelta(days=random.randint(1, 7))
            )
            db.session.add(item)
            lost_items.append(item)
        db.session.commit()
        
        found_items_data = [
            {'title': '拾获黑色钱包', 'description': '在食堂捡到一个黑色皮质钱包，内有证件', 'category': cat_keys, 'user': users[3], 'location': '第一食堂', 'status': 'open'},
            {'title': '拾获iPhone手机', 'description': '在图书馆三楼捡到一部iPhone手机，黑色，带透明壳', 'category': cat_electronics, 'user': users[4], 'location': '图书馆三楼', 'status': 'open'},
            {'title': '拾获一串钥匙', 'description': '在教学楼B栋捡到一串钥匙，带蓝色钥匙扣', 'category': cat_keys, 'user': users[0], 'location': '教学楼B栋', 'status': 'open'},
            {'title': '拾获黑色外套', 'description': '在体育馆捡到一件黑色运动外套，耐克品牌', 'category': cat_clothes, 'user': users[1], 'location': '体育馆', 'status': 'open'},
            {'title': '拾获身份证', 'description': '在校门口捡到一张身份证', 'category': cat_docs, 'user': users[4], 'location': '校门口', 'status': 'open'},
        ]
        
        found_items = []
        for item_data in found_items_data:
            item = FoundItem(
                title=item_data['title'], description=item_data['description'],
                category_id=item_data['category'].id, user_id=item_data['user'].id,
                location=item_data['location'], status=item_data['status'],
                audit_status='approved', is_deleted=False,
                contact_info=item_data['user'].phone,
                found_time=datetime.now() - timedelta(days=random.randint(0, 5)),
                created_at=datetime.now() - timedelta(days=random.randint(0, 5))
            )
            db.session.add(item)
            found_items.append(item)
        db.session.commit()
        
        configs = [
            {'key': 'match_threshold', 'value': '0.50', 'desc': '匹配阈值'},
            {'key': 'text_weight', 'value': '0.40', 'desc': '文本相似度权重'},
            {'key': 'image_weight', 'value': '0.30', 'desc': '图片相似度权重'},
            {'key': 'category_weight', 'value': '0.30', 'desc': '分类匹配权重'},
        ]
        for c in configs:
            config = SystemConfig(config_key=c['key'], config_value=c['value'], description=c['desc'])
            db.session.add(config)
        db.session.commit()
        
        print("示例数据初始化完成！")

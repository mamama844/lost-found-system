from app import create_app, db
from app.models.models import User, Category

app = create_app()

with app.app_context():
    print("正在初始化数据库...")
    
    db.create_all()
    
    if Category.query.count() == 0:
        categories = [
            Category(name='电子产品', description='手机、电脑、平板等电子设备'),
            Category(name='证件卡片', description='身份证、学生证、银行卡等'),
            Category(name='生活用品', description='钥匙、钱包、眼镜等日常用品'),
            Category(name='学习用品', description='书籍、文具、书包等'),
            Category(name='运动器材', description='球类、球拍等运动相关物品'),
            Category(name='服饰配饰', description='衣服、鞋子、饰品等'),
            Category(name='其他', description='其他未分类物品')
        ]
        for cat in categories:
            db.session.add(cat)
        db.session.commit()
        print("已添加默认分类")
    
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@example.com',
            real_name='系统管理员',
            is_admin=True,
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("已创建管理员账号:")
        print("  用户名: admin")
        print("  密码: admin123")
        print("  请登录后立即修改密码！")
    else:
        print("管理员账号已存在")
        if not admin.is_admin:
            admin.is_admin = True
            db.session.commit()
            print("已将 admin 设置为管理员")
    
    print("\n数据库初始化完成！")
    print("启动命令: python run.py")

import sqlite3

conn = sqlite3.connect('instance/lost_found.db')
cursor = conn.cursor()

print("更新分类表...")

cursor.execute("DELETE FROM categories")

categories = [
    (1, '电子产品', '手机、电脑、平板、手表等电子设备'),
    (2, '证件卡片', '身份证、学生证、银行卡、会员卡等'),
    (3, '钥匙', '各类钥匙、门禁卡等'),
    (4, '生活用品', '钱包、眼镜、雨伞、背包等日常用品'),
    (5, '书籍文具', '书籍、笔记本、文具等'),
    (6, '衣物配饰', '衣服、鞋子、饰品等'),
    (7, '运动器材', '球类、球拍等运动相关物品'),
    (8, '其他', '其他未分类物品'),
]

for id, name, desc in categories:
    cursor.execute("INSERT INTO categories (id, name, description) VALUES (?, ?, ?)", (id, name, desc))
    print(f"  {id}. {name} - {desc}")

conn.commit()
conn.close()
print("\n分类表更新完成！")

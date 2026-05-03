import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'lost_found.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

lost_images = [
    'uploads/lost/20260310005146_2026-03-09_200518.png',
    'uploads/lost/20260310010508_2025-06-17_024112.png',
    'uploads/lost/20260310022626_2026-03-10_022603.png',
    'uploads/lost/20260310023619_2026-03-10_023148.png',
    'uploads/lost/20260312203144_2026-03-10_022810.png',
    'uploads/lost/20260312203146_2026-03-10_022810.png',
    'uploads/lost/20260310005146_2026-03-09_200518.png',
    'uploads/lost/20260310010508_2025-06-17_024112.png',
]

found_images = [
    'uploads/found/20260310005943_2025-06-17_032151.png',
    'uploads/found/20260310010747_2025-06-19_123539.png',
    'uploads/found/20260310011045_2025-06-19_123539.png',
    'uploads/found/20260310021119_2025-06-17_013311.png',
    'uploads/found/20260310022923_2026-03-10_022810.png',
    'uploads/found/20260310023330_2026-03-10_023148.png',
    'uploads/found/20260310005943_2025-06-17_032151.png',
    'uploads/found/20260310010747_2025-06-19_123539.png',
]

print("更新寻物启事图片路径...")
cursor.execute("SELECT id FROM lost_items ORDER BY id")
lost_ids = [row[0] for row in cursor.fetchall()]

for i, item_id in enumerate(lost_ids):
    image_path = lost_images[i % len(lost_images)]
    cursor.execute("UPDATE lost_items SET image_path = ? WHERE id = ?", (image_path, item_id))
    print(f"  更新 ID {item_id}: {image_path}")

print("\n更新失物招领图片路径...")
cursor.execute("SELECT id FROM found_items ORDER BY id")
found_ids = [row[0] for row in cursor.fetchall()]

for i, item_id in enumerate(found_ids):
    image_path = found_images[i % len(found_images)]
    cursor.execute("UPDATE found_items SET image_path = ? WHERE id = ?", (image_path, item_id))
    print(f"  更新 ID {item_id}: {image_path}")

conn.commit()
conn.close()

print("\n图片路径更新完成！")

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.models import LostItem, FoundItem, MatchRecord
from app.utils.matcher import MatchingEngine

app = create_app()

with app.app_context():
    print("清理旧的匹配记录...")
    MatchRecord.query.delete()
    db.session.commit()
    print("旧匹配记录已清理")
    
    engine = MatchingEngine()
    
    lost_items = LostItem.query.filter_by(status='open').all()
    found_items = FoundItem.query.filter_by(status='open').all()
    
    print(f"\n重新匹配 {len(lost_items)} 个丢失物品...")
    for item in lost_items:
        engine.auto_match_lost_item(item)
    
    print(f"\n重新匹配 {len(found_items)} 个拾获物品...")
    for item in found_items:
        engine.auto_match_found_item(item)
    
    total = MatchRecord.query.count()
    print(f"\n匹配完成！共创建 {total} 条匹配记录")
    
    print("\n匹配记录详情：")
    records = MatchRecord.query.all()
    for r in records:
        print(f"  #{r.id}: 总分={r.similarity_score:.2%}, 文本={r.text_similarity:.2%}, 图像={r.image_similarity:.2%}")

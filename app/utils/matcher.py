import os
from PIL import Image
from app import db
from app.models.models import LostItem, FoundItem, MatchRecord, SystemConfig
from flask import current_app

try:
    import imagehash
    IMAGEHASH_AVAILABLE = True
except ImportError:
    IMAGEHASH_AVAILABLE = False

try:
    from app.utils.semantic_matcher import compute_semantic_similarity
    SEMANTIC_MATCHER_AVAILABLE = True
except ImportError as e:
    SEMANTIC_MATCHER_AVAILABLE = False

ADVANCED_MATCHING = SEMANTIC_MATCHER_AVAILABLE


class MatchingEngine:
    
    def __init__(self, use_advanced=True):
        self.threshold = 0.50
        self.use_advanced = use_advanced and ADVANCED_MATCHING
        self.weights = {
            'image_hash': 0.30,
            'semantic_text': 0.40,
            'category': 0.30
        }
        self._load_config()
    
    def _load_config(self):
        try:
            config_keys = {
                'match_threshold': ('threshold', float),
                'text_weight': ('semantic_text', float),
                'image_weight': ('image_hash', float),
                'category_weight': ('category', float),
            }
            for db_key, (attr, cast) in config_keys.items():
                config = SystemConfig.query.filter_by(config_key=db_key).first()
                if config and config.config_value:
                    value = cast(config.config_value)
                    if attr == 'threshold':
                        self.threshold = value
                    else:
                        self.weights[attr] = value
            total = sum(self.weights.values())
            if total > 0:
                for k in self.weights:
                    self.weights[k] /= total
        except Exception as e:
            print(f"加载匹配配置失败，使用默认值: {e}")
    
    def rematch_all(self):
        MatchRecord.query.filter_by(status='pending').delete()
        db.session.commit()
        
        lost_items = LostItem.query.filter_by(status='open', is_deleted=False, audit_status='approved').all()
        found_items = FoundItem.query.filter_by(status='open', is_deleted=False, audit_status='approved').all()
        
        count = 0
        for lost_item in lost_items:
            for found_item in found_items:
                if lost_item.category_id != found_item.category_id:
                    continue
                details = self.get_match_details(lost_item, found_item)
                similarity = details['total_similarity']
                if similarity >= self.threshold:
                    existing = MatchRecord.query.filter_by(
                        lost_item_id=lost_item.id,
                        found_item_id=found_item.id
                    ).first()
                    if not existing:
                        match = MatchRecord(
                            lost_item_id=lost_item.id,
                            found_item_id=found_item.id,
                            similarity_score=similarity,
                            text_similarity=details['text_similarity'],
                            image_similarity=details['image_similarity'],
                            status='pending'
                        )
                        db.session.add(match)
                        count += 1
        
        db.session.commit()
        return count
    
    def compute_image_hash(self, image_path):
        if not IMAGEHASH_AVAILABLE:
            return None
        try:
            if not image_path:
                return None
            upload_dir = current_app.config.get('UPLOAD_FOLDER', os.path.join(current_app.root_path, 'static/uploads'))
            if image_path.startswith('uploads/'):
                rel_path = image_path[len('uploads/'):]
                full_path = os.path.normpath(os.path.join(upload_dir, rel_path))
            else:
                full_path = os.path.normpath(os.path.join(upload_dir, image_path))
            if not os.path.exists(full_path):
                full_path = os.path.normpath(os.path.join(current_app.root_path, 'static', image_path))
            if not os.path.exists(full_path):
                return None
            img = Image.open(full_path)
            return str(imagehash.phash(img))
        except Exception as e:
            print(f"计算图片哈希失败: {e}")
            return None
    
    def compute_hash_similarity(self, hash1, hash2):
        if not IMAGEHASH_AVAILABLE:
            return 0.0
        if not hash1 or not hash2:
            return 0.0
        
        try:
            h1 = imagehash.hex_to_hash(hash1)
            h2 = imagehash.hex_to_hash(hash2)
            distance = h1 - h2
            max_distance = 64
            similarity = 1 - (distance / max_distance)
            return max(0, similarity)
        except Exception as e:
            print(f"计算哈希相似度失败: {e}")
            return 0.0
    
    def compute_text_similarity(self, text1, text2):
        if not text1 or not text2:
            return 0.0
        
        if self.use_advanced and SEMANTIC_MATCHER_AVAILABLE:
            try:
                return compute_semantic_similarity(text1, text2)
            except Exception as e:
                print(f"语义相似度计算失败: {e}")
        
        text1_lower = text1.lower()
        text2_lower = text2.lower()
        
        common_chars = set(text1_lower) & set(text2_lower)
        all_chars = set(text1_lower) | set(text2_lower)
        
        if not all_chars:
            return 0.0
        
        char_similarity = len(common_chars) / len(all_chars)
        
        keywords1 = self._extract_keywords(text1_lower)
        keywords2 = self._extract_keywords(text2_lower)
        
        if keywords1 and keywords2:
            keyword_intersection = keywords1 & keywords2
            keyword_union = keywords1 | keywords2
            keyword_similarity = len(keyword_intersection) / len(keyword_union)
        else:
            keyword_similarity = 0.0
        
        return (char_similarity * 0.4 + keyword_similarity * 0.6)
    
    def _extract_keywords(self, text):
        keywords = set()
        
        common_words = {'的', '了', '是', '在', '有', '和', '与', '或', '等', '这', '那', 
                       '我', '你', '他', '她', '它', '们', '着', '过', '被', '把', '给',
                       '向', '从', '到', '对', '为', '一', '个', '上', '下', '中', '里',
                       '不', '没', '很', '都', '也', '就', '会', '能', '要', '想', '可'}
        
        for char in text:
            if char.isalnum() and char not in common_words:
                keywords.add(char)
        
        item_keywords = {
            '手机', 'iphone', '华为', '小米', 'oppo', 'vivo', '三星',
            '电脑', '笔记本', '平板', 'ipad', 'macbook',
            '钥匙', '钱包', '卡', '身份证', '学生证', '银行卡',
            '书', '课本', '笔记', '书包', '笔',
            '衣服', '外套', '裤子', '鞋子', '帽子', '眼镜', '手表', '雨伞',
            '球', '篮球', '足球', '羽毛球', '乒乓球',
            '黑色', '白色', '红色', '蓝色', '绿色', '黄色',
            '地铁', '公交', '商场', '公园', '餐厅', '超市', '银行', '健身房',
            '丢失', '遗失', '捡到', '拾获', '找到'
        }
        
        for kw in item_keywords:
            if kw in text:
                keywords.add(kw)
        
        return keywords
    
    def compute_similarity(self, item1, item2):
        if item1.category_id and item2.category_id:
            if item1.category_id != item2.category_id:
                return 0.0
        
        hash1 = item1.image_hash if hasattr(item1, 'image_hash') and item1.image_hash else None
        hash2 = item2.image_hash if hasattr(item2, 'image_hash') and item2.image_hash else None
        
        if not hash1 and item1.image_path:
            hash1 = self.compute_image_hash(item1.image_path)
        if not hash2 and item2.image_path:
            hash2 = self.compute_image_hash(item2.image_path)
        
        img_sim = 0.0
        if hash1 and hash2:
            img_sim = self.compute_hash_similarity(hash1, hash2)
        
        text1 = f"{item1.title} {item1.description or ''}"
        text2 = f"{item2.title} {item2.description or ''}"
        text_sim = self.compute_text_similarity(text1, text2)
        
        total_score = (
            img_sim * self.weights['image_hash'] +
            text_sim * self.weights['semantic_text'] +
            1.0 * self.weights['category']
        )
        
        return total_score
    
    def get_match_details(self, item1, item2):
        details = {
            'image_similarity': 0.0,
            'text_similarity': 0.0,
            'category_match': False,
            'total_similarity': 0.0,
            'has_image1': False,
            'has_image2': False
        }
        
        hash1 = item1.image_hash if hasattr(item1, 'image_hash') and item1.image_hash else None
        hash2 = item2.image_hash if hasattr(item2, 'image_hash') and item2.image_hash else None
        
        if not hash1 and item1.image_path:
            hash1 = self.compute_image_hash(item1.image_path)
        if not hash2 and item2.image_path:
            hash2 = self.compute_image_hash(item2.image_path)
        
        details['has_image1'] = hash1 is not None
        details['has_image2'] = hash2 is not None
        
        if hash1 and hash2:
            details['image_similarity'] = self.compute_hash_similarity(hash1, hash2)
        else:
            details['image_similarity'] = 0.0
        
        text1 = f"{item1.title} {item1.description or ''}"
        text2 = f"{item2.title} {item2.description or ''}"
        details['text_similarity'] = self.compute_text_similarity(text1, text2)
        
        if item1.category_id and item2.category_id:
            details['category_match'] = item1.category_id == item2.category_id
        
        details['total_similarity'] = self.compute_similarity(item1, item2)
        
        return details
    
    def auto_match_lost_item(self, lost_item):
        found_items = FoundItem.query.filter_by(status='open').all()
        
        if not found_items:
            return
        
        print(f"开始匹配丢失物品 #{lost_item.id}，共 {len(found_items)} 个拾获物品")
        
        for found_item in found_items:
            if lost_item.category_id != found_item.category_id:
                continue
            
            details = self.get_match_details(lost_item, found_item)
            similarity = details['total_similarity']
            
            if similarity >= self.threshold:
                existing = MatchRecord.query.filter_by(
                    lost_item_id=lost_item.id,
                    found_item_id=found_item.id
                ).first()
                
                if not existing:
                    match = MatchRecord(
                        lost_item_id=lost_item.id,
                        found_item_id=found_item.id,
                        similarity_score=similarity,
                        text_similarity=details['text_similarity'],
                        image_similarity=details['image_similarity'],
                        status='pending'
                    )
                    db.session.add(match)
                    print(f"  创建匹配记录: 拾获物品 #{found_item.id}")
                    print(f"    总相似度: {similarity:.2%}")
                    print(f"    文本相似度: {details['text_similarity']:.2%}")
                    print(f"    图像相似度: {details['image_similarity']:.2%}")
        
        db.session.commit()
    
    def auto_match_found_item(self, found_item):
        lost_items = LostItem.query.filter_by(status='open').all()
        
        if not lost_items:
            return
        
        print(f"开始匹配拾获物品 #{found_item.id}，共 {len(lost_items)} 个丢失物品")
        
        for lost_item in lost_items:
            if lost_item.category_id != found_item.category_id:
                continue
            
            details = self.get_match_details(found_item, lost_item)
            similarity = details['total_similarity']
            
            if similarity >= self.threshold:
                existing = MatchRecord.query.filter_by(
                    lost_item_id=lost_item.id,
                    found_item_id=found_item.id
                ).first()
                
                if not existing:
                    match = MatchRecord(
                        lost_item_id=lost_item.id,
                        found_item_id=found_item.id,
                        similarity_score=similarity,
                        text_similarity=details['text_similarity'],
                        image_similarity=details['image_similarity'],
                        status='pending'
                    )
                    db.session.add(match)
                    print(f"  创建匹配记录: 丢失物品 #{lost_item.id}")
                    print(f"    总相似度: {similarity:.2%}")
                    print(f"    文本相似度: {details['text_similarity']:.2%}")
                    print(f"    图像相似度: {details['image_similarity']:.2%}")
        
        db.session.commit()

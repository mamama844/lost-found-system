from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models.models import Favorite, LostItem, FoundItem

favorite_bp = Blueprint('favorite', __name__)


@favorite_bp.route('/toggle', methods=['POST'])
@login_required
def toggle():
    data = request.get_json()
    item_type = data.get('item_type') or data.get('type')
    item_id = data.get('item_id') or data.get('id')
    
    if item_type not in ['lost', 'found']:
        return jsonify({'success': False, 'message': '无效的物品类型'}), 400
    
    if item_type == 'lost':
        item = LostItem.query.get(item_id)
    else:
        item = FoundItem.query.get(item_id)
    
    if not item:
        return jsonify({'success': False, 'message': '物品不存在'}), 404
    
    existing = Favorite.query.filter_by(
        user_id=current_user.id,
        item_type=item_type,
        item_id=item_id
    ).first()
    
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({
            'success': True,
            'action': 'removed',
            'message': '已取消收藏'
        })
    else:
        favorite = Favorite(
            user_id=current_user.id,
            item_type=item_type,
            item_id=item_id
        )
        db.session.add(favorite)
        db.session.commit()
        return jsonify({
            'success': True,
            'action': 'added',
            'message': '已添加收藏'
        })


@favorite_bp.route('/check/<item_type>/<int:item_id>')
@login_required
def check(item_type, item_id):
    existing = Favorite.query.filter_by(
        user_id=current_user.id,
        item_type=item_type,
        item_id=item_id
    ).first()
    
    return jsonify({'is_favorited': existing is not None})


@favorite_bp.route('/list')
@login_required
def list_favorites():
    favorites = Favorite.query.filter_by(user_id=current_user.id).order_by(Favorite.created_at.desc()).all()
    
    result = []
    for fav in favorites:
        if fav.item_type == 'lost':
            item = LostItem.query.get(fav.item_id)
        else:
            item = FoundItem.query.get(fav.item_id)
        
        if item:
            result.append({
                'id': fav.id,
                'item_type': fav.item_type,
                'item_id': item.id,
                'title': item.title,
                'location': item.location,
                'status': item.status,
                'image_path': item.image_path,
                'created_at': item.created_at.strftime('%Y-%m-%d %H:%M')
            })
    
    return jsonify({'favorites': result})

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models.models import Comment, LostItem, FoundItem

comment_bp = Blueprint('comment', __name__)


@comment_bp.route('/add', methods=['POST'])
@login_required
def add():
    data = request.get_json()
    item_type = data.get('item_type') or data.get('type')
    item_id = data.get('item_id') or data.get('id')
    content = data.get('content', '').strip()
    
    if item_type not in ['lost', 'found']:
        return jsonify({'success': False, 'message': '无效的物品类型'}), 400
    
    if not content:
        return jsonify({'success': False, 'message': '评论内容不能为空'}), 400
    
    if len(content) > 500:
        return jsonify({'success': False, 'message': '评论内容不能超过500字'}), 400
    
    if item_type == 'lost':
        item = LostItem.query.get(item_id)
    else:
        item = FoundItem.query.get(item_id)
    
    if not item:
        return jsonify({'success': False, 'message': '物品不存在'}), 404
    
    comment = Comment(
        user_id=current_user.id,
        item_type=item_type,
        item_id=item_id,
        content=content
    )
    db.session.add(comment)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '评论成功',
        'comment': {
            'id': comment.id,
            'username': current_user.username,
            'content': comment.content,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M')
        }
    })


@comment_bp.route('/list/<item_type>/<int:item_id>')
def list_comments(item_type, item_id):
    comments = Comment.query.filter_by(
        item_type=item_type,
        item_id=item_id
    ).order_by(Comment.created_at.desc()).all()
    
    result = [{
        'id': c.id,
        'username': c.user.username,
        'content': c.content,
        'created_at': c.created_at.strftime('%Y-%m-%d %H:%M'),
        'is_owner': current_user.is_authenticated and c.user_id == current_user.id
    } for c in comments]
    
    return jsonify({'comments': result})


@comment_bp.route('/delete/<int:id>', methods=['DELETE'])
@login_required
def delete(id):
    comment = Comment.query.get_or_404(id)
    
    if comment.user_id != current_user.id:
        return jsonify({'success': False, 'message': '无权删除'}), 403
    
    db.session.delete(comment)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '评论已删除'})

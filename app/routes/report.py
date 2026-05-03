from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models.models import Report, LostItem, FoundItem

report_bp = Blueprint('report', __name__)


@report_bp.route('/submit', methods=['POST'])
@login_required
def submit():
    data = request.get_json()
    item_type = data.get('item_type') or data.get('type')
    item_id = data.get('item_id') or data.get('id')
    reason = data.get('reason', '').strip()
    description = data.get('detail', '').strip() or data.get('description', '').strip()
    
    if item_type not in ['lost', 'found']:
        return jsonify({'success': False, 'message': '无效的物品类型'}), 400
    
    if not reason:
        return jsonify({'success': False, 'message': '请选择举报原因'}), 400
    
    if item_type == 'lost':
        item = LostItem.query.get(item_id)
    else:
        item = FoundItem.query.get(item_id)
    
    if not item:
        return jsonify({'success': False, 'message': '物品不存在'}), 404
    
    existing = Report.query.filter_by(
        user_id=current_user.id,
        item_type=item_type,
        item_id=item_id,
        status='pending'
    ).first()
    
    if existing:
        return jsonify({'success': False, 'message': '您已举报过该物品，请等待处理'}), 400
    
    report = Report(
        user_id=current_user.id,
        item_type=item_type,
        item_id=item_id,
        reason=reason,
        description=description
    )
    db.session.add(report)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '举报已提交，我们会尽快处理'
    })


@report_bp.route('/check/<item_type>/<int:item_id>')
@login_required
def check(item_type, item_id):
    existing = Report.query.filter_by(
        user_id=current_user.id,
        item_type=item_type,
        item_id=item_id,
        status='pending'
    ).first()
    
    return jsonify({'has_reported': existing is not None})

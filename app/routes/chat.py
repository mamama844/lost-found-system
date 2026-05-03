from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.models import ChatMessage, MatchRecord, User, LostItem, FoundItem
from datetime import datetime

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/list')
@login_required
def chat_list():
    sent_ids = db.session.query(ChatMessage.receiver_id).filter(
        ChatMessage.sender_id == current_user.id
    ).distinct()
    received_ids = db.session.query(ChatMessage.sender_id).filter(
        ChatMessage.receiver_id == current_user.id
    ).distinct()
    
    partner_ids = set()
    for r in sent_ids:
        partner_ids.add(r[0])
    for r in received_ids:
        partner_ids.add(r[0])
    
    partners = []
    for pid in partner_ids:
        user = User.query.get(pid)
        if user:
            last_msg = ChatMessage.query.filter(
                ((ChatMessage.sender_id == current_user.id) & (ChatMessage.receiver_id == pid)) |
                ((ChatMessage.sender_id == pid) & (ChatMessage.receiver_id == current_user.id))
            ).order_by(ChatMessage.created_at.desc()).first()
            unread = ChatMessage.query.filter_by(
                sender_id=pid, receiver_id=current_user.id, is_read=False
            ).count()
            partners.append({
                'user': user,
                'last_message': last_msg,
                'unread_count': unread
            })
    
    partners.sort(key=lambda x: x['last_message'].created_at if x['last_message'] else datetime.min, reverse=True)
    
    return render_template('chat/list.html', partners=partners)


@chat_bp.route('/with/<int:user_id>', methods=['GET', 'POST'])
@login_required
def conversation(user_id):
    other_user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        if content:
            match_id = request.form.get('match_id', type=int)
            msg = ChatMessage(
                sender_id=current_user.id,
                receiver_id=user_id,
                content=content,
                match_id=match_id
            )
            db.session.add(msg)
            db.session.commit()
            return redirect(url_for('chat.conversation', user_id=user_id))
    
    ChatMessage.query.filter_by(
        sender_id=user_id, receiver_id=current_user.id, is_read=False
    ).update({'is_read': True})
    db.session.commit()
    
    messages = ChatMessage.query.filter(
        ((ChatMessage.sender_id == current_user.id) & (ChatMessage.receiver_id == user_id)) |
        ((ChatMessage.sender_id == user_id) & (ChatMessage.receiver_id == current_user.id))
    ).order_by(ChatMessage.created_at.asc()).all()
    
    my_lost = LostItem.query.filter_by(user_id=current_user.id, is_deleted=False).all()
    my_found = FoundItem.query.filter_by(user_id=current_user.id, is_deleted=False).all()
    lost_ids = [i.id for i in my_lost]
    found_ids = [i.id for i in my_found]
    
    related_matches = MatchRecord.query.filter(
        ((MatchRecord.lost_item_id.in_(lost_ids)) | (MatchRecord.found_item_id.in_(found_ids)))
    ).all()
    
    return render_template('chat/conversation.html',
                          other_user=other_user,
                          messages=messages,
                          related_matches=related_matches)


@chat_bp.route('/send', methods=['POST'])
@login_required
def send_message():
    data = request.get_json()
    receiver_id = data.get('receiver_id')
    content = data.get('content', '').strip()
    match_id = data.get('match_id')
    
    if not content or not receiver_id:
        return jsonify({'success': False, 'message': '参数错误'}), 400
    
    msg = ChatMessage(
        sender_id=current_user.id,
        receiver_id=receiver_id,
        content=content,
        match_id=match_id
    )
    db.session.add(msg)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': {
            'id': msg.id,
            'content': msg.content,
            'sender_id': msg.sender_id,
            'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M'),
            'sender_name': current_user.username
        }
    })


@chat_bp.route('/unread-count')
@login_required
def unread_count():
    count = ChatMessage.query.filter_by(
        receiver_id=current_user.id, is_read=False
    ).count()
    return jsonify({'count': count})

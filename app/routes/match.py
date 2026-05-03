from flask import Blueprint, render_template, redirect, url_for, flash, current_app, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.models import MatchRecord, LostItem, FoundItem, User, Notification
from app.utils.email_service import email_service
from datetime import datetime, timedelta

match_bp = Blueprint('match', __name__)


@match_bp.route('/list')
@login_required
def list_matches():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all')
    
    lost_query = MatchRecord.query.join(
        LostItem, MatchRecord.lost_item_id == LostItem.id
    ).filter(
        LostItem.user_id == current_user.id
    )
    
    found_query = MatchRecord.query.join(
        FoundItem, MatchRecord.found_item_id == FoundItem.id
    ).filter(
        FoundItem.user_id == current_user.id
    )
    
    if status != 'all':
        lost_query = lost_query.filter(MatchRecord.status == status)
        found_query = found_query.filter(MatchRecord.status == status)
    
    lost_matches = lost_query.order_by(MatchRecord.similarity_score.desc()).all()
    found_matches = found_query.order_by(MatchRecord.similarity_score.desc()).all()
    
    all_matches = list(set(lost_matches + found_matches))
    all_matches.sort(key=lambda x: x.similarity_score, reverse=True)
    
    for match in all_matches:
        match.lost_item_info = LostItem.query.get(match.lost_item_id)
        match.found_item_info = FoundItem.query.get(match.found_item_id)
    
    return render_template('match/list.html', matches=all_matches, status=status)


@match_bp.route('/<int:id>/confirm', methods=['POST'])
@login_required
def confirm_match(id):
    match = MatchRecord.query.get_or_404(id)
    
    lost_item = LostItem.query.get(match.lost_item_id)
    found_item = FoundItem.query.get(match.found_item_id)
    
    if lost_item.user_id != current_user.id and found_item.user_id != current_user.id:
        flash('无权操作', 'danger')
        return redirect(url_for('match.list_matches'))
    
    if lost_item.user_id == current_user.id:
        match.lost_confirmed = True
    if found_item.user_id == current_user.id:
        match.found_confirmed = True
    
    if match.lost_confirmed and match.found_confirmed:
        match.status = 'confirmed'
        lost_item.status = 'closed'
        found_item.status = 'closed'
        
        MatchRecord.query.filter(
            MatchRecord.lost_item_id == match.lost_item_id,
            MatchRecord.id != id,
            MatchRecord.status == 'pending'
        ).update({'status': 'rejected'})
        
        MatchRecord.query.filter(
            MatchRecord.found_item_id == match.found_item_id,
            MatchRecord.id != id,
            MatchRecord.status == 'pending'
        ).update({'status': 'rejected'})
        
        lost_owner = User.query.get(lost_item.user_id)
        found_owner = User.query.get(found_item.user_id)
        
        notification1 = Notification(
            user_id=lost_owner.id,
            title='匹配成功！',
            content=f'您丢失的物品"{lost_item.title}"已找到匹配！请联系拾获者。',
            notification_type='match',
            related_id=match.id
        )
        notification2 = Notification(
            user_id=found_owner.id,
            title='匹配成功！',
            content=f'您拾获的物品"{found_item.title}"已找到失主！请联系失主。',
            notification_type='match',
            related_id=match.id
        )
        db.session.add(notification1)
        db.session.add(notification2)
        
        if current_app.config.get('MAIL_ENABLED'):
            try:
                email_service.send_match_notification(
                    lost_owner.email, lost_owner.username, 
                    lost_item, found_item, match.similarity_score
                )
                email_service.send_match_notification(
                    found_owner.email, found_owner.username,
                    found_item, lost_item, match.similarity_score
                )
            except:
                pass
        
        flash('双方已确认，匹配成功！', 'success')
    else:
        flash('已确认，等待对方确认', 'success')
    
    db.session.commit()
    return redirect(url_for('match.list_matches'))


@match_bp.route('/<int:id>/reject', methods=['POST'])
@login_required
def reject_match(id):
    match = MatchRecord.query.get_or_404(id)
    
    lost_item = LostItem.query.get(match.lost_item_id)
    found_item = FoundItem.query.get(match.found_item_id)
    
    if lost_item.user_id != current_user.id and found_item.user_id != current_user.id:
        flash('无权操作', 'danger')
        return redirect(url_for('match.list_matches'))
    
    match.status = 'rejected'
    db.session.commit()
    
    flash('匹配已拒绝', 'info')
    return redirect(url_for('match.list_matches'))


@match_bp.route('/detail/<int:id>')
@login_required
def detail(id):
    match = MatchRecord.query.get_or_404(id)
    
    lost_item = LostItem.query.get(match.lost_item_id)
    found_item = FoundItem.query.get(match.found_item_id)
    
    if lost_item.user_id != current_user.id and found_item.user_id != current_user.id and not current_user.is_admin:
        flash('无权查看', 'danger')
        return redirect(url_for('match.list_matches'))
    
    return render_template('match/detail.html', match=match, 
                          lost_item=lost_item, found_item=found_item)


def auto_expire_matches():
    expired_matches = MatchRecord.query.filter(
        MatchRecord.status == 'pending',
        MatchRecord.expires_at < datetime.now()
    ).all()
    
    for match in expired_matches:
        match.status = 'rejected'
        
        lost_item = LostItem.query.get(match.lost_item_id)
        if lost_item:
            notification = Notification(
                user_id=lost_item.user_id,
                title='匹配已过期',
                content=f'您的物品"{lost_item.title}"的匹配记录已过期，系统已自动拒绝。',
                notification_type='match'
            )
            db.session.add(notification)
    
    db.session.commit()
    return len(expired_matches)


def set_match_expiry(match):
    match.expires_at = datetime.now() + timedelta(hours=72)

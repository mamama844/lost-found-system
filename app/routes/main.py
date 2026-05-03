from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from app.models.models import LostItem, FoundItem, Category, ForumPost, MatchRecord, User
from sqlalchemy import or_

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    recent_lost = LostItem.query.filter_by(
        status='open', audit_status='approved', is_deleted=False
    ).order_by(LostItem.created_at.desc()).limit(6).all()
    recent_found = FoundItem.query.filter_by(
        status='open', audit_status='approved', is_deleted=False
    ).order_by(FoundItem.created_at.desc()).limit(6).all()
    categories = Category.query.filter_by(is_active=True).all()
    
    confirmed_matches = MatchRecord.query.filter_by(status='confirmed').count()
    total_matches = MatchRecord.query.count()
    
    confirmed_match_list = MatchRecord.query.filter_by(status='confirmed').order_by(
        MatchRecord.created_at.desc()
    ).limit(6).all()
    
    thank_you_posts = ForumPost.query.filter_by(
        status='active', audit_status='approved', category='感谢信'
    ).order_by(ForumPost.created_at.desc()).limit(3).all()
    
    if not thank_you_posts:
        thank_you_posts = ForumPost.query.filter_by(
            status='active', audit_status='approved'
        ).filter(ForumPost.title.contains('感谢')).order_by(
            ForumPost.created_at.desc()
        ).limit(3).all()
    
    from datetime import datetime
    stats = {
        'lost_count': LostItem.query.filter_by(status='open', audit_status='approved', is_deleted=False).count(),
        'found_count': FoundItem.query.filter_by(status='open', audit_status='approved', is_deleted=False).count(),
        'resolved_count': LostItem.query.filter_by(status='closed', is_deleted=False).count() + 
                          FoundItem.query.filter_by(status='closed', is_deleted=False).count(),
        'confirmed_matches': confirmed_matches,
        'total_matches': total_matches,
        'total_users': 0,
        'today_lost': 0,
        'today_found': 0,
    }
    
    stats['total_users'] = User.query.filter_by(is_active=True).count()
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    stats['today_lost'] = LostItem.query.filter(
        LostItem.created_at >= today, LostItem.audit_status == 'approved', LostItem.is_deleted == False
    ).count()
    stats['today_found'] = FoundItem.query.filter(
        FoundItem.created_at >= today, FoundItem.audit_status == 'approved', FoundItem.is_deleted == False
    ).count()
    
    return render_template('index.html', 
                          recent_lost=recent_lost, 
                          recent_found=recent_found,
                          categories=categories,
                          stats=stats,
                          thank_you_posts=thank_you_posts,
                          confirmed_match_list=confirmed_match_list)


@main_bp.route('/search')
def search():
    query = request.args.get('q', '').strip()
    lost_results = []
    found_results = []
    
    if query:
        lost_results = LostItem.query.filter(
            LostItem.audit_status == 'approved',
            LostItem.is_deleted == False,
            or_(
                LostItem.title.contains(query),
                LostItem.description.contains(query),
                LostItem.location.contains(query)
            )
        ).order_by(LostItem.created_at.desc()).limit(20).all()
        
        found_results = FoundItem.query.filter(
            FoundItem.audit_status == 'approved',
            FoundItem.is_deleted == False,
            or_(
                FoundItem.title.contains(query),
                FoundItem.description.contains(query),
                FoundItem.location.contains(query)
            )
        ).order_by(FoundItem.created_at.desc()).limit(20).all()
    
    return render_template('search_results.html', 
                          query=query,
                          lost_results=lost_results,
                          found_results=found_results)


@main_bp.route('/profile')
@login_required
def profile():
    my_lost = LostItem.query.filter_by(user_id=current_user.id, is_deleted=False).order_by(LostItem.created_at.desc()).all()
    my_found = FoundItem.query.filter_by(user_id=current_user.id, is_deleted=False).order_by(FoundItem.created_at.desc()).all()
    my_match_count = MatchRecord.query.filter(
        (MatchRecord.lost_item_id.in_([i.id for i in my_lost])) |
        (MatchRecord.found_item_id.in_([i.id for i in my_found]))
    ).count()
    
    stats = {
        'lost_count': len(my_lost),
        'found_count': len(my_found),
        'resolved_lost': sum(1 for item in my_lost if item.status == 'closed'),
        'resolved_found': sum(1 for item in my_found if item.status == 'closed')
    }
    
    return render_template('profile.html', 
                          my_lost=my_lost, 
                          my_found=my_found,
                          stats=stats,
                          my_lost_count=len(my_lost),
                          my_found_count=len(my_found),
                          my_match_count=my_match_count)

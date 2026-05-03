from flask import Blueprint, render_template, jsonify, send_file
from flask_login import login_required
from app import db
from app.models.models import LostItem, FoundItem, Category, MatchRecord, User
from app.utils.excel_export import export_items_to_excel, export_matches_to_excel
from sqlalchemy import func
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    return render_template('dashboard/index.html')


@dashboard_bp.route('/export/lost')
@login_required
def export_lost():
    items = LostItem.query.order_by(LostItem.created_at.desc()).all()
    buffer = export_items_to_excel(items, 'lost')
    filename = f"丢失物品_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(
        buffer,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )


@dashboard_bp.route('/export/found')
@login_required
def export_found():
    items = FoundItem.query.order_by(FoundItem.created_at.desc()).all()
    buffer = export_items_to_excel(items, 'found')
    filename = f"拾获物品_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(
        buffer,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )


@dashboard_bp.route('/export/matches')
@login_required
def export_matches():
    matches = MatchRecord.query.order_by(MatchRecord.created_at.desc()).all()
    buffer = export_matches_to_excel(matches)
    filename = f"匹配记录_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(
        buffer,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )


@dashboard_bp.route('/api/stats/overview')
def overview_stats():
    total_lost = LostItem.query.count()
    total_found = FoundItem.query.count()
    open_lost = LostItem.query.filter_by(status='open').count()
    open_found = FoundItem.query.filter_by(status='open').count()
    resolved = LostItem.query.filter_by(status='closed').count() + FoundItem.query.filter_by(status='closed').count()
    total_matches = MatchRecord.query.count()
    confirmed_matches = MatchRecord.query.filter_by(status='confirmed').count()
    
    return jsonify({
        'total_lost': total_lost,
        'total_found': total_found,
        'open_lost': open_lost,
        'open_found': open_found,
        'resolved': resolved,
        'total_matches': total_matches,
        'confirmed_matches': confirmed_matches,
        'match_rate': round(confirmed_matches / total_matches * 100, 1) if total_matches > 0 else 0
    })


@dashboard_bp.route('/api/stats/category')
def category_stats():
    categories = Category.query.all()
    
    result = {
        'categories': [],
        'lost_counts': [],
        'found_counts': []
    }
    
    for cat in categories:
        lost_count = LostItem.query.filter_by(category_id=cat.id).count()
        found_count = FoundItem.query.filter_by(category_id=cat.id).count()
        
        result['categories'].append(cat.name)
        result['lost_counts'].append(lost_count)
        result['found_counts'].append(found_count)
    
    return jsonify(result)


@dashboard_bp.route('/api/stats/trend')
def trend_stats():
    today = datetime.now()
    dates = []
    lost_trend = []
    found_trend = []
    
    for i in range(7):
        date = today - timedelta(days=6-i)
        dates.append(date.strftime('%m-%d'))
        
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        lost_count = LostItem.query.filter(
            LostItem.created_at >= day_start,
            LostItem.created_at < day_end
        ).count()
        
        found_count = FoundItem.query.filter(
            FoundItem.created_at >= day_start,
            FoundItem.created_at < day_end
        ).count()
        
        lost_trend.append(lost_count)
        found_trend.append(found_count)
    
    return jsonify({
        'dates': dates,
        'lost_trend': lost_trend,
        'found_trend': found_trend
    })


@dashboard_bp.route('/api/stats/match_score')
def match_score_stats():
    matches = MatchRecord.query.filter(
        MatchRecord.similarity_score >= 0.3
    ).order_by(MatchRecord.similarity_score.desc()).limit(20).all()
    
    return jsonify({
        'matches': [{
            'id': m.id,
            'lost_title': m.lost_item.title if m.lost_item else '未知',
            'found_title': m.found_item.title if m.found_item else '未知',
            'score': round(m.similarity_score * 100, 1),
            'status': m.status
        } for m in matches]
    })


@dashboard_bp.route('/api/stats/location')
def location_stats():
    lost_locations = db.session.query(
        LostItem.location,
        func.count(LostItem.id).label('count')
    ).filter(
        LostItem.location.isnot(None),
        LostItem.location != ''
    ).group_by(LostItem.location).order_by(
        func.count(LostItem.id).desc()
    ).limit(10).all()
    
    found_locations = db.session.query(
        FoundItem.location,
        func.count(FoundItem.id).label('count')
    ).filter(
        FoundItem.location.isnot(None),
        FoundItem.location != ''
    ).group_by(FoundItem.location).order_by(
        func.count(FoundItem.id).desc()
    ).limit(10).all()
    
    return jsonify({
        'lost_locations': [{'name': l[0], 'value': l[1]} for l in lost_locations if l[0]],
        'found_locations': [{'name': l[0], 'value': l[1]} for l in found_locations if l[0]]
    })

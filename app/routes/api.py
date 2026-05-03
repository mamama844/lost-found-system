from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.models import LostItem, FoundItem, Category, MatchRecord, User
from datetime import datetime

api_bp = Blueprint('api', __name__)


@api_bp.route('/search')
def search():
    keyword = request.args.get('q', '')
    item_type = request.args.get('type', 'all')
    page = request.args.get('page', 1, type=int)
    
    results = {'lost': [], 'found': []}
    
    if item_type in ['all', 'lost']:
        lost_items = LostItem.query.filter(
            LostItem.status == 'open',
            db.or_(
                LostItem.title.contains(keyword),
                LostItem.description.contains(keyword),
                LostItem.location.contains(keyword)
            )
        ).order_by(LostItem.created_at.desc()).limit(10).all()
        
        results['lost'] = [{
            'id': item.id,
            'title': item.title,
            'description': item.description,
            'location': item.location,
            'category': item.category.name if item.category else None,
            'image_path': item.image_path,
            'created_at': item.created_at.strftime('%Y-%m-%d %H:%M')
        } for item in lost_items]
    
    if item_type in ['all', 'found']:
        found_items = FoundItem.query.filter(
            FoundItem.status == 'open',
            db.or_(
                FoundItem.title.contains(keyword),
                FoundItem.description.contains(keyword),
                FoundItem.location.contains(keyword)
            )
        ).order_by(FoundItem.created_at.desc()).limit(10).all()
        
        results['found'] = [{
            'id': item.id,
            'title': item.title,
            'description': item.description,
            'location': item.location,
            'category': item.category.name if item.category else None,
            'image_path': item.image_path,
            'created_at': item.created_at.strftime('%Y-%m-%d %H:%M')
        } for item in found_items]
    
    return jsonify(results)


@api_bp.route('/categories')
def get_categories():
    categories = Category.query.all()
    return jsonify({
        'categories': [{
            'id': c.id,
            'name': c.name,
            'description': c.description
        } for c in categories]
    })


@api_bp.route('/lost', methods=['GET'])
def list_lost():
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    
    query = LostItem.query.filter_by(status='open')
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    items = query.order_by(LostItem.created_at.desc()).paginate(page=page, per_page=20)
    
    return jsonify({
        'items': [{
            'id': item.id,
            'title': item.title,
            'description': item.description,
            'location': item.location,
            'lost_time': item.lost_time.strftime('%Y-%m-%d %H:%M') if item.lost_time else None,
            'category': item.category.name if item.category else None,
            'image_path': item.image_path,
            'contact_info': item.contact_info,
            'created_at': item.created_at.strftime('%Y-%m-%d %H:%M')
        } for item in items.items],
        'total': items.total,
        'pages': items.pages,
        'current_page': page
    })


@api_bp.route('/found', methods=['GET'])
def list_found():
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    
    query = FoundItem.query.filter_by(status='open')
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    items = query.order_by(FoundItem.created_at.desc()).paginate(page=page, per_page=20)
    
    return jsonify({
        'items': [{
            'id': item.id,
            'title': item.title,
            'description': item.description,
            'location': item.location,
            'found_time': item.found_time.strftime('%Y-%m-%d %H:%M') if item.found_time else None,
            'category': item.category.name if item.category else None,
            'image_path': item.image_path,
            'contact_info': item.contact_info,
            'created_at': item.created_at.strftime('%Y-%m-%d %H:%M')
        } for item in items.items],
        'total': items.total,
        'pages': items.pages,
        'current_page': page
    })


@api_bp.route('/match/<int:lost_id>/<int:found_id>')
def get_match_detail(lost_id, found_id):
    from app.utils.matcher import MatchingEngine
    
    lost_item = LostItem.query.get_or_404(lost_id)
    found_item = FoundItem.query.get_or_404(found_id)
    
    engine = MatchingEngine()
    details = engine.get_match_details(lost_item, found_item)
    
    return jsonify({
        'lost_item': {
            'id': lost_item.id,
            'title': lost_item.title,
            'description': lost_item.description
        },
        'found_item': {
            'id': found_item.id,
            'title': found_item.title,
            'description': found_item.description
        },
        'match_details': details
    })


@api_bp.route('/recommend/<int:item_id>')
def recommend_matches(item_id):
    item_type = request.args.get('type', 'lost')
    
    from app.utils.matcher import MatchingEngine
    engine = MatchingEngine()
    
    recommendations = []
    
    if item_type == 'lost':
        lost_item = LostItem.query.get_or_404(item_id)
        found_items = FoundItem.query.filter_by(status='open').limit(50).all()
        
        for found_item in found_items:
            similarity = engine.compute_similarity(lost_item, found_item)
            if similarity >= 0.5:
                recommendations.append({
                    'id': found_item.id,
                    'title': found_item.title,
                    'location': found_item.location,
                    'similarity': round(similarity * 100, 1),
                    'image_path': found_item.image_path
                })
    else:
        found_item = FoundItem.query.get_or_404(item_id)
        lost_items = LostItem.query.filter_by(status='open').limit(50).all()
        
        for lost_item in lost_items:
            similarity = engine.compute_similarity(found_item, lost_item)
            if similarity >= 0.5:
                recommendations.append({
                    'id': lost_item.id,
                    'title': lost_item.title,
                    'location': lost_item.location,
                    'similarity': round(similarity * 100, 1),
                    'image_path': lost_item.image_path
                })
    
    recommendations.sort(key=lambda x: x['similarity'], reverse=True)
    
    return jsonify({
        'recommendations': recommendations[:10]
    })


@api_bp.route('/stats')
def get_stats():
    total_lost = LostItem.query.count()
    total_found = FoundItem.query.count()
    open_lost = LostItem.query.filter_by(status='open').count()
    open_found = FoundItem.query.filter_by(status='open').count()
    resolved = LostItem.query.filter_by(status='closed').count() + FoundItem.query.filter_by(status='closed').count()
    
    return jsonify({
        'total_lost': total_lost,
        'total_found': total_found,
        'open_lost': open_lost,
        'open_found': open_found,
        'resolved': resolved
    })

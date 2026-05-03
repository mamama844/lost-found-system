from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
from app import db
from app.models.models import FoundItem, Category, LostItem, MatchRecord, Notification
from app.forms.forms import FoundItemForm
from app.utils.matcher import MatchingEngine

found_bp = Blueprint('found', __name__)


def save_images(image_files):
    paths = []
    for image_file in image_files:
        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"{timestamp}_{filename}"
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'found')
            os.makedirs(upload_path, exist_ok=True)
            image_path = os.path.join(upload_path, filename)
            image_file.save(image_path)
            paths.append(f"uploads/found/{filename}")
    return paths


@found_bp.route('/list')
def list_items():
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    status = request.args.get('status', 'open')
    keyword = request.args.get('keyword', '')
    
    query = FoundItem.query.filter_by(is_deleted=False, audit_status='approved')
    if category_id:
        query = query.filter_by(category_id=category_id)
    if status:
        query = query.filter_by(status=status)
    if keyword:
        query = query.filter(
            (FoundItem.title.contains(keyword)) |
            (FoundItem.description.contains(keyword)) |
            (FoundItem.location.contains(keyword))
        )
    
    items = query.order_by(FoundItem.created_at.desc()).paginate(page=page, per_page=12)
    categories = Category.query.filter_by(is_active=True).all()
    
    return render_template('found/list.html', items=items, categories=categories,
                          keyword=keyword, status=status)


@found_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if not current_user.can_publish():
        flash('您的信用分过低，暂时无法发布物品', 'danger')
        return redirect(url_for('found.list_items'))
    
    form = FoundItemForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.filter_by(is_active=True).all()]
    
    if form.validate_on_submit():
        image_paths = []
        image_hash = None
        
        if 'images' in request.files:
            files = request.files.getlist('images')
            image_paths = save_images(files)
        
        if image_paths:
            matcher = MatchingEngine()
            image_hash = matcher.compute_image_hash(image_paths[0])
        
        item = FoundItem(
            title=form.title.data,
            description=form.description.data,
            category_id=form.category_id.data,
            user_id=current_user.id,
            location=form.location.data,
            found_time=form.found_time.data,
            image_path=image_paths[0] if image_paths else None,
            image_paths=json.dumps(image_paths) if image_paths else None,
            image_hash=image_hash,
            contact_info=form.contact_info.data,
            audit_status='pending'
        )
        db.session.add(item)
        db.session.commit()
        
        flash('拾获物品发布成功！等待审核通过后将自动匹配。', 'success')
        return redirect(url_for('found.detail', id=item.id))
    
    return render_template('found/create.html', form=form, categories=Category.query.filter_by(is_active=True).all())


@found_bp.route('/<int:id>')
def detail(id):
    item = FoundItem.query.get_or_404(id)
    
    if item.is_deleted:
        flash('该物品已被删除', 'warning')
        return redirect(url_for('found.list_items'))
    
    if item.audit_status != 'approved' and (not current_user.is_authenticated or 
        (current_user.id != item.user_id and not current_user.is_admin)):
        flash('该物品正在审核中', 'warning')
        return redirect(url_for('found.list_items'))
    
    item.view_count += 1
    db.session.commit()
    
    matches = item.matches.filter_by(status='pending').order_by(db.text('similarity_score desc')).limit(5).all()
    
    for match in matches:
        if match.lost_item:
            matcher = MatchingEngine()
            details = matcher.get_match_details(item, match.lost_item)
            match.match_details = details
    
    image_paths = []
    if item.image_paths:
        try:
            image_paths = json.loads(item.image_paths)
        except:
            if item.image_path:
                image_paths = [item.image_path]
    
    return render_template('found/detail.html', item=item, matches=matches, image_paths=image_paths)


@found_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    item = FoundItem.query.get_or_404(id)
    
    if item.user_id != current_user.id and not current_user.is_admin:
        flash('无权编辑此物品', 'danger')
        return redirect(url_for('found.detail', id=id))
    
    if request.method == 'POST':
        item.title = request.form.get('title')
        item.description = request.form.get('description')
        item.category_id = request.form.get('category_id', type=int)
        item.location = request.form.get('location')
        item.contact_info = request.form.get('contact_info')
        
        found_time_str = request.form.get('found_time')
        if found_time_str:
            try:
                item.found_time = datetime.strptime(found_time_str, '%Y-%m-%dT%H:%M')
            except:
                pass
        
        if 'images' in request.files:
            files = request.files.getlist('images')
            new_paths = save_images(files)
            if new_paths:
                item.image_paths = json.dumps(new_paths)
                item.image_path = new_paths[0]
        
        if item.audit_status == 'approved':
            item.audit_status = 'pending'
            flash('物品已更新，需要重新审核', 'success')
        else:
            flash('物品已更新', 'success')
        
        db.session.commit()
        return redirect(url_for('found.detail', id=id))
    
    categories = Category.query.filter_by(is_active=True).all()
    image_paths = []
    if item.image_paths:
        try:
            image_paths = json.loads(item.image_paths)
        except:
            if item.image_path:
                image_paths = [item.image_path]
    
    return render_template('found/edit.html', item=item, categories=categories, image_paths=image_paths)


@found_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    item = FoundItem.query.get_or_404(id)
    
    if item.user_id != current_user.id and not current_user.is_admin:
        flash('无权删除此物品', 'danger')
        return redirect(url_for('found.detail', id=id))
    
    item.is_deleted = True
    db.session.commit()
    
    flash('物品已删除', 'success')
    return redirect(url_for('found.list_items'))


@found_bp.route('/<int:id>/close', methods=['POST'])
@login_required
def close(id):
    item = FoundItem.query.get_or_404(id)
    if item.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'success': False, 'message': '无权操作'})
    
    item.status = 'closed'
    item.status_note = request.form.get('note', '已归还')
    db.session.commit()
    
    return jsonify({'success': True, 'message': '物品状态已更新为已归还'})


@found_bp.route('/<int:id>/rematch')
@login_required
def rematch(id):
    item = FoundItem.query.get_or_404(id)
    
    if item.user_id != current_user.id and not current_user.is_admin:
        flash('无权操作', 'danger')
        return redirect(url_for('found.detail', id=id))
    
    MatchRecord.query.filter_by(found_item_id=item.id).delete()
    db.session.commit()
    
    matcher = MatchingEngine()
    matcher.auto_match_found_item(item)
    
    flash('重新匹配完成！', 'success')
    return redirect(url_for('found.detail', id=id))

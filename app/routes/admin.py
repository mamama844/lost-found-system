from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file, make_response, current_app
from flask_login import login_required, current_user, login_user, logout_user
from functools import wraps
from app import db
from app.models.models import User, LostItem, FoundItem, Comment, Report, ForumPost, ForumReply, Category, MatchRecord, Notification, SystemConfig, UserLog, PostLike, ForumBoard, CreditRecord, SystemBackup, SystemStats, PostCollection
from sqlalchemy import func
from datetime import datetime, timedelta
import os
import csv
import io
import json
import shutil
try:
    import psutil
except ImportError:
    psutil = None

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('需要管理员权限', 'danger')
            return redirect(url_for('admin.admin_login'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_admin:
            login_user(user)
            log = UserLog(
                user_id=user.id,
                action='admin_login',
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            db.session.add(log)
            db.session.commit()
            return redirect(url_for('admin.dashboard'))
        else:
            flash('管理员账号或密码错误', 'danger')
    
    return render_template('admin/login.html')


@admin_bp.route('/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('admin.admin_login'))


@admin_bp.route('/')
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    total_users = User.query.count()
    total_lost = LostItem.query.filter_by(is_deleted=False).count()
    total_found = FoundItem.query.filter_by(is_deleted=False).count()
    total_matches = MatchRecord.query.count()
    pending_reports = Report.query.filter_by(status='pending').count()
    active_posts = ForumPost.query.filter_by(status='active', audit_status='approved').count()
    pending_audit_lost = LostItem.query.filter_by(audit_status='pending', is_deleted=False).count()
    pending_audit_found = FoundItem.query.filter_by(audit_status='pending', is_deleted=False).count()
    pending_audit_posts = ForumPost.query.filter_by(audit_status='pending', status='active').count()
    
    match_pending = MatchRecord.query.filter_by(status='pending').count()
    match_confirmed = MatchRecord.query.filter_by(status='confirmed').count()
    match_rejected = MatchRecord.query.filter_by(status='rejected').count()
    
    today = datetime.now()
    trend_range = request.args.get('trend', '7d')
    
    if trend_range == '30d':
        days = 30
    elif trend_range == '1y':
        days = 365
    else:
        days = 7
    
    dates = []
    user_trend = []
    lost_trend = []
    found_trend = []
    
    if days <= 31:
        for i in range(days):
            date = today - timedelta(days=days-1-i)
            date_str = date.strftime('%Y-%m-%d')
            dates.append(date.strftime('%m-%d'))
            
            day_start = datetime.strptime(date_str, '%Y-%m-%d')
            day_end = day_start + timedelta(days=1)
            
            user_trend.append(User.query.filter(User.created_at >= day_start, User.created_at < day_end).count())
            lost_trend.append(LostItem.query.filter(LostItem.created_at >= day_start, LostItem.created_at < day_end).count())
            found_trend.append(FoundItem.query.filter(FoundItem.created_at >= day_start, FoundItem.created_at < day_end).count())
    else:
        for i in range(12):
            month_start = today.replace(day=1) - timedelta(days=30*i)
            month_start = month_start.replace(day=1)
            if i > 0:
                month_start = (today.replace(day=1) - timedelta(days=30*(i-1))).replace(day=1)
                month_start = month_start.replace(day=1)
            month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
            
            dates.insert(0, month_start.strftime('%Y-%m'))
            user_trend.insert(0, User.query.filter(User.created_at >= month_start, User.created_at < month_end).count())
            lost_trend.insert(0, LostItem.query.filter(LostItem.created_at >= month_start, LostItem.created_at < month_end).count())
            found_trend.insert(0, FoundItem.query.filter(FoundItem.created_at >= month_start, FoundItem.created_at < month_end).count())
    
    categories = Category.query.all()
    category_stats = []
    for cat in categories:
        lost_count = LostItem.query.filter_by(category_id=cat.id, is_deleted=False).count()
        found_count = FoundItem.query.filter_by(category_id=cat.id, is_deleted=False).count()
        category_stats.append({
            'name': cat.name,
            'lost': lost_count,
            'found': found_count
        })
    
    match_stats = {
        'total': total_matches,
        'pending': match_pending,
        'confirmed': match_confirmed,
        'rejected': match_rejected
    }
    
    try:
        if psutil:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            system_info = {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_used': round(memory.used / (1024**3), 2),
                'memory_total': round(memory.total / (1024**3), 2),
                'disk_percent': disk.percent,
                'disk_used': round(disk.used / (1024**3), 2),
                'disk_total': round(disk.total / (1024**3), 2)
            }
        else:
            raise Exception('psutil not available')
    except:
        system_info = {
            'cpu_percent': 0,
            'memory_percent': 0,
            'memory_used': 0,
            'memory_total': 0,
            'disk_percent': 0,
            'disk_used': 0,
            'disk_total': 0
        }
    
    return render_template('admin/dashboard.html',
        total_users=total_users,
        total_lost=total_lost,
        total_found=total_found,
        total_matches=total_matches,
        pending_reports=pending_reports,
        active_posts=active_posts,
        pending_audit_lost=pending_audit_lost,
        pending_audit_found=pending_audit_found,
        pending_audit_posts=pending_audit_posts,
        dates=dates,
        user_trend=user_trend,
        lost_trend=lost_trend,
        found_trend=found_trend,
        category_stats=category_stats,
        match_stats=match_stats,
        system_info=system_info,
        trend_range=trend_range
    )


@admin_bp.route('/users')
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    role = request.args.get('role', '')
    status = request.args.get('status', '')
    
    query = User.query
    if search:
        query = query.filter(
            (User.username.contains(search)) |
            (User.email.contains(search)) |
            (User.phone.contains(search))
        )
    if role == 'admin':
        query = query.filter_by(is_admin=True)
    elif role == 'user':
        query = query.filter_by(is_admin=False)
    if status == 'active':
        query = query.filter_by(is_active=True)
    elif status == 'disabled':
        query = query.filter_by(is_active=False)
    
    users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/users.html', users=users, search=search, role=role, status=status)


@admin_bp.route('/user/<int:id>/toggle', methods=['POST'])
@admin_required
def toggle_user(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        return jsonify({'success': False, 'message': '不能禁用自己的账号'})
    
    user.is_active = not user.is_active
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '账号已禁用' if not user.is_active else '账号已启用',
        'is_active': user.is_active
    })


@admin_bp.route('/user/<int:id>/admin', methods=['POST'])
@admin_required
def toggle_admin(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        return jsonify({'success': False, 'message': '不能修改自己的权限'})
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '已设为管理员' if user.is_admin else '已取消管理员',
        'is_admin': user.is_admin
    })


@admin_bp.route('/user/<int:id>/delete', methods=['POST'])
@admin_required
def delete_user(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        return jsonify({'success': False, 'message': '不能删除自己的账号'})
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '用户已删除'})


@admin_bp.route('/user/<int:id>/logs')
@admin_required
def user_logs(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    logs = UserLog.query.filter_by(user_id=id).order_by(UserLog.created_at.desc()).paginate(page=page, per_page=50)
    return render_template('admin/user_logs.html', user=user, logs=logs)


@admin_bp.route('/users/export')
@admin_required
def export_users():
    users = User.query.all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', '用户名', '邮箱', '手机号', '真实姓名', '信用分', '是否管理员', '是否激活', '注册时间'])
    
    for user in users:
        writer.writerow([
            user.id,
            user.username,
            user.email,
            user.phone or '',
            user.real_name or '',
            user.credit_score,
            '是' if user.is_admin else '否',
            '是' if user.is_active else '否',
            user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else ''
        ])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'users_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )


@admin_bp.route('/items')
@admin_required
def items():
    page = request.args.get('page', 1, type=int)
    item_type = request.args.get('type', 'all')
    audit_status = request.args.get('audit', 'all')
    
    lost_items = []
    found_items = []
    
    if item_type == 'lost':
        query = LostItem.query.filter_by(is_deleted=False)
        if audit_status != 'all':
            query = query.filter_by(audit_status=audit_status)
        lost_items = query.order_by(LostItem.created_at.desc()).paginate(page=page, per_page=20)
    elif item_type == 'found':
        query = FoundItem.query.filter_by(is_deleted=False)
        if audit_status != 'all':
            query = query.filter_by(audit_status=audit_status)
        found_items = query.order_by(FoundItem.created_at.desc()).paginate(page=page, per_page=20)
    else:
        lost_query = LostItem.query.filter_by(is_deleted=False)
        if audit_status != 'all':
            lost_query = lost_query.filter_by(audit_status=audit_status)
        found_query = FoundItem.query.filter_by(is_deleted=False)
        if audit_status != 'all':
            found_query = found_query.filter_by(audit_status=audit_status)
        
        all_items_raw = []
        for item in lost_query.all():
            all_items_raw.append(('lost', item))
        for item in found_query.all():
            all_items_raw.append(('found', item))
        all_items_raw.sort(key=lambda x: x[1].created_at, reverse=True)
        
        per_page = 20
        total = len(all_items_raw)
        start = (page - 1) * per_page
        end = start + per_page
        page_items = all_items_raw[start:end]
        
        from flask import abort
        class FakePagination:
            def __init__(self, items, page, per_page, total):
                self.items = items
                self.page = page
                self.per_page = per_page
                self.total = total
                self.pages = (total + per_page - 1) // per_page
                self.has_prev = page > 1
                self.has_next = page < self.pages
                self.prev_num = page - 1
                self.next_num = page + 1
            def iter_pages(self, left_edge=1, right_edge=1, left_current=2, right_current=2):
                last = 0
                for num in range(1, self.pages + 1):
                    if num <= left_edge or num > self.pages - right_edge or (num >= self.page - left_current and num <= self.page + right_current):
                        if last + 1 != num:
                            yield None
                        yield num
                        last = num
        
        all_items = FakePagination(page_items, page, per_page, total)
    
    return render_template('admin/items.html', 
                          item_type=item_type, audit_status=audit_status,
                          lost_items=lost_items, found_items=found_items,
                          all_items=all_items if item_type == 'all' else None)


@admin_bp.route('/item/<item_type>/<int:id>/audit', methods=['POST'])
@admin_required
def audit_item(item_type, id):
    if item_type == 'lost':
        item = LostItem.query.get_or_404(id)
    else:
        item = FoundItem.query.get_or_404(id)
    
    action = request.json.get('action')
    reason = request.json.get('reason', '')
    
    if action == 'approve':
        item.audit_status = 'approved'
        item.audit_reason = None
        
        notification = Notification(
            user_id=item.user_id,
            title='物品审核通过',
            content=f'您发布的物品"{item.title}"已通过审核，现在可以在系统中展示。',
            notification_type='audit'
        )
        db.session.add(notification)
        
        from app.utils.matcher import MatchingEngine
        matcher = MatchingEngine()
        if item_type == 'lost':
            matcher.auto_match_lost_item(item)
        else:
            matcher.auto_match_found_item(item)
        
        db.session.commit()
        return jsonify({'success': True, 'message': '审核通过'})
    elif action == 'reject':
        item.audit_status = 'rejected'
        item.audit_reason = reason
        
        notification = Notification(
            user_id=item.user_id,
            title='物品审核未通过',
            content=f'您发布的物品"{item.title}"未通过审核。原因：{reason}',
            notification_type='audit'
        )
        db.session.add(notification)
        db.session.commit()
        return jsonify({'success': True, 'message': '已拒绝'})


@admin_bp.route('/item/<item_type>/<int:id>/delete', methods=['POST'])
@admin_required
def delete_item(item_type, id):
    if item_type == 'lost':
        item = LostItem.query.get_or_404(id)
    else:
        item = FoundItem.query.get_or_404(id)
    
    item.is_deleted = True
    db.session.commit()
    
    return jsonify({'success': True, 'message': '物品已删除'})


@admin_bp.route('/categories')
@admin_required
def categories():
    categories = Category.query.order_by(Category.sort_order).all()
    return render_template('admin/categories.html', categories=categories)


@admin_bp.route('/category/add', methods=['POST'])
@admin_required
def add_category():
    name = request.json.get('name')
    description = request.json.get('description', '')
    icon = request.json.get('icon', '')
    sort_order = request.json.get('sort_order', 0)
    
    if not name:
        return jsonify({'success': False, 'message': '分类名称不能为空'})
    
    existing = Category.query.filter_by(name=name).first()
    if existing:
        return jsonify({'success': False, 'message': '分类名称已存在'})
    
    category = Category(
        name=name,
        description=description,
        icon=icon,
        sort_order=sort_order
    )
    db.session.add(category)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '分类添加成功', 'id': category.id})


@admin_bp.route('/category/<int:id>/edit', methods=['POST'])
@admin_required
def edit_category(id):
    category = Category.query.get_or_404(id)
    
    name = request.json.get('name')
    description = request.json.get('description', '')
    icon = request.json.get('icon', '')
    sort_order = request.json.get('sort_order', 0)
    is_active = request.json.get('is_active', True)
    
    if name:
        existing = Category.query.filter(Category.name == name, Category.id != id).first()
        if existing:
            return jsonify({'success': False, 'message': '分类名称已存在'})
        category.name = name
    
    category.description = description
    category.icon = icon
    category.sort_order = sort_order
    category.is_active = is_active
    db.session.commit()
    
    return jsonify({'success': True, 'message': '分类修改成功'})


@admin_bp.route('/category/<int:id>/delete', methods=['POST'])
@admin_required
def delete_category(id):
    category = Category.query.get_or_404(id)
    
    lost_count = LostItem.query.filter_by(category_id=id).count()
    found_count = FoundItem.query.filter_by(category_id=id).count()
    
    if lost_count > 0 or found_count > 0:
        return jsonify({'success': False, 'message': f'该分类下有{lost_count + found_count}个物品，无法删除'})
    
    db.session.delete(category)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '分类已删除'})


@admin_bp.route('/matches')
@admin_required
def matches():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all')
    
    query = MatchRecord.query
    if status != 'all':
        query = query.filter_by(status=status)
    
    matches = query.order_by(MatchRecord.created_at.desc()).paginate(page=page, per_page=20)
    
    for match in matches.items:
        match.lost_item_info = LostItem.query.get(match.lost_item_id)
        match.found_item_info = FoundItem.query.get(match.found_item_id)
    
    return render_template('admin/matches.html', matches=matches, status=status)


@admin_bp.route('/match/config', methods=['GET', 'POST'])
@admin_required
def match_config():
    if request.method == 'POST':
        threshold = request.json.get('threshold', 0.5)
        text_weight = request.json.get('text_weight', 0.4)
        image_weight = request.json.get('image_weight', 0.3)
        category_weight = request.json.get('category_weight', 0.3)
        
        configs = {
            'match_threshold': str(threshold),
            'text_weight': str(text_weight),
            'image_weight': str(image_weight),
            'category_weight': str(category_weight)
        }
        
        for key, value in configs.items():
            config = SystemConfig.query.filter_by(config_key=key).first()
            if config:
                config.config_value = value
            else:
                config = SystemConfig(config_key=key, config_value=value)
                db.session.add(config)
        
        db.session.commit()
        return jsonify({'success': True, 'message': '配置已保存'})
    
    configs = {
        'match_threshold': 0.5,
        'text_weight': 0.4,
        'image_weight': 0.3,
        'category_weight': 0.3
    }
    for key in list(configs.keys()):
        config = SystemConfig.query.filter_by(config_key=key).first()
        if config:
            try:
                configs[key] = float(config.config_value)
            except (ValueError, TypeError):
                pass
    
    return render_template('admin/match_config.html', configs=configs)


@admin_bp.route('/match/rematch-all', methods=['POST'])
@admin_required
def rematch_all():
    from app.utils.matcher import MatchingEngine
    matcher = MatchingEngine()
    count = matcher.rematch_all()
    return jsonify({'success': True, 'message': f'重新匹配完成，共生成 {count} 条新匹配记录', 'count': count})


@admin_bp.route('/matches/export')
@admin_required
def export_matches():
    matches = MatchRecord.query.order_by(MatchRecord.created_at.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', '丢失物品ID', '拾获物品ID', '综合相似度', '文本相似度', '图片相似度', '状态', '创建时间'])
    
    for match in matches:
        writer.writerow([
            match.id,
            match.lost_item_id,
            match.found_item_id,
            f'{match.similarity_score*100:.1f}%',
            f'{match.text_similarity*100:.1f}%',
            f'{match.image_similarity*100:.1f}%',
            match.status,
            match.created_at.strftime('%Y-%m-%d %H:%M:%S') if match.created_at else ''
        ])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'matches_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )


@admin_bp.route('/reports')
@admin_required
def reports():
    page = request.args.get('page', 1, type=int)
    reports = Report.query.order_by(Report.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/reports.html', reports=reports)


@admin_bp.route('/report/<int:id>/handle', methods=['POST'])
@admin_required
def handle_report(id):
    report = Report.query.get_or_404(id)
    action = request.json.get('action')
    
    if action == 'approve':
        if report.item_type == 'lost':
            item = LostItem.query.get(report.item_id)
        else:
            item = FoundItem.query.get(report.item_id)
        
        if item:
            item.is_deleted = True
        
        report.status = 'resolved'
        db.session.commit()
        return jsonify({'success': True, 'message': '举报已处理，违规内容已删除'})
    
    elif action == 'reject':
        report.status = 'rejected'
        db.session.commit()
        return jsonify({'success': True, 'message': '举报已驳回'})


@admin_bp.route('/comments')
@admin_required
def comments():
    page = request.args.get('page', 1, type=int)
    comments = Comment.query.filter_by(is_deleted=False).order_by(Comment.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/comments.html', comments=comments)


@admin_bp.route('/comment/<int:id>/delete', methods=['POST'])
@admin_required
def delete_comment(id):
    comment = Comment.query.get_or_404(id)
    comment.is_deleted = True
    db.session.commit()
    return jsonify({'success': True, 'message': '评论已删除'})


@admin_bp.route('/forum')
@admin_required
def forum():
    page = request.args.get('page', 1, type=int)
    audit_status = request.args.get('audit', 'all')
    
    query = ForumPost.query
    if audit_status != 'all':
        query = query.filter_by(audit_status=audit_status)
    
    posts = query.order_by(ForumPost.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/forum.html', posts=posts, audit_status=audit_status)


@admin_bp.route('/forum/<int:id>/delete', methods=['POST'])
@admin_required
def delete_post(id):
    post = ForumPost.query.get_or_404(id)
    post.status = 'deleted'
    db.session.commit()
    return jsonify({'success': True, 'message': '帖子已删除'})


@admin_bp.route('/forum/<int:id>/toggle_pin', methods=['POST'])
@admin_required
def toggle_pin(id):
    post = ForumPost.query.get_or_404(id)
    post.is_pinned = not post.is_pinned
    db.session.commit()
    return jsonify({
        'success': True,
        'message': '已置顶' if post.is_pinned else '已取消置顶',
        'is_pinned': post.is_pinned
    })


@admin_bp.route('/forum/<int:id>/toggle_lock', methods=['POST'])
@admin_required
def toggle_lock(id):
    post = ForumPost.query.get_or_404(id)
    post.is_locked = not post.is_locked
    db.session.commit()
    return jsonify({
        'success': True,
        'message': '已锁定' if post.is_locked else '已解锁',
        'is_locked': post.is_locked
    })


@admin_bp.route('/forum/<int:id>/audit', methods=['POST'])
@admin_required
def audit_post(id):
    post = ForumPost.query.get_or_404(id)
    action = request.json.get('action')
    reason = request.json.get('reason', '')
    
    if action == 'approve':
        post.audit_status = 'approved'
        post.audit_reason = None
        notification = Notification(
            user_id=post.user_id,
            title='帖子审核通过',
            content=f'您的帖子"{post.title}"已通过审核。',
            notification_type='audit'
        )
        db.session.add(notification)
    elif action == 'reject':
        post.audit_status = 'rejected'
        post.audit_reason = reason
        notification = Notification(
            user_id=post.user_id,
            title='帖子审核未通过',
            content=f'您的帖子"{post.title}"未通过审核。原因：{reason}',
            notification_type='audit'
        )
        db.session.add(notification)
    
    db.session.commit()
    return jsonify({'success': True, 'message': '审核完成'})


@admin_bp.route('/forum-boards')
@admin_required
def forum_boards():
    boards = ForumBoard.query.order_by(ForumBoard.sort_order).all()
    return render_template('admin/forum_boards.html', boards=boards)


@admin_bp.route('/forum-board/add', methods=['POST'])
@admin_required
def add_forum_board():
    name = request.json.get('name')
    description = request.json.get('description', '')
    icon = request.json.get('icon', '')
    sort_order = request.json.get('sort_order', 0)
    
    if not name:
        return jsonify({'success': False, 'message': '板块名称不能为空'})
    
    board = ForumBoard(
        name=name,
        description=description,
        icon=icon,
        sort_order=sort_order
    )
    db.session.add(board)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '板块添加成功', 'id': board.id})


@admin_bp.route('/forum-board/<int:id>/edit', methods=['POST'])
@admin_required
def edit_forum_board(id):
    board = ForumBoard.query.get_or_404(id)
    
    board.name = request.json.get('name', board.name)
    board.description = request.json.get('description', board.description)
    board.icon = request.json.get('icon', board.icon)
    board.sort_order = request.json.get('sort_order', board.sort_order)
    board.is_active = request.json.get('is_active', board.is_active)
    
    db.session.commit()
    return jsonify({'success': True, 'message': '板块修改成功'})


@admin_bp.route('/forum-board/<int:id>/delete', methods=['POST'])
@admin_required
def delete_forum_board(id):
    board = ForumBoard.query.get_or_404(id)
    
    post_count = ForumPost.query.filter_by(board_id=id).count()
    if post_count > 0:
        return jsonify({'success': False, 'message': f'该板块下有{post_count}个帖子，无法删除'})
    
    db.session.delete(board)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '板块已删除'})


@admin_bp.route('/notifications')
@admin_required
def notifications():
    page = request.args.get('page', 1, type=int)
    notifications = Notification.query.order_by(Notification.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/notifications.html', notifications=notifications)


@admin_bp.route('/notification/send', methods=['POST'])
@admin_required
def send_notification():
    user_id = request.json.get('user_id')
    title = request.json.get('title')
    content = request.json.get('content', '')
    notification_type = request.json.get('type', 'system')
    
    if not title:
        return jsonify({'success': False, 'message': '标题不能为空'})
    
    if user_id == 'all':
        users = User.query.filter_by(is_active=True).all()
        for user in users:
            notification = Notification(
                user_id=user.id,
                title=title,
                content=content,
                notification_type=notification_type
            )
            db.session.add(notification)
    else:
        notification = Notification(
            user_id=user_id,
            title=title,
            content=content,
            notification_type=notification_type
        )
        db.session.add(notification)
    
    db.session.commit()
    return jsonify({'success': True, 'message': '通知发送成功'})


@admin_bp.route('/logs')
@admin_required
def logs():
    page = request.args.get('page', 1, type=int)
    action = request.args.get('action', '')
    user_id = request.args.get('user_id', type=int)
    
    query = UserLog.query
    if action:
        query = query.filter_by(action=action)
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    logs = query.order_by(UserLog.created_at.desc()).paginate(page=page, per_page=50)
    return render_template('admin/logs.html', logs=logs, action=action, user_id=user_id)


@admin_bp.route('/logs/export')
@admin_required
def export_logs():
    action = request.args.get('action', '')
    user_id = request.args.get('user_id', type=int)
    
    query = UserLog.query
    if action:
        query = query.filter_by(action=action)
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    logs = query.order_by(UserLog.created_at.desc()).limit(10000).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', '用户ID', '用户名', '操作', '详情', 'IP地址', '时间'])
    
    for log in logs:
        user = User.query.get(log.user_id) if log.user_id else None
        writer.writerow([
            log.id,
            log.user_id or '',
            user.username if user else '',
            log.action,
            log.detail or '',
            log.ip_address or '',
            log.created_at.strftime('%Y-%m-%d %H:%M:%S') if log.created_at else ''
        ])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )


@admin_bp.route('/logs/cleanup', methods=['POST'])
@admin_required
def cleanup_logs():
    days = request.json.get('days', 90)
    cutoff = datetime.now() - timedelta(days=days)
    deleted = UserLog.query.filter(UserLog.created_at < cutoff).delete()
    db.session.commit()
    return jsonify({'success': True, 'message': f'已删除{deleted}条过期日志'})


@admin_bp.route('/system-config', methods=['GET', 'POST'])
@admin_required
def system_config():
    if request.method == 'POST':
        configs = request.json
        for key, value in configs.items():
            config = SystemConfig.query.filter_by(config_key=key).first()
            if config:
                config.config_value = str(value)
            else:
                config = SystemConfig(config_key=key, config_value=str(value))
                db.session.add(config)
        db.session.commit()
        return jsonify({'success': True, 'message': '配置已保存'})
    
    configs = {}
    for config in SystemConfig.query.all():
        configs[config.config_key] = config.config_value
    
    return render_template('admin/system_config.html', configs=configs)


@admin_bp.route('/backup', methods=['GET', 'POST'])
@admin_required
def backup():
    if request.method == 'POST':
        action = request.json.get('action')
        
        if action == 'create':
            backup_dir = os.path.join(current_app.root_path, '..', 'backups')
            backup_dir = os.path.abspath(backup_dir)
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'backup_{timestamp}.db'
            backup_path = os.path.join(backup_dir, filename)
            
            db_path = os.path.join(current_app.root_path, '..', 'instance', 'lost_found.db')
            db_path = os.path.abspath(db_path)
            if os.path.exists(db_path):
                shutil.copy2(db_path, backup_path)
                file_size = os.path.getsize(backup_path)
                
                backup_record = SystemBackup(
                    filename=filename,
                    file_path=backup_path,
                    file_size=file_size,
                    backup_type='manual'
                )
                db.session.add(backup_record)
                db.session.commit()
                
                return jsonify({'success': True, 'message': '备份创建成功', 'filename': filename})
            else:
                return jsonify({'success': False, 'message': '数据库文件不存在'})
        
        elif action == 'restore':
            backup_id = request.json.get('backup_id')
            backup = SystemBackup.query.get_or_404(backup_id)
            
            bfp = backup.file_path
            if not os.path.isabs(bfp):
                bfp = os.path.abspath(os.path.join(current_app.root_path, '..', bfp))
            if os.path.exists(bfp):
                db_path = os.path.join(current_app.root_path, '..', 'instance', 'lost_found.db')
                db_path = os.path.abspath(db_path)
                shutil.copy2(bfp, db_path)
                return jsonify({'success': True, 'message': '数据库已恢复，请重启服务器'})
            else:
                return jsonify({'success': False, 'message': '备份文件不存在'})
        
        elif action == 'delete':
            backup_id = request.json.get('backup_id')
            backup = SystemBackup.query.get_or_404(backup_id)
            
            bfp = backup.file_path
            if not os.path.isabs(bfp):
                bfp = os.path.abspath(os.path.join(current_app.root_path, '..', bfp))
            if os.path.exists(bfp):
                os.remove(bfp)
            db.session.delete(backup)
            db.session.commit()
            
            return jsonify({'success': True, 'message': '备份已删除'})
    
    backups = SystemBackup.query.order_by(SystemBackup.created_at.desc()).all()
    return render_template('admin/backup.html', backups=backups)


@admin_bp.route('/backup/download/<int:id>')
@admin_required
def download_backup(id):
    backup = SystemBackup.query.get_or_404(id)
    file_path = backup.file_path
    if not os.path.isabs(file_path):
        file_path = os.path.abspath(os.path.join(current_app.root_path, '..', file_path))
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=backup.filename)
    else:
        flash('备份文件不存在', 'danger')
        return redirect(url_for('admin.backup'))


@admin_bp.route('/statistics')
@admin_required
def statistics():
    period = request.args.get('period', 'week')
    
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    if period == 'week':
        start_date = today - timedelta(days=7)
    elif period == 'month':
        start_date = today - timedelta(days=30)
    elif period == 'year':
        start_date = today - timedelta(days=365)
    else:
        start_date = today - timedelta(days=7)
    
    stats = {
        'new_users': User.query.filter(User.created_at >= start_date).count(),
        'new_lost': LostItem.query.filter(LostItem.created_at >= start_date, LostItem.is_deleted == False).count(),
        'new_found': FoundItem.query.filter(FoundItem.created_at >= start_date, FoundItem.is_deleted == False).count(),
        'new_matches': MatchRecord.query.filter(MatchRecord.created_at >= start_date).count(),
        'confirmed_matches': MatchRecord.query.filter(MatchRecord.created_at >= start_date, MatchRecord.status == 'confirmed').count(),
        'new_posts': ForumPost.query.filter(ForumPost.created_at >= start_date).count(),
    }
    
    match_success_rate = 0
    total_matches = MatchRecord.query.filter(MatchRecord.created_at >= start_date).count()
    if total_matches > 0:
        confirmed = MatchRecord.query.filter(MatchRecord.created_at >= start_date, MatchRecord.status == 'confirmed').count()
        match_success_rate = round(confirmed / total_matches * 100, 1)
    
    daily_stats = []
    for i in range(7):
        date = today - timedelta(days=6-i)
        day_end = date + timedelta(days=1)
        
        daily_stats.append({
            'date': date.strftime('%m-%d'),
            'users': User.query.filter(User.created_at >= date, User.created_at < day_end).count(),
            'lost': LostItem.query.filter(LostItem.created_at >= date, LostItem.created_at < day_end).count(),
            'found': FoundItem.query.filter(FoundItem.created_at >= date, FoundItem.created_at < day_end).count(),
            'matches': MatchRecord.query.filter(MatchRecord.created_at >= date, MatchRecord.created_at < day_end).count(),
        })
    
    return render_template('admin/statistics.html', 
                          stats=stats, 
                          period=period,
                          match_success_rate=match_success_rate,
                          daily_stats=daily_stats)


@admin_bp.route('/online-users')
@admin_required
def online_users():
    threshold = datetime.now() - timedelta(minutes=30)
    online_user_ids = UserLog.query.filter(
        UserLog.action == 'login',
        UserLog.created_at >= threshold
    ).with_entities(UserLog.user_id).distinct().all()
    
    online_users = []
    for user_id in online_user_ids:
        user = User.query.get(user_id)
        if user:
            last_action = UserLog.query.filter_by(user_id=user.id).order_by(UserLog.created_at.desc()).first()
            online_users.append({
                'user': user,
                'last_action': last_action.created_at if last_action else None
            })
    
    return render_template('admin/online_users.html', online_users=online_users)

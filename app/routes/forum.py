from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.models import ForumPost, ForumReply, PostLike, User, Notification, PostCollection, ForumBoard
from datetime import datetime

forum_bp = Blueprint('forum', __name__)


@forum_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    board_id = request.args.get('board', type=int)
    sort = request.args.get('sort', 'latest')
    
    query = ForumPost.query.filter_by(status='active', audit_status='approved')
    if category:
        query = query.filter_by(category=category)
    if board_id:
        query = query.filter_by(board_id=board_id)
    
    if sort == 'hot':
        query = query.order_by(ForumPost.like_count.desc(), ForumPost.views.desc())
    else:
        query = query.order_by(ForumPost.is_pinned.desc(), ForumPost.created_at.desc())
    
    posts = query.paginate(page=page, per_page=15)
    
    categories = ['综合讨论', '寻物经验', '防骗指南', '感谢信', '其他']
    boards = ForumBoard.query.filter_by(is_active=True).order_by(ForumBoard.sort_order).all()
    
    hot_posts = ForumPost.query.filter_by(status='active', audit_status='approved')\
        .order_by(ForumPost.like_count.desc(), ForumPost.views.desc())\
        .limit(5).all()
    
    stats = {
        'total_posts': ForumPost.query.filter_by(status='active', audit_status='approved').count(),
        'total_replies': ForumReply.query.filter_by(status='active').count(),
        'today_posts': ForumPost.query.filter(
            ForumPost.status == 'active',
            ForumPost.audit_status == 'approved',
            ForumPost.created_at >= datetime.now().replace(hour=0, minute=0, second=0)
        ).count()
    }
    
    return render_template('forum/index.html', posts=posts, categories=categories, boards=boards,
                          current_category=category, stats=stats, hot_posts=hot_posts, sort=sort)


@forum_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if not current_user.can_publish():
        flash('您的信用分过低，暂时无法发帖', 'danger')
        return redirect(url_for('forum.index'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category = request.form.get('category', '综合讨论')
        board_id = request.form.get('board_id', type=int)
        
        if not title or not content:
            flash('请填写完整信息', 'danger')
            return redirect(url_for('forum.create'))
        
        post = ForumPost(
            user_id=current_user.id,
            title=title,
            content=content,
            category=category,
            board_id=board_id,
            audit_status='pending'
        )
        db.session.add(post)
        db.session.commit()
        
        flash('发帖成功，等待审核！', 'success')
        return redirect(url_for('forum.index'))
    
    categories = ['综合讨论', '寻物经验', '防骗指南', '感谢信', '其他']
    boards = ForumBoard.query.filter_by(is_active=True).order_by(ForumBoard.sort_order).all()
    return render_template('forum/create.html', categories=categories, boards=boards)


@forum_bp.route('/<int:id>')
def detail(id):
    post = ForumPost.query.get_or_404(id)
    
    if post.status != 'active':
        flash('该帖子已被删除', 'warning')
        return redirect(url_for('forum.index'))
    
    if post.audit_status != 'approved' and (not current_user.is_authenticated or 
        (current_user.id != post.user_id and not current_user.is_admin)):
        flash('该帖子正在审核中', 'warning')
        return redirect(url_for('forum.index'))
    
    post.views += 1
    db.session.commit()
    
    page = request.args.get('page', 1, type=int)
    replies = ForumReply.query.filter_by(post_id=id, status='active', audit_status='approved')\
        .order_by(ForumReply.created_at.asc())\
        .paginate(page=page, per_page=20)
    
    is_liked = False
    is_collected = False
    if current_user.is_authenticated:
        is_liked = PostLike.query.filter_by(post_id=id, user_id=current_user.id).first() is not None
        is_collected = PostCollection.query.filter_by(post_id=id, user_id=current_user.id).first() is not None
    
    return render_template('forum/detail.html', post=post, replies=replies, 
                          is_liked=is_liked, is_collected=is_collected)


@forum_bp.route('/<int:id>/reply', methods=['POST'])
@login_required
def reply(id):
    post = ForumPost.query.get_or_404(id)
    
    if post.is_locked:
        flash('该帖子已被锁定，无法回复', 'warning')
        return redirect(url_for('forum.detail', id=id))
    
    if post.status != 'active':
        flash('该帖子已被删除', 'warning')
        return redirect(url_for('forum.index'))
    
    content = request.form.get('content')
    if not content:
        flash('请输入回复内容', 'danger')
        return redirect(url_for('forum.detail', id=id))
    
    reply = ForumReply(
        post_id=id,
        user_id=current_user.id,
        content=content,
        audit_status='approved'
    )
    db.session.add(reply)
    
    if post.user_id != current_user.id:
        notification = Notification(
            user_id=post.user_id,
            title=f'您的帖子有新回复',
            content=f'用户 {current_user.username} 回复了您的帖子《{post.title}》',
            notification_type='reply',
            related_id=post.id
        )
        db.session.add(notification)
    
    db.session.commit()
    
    flash('回复成功！', 'success')
    return redirect(url_for('forum.detail', id=id))


@forum_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    post = ForumPost.query.get_or_404(id)
    
    if post.user_id != current_user.id and not current_user.is_admin:
        flash('没有权限删除此帖子', 'danger')
        return redirect(url_for('forum.detail', id=id))
    
    post.status = 'deleted'
    db.session.commit()
    
    flash('帖子已删除', 'success')
    return redirect(url_for('forum.index'))


@forum_bp.route('/<int:id>/like', methods=['POST'])
@login_required
def toggle_like(id):
    post = ForumPost.query.get_or_404(id)
    
    if post.status != 'active':
        return jsonify({'success': False, 'message': '帖子不存在'})
    
    existing_like = PostLike.query.filter_by(post_id=id, user_id=current_user.id).first()
    
    if existing_like:
        db.session.delete(existing_like)
        post.like_count = max(0, post.like_count - 1)
        db.session.commit()
        return jsonify({
            'success': True,
            'liked': False,
            'like_count': post.like_count,
            'message': '已取消点赞'
        })
    else:
        like = PostLike(post_id=id, user_id=current_user.id)
        db.session.add(like)
        post.like_count += 1
        
        if post.user_id != current_user.id:
            notification = Notification(
                user_id=post.user_id,
                title=f'有人赞了您的帖子',
                content=f'用户 {current_user.username} 赞了您的帖子《{post.title}》',
                notification_type='like',
                related_id=post.id
            )
            db.session.add(notification)
        
        db.session.commit()
        return jsonify({
            'success': True,
            'liked': True,
            'like_count': post.like_count,
            'message': '点赞成功'
        })


@forum_bp.route('/<int:id>/collect', methods=['POST'])
@login_required
def toggle_collect(id):
    post = ForumPost.query.get_or_404(id)
    
    if post.status != 'active':
        return jsonify({'success': False, 'message': '帖子不存在'})
    
    existing = PostCollection.query.filter_by(post_id=id, user_id=current_user.id).first()
    
    if existing:
        db.session.delete(existing)
        post.collect_count = max(0, post.collect_count - 1)
        db.session.commit()
        return jsonify({
            'success': True,
            'collected': False,
            'collect_count': post.collect_count,
            'message': '已取消收藏'
        })
    else:
        collection = PostCollection(post_id=id, user_id=current_user.id)
        db.session.add(collection)
        post.collect_count += 1
        db.session.commit()
        return jsonify({
            'success': True,
            'collected': True,
            'collect_count': post.collect_count,
            'message': '收藏成功'
        })


@forum_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    post = ForumPost.query.get_or_404(id)
    
    if post.user_id != current_user.id and not current_user.is_admin:
        flash('没有权限编辑此帖子', 'danger')
        return redirect(url_for('forum.detail', id=id))
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category = request.form.get('category', '综合讨论')
        
        if not title or not content:
            flash('请填写完整信息', 'danger')
            return redirect(url_for('forum.edit', id=id))
        
        post.title = title
        post.content = content
        post.category = category
        post.updated_at = datetime.now()
        db.session.commit()
        
        flash('帖子已更新', 'success')
        return redirect(url_for('forum.detail', id=id))
    
    categories = ['综合讨论', '寻物经验', '防骗指南', '感谢信', '其他']
    return render_template('forum/edit.html', post=post, categories=categories)


@forum_bp.route('/my-posts')
@login_required
def my_posts():
    page = request.args.get('page', 1, type=int)
    posts = ForumPost.query.filter_by(user_id=current_user.id)\
        .order_by(ForumPost.created_at.desc())\
        .paginate(page=page, per_page=15)
    
    return render_template('forum/my_posts.html', posts=posts)


@forum_bp.route('/my-collections')
@login_required
def my_collections():
    page = request.args.get('page', 1, type=int)
    collections = PostCollection.query.filter_by(user_id=current_user.id)\
        .order_by(PostCollection.created_at.desc())\
        .paginate(page=page, per_page=15)
    
    return render_template('forum/my_collections.html', collections=collections)


@forum_bp.route('/reply/<int:id>/delete', methods=['POST'])
@login_required
def delete_reply(id):
    reply = ForumReply.query.get_or_404(id)
    
    if reply.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'success': False, 'message': '没有权限删除此回复'})
    
    reply.status = 'deleted'
    db.session.commit()
    
    return jsonify({'success': True, 'message': '回复已删除'})

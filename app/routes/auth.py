from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import db, login_manager
from app.models.models import User, UserLog, Notification, PasswordReset, CreditRecord
from app.forms.forms import LoginForm, RegisterForm
from werkzeug.utils import secure_filename
import os
import re
import secrets
from datetime import datetime, timedelta
from functools import wraps

auth_bp = Blueprint('auth', __name__)

verification_codes = {}


@auth_bp.route('/send-code', methods=['POST'])
def send_verification_code():
    data = request.get_json()
    code_type = data.get('type')
    target = data.get('target', '').strip()
    
    if not target:
        return jsonify({'success': False, 'message': '请填写目标地址'})
    
    if code_type == 'email':
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', target):
            return jsonify({'success': False, 'message': '邮箱格式不正确'})
        existing = User.query.filter_by(email=target).first()
        if existing:
            return jsonify({'success': False, 'message': '该邮箱已被注册'})
    elif code_type == 'phone':
        if not re.match(r'^1[3-9]\d{9}$', target):
            return jsonify({'success': False, 'message': '手机号格式不正确'})
        existing = User.query.filter_by(phone=target).first()
        if existing:
            return jsonify({'success': False, 'message': '该手机号已被注册'})
    
    code = str(secrets.randbelow(900000) + 100000)
    key = f"{code_type}:{target}"
    verification_codes[key] = {
        'code': code,
        'expires': datetime.now() + timedelta(minutes=5)
    }
    
    return jsonify({'success': True, 'code': code, 'message': '验证码已发送'})


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        email_code = request.form.get('email_code', '').strip()
        phone_code = request.form.get('phone_code', '').strip()
        
        email_key = f"email:{form.email.data}"
        phone_key = f"phone:{form.phone.data}" if form.phone.data else None
        
        if email_key not in verification_codes:
            flash('请先获取邮箱验证码', 'danger')
            return redirect(url_for('auth.register'))
        
        stored_email = verification_codes[email_key]
        if stored_email['expires'] < datetime.now() or stored_email['code'] != email_code:
            flash('邮箱验证码错误或已过期', 'danger')
            return redirect(url_for('auth.register'))
        
        if phone_key and phone_key in verification_codes:
            stored_phone = verification_codes[phone_key]
            if stored_phone['expires'] < datetime.now() or stored_phone['code'] != phone_code:
                flash('手机验证码错误或已过期', 'danger')
                return redirect(url_for('auth.register'))
        
        existing_user = User.query.filter(
            (User.username == form.username.data) | 
            (User.email == form.email.data) |
            (User.phone == form.phone.data)
        ).first()
        
        if existing_user:
            if existing_user.username == form.username.data:
                flash('用户名已被使用', 'danger')
            elif existing_user.email == form.email.data:
                flash('邮箱已被使用', 'danger')
            else:
                flash('手机号已被使用', 'danger')
            return redirect(url_for('auth.register'))
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            real_name=form.real_name.data,
            phone=form.phone.data,
            credit_score=100,
            is_active=True,
            is_admin=False
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        log = UserLog(
            user_id=user.id,
            action='register',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db.session.add(log)
        db.session.commit()
        
        flash('注册成功，请登录！', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        login_input = form.username.data
        password = form.password.data
        remember = request.form.get('remember') == 'on'
        
        user = User.query.filter(
            (User.username == login_input) | 
            (User.email == login_input) |
            (User.phone == login_input)
        ).first()
        
        if user is None:
            flash('用户名/邮箱/手机号或密码错误', 'danger')
            return redirect(url_for('auth.login'))
        
        if user.is_locked():
            remaining = (user.locked_until - datetime.now()).seconds // 60
            flash(f'账号已被锁定，请{remaining}分钟后再试', 'danger')
            return redirect(url_for('auth.login'))
        
        if not user.check_password(password):
            user.add_login_fail()
            db.session.commit()
            remaining = 5 - user.login_fail_count
            if remaining > 0:
                flash(f'密码错误，还剩{remaining}次机会', 'danger')
            else:
                flash('连续5次密码错误，账号已锁定1小时', 'danger')
            return redirect(url_for('auth.login'))
        
        if not user.is_active:
            flash('您的账号已被禁用', 'danger')
            return redirect(url_for('auth.login'))
        
        user.reset_login_fail()
        login_user(user, remember=remember)
        
        log = UserLog(
            user_id=user.id,
            action='login',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db.session.add(log)
        db.session.commit()
        
        next_page = request.args.get('next')
        flash('登录成功！', 'success')
        return redirect(next_page or url_for('main.index'))
    
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    log = UserLog(
        user_id=current_user.id,
        action='logout',
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    db.session.add(log)
    db.session.commit()
    
    logout_user()
    flash('已退出登录', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            PasswordReset.query.filter_by(email=email, used=False).update({'used': True})
            
            token = secrets.token_urlsafe(32)
            reset = PasswordReset(email=email, token=token)
            db.session.add(reset)
            db.session.commit()
            
            reset_link = url_for('auth.reset_password', token=token, _external=True)
            try:
                from app.utils.email_service import email_service
                email_service.send_password_reset(email, reset_link)
                flash('密码重置链接已发送到您的邮箱，请查收', 'success')
            except Exception as e:
                flash(f'邮件发送失败，请联系管理员。重置链接: {reset_link}', 'warning')
        else:
            flash('该邮箱未注册', 'danger')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    reset = PasswordReset.query.filter_by(token=token, used=False).first()
    
    if not reset or not reset.is_valid():
        flash('重置链接无效或已过期', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('两次输入的密码不一致', 'danger')
            return redirect(url_for('auth.reset_password', token=token))
        
        if len(password) < 6:
            flash('密码长度至少6位', 'danger')
            return redirect(url_for('auth.reset_password', token=token))
        
        user = User.query.filter_by(email=reset.email).first()
        if user:
            user.set_password(password)
            reset.used = True
            db.session.commit()
            flash('密码已重置，请登录', 'success')
            return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', token=token)


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not old_password or not new_password or not confirm_password:
            flash('请填写所有字段', 'danger')
            return redirect(url_for('auth.change_password'))
        
        if not current_user.check_password(old_password):
            flash('原密码错误', 'danger')
            return redirect(url_for('auth.change_password'))
        
        if new_password != confirm_password:
            flash('两次输入的新密码不一致', 'danger')
            return redirect(url_for('auth.change_password'))
        
        if len(new_password) < 6:
            flash('新密码长度至少6位', 'danger')
            return redirect(url_for('auth.change_password'))
        
        current_user.set_password(new_password)
        
        log = UserLog(
            user_id=current_user.id,
            action='change_password',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db.session.add(log)
        db.session.commit()
        
        flash('密码修改成功', 'success')
        return redirect(url_for('auth.change_password'))
    
    return render_template('auth/change_password.html')


@auth_bp.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        real_name = request.form.get('real_name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        
        if email and email != current_user.email:
            existing = User.query.filter_by(email=email).first()
            if existing:
                flash('该邮箱已被使用', 'danger')
                return redirect(url_for('auth.edit_profile'))
            current_user.email = email
        
        if phone and phone != current_user.phone:
            existing = User.query.filter_by(phone=phone).first()
            if existing:
                flash('该手机号已被使用', 'danger')
                return redirect(url_for('auth.edit_profile'))
            current_user.phone = phone
        
        current_user.real_name = real_name
        
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and file.filename:
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                filename = secure_filename(file.filename)
                ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                
                if ext in allowed_extensions:
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    new_filename = f"avatar_{current_user.id}_{timestamp}.{ext}"
                    upload_path = os.path.join('app', 'static', 'uploads', 'avatars')
                    os.makedirs(upload_path, exist_ok=True)
                    file.save(os.path.join(upload_path, new_filename))
                    current_user.avatar = f"uploads/avatars/{new_filename}"
                else:
                    flash('头像格式不支持，仅支持png/jpg/jpeg/gif', 'warning')
        
        log = UserLog(
            user_id=current_user.id,
            action='edit_profile',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db.session.add(log)
        db.session.commit()
        
        flash('个人信息已更新', 'success')
        return redirect(url_for('auth.edit_profile'))
    
    return render_template('auth/edit_profile.html')


@auth_bp.route('/notifications')
@login_required
def notifications():
    page = request.args.get('page', 1, type=int)
    notifications = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc())\
        .paginate(page=page, per_page=20)
    
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    
    return render_template('auth/notifications.html', 
                          notifications=notifications, 
                          unread_count=unread_count)


@auth_bp.route('/notification/<int:id>/read', methods=['POST'])
@login_required
def mark_notification_read(id):
    notification = Notification.query.get_or_404(id)
    
    if notification.user_id != current_user.id:
        return jsonify({'success': False, 'message': '无权操作'})
    
    notification.is_read = True
    db.session.commit()
    
    return jsonify({'success': True})


@auth_bp.route('/notifications/read-all', methods=['POST'])
@login_required
def mark_all_notifications_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False)\
        .update({'is_read': True})
    db.session.commit()
    
    return jsonify({'success': True, 'message': '全部已读'})


@auth_bp.route('/notification/count')
@login_required
def notification_count():
    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({'count': count})


@auth_bp.route('/credit-records')
@login_required
def credit_records():
    page = request.args.get('page', 1, type=int)
    records = CreditRecord.query.filter_by(user_id=current_user.id)\
        .order_by(CreditRecord.created_at.desc())\
        .paginate(page=page, per_page=20)
    
    return render_template('auth/credit_records.html', records=records)

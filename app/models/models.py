from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(256), nullable=False)
    real_name = db.Column(db.String(50))
    avatar = db.Column(db.String(255), default='default_avatar.png')
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    credit_score = db.Column(db.Integer, default=100)
    login_fail_count = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    remember_token = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    lost_items = db.relationship('LostItem', backref='owner', lazy='dynamic')
    found_items = db.relationship('FoundItem', backref='finder', lazy='dynamic')
    favorites = db.relationship('Favorite', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    posts = db.relationship('ForumPost', backref='author', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    credit_records = db.relationship('CreditRecord', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    collections = db.relationship('PostCollection', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def add_credit(self, points, reason=''):
        old_score = self.credit_score
        self.credit_score = min(100, self.credit_score + points)
        if self.credit_score != old_score:
            record = CreditRecord(
                user_id=self.id,
                change=points,
                reason=reason,
                old_score=old_score,
                new_score=self.credit_score
            )
            db.session.add(record)
    
    def deduct_credit(self, points, reason=''):
        old_score = self.credit_score
        self.credit_score = max(0, self.credit_score - points)
        if self.credit_score != old_score:
            record = CreditRecord(
                user_id=self.id,
                change=-points,
                reason=reason,
                old_score=old_score,
                new_score=self.credit_score
            )
            db.session.add(record)
    
    def can_publish(self):
        return self.credit_score >= 30
    
    def is_locked(self):
        if self.locked_until and self.locked_until > datetime.now():
            return True
        return False
    
    def reset_login_fail(self):
        self.login_fail_count = 0
        self.locked_until = None
    
    def add_login_fail(self):
        self.login_fail_count += 1
        if self.login_fail_count >= 5:
            from datetime import timedelta
            self.locked_until = datetime.now() + timedelta(hours=1)


class CreditRecord(db.Model):
    __tablename__ = 'credit_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    change = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(200))
    old_score = db.Column(db.Integer)
    new_score = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.now)


class PasswordReset(db.Model):
    __tablename__ = 'password_resets'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    token = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    used = db.Column(db.Boolean, default=False)
    
    def is_valid(self):
        from datetime import timedelta
        return not self.used and self.created_at > datetime.now() - timedelta(hours=1)


class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    icon = db.Column(db.String(50))
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    lost_items = db.relationship('LostItem', backref='category', lazy='dynamic')
    found_items = db.relationship('FoundItem', backref='category', lazy='dynamic')


class LostItem(db.Model):
    __tablename__ = 'lost_items'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    location = db.Column(db.String(200))
    lost_time = db.Column(db.DateTime)
    image_path = db.Column(db.String(255))
    image_paths = db.Column(db.Text)
    image_hash = db.Column(db.String(64))
    status = db.Column(db.String(20), default='open')
    status_note = db.Column(db.String(200))
    audit_status = db.Column(db.String(20), default='pending')
    audit_reason = db.Column(db.String(200))
    contact_info = db.Column(db.String(200))
    is_deleted = db.Column(db.Boolean, default=False)
    view_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    matches = db.relationship('MatchRecord', backref='lost_item', lazy='dynamic',
                              foreign_keys='MatchRecord.lost_item_id')
    comments = db.relationship('Comment', backref='lost_item', lazy='dynamic',
                               foreign_keys='Comment.item_id',
                               primaryjoin="and_(Comment.item_id==LostItem.id, Comment.item_type=='lost')",
                               overlaps="found_item")


class FoundItem(db.Model):
    __tablename__ = 'found_items'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    location = db.Column(db.String(200))
    found_time = db.Column(db.DateTime)
    image_path = db.Column(db.String(255))
    image_paths = db.Column(db.Text)
    image_hash = db.Column(db.String(64))
    status = db.Column(db.String(20), default='open')
    status_note = db.Column(db.String(200))
    audit_status = db.Column(db.String(20), default='pending')
    audit_reason = db.Column(db.String(200))
    contact_info = db.Column(db.String(200))
    is_deleted = db.Column(db.Boolean, default=False)
    view_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    matches = db.relationship('MatchRecord', backref='found_item', lazy='dynamic',
                              foreign_keys='MatchRecord.found_item_id')
    comments = db.relationship('Comment', backref='found_item', lazy='dynamic',
                               foreign_keys='Comment.item_id',
                               primaryjoin="and_(Comment.item_id==FoundItem.id, Comment.item_type=='found')",
                               overlaps="lost_item")


class MatchRecord(db.Model):
    __tablename__ = 'match_records'
    
    id = db.Column(db.Integer, primary_key=True)
    lost_item_id = db.Column(db.Integer, db.ForeignKey('lost_items.id'))
    found_item_id = db.Column(db.Integer, db.ForeignKey('found_items.id'))
    similarity_score = db.Column(db.Float, default=0.0)
    text_similarity = db.Column(db.Float, default=0.0)
    image_similarity = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='pending')
    lost_confirmed = db.Column(db.Boolean, default=False)
    found_confirmed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    expires_at = db.Column(db.DateTime)


class Favorite(db.Model):
    __tablename__ = 'favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    item_type = db.Column(db.String(10), nullable=False)
    item_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'item_type', 'item_id', name='unique_favorite'),
    )


class Comment(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    item_type = db.Column(db.String(10), nullable=False)
    item_id = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    audit_status = db.Column(db.String(20), default='approved')
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    user = db.relationship('User', backref='comments')


class Report(db.Model):
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    item_type = db.Column(db.String(10), nullable=False)
    item_id = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    user = db.relationship('User', backref='reports')


class ForumBoard(db.Model):
    __tablename__ = 'forum_boards'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    icon = db.Column(db.String(50))
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)


class ForumPost(db.Model):
    __tablename__ = 'forum_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default='综合讨论')
    board_id = db.Column(db.Integer, db.ForeignKey('forum_boards.id'))
    views = db.Column(db.Integer, default=0)
    like_count = db.Column(db.Integer, default=0)
    collect_count = db.Column(db.Integer, default=0)
    is_pinned = db.Column(db.Boolean, default=False)
    is_locked = db.Column(db.Boolean, default=False)
    audit_status = db.Column(db.String(20), default='pending')
    audit_reason = db.Column(db.String(200))
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    replies = db.relationship('ForumReply', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    likes = db.relationship('PostLike', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    collections = db.relationship('PostCollection', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    board = db.relationship('ForumBoard', backref='posts')


class ForumReply(db.Model):
    __tablename__ = 'forum_replies'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    audit_status = db.Column(db.String(20), default='approved')
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    user = db.relationship('User', backref='replies')


class PostLike(db.Model):
    __tablename__ = 'post_likes'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    __table_args__ = (
        db.UniqueConstraint('post_id', 'user_id', name='unique_post_like'),
    )


class PostCollection(db.Model):
    __tablename__ = 'post_collections'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    __table_args__ = (
        db.UniqueConstraint('post_id', 'user_id', name='unique_post_collection'),
    )


class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    notification_type = db.Column(db.String(20), default='system')
    related_id = db.Column(db.Integer)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)


class SystemConfig(db.Model):
    __tablename__ = 'system_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    config_key = db.Column(db.String(50), unique=True, nullable=False)
    config_value = db.Column(db.String(500))
    description = db.Column(db.String(200))
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class UserLog(db.Model):
    __tablename__ = 'user_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(50), nullable=False)
    detail = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    user = db.relationship('User', backref='logs')


class SystemBackup(db.Model):
    __tablename__ = 'system_backups'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    backup_type = db.Column(db.String(20), default='manual')
    status = db.Column(db.String(20), default='completed')
    created_at = db.Column(db.DateTime, default=datetime.now)


class SystemStats(db.Model):
    __tablename__ = 'system_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    new_users = db.Column(db.Integer, default=0)
    new_lost_items = db.Column(db.Integer, default=0)
    new_found_items = db.Column(db.Integer, default=0)
    new_matches = db.Column(db.Integer, default=0)
    confirmed_matches = db.Column(db.Integer, default=0)
    new_posts = db.Column(db.Integer, default=0)
    new_replies = db.Column(db.Integer, default=0)
    active_users = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)


class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('match_records.id'))
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')
    match = db.relationship('MatchRecord', backref='messages')

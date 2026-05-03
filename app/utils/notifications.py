from flask import Blueprint, render_template
from flask_login import login_required, current_user
from flask_socketio import emit, join_room, leave_room
from app import db
from app.models.models import MatchRecord

socketio_bp = Blueprint('socketio', __name__)


def init_socketio(socketio):
    
    @socketio.on('connect')
    def handle_connect():
        from flask_login import current_user
        if current_user.is_authenticated:
            join_room(f'user_{current_user.id}')
            emit('connected', {'message': '连接成功'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        from flask_login import current_user
        if current_user.is_authenticated:
            leave_room(f'user_{current_user.id}')
    
    @socketio.on('join_room')
    def on_join(data):
        room = data.get('room')
        if room:
            join_room(room)
    
    @socketio.on('leave_room')
    def on_leave(data):
        room = data.get('room')
        if room:
            leave_room(room)


def notify_match(socketio, user_id, match_data):
    if socketio:
        socketio.emit('new_match', match_data, room=f'user_{user_id}')


def notify_match_confirmed(socketio, user_id, match_data):
    if socketio:
        socketio.emit('match_confirmed', match_data, room=f'user_{user_id}')


def notify_item_closed(socketio, user_id, item_data):
    if socketio:
        socketio.emit('item_closed', item_data, room=f'user_{user_id}')

# app/events.py
from flask_socketio import join_room

def setup_events(socketio):
    @socketio.on('join')
    def on_join(data):
        room = data.get('room')
        if room:
            join_room(room)
            print(f"Cliente entrou na sala: {room}")
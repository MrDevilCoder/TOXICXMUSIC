import json
import os
from datetime import datetime

class Database:
    def __init__(self, file_path='data/bot_data.json'):
        self.file_path = file_path
        self.data = self.load_data()
    
    def load_data(self):
        """Load data from JSON file"""
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as f:
                return json.load(f)
        return {
            'users': {},
            'playlists': {},
            'settings': {},
            'premium_users': {},
            'custom_stickers': {}
        }
    
    def save_data(self):
        """Save data to JSON file"""
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def add_user(self, user_id, username, first_name):
        """Add or update user"""
        user_id = str(user_id)
        if user_id not in self.data['users']:
            self.data['users'][user_id] = {
                'username': username,
                'first_name': first_name,
                'joined_date': datetime.now().isoformat(),
                'songs_played': 0,
                'playlists': []
            }
        self.save_data()
    
    def increment_songs_played(self, user_id):
        """Increment songs played counter"""
        user_id = str(user_id)
        if user_id in self.data['users']:
            self.data['users'][user_id]['songs_played'] += 1
            self.save_data()
    
    def get_user_stats(self, user_id):
        """Get user statistics"""
        user_id = str(user_id)
        return self.data['users'].get(user_id, {})
    
    def create_playlist(self, user_id, name):
        """Create a playlist"""
        user_id = str(user_id)
        playlist_id = f"pl_{len(self.data['playlists']) + 1}"
        
        self.data['playlists'][playlist_id] = {
            'name': name,
            'owner': user_id,
            'songs': [],
            'created': datetime.now().isoformat()
        }
        
        if user_id in self.data['users']:
            self.data['users'][user_id]['playlists'].append(playlist_id)
        
        self.save_data()
        return playlist_id
    
    def add_to_playlist(self, playlist_id, song_info):
        """Add song to playlist"""
        if playlist_id in self.data['playlists']:
            self.data['playlists'][playlist_id]['songs'].append(song_info)
            self.save_data()
            return True
        return False

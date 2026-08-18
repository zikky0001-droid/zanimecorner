"""
DEV ZIKKY TELEGRAM - JSON Database Operations
"""

import json
import os
import time
from pathlib import Path

from config import Config

class Database:
    """JSON database handler"""
    
    def __init__(self):
        self.db_path = Path(Config.DATABASE_PATH)
        self.db_path.mkdir(parents=True, exist_ok=True)
        self._cache = {}
        
        # Create default database files
        self._init_databases()
    
    def _init_databases(self):
        """Initialize all database files if they don't exist"""
        default_files = ['groups', 'users', 'warnings', 'store']
        for name in default_files:
            file_path = self._get_file_path(name)
            if not file_path.exists():
                with open(file_path, 'w') as f:
                    json.dump({}, f, indent=2)
    
    def _get_file_path(self, name):
        """Get full file path"""
        return self.db_path / f'{name}.json'
    
    def _load_db(self, name):
        """Load database file"""
        file_path = self._get_file_path(name)
        if name in self._cache:
            return self._cache[name]
        
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._cache[name] = data
                    return data
            except Exception as e:
                print(f"⚠️ Error loading {name}.json: {e}")
        
        data = {}
        self._save_db(name, data)
        return data
    
    def _save_db(self, name, data):
        """Save database file"""
        file_path = self._get_file_path(name)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self._cache[name] = data
        except Exception as e:
            print(f"❌ Error saving {name}.json: {e}")
    
    # ============================================
    # GROUP SETTINGS
    # ============================================
    
    def get_group_settings(self, group_id):
        """Get settings for a group"""
        groups = self._load_db('groups')
        group_id = str(group_id)
        if group_id not in groups:
            groups[group_id] = Config.DEFAULT_GROUP_SETTINGS.copy()
            self._save_db('groups', groups)
        return groups[group_id]
    
    def update_group_settings(self, group_id, settings):
        """Update group settings"""
        groups = self._load_db('groups')
        group_id = str(group_id)
        if group_id not in groups:
            groups[group_id] = Config.DEFAULT_GROUP_SETTINGS.copy()
        groups[group_id].update(settings)
        self._save_db('groups', groups)
    
    # ============================================
    # USER DATA
    # ============================================
    
    def get_user(self, user_id):
        """Get user data"""
        users = self._load_db('users')
        user_id = str(user_id)
        if user_id not in users:
            users[user_id] = {
                'registered': int(time.time()),
                'premium': False,
                'banned': False
            }
            self._save_db('users', users)
        return users[user_id]
    
    def update_user(self, user_id, data):
        """Update user data"""
        users = self._load_db('users')
        user_id = str(user_id)
        if user_id not in users:
            users[user_id] = {'registered': int(time.time())}
        users[user_id].update(data)
        self._save_db('users', users)
    
    # ============================================
    # WARNINGS
    # ============================================
    
    def add_warning(self, group_id, user_id, reason):
        """Add warning for user"""
        warnings = self._load_db('warnings')
        key = f"{group_id}_{user_id}"
        if key not in warnings:
            warnings[key] = {'count': 0, 'warnings': []}
        warnings[key]['count'] += 1
        warnings[key]['warnings'].append({
            'reason': reason,
            'date': int(time.time())
        })
        self._save_db('warnings', warnings)
        return warnings[key]
    
    def clear_warnings(self, group_id, user_id):
        """Clear warnings for user"""
        warnings = self._load_db('warnings')
        key = f"{group_id}_{user_id}"
        if key in warnings:
            del warnings[key]
            self._save_db('warnings', warnings)
    
    def get_warnings(self, group_id, user_id):
        """Get warnings for user"""
        warnings = self._load_db('warnings')
        key = f"{group_id}_{user_id}"
        return warnings.get(key, {'count': 0, 'warnings': []})
    
    # ============================================
    # STORE (Persistent data)
    # ============================================
    
    def get_store(self, key, default=None):
        """Get value from store"""
        store = self._load_db('store')
        return store.get(key, default)
    
    def set_store(self, key, value):
        """Set value in store"""
        store = self._load_db('store')
        store[key] = value
        self._save_db('store', store)
        
        
        
import json
import os
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class GamificationSystem:
    def __init__(self):
        self.data_file = "data/gamification.json"
        self.achievements_file = "data/achievements.json"
        self.user_data = self.load_user_data()
        self.achievements = self.load_achievements()
    
    def load_user_data(self):
        """Load user gamification data"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_user_data(self):
        """Save user gamification data"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.user_data, f, ensure_ascii=False, indent=2)
    
    def load_achievements(self):
        """Load achievement definitions"""
        return {
            "first_chat": {
                "name": "👋 First Hello",
                "description": "Chat pertama dengan Miawka",
                "exp": 10,
                "icon": "🎉"
            },
            "chatty": {
                "name": "💬 Chatty Cat",
                "description": "Chat 10 kali dengan Miawka",
                "exp": 50,
                "icon": "😸",
                "requirement": 10
            },
            "social_butterfly": {
                "name": "🦋 Social Butterfly",
                "description": "Chat 50 kali dengan Miawka",
                "exp": 200,
                "icon": "✨",
                "requirement": 50
            },
            "miaw_addict": {
                "name": "🔥 Miaw Addict",
                "description": "Chat 100 kali dengan Miawka",
                "exp": 500,
                "icon": "💖",
                "requirement": 100
            },
            "sensei_student": {
                "name": "📚 Sensei's Student",
                "description": "Belajar dengan Sensei 5 kali",
                "exp": 75,
                "icon": "🎓",
                "requirement": 5
            },
            "knowledge_seeker": {
                "name": "🔍 Knowledge Seeker",
                "description": "Gunakan VTuber commands 10 kali",
                "exp": 100,
                "icon": "🎯",
                "requirement": 10
            },
            "tsundere_whisperer": {
                "name": "😤 Tsundere Whisperer",
                "description": "Dapatkan reaksi tsundere 20 kali",
                "exp": 150,
                "icon": "💢",
                "requirement": 20
            },
            "pat_master": {
                "name": "🐱 Pat Master",
                "description": "Pat Miawka 15 kali",
                "exp": 80,
                "icon": "✋",
                "requirement": 15
            },
            "daily_visitor": {
                "name": "📅 Daily Visitor",
                "description": "Chat setiap hari selama 7 hari berturut-turut",
                "exp": 300,
                "icon": "🌟",
                "requirement": 7
            },
            "trending_expert": {
                "name": "📈 Trending Expert",
                "description": "Check trending topics 20 kali",
                "exp": 120,
                "icon": "🔥",
                "requirement": 20
            }
        }
    
    def get_user_profile(self, user_id: str) -> Dict:
        """Get or create user profile"""
        if user_id not in self.user_data:
            self.user_data[user_id] = {
                "level": 1,
                "exp": 0,
                "total_exp": 0,
                "coins": 0,
                "miaw_interactions": 0,
                "sensei_interactions": 0,
                "vtuber_commands": 0,
                "tsundere_reactions": 0,
                "pat_count": 0,
                "daily_streak": 0,
                "last_daily": None,
                "achievements": [],
                "created_at": datetime.now().isoformat(),
                "last_interaction": datetime.now().isoformat(),
                "special_items": []
            }
        return self.user_data[user_id]
    
    def add_exp(self, user_id: str, exp: int, source: str = "general") -> Dict:
        """Add experience and handle level ups"""
        profile = self.get_user_profile(user_id)
        old_level = profile["level"]
        
        profile["exp"] += exp
        profile["total_exp"] += exp
        profile["coins"] += exp // 2  # Get coins as half of exp
        
        # Level up calculation
        exp_needed = self.get_exp_for_level(profile["level"] + 1)
        level_ups = 0
        
        while profile["exp"] >= exp_needed:
            profile["exp"] -= exp_needed
            profile["level"] += 1
            level_ups += 1
            profile["coins"] += profile["level"] * 10  # Bonus coins per level
            exp_needed = self.get_exp_for_level(profile["level"] + 1)
        
        self.save_user_data()
        
        return {
            "old_level": old_level,
            "new_level": profile["level"],
            "level_ups": level_ups,
            "exp_gained": exp,
            "total_exp": profile["total_exp"],
            "coins_gained": exp // 2 + (level_ups * profile["level"] * 10),
            "source": source
        }
    
    def get_exp_for_level(self, level: int) -> int:
        """Calculate exp needed for specific level"""
        return 100 + (level - 1) * 25
    
    def track_interaction(self, user_id: str, interaction_type: str) -> List[Dict]:
        """Track user interaction and check for achievements"""
        profile = self.get_user_profile(user_id)
        new_achievements = []
        
        # Update interaction counts
        if interaction_type == "miaw":
            profile["miaw_interactions"] += 1
        elif interaction_type == "sensei":
            profile["sensei_interactions"] += 1
        elif interaction_type == "vtuber":
            profile["vtuber_commands"] += 1
        elif interaction_type == "tsundere":
            profile["tsundere_reactions"] += 1
        elif interaction_type == "pat":
            profile["pat_count"] += 1
        
        # Update daily streak
        today = datetime.now().date().isoformat()
        if profile["last_daily"] != today:
            yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()
            if profile["last_daily"] == yesterday:
                profile["daily_streak"] += 1
            else:
                profile["daily_streak"] = 1
            profile["last_daily"] = today
        
        profile["last_interaction"] = datetime.now().isoformat()
        
        # Check achievements
        new_achievements = self.check_achievements(user_id)
        
        self.save_user_data()
        return new_achievements
    
    def check_achievements(self, user_id: str) -> List[Dict]:
        """Check and award new achievements"""
        profile = self.get_user_profile(user_id)
        new_achievements = []
        
        for ach_id, achievement in self.achievements.items():
            if ach_id in profile["achievements"]:
                continue  # Already has this achievement
            
            earned = False
            
            # Check achievement conditions
            if ach_id == "first_chat" and profile["miaw_interactions"] >= 1:
                earned = True
            elif ach_id == "chatty" and profile["miaw_interactions"] >= 10:
                earned = True
            elif ach_id == "social_butterfly" and profile["miaw_interactions"] >= 50:
                earned = True
            elif ach_id == "miaw_addict" and profile["miaw_interactions"] >= 100:
                earned = True
            elif ach_id == "sensei_student" and profile["sensei_interactions"] >= 5:
                earned = True
            elif ach_id == "knowledge_seeker" and profile["vtuber_commands"] >= 10:
                earned = True
            elif ach_id == "tsundere_whisperer" and profile["tsundere_reactions"] >= 20:
                earned = True
            elif ach_id == "pat_master" and profile["pat_count"] >= 15:
                earned = True
            elif ach_id == "daily_visitor" and profile["daily_streak"] >= 7:
                earned = True
            elif ach_id == "trending_expert" and profile["vtuber_commands"] >= 20:
                earned = True
            
            if earned:
                profile["achievements"].append(ach_id)
                exp_reward = achievement.get("exp", 0)
                profile["exp"] += exp_reward
                profile["total_exp"] += exp_reward
                profile["coins"] += exp_reward
                
                new_achievements.append({
                    "id": ach_id,
                    "achievement": achievement,
                    "exp_reward": exp_reward
                })
        
        return new_achievements

# Global gamification instance
gamification = GamificationSystem()

def get_level_title(level: int) -> str:
    """Get title based on user level"""
    if level >= 50:
        return "🏆 Miawka Legend"
    elif level >= 30:
        return "⭐ VTuber Expert"
    elif level >= 20:
        return "🎯 Chat Master"
    elif level >= 15:
        return "🔥 Super Fan"
    elif level >= 10:
        return "💫 Rising Star"
    elif level >= 5:
        return "🌟 Regular"
    else:
        return "🐱 Newbie"

def format_exp_bar(current_exp: int, needed_exp: int, length: int = 10) -> str:
    """Create visual EXP bar"""
    filled = int((current_exp / needed_exp) * length)
    empty = length - filled
    return f"{'█' * filled}{'░' * empty}"
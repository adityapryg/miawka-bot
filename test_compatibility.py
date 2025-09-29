#!/usr/bin/env python3
"""
Test script for Miawka Bot - Python 3.11 compatibility test
"""

import sys
import json
import os

def test_python_version():
    """Test Python version compatibility"""
    print(f"🐍 Python Version: {sys.version}")
    major, minor = sys.version_info[:2]
    
    if major == 3 and minor >= 8:
        print("✅ Python version compatible with discord.py 2.x")
        return True
    else:
        print("❌ Python version too old for discord.py 2.x")
        return False

def test_core_imports():
    """Test core module imports"""
    try:
        # Test gamification system
        print("\n📊 Testing gamification system...")
        from core.gamification import gamification, get_level_title
        print(f"✅ Gamification loaded: {len(gamification.achievements)} achievements")
        
        # Test user profile
        test_user = "test_user_123"
        profile = gamification.get_user_profile(test_user)
        print(f"✅ User profile created: Level {profile['level']}")
        
        # Test EXP system
        result = gamification.add_exp(test_user, 25, "test")
        print(f"✅ EXP system working: +{result['exp_gained']} EXP")
        
        return True
    except Exception as e:
        print(f"❌ Core imports failed: {e}")
        return False

def test_data_files():
    """Test data file structure"""
    try:
        print("\n📁 Testing data files...")
        
        # Check data directory
        data_dir = "data"
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            print("✅ Data directory created")
        else:
            print("✅ Data directory exists")
        
        # Check achievements.json
        achievements_file = "data/achievements.json"
        if os.path.exists(achievements_file):
            with open(achievements_file, 'r', encoding='utf-8') as f:
                achievements = json.load(f)
            print(f"✅ Achievements file loaded: {len(achievements)} achievements")
        else:
            print("⚠️ Achievements file missing")
        
        # Check gamification.json
        gamification_file = "data/gamification.json"
        if os.path.exists(gamification_file):
            print("✅ Gamification data file exists")
        else:
            # Create empty file
            with open(gamification_file, 'w') as f:
                json.dump({}, f)
            print("✅ Gamification data file created")
        
        return True
    except Exception as e:
        print(f"❌ Data files test failed: {e}")
        return False

def test_discord_compatibility():
    """Test Discord.py compatibility (without actual connection)"""
    try:
        print("\n🤖 Testing Discord.py compatibility...")
        import discord
        from discord.ext import commands
        
        # Test intents
        intents = discord.Intents.default()
        if hasattr(intents, 'message_content'):
            intents.message_content = True
            print("✅ Discord.py 2.x intents available")
        else:
            print("⚠️ Using Discord.py 1.x (message_content not available)")
        
        # Test bot creation
        bot = commands.Bot(command_prefix='!', intents=intents)
        print("✅ Bot instance created successfully")
        
        return True
    except ImportError:
        print("❌ Discord.py not installed")
        return False
    except Exception as e:
        print(f"❌ Discord compatibility test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🎮 Miawka Bot Compatibility Test")
    print("=" * 40)
    
    tests = [
        test_python_version,
        test_data_files, 
        test_core_imports,
        test_discord_compatibility
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 40)
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Bot is ready to deploy!")
        return True
    else:
        print("⚠️ Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
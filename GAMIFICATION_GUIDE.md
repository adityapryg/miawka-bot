# 🎮 Miawka Bot - Gamification System Guide

## Overview
The Miawka Bot now includes a comprehensive gamification system that rewards users for interacting with different bot features. Users can earn EXP, level up, unlock achievements, collect coins, and maintain daily streaks!

## 🎯 Core Features

### Level System
- **Levels 1-20+** with progressive EXP requirements
- **Level Titles**: Newbie → Regular → Rising Star → Super Fan → Chat Master → VTuber Expert → Miawka Legend
- **EXP Formula**: Level N requires `100 + (N-1) * 25` total EXP
- **Coin Rewards**: Earn coins equal to half your EXP gained + level-up bonuses

### 🏆 Achievement System
**10 Different Achievements to Unlock:**

1. **🎉 First Chat** - Send your first message to Miawka
2. **💬 Chatty** - Have 50+ conversations with Miawka  
3. **🌟 Social Butterfly** - Interact with both Miawka and Sensei
4. **😻 Miaw Addict** - Have 100+ interactions with Miawka
5. **📚 Sensei Student** - Have 30+ learning sessions with Sensei
6. **🧠 Knowledge Seeker** - Have 100+ interactions with Sensei
7. **😤 Tsundere Whisperer** - Trigger 50+ tsundere reactions from Miawka
8. **🤲 Pat Master** - Give Miawka 25+ head pats
9. **🔥 Daily Visitor** - Maintain a 7-day daily streak
10. **📈 Trending Expert** - Use VTuber commands 20+ times

### 💰 Currency System
- **Coins**: Earn coins from all activities (half your EXP gain)
- **Daily Rewards**: Base 50 EXP + streak bonuses (up to 150 bonus EXP)
- **Level Up Bonuses**: Extra coins when you reach new levels

## 🎮 Commands

### Profile & Stats
- `!profile [@user]` - View detailed user profile with level, EXP, coins, and achievements
- `!achievements [@user]` - See all unlocked and locked achievements
- `!daily` - Claim daily rewards and maintain your streak

### Leaderboards
- `!leaderboard` or `!leaderboard level` - Top users by level
- `!leaderboard exp` - Top users by total EXP earned
- `!leaderboard coins` - Top users by coins collected
- `!leaderboard chats` - Most active chatters with Miawka
- `!leaderboard achievements` - Users with most achievements

## 💎 EXP Rewards by Activity

### Chat Activities (Miawka)
- **Base Chat**: 10 EXP per message
- **Conversation Bonus**: +2 EXP per message in ongoing conversation (max +20)
- **Special Keywords**: +5 EXP for mentioning "miaw", "miawka", "neko", "cat"
- **Tsundere Interactions**: +3 EXP for "tsundere", "baka", "stupid", "dummy"
- **Head Pats**: +8 EXP for patting Miawka (*pat*, 🤲)

### Educational Activities (Sensei)
- **Base Learning**: 15 EXP per session (higher than chat!)
- **Educational Keywords**: +2 EXP for "why", "how", "explain", "teach", etc.
- **Questions**: +3 EXP for messages containing "?"

### VTuber Activities
- **VTuber News**: 12 EXP per use
- **Trending/Games/Culture**: 10 EXP per command
- **Collaboration**: 15 EXP per use (networking bonus!)

### Daily Activities
- **Daily Rewards**: 50-200 EXP based on streak
- **Achievement Unlocks**: Bonus EXP when completing achievements

## 📊 Progression System

### Level Requirements
```
Level 1: 0 EXP (Starting level)
Level 2: 100 EXP
Level 3: 125 EXP  
Level 4: 150 EXP
Level 5: 175 EXP
...
Level 10: 325 EXP
Level 20: 575 EXP
```

### Daily Streak Bonuses
- **Day 1-7**: +5 EXP per day streak
- **Day 8-14**: +10 EXP per day streak  
- **Day 15-30**: +15 EXP per day streak (Max bonus: +150 EXP)

## 🎊 Special Features

### Real-Time Notifications
- **Level Up**: Instant notification when you reach a new level
- **Achievement Unlock**: Celebration message when earning achievements
- **Visual EXP Bar**: See your progress toward the next level

### Statistics Tracking
The bot tracks detailed statistics:
- Total EXP earned and current level
- Coins collected and spent
- Interaction counts per bot feature
- Daily streak maintenance
- Achievement completion dates

### Social Features
- **Profile Viewing**: Check other users' progress
- **Leaderboards**: Compete with friends
- **Achievement Showcasing**: Display your accomplishments

## 🚀 Tips for Fast Progression

1. **Daily Login**: Claim `!daily` rewards every day for streak bonuses
2. **Diverse Interaction**: Use both Miawka and Sensei for variety bonuses
3. **VTuber Commands**: High EXP rewards for content creation help
4. **Special Keywords**: Mention "miaw", ask questions, give head pats
5. **Consistent Activity**: Regular interaction builds conversation bonuses

## 🔧 Technical Details

### Data Storage
- **JSON-based**: User data stored in `user_gamification.json`
- **Persistent**: All progress saved between bot restarts
- **Backup Safe**: Regular data validation and error handling

### Performance
- **Efficient**: Minimal performance impact on bot response times
- **Scalable**: Handles hundreds of users without slowdown
- **Clean**: Automatic data cleanup and optimization

---

**Ready to start your journey? Try `!profile` to see your current stats and `!daily` to begin your streak!** 🎮✨
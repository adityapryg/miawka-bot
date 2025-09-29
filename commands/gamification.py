import discord
from discord.ext import commands
from core.gamification import gamification, get_level_title, format_exp_bar
from datetime import datetime

def setup_gamification_commands(bot):
    
    @bot.command(name='profile')
    async def user_profile(ctx, member: discord.Member = None):
        """Show detailed user profile with gamification stats"""
        target = member or ctx.author
        user_id = str(target.id)
        profile = gamification.get_user_profile(user_id)
        
        level_title = get_level_title(profile["level"])
        exp_needed = gamification.get_exp_for_level(profile["level"] + 1)
        exp_bar = format_exp_bar(profile["exp"], exp_needed, 15)
        
        embed = discord.Embed(
            title=f"🎮 {target.display_name}'s Profile",
            description=f"**{level_title}** - Level {profile['level']}",
            color=0x3498db
        )
        
        embed.set_thumbnail(url=target.display_avatar.url)
        
        # Level & EXP Info
        embed.add_field(
            name="📈 Progress",
            value=f"**Level:** {profile['level']}\n**EXP:** {profile['exp']}/{exp_needed}\n{exp_bar}\n**Total EXP:** {profile['total_exp']:,}",
            inline=True
        )
        
        # Currency & Stats
        embed.add_field(
            name="💰 Currency & Stats",
            value=f"**Coins:** 🪙 {profile['coins']:,}\n**Daily Streak:** 🔥 {profile['daily_streak']} days\n**Achievements:** 🏆 {len(profile['achievements'])}/{len(gamification.achievements)}",
            inline=True
        )
        
        # Interaction Stats
        embed.add_field(
            name="💬 Interactions",
            value=f"**Miaw Chats:** {profile['miaw_interactions']:,}\n**Sensei Sessions:** {profile['sensei_interactions']:,}\n**VTuber Commands:** {profile['vtuber_commands']:,}\n**Tsundere Reactions:** {profile['tsundere_reactions']:,}\n**Pat Count:** {profile['pat_count']:,}",
            inline=False
        )
        
        # Recent achievements
        recent_achievements = profile['achievements'][-3:] if profile['achievements'] else []
        if recent_achievements:
            ach_text = "\n".join([
                f"{gamification.achievements[ach_id]['icon']} {gamification.achievements[ach_id]['name']}"
                for ach_id in recent_achievements
            ])
            embed.add_field(
                name="🏆 Recent Achievements",
                value=ach_text,
                inline=False
            )
        
        # Member since
        created_date = datetime.fromisoformat(profile['created_at']).strftime("%d %b %Y")
        embed.set_footer(text=f"Member since {created_date} • Use !achievements for full list")
        
        await ctx.reply(embed=embed)
    
    @bot.command(name='achievements')
    async def show_achievements(ctx, member: discord.Member = None):
        """Show user's achievements"""
        target = member or ctx.author
        user_id = str(target.id)
        profile = gamification.get_user_profile(user_id)
        
        embed = discord.Embed(
            title=f"🏆 {target.display_name}'s Achievements",
            description=f"Unlocked: {len(profile['achievements'])}/{len(gamification.achievements)}",
            color=0xf1c40f
        )
        
        unlocked_text = ""
        locked_text = ""
        
        for ach_id, achievement in gamification.achievements.items():
            ach_line = f"{achievement['icon']} **{achievement['name']}**\n{achievement['description']} (+{achievement['exp']} EXP)\n"
            
            if ach_id in profile['achievements']:
                unlocked_text += ach_line + "\n"
            else:
                locked_text += f"🔒 ~~{achievement['name']}~~\n{achievement['description']}\n\n"
        
        if unlocked_text:
            embed.add_field(name="✅ Unlocked", value=unlocked_text[:1024], inline=False)
        
        if locked_text:
            embed.add_field(name="🔒 Locked", value=locked_text[:1024], inline=False)
        
        await ctx.reply(embed=embed)
    
    @bot.command(name='leaderboard')
    async def leaderboard(ctx, category: str = "level"):
        """Show leaderboards - categories: level, exp, coins, chats"""
        valid_categories = {
            "level": ("level", "🏆 Level Leaderboard", "Level"),
            "exp": ("total_exp", "✨ EXP Leaderboard", "Total EXP"),
            "coins": ("coins", "🪙 Coins Leaderboard", "Coins"),
            "chats": ("miaw_interactions", "💬 Chat Leaderboard", "Chats"),
            "achievements": ("achievements", "🏆 Achievement Leaderboard", "Achievements")
        }
        
        if category not in valid_categories:
            await ctx.reply(f"❌ Invalid category! Use: {', '.join(valid_categories.keys())}")
            return
        
        sort_key, title, display_name = valid_categories[category]
        
        # Sort users
        if sort_key == "achievements":
            sorted_users = sorted(
                gamification.user_data.items(),
                key=lambda x: len(x[1][sort_key]),
                reverse=True
            )[:10]
        else:
            sorted_users = sorted(
                gamification.user_data.items(),
                key=lambda x: x[1][sort_key],
                reverse=True
            )[:10]
        
        embed = discord.Embed(
            title=title,
            color=0xe74c3c
        )
        
        leaderboard_text = ""
        medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
        
        for i, (user_id, data) in enumerate(sorted_users):
            try:
                user = bot.get_user(int(user_id))
                username = user.display_name if user else f"User {user_id[:6]}"
            except:
                username = f"User {user_id[:6]}"
            
            if sort_key == "achievements":
                value = len(data[sort_key])
            else:
                value = data[sort_key]
            
            level_title = get_level_title(data["level"])
            leaderboard_text += f"{medals[i]} **{username}** - Level {data['level']}\n{level_title}\n{display_name}: {value:,}\n\n"
        
        embed.description = leaderboard_text
        embed.set_footer(text="Keep chatting to climb the leaderboard! 🚀")
        
        await ctx.reply(embed=embed)
    
    @bot.command(name='daily')
    async def daily_reward(ctx):
        """Claim daily rewards"""
        user_id = str(ctx.author.id)
        profile = gamification.get_user_profile(user_id)
        
        today = datetime.now().date().isoformat()
        if profile.get("last_daily_claim") == today:
            await ctx.reply("😤 Kamu udah claim daily reward hari ini! Balik lagi besok ya~")
            return
        
        # Calculate daily reward based on streak
        base_reward = 50
        streak_bonus = min(profile["daily_streak"], 30) * 5  # Max 150 bonus
        total_exp = base_reward + streak_bonus
        coins_reward = total_exp // 2
        
        # Add rewards
        exp_result = gamification.add_exp(user_id, total_exp, "daily_reward")
        profile["last_daily_claim"] = today
        gamification.save_user_data()
        
        embed = discord.Embed(
            title="🎁 Daily Reward Claimed!",
            description=f"Selamat datang kembali, {ctx.author.display_name}!",
            color=0x2ecc71
        )
        
        embed.add_field(
            name="🎯 Rewards",
            value=f"**EXP:** +{total_exp} ({base_reward} base + {streak_bonus} streak bonus)\n**Coins:** +{coins_reward} 🪙\n**Daily Streak:** 🔥 {profile['daily_streak']} days",
            inline=False
        )
        
        if exp_result["level_ups"] > 0:
            level_title = get_level_title(exp_result["new_level"])
            embed.add_field(
                name="🎉 Level Up!",
                value=f"Congratulations! You're now Level {exp_result['new_level']} - {level_title}!",
                inline=False
            )
        
        embed.set_footer(text="Come back tomorrow for more rewards! Streak bonus increases daily! 🌟")
        
        await ctx.reply(embed=embed)
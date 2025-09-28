import discord
from discord.ext import commands
from core.globals import reset_user_state, get_user_stats, cleanup_old_conversations, conversation_histories, user_moods

def setup_utility_commands(bot):
    @bot.command(name='reset')
    @commands.cooldown(rate=1, per=300, type=commands.BucketType.user)  # 1 time per 5 minutes
    async def reset_user_data(ctx, context=None):
        """Reset your conversation history and mood for miaw, sensei, or both"""
        user_id = ctx.author.id
        
        if context is None:
            # Reset both miaw and sensei
            reset_user_state(user_id, 'miaw')
            reset_user_state(user_id, 'sensei')
            
            embed = discord.Embed(
                title="🔄 Data Reset Complete",
                description="All your conversation history and moods have been reset for both **Miaw** and **Sensei**!",
                color=0x00ff00
            )
            embed.add_field(
                name="What was reset:",
                value="• Chat history with Miawka\n• Chat history with Sensei\n• Current moods\n• Cooldown timers",
                inline=False
            )
            await ctx.reply(embed=embed)
        
        elif context.lower() in ['miaw', 'miawka']:
            reset_user_state(user_id, 'miaw')
            await ctx.reply("🐱 Miawka's memory about you has been reset! She'll treat you like a new friend nya~")
        
        elif context.lower() in ['sensei', 'teacher']:
            reset_user_state(user_id, 'sensei')
            await ctx.reply("👨‍🏫 Sensei's memory about your learning progress has been reset! Time for a fresh start!")
        
        else:
            embed = discord.Embed(
                title="❌ Invalid Context",
                description="Use `!reset` to reset everything, or specify:",
                color=0xff0000
            )
            embed.add_field(
                name="Valid options:",
                value="`!reset miaw` - Reset Miawka only\n`!reset sensei` - Reset Sensei only\n`!reset` - Reset both",
                inline=False
            )
            await ctx.reply(embed=embed)

    @bot.command(name='stats', aliases=['mystats'])
    @commands.cooldown(rate=2, per=60, type=commands.BucketType.user)
    async def user_statistics(ctx, target_user: discord.Member = None):
        """Show your interaction statistics with the bot"""
        
        # Admin can check other users' stats
        if target_user and not ctx.author.guild_permissions.administrator:
            await ctx.reply("❌ Only administrators can check other users' stats!")
            return
        
        user_to_check = target_user or ctx.author
        user_id = user_to_check.id
        stats = get_user_stats(user_id)
        
        embed = discord.Embed(
            title=f"📊 Bot Interaction Stats",
            description=f"Statistics for {user_to_check.mention}",
            color=0x3498db
        )
        
        # Conversation stats
        embed.add_field(
            name="💬 Conversation History",
            value=f"**Miawka:** {stats['miaw_conversations']} messages\n**Sensei:** {stats['sensei_conversations']} messages",
            inline=True
        )
        
        # Current moods
        miaw_mood = stats['current_moods']['miaw']
        sensei_mood = stats['current_moods']['sensei']
        
        embed.add_field(
            name="😺 Current Moods",
            value=f"**Miawka:** {miaw_mood}\n**Sensei:** {sensei_mood}",
            inline=True
        )
        
        # Total interactions
        total_interactions = stats['miaw_conversations'] + stats['sensei_conversations']
        embed.add_field(
            name="🎯 Total Interactions",
            value=f"{total_interactions} messages",
            inline=True
        )
        
        # Active status
        is_active_miaw = len(conversation_histories['miaw'].get(user_id, [])) > 0
        is_active_sensei = len(conversation_histories['sensei'].get(user_id, [])) > 0
        
        status_indicators = []
        if is_active_miaw:
            status_indicators.append("🐱 Active with Miawka")
        if is_active_sensei:
            status_indicators.append("👨‍🏫 Active with Sensei")
        if not status_indicators:
            status_indicators.append("😴 No recent activity")
        
        embed.add_field(
            name="🔥 Activity Status",
            value="\n".join(status_indicators),
            inline=False
        )
        
        embed.set_footer(text="Use !reset to clear your data")
        await ctx.reply(embed=embed)

    @bot.command(name='cleanup')
    @commands.has_permissions(administrator=True)
    async def manual_cleanup(ctx):
        """Manually trigger conversation history cleanup (Admin only)"""
        
        # Count conversations before cleanup
        total_before = 0
        for context in conversation_histories.values():
            for user_conversations in context.values():
                total_before += len(user_conversations)
        
        # Perform cleanup
        cleanup_old_conversations()
        
        # Count conversations after cleanup
        total_after = 0
        for context in conversation_histories.values():
            for user_conversations in context.values():
                total_after += len(user_conversations)
        
        cleaned = total_before - total_after
        
        embed = discord.Embed(
            title="🧹 Cleanup Complete",
            description="Old conversation histories have been cleaned up!",
            color=0x00ff00
        )
        embed.add_field(
            name="Results:",
            value=f"**Before:** {total_before} total messages\n**After:** {total_after} total messages\n**Cleaned:** {cleaned} old messages",
            inline=False
        )
        embed.add_field(
            name="Info:",
            value=f"Conversations are limited to {10} messages per user to prevent memory issues.",
            inline=False
        )
        
        await ctx.reply(embed=embed)

    @bot.command(name='botstats')
    @commands.has_permissions(administrator=True)
    async def bot_statistics(ctx):
        """Show overall bot usage statistics (Admin only)"""
        
        # Count total users and conversations
        miaw_users = len(conversation_histories['miaw'])
        sensei_users = len(conversation_histories['sensei'])
        total_users = len(set(list(conversation_histories['miaw'].keys()) + list(conversation_histories['sensei'].keys())))
        
        # Count total messages
        total_miaw_messages = sum(len(conversations) for conversations in conversation_histories['miaw'].values())
        total_sensei_messages = sum(len(conversations) for conversations in conversation_histories['sensei'].values())
        
        # Count active moods
        active_miaw_moods = len(user_moods['miaw'])
        active_sensei_moods = len(user_moods['sensei'])
        
        embed = discord.Embed(
            title="🤖 Bot Usage Statistics",
            description="Overall bot performance and usage data",
            color=0x9b59b6
        )
        
        embed.add_field(
            name="👥 User Statistics",
            value=f"**Total Users:** {total_users}\n**Miaw Users:** {miaw_users}\n**Sensei Users:** {sensei_users}",
            inline=True
        )
        
        embed.add_field(
            name="💬 Message Statistics",
            value=f"**Total Messages:** {total_miaw_messages + total_sensei_messages}\n**Miaw Messages:** {total_miaw_messages}\n**Sensei Messages:** {total_sensei_messages}",
            inline=True
        )
        
        embed.add_field(
            name="😊 Active Moods",
            value=f"**Miaw Moods:** {active_miaw_moods}\n**Sensei Moods:** {active_sensei_moods}",
            inline=True
        )
        
        embed.set_footer(text="Use !cleanup to clean old conversations")
        await ctx.reply(embed=embed)

    # Error handlers
    @reset_user_data.error
    async def reset_error(ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(f"⏱️ You can only reset your data once every 5 minutes. Try again in {error.retry_after:.0f} seconds.")

    @user_statistics.error
    async def stats_error(ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(f"⏱️ Stats command is on cooldown. Try again in {error.retry_after:.0f} seconds.")

    @manual_cleanup.error
    async def cleanup_error(ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply("❌ You need administrator permissions to use cleanup command!")

    @bot_statistics.error
    async def botstats_error(ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply("❌ You need administrator permissions to view bot statistics!")
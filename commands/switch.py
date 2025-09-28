import os
import discord
from discord.ext import commands
from core.globals import LLM_PROVIDER

def setup_switch_command(bot):
    @bot.command(name='switch')
    @commands.has_permissions(administrator=True)  # Only admins can switch providers
    async def switch_provider(ctx, provider=None):
        """Switch between OpenAI and Perplexity API providers"""
        
        if provider is None:
            current_provider = os.getenv('LLM_PROVIDER', 'openai')
            embed_color = 0x00ff00 if current_provider == 'openai' else 0xff6600
            
            embed = discord.Embed(
                title="🔄 Current LLM Provider",
                description=f"Currently using: **{current_provider.upper()}**",
                color=embed_color
            )
            embed.add_field(
                name="Available Commands:",
                value="`!switch openai` - Switch to OpenAI\n`!switch perplexity` - Switch to Perplexity",
                inline=False
            )
            embed.add_field(
                name="Current Models:",
                value=f"**Miaw:** {'gpt-4o-mini' if current_provider == 'openai' else 'sonar'}\n**Sensei:** {'gpt-4' if current_provider == 'openai' else 'sonar-reasoning'}",
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        provider = provider.lower()
        if provider not in ['openai', 'perplexity']:
            await ctx.send("❌ Invalid provider! Use `openai` or `perplexity`")
            return
        
        # Update environment variable
        os.environ['LLM_PROVIDER'] = provider
        
        # Update the global variable
        import core.globals as globals_module
        globals_module.LLM_PROVIDER = provider
        
        # Success message
        emoji = "🤖" if provider == 'openai' else "🔍"
        color = 0x00ff00 if provider == 'openai' else 0xff6600
        
        models_info = {
            'openai': {'miaw': 'gpt-4o-mini', 'sensei': 'gpt-4'},
            'perplexity': {'miaw': 'sonar', 'sensei': 'sonar-reasoning'}
        }
        
        embed = discord.Embed(
            title=f"{emoji} Switched to {provider.upper()}",
            description=f"LLM provider successfully changed to **{provider.upper()}**",
            color=color
        )
        embed.add_field(
            name="New Models:",
            value=f"**Miaw:** {models_info[provider]['miaw']}\n**Sensei:** {models_info[provider]['sensei']}",
            inline=False
        )
        
        if provider == 'perplexity':
            embed.add_field(
                name="Note:",
                value="Sensei will now include citations from web searches! 📚",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @switch_provider.error
    async def switch_error(ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You need administrator permissions to switch LLM providers!")
        else:
            print(f"Switch command error: {error}")  # Debug logging
            await ctx.send(f"❌ An error occurred while switching providers: {str(error)}")
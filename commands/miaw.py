import openai
import re
import asyncio
import random
import discord
from discord.ext import commands
from core.globals import conversation_histories, SYSTEM_PROMPT_MIAW, create_mood_prompt, update_mood, get_llm_config, cleanup_old_conversations

# Try to import gamification, but don't crash if it fails
try:
    from core.gamification import gamification, get_level_title, format_exp_bar
    GAMIFICATION_ENABLED = True
except Exception as e:
    print(f"Gamification import error: {e}")
    GAMIFICATION_ENABLED = False

def clean_response(text):
    """Remove unwanted content like think tags from AI responses"""
    # Remove <think>...</think> blocks
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove citations/references like [1], [2], [3] etc.
    text = re.sub(r'\[\d+\]', '', text)
    
    # Clean up extra whitespace and newlines
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Replace triple+ newlines with double
    text = text.strip()
    
    return text

# Interactive reactions based on message content
MIAW_REACTIONS = {
    'positive': ['😸', '🥰', '😊', '💖', '✨', '🌟'],
    'tsundere': ['😤', '🙄', '😏', '💢', '😾', '🐱'],
    'excited': ['🎉', '⭐', '🔥', '💫', '🌸', '💕'],
    'confused': ['😵', '🤔', '❓', '😅', '🙃', '🤷‍♀️'],
    'sleepy': ['😴', '💤', '🥱', '😪', '🌙', '💭']
}

def get_interactive_reaction(message_content, mood):
    """Get appropriate reaction based on message content and mood"""
    message_lower = message_content.lower()
    
    # Detect message sentiment
    if any(word in message_lower for word in ['sad', 'sedih', 'down', 'bete', 'galau']):
        return random.choice(MIAW_REACTIONS['positive'])
    elif any(word in message_lower for word in ['happy', 'senang', 'excited', 'hype']):
        return random.choice(MIAW_REACTIONS['excited'])
    elif any(word in message_lower for word in ['confused', 'bingung', 'ga ngerti']):
        return random.choice(MIAW_REACTIONS['confused'])
    elif any(word in message_lower for word in ['tired', 'capek', 'sleepy', 'ngantuk']):
        return random.choice(MIAW_REACTIONS['sleepy'])
    elif mood == 'tsundere':
        return random.choice(MIAW_REACTIONS['tsundere'])
    else:
        return random.choice(MIAW_REACTIONS['positive'])

def detect_special_interactions(message_content):
    """Detect special interaction patterns"""
    message_lower = message_content.lower()
    
    interactions = {
        'greeting': any(word in message_lower for word in ['hi', 'hai', 'hello', 'halo', 'hey']),
        'farewell': any(word in message_lower for word in ['bye', 'goodbye', 'dadah', 'see you', 'sampai jumpa']),
        'compliment': any(word in message_lower for word in ['cute', 'lucu', 'cantik', 'imut', 'kawaii']),
        'question': '?' in message_content,
        'love': any(word in message_lower for word in ['love', 'sayang', 'cinta', 'suka']),
        'pat': any(word in message_lower for word in ['pat', 'elus', 'usap', '*pat*']),
        'food': any(word in message_lower for word in ['makan', 'food', 'lapar', 'hungry']),
        'game': any(word in message_lower for word in ['game', 'main', 'play', 'gaming']),
        'sing': any(word in message_lower for word in ['sing', 'nyanyi', 'lagu', 'song'])
    }
    
    return interactions

async def add_interactive_elements(ctx, message_content, mood):
    """Add interactive elements like reactions, typing delays, etc."""
    interactions = detect_special_interactions(message_content)
    
    # Add reaction emoji
    reaction = get_interactive_reaction(message_content, mood)
    try:
        await ctx.message.add_reaction(reaction)
    except:
        pass  # Ignore if reaction fails
    
    # Special typing delays for different interactions
    if interactions['question']:
        await asyncio.sleep(random.uniform(1.5, 3.0))  # Think longer for questions
    elif interactions['compliment']:
        await asyncio.sleep(random.uniform(0.5, 1.5))  # Quick shy response
    else:
        await asyncio.sleep(random.uniform(0.5, 2.0))  # Normal delay

def enhance_system_prompt_with_context(base_prompt, interactions, user_name):
    """Enhance system prompt with contextual information"""
    context_additions = []
    
    if interactions['greeting']:
        context_additions.append(f"User {user_name} sedang menyapa kamu. Respond naturally dengan style tsundere.")
    
    if interactions['compliment']:
        context_additions.append("User memberikan compliment. Act tsundere - malu tapi senang, jangan langsung terima, tapi tunjukkan kamu secretly happy.")
    
    if interactions['farewell']:
        context_additions.append("User akan pergi. Act like you don't care but actually don't want them to leave (tsundere style).")
    
    if interactions['pat']:
        context_additions.append("User wants to pat you. React dengan malu-malu tapi secretly enjoy it. Maybe purr a little (nyaa~).")
    
    if interactions['love']:
        context_additions.append("User mengatakan sesuatu tentang love/suka. Be very tsundere - deny it but be flustered (baka! It's not like I like you or anything!).")
    
    if interactions['question']:
        context_additions.append("User bertanya sesuatu. Be helpful but maintain your tsundere personality.")
    
    enhanced_prompt = base_prompt
    if context_additions:
        enhanced_prompt += f"\n\nCONTEXT KHUSUS: {' '.join(context_additions)}"
    
    return enhanced_prompt

def handle_gamification_rewards(ctx, user_id, interactions, exp_reward):
    """Handle gamification rewards safely"""
    if not GAMIFICATION_ENABLED:
        return None, []
    
    try:
        # Track interaction and get achievements
        new_achievements = gamification.track_interaction(user_id, "miaw")
        if interactions.get('tsundere'):
            gamification.track_interaction(user_id, "tsundere")
        if interactions.get('pat'):
            gamification.track_interaction(user_id, "pat")
        
        # Add EXP
        exp_result = gamification.add_exp(user_id, exp_reward, "miaw_chat")
        
        return exp_result, new_achievements
    except Exception as e:
        print(f"Gamification error: {e}")
        return None, []

def setup_miaw_command(bot):
    @bot.command(name='miaw')
    @commands.cooldown(rate=3, per=60, type=commands.BucketType.user)
    async def chat_with_cat(ctx, *, message=None):
        user_id = str(ctx.author.id)  # Convert to string for JSON
        user_name = ctx.author.display_name
        
        # Show help/explanation if no message provided
        if message is None:
            embed = discord.Embed(
                title="🐱✨ Hai, aku Miawka!",
                description="Aku adalah kucing AI yang tsundere dan super interactive!",
                color=0xff69b4
            )
            
            embed.add_field(
                name="💬 Cara Menggunakan:",
                value="`!miaw [pesan kamu]`\nContoh: `!miaw halo miawka cantik!`",
                inline=False
            )
            
            embed.add_field(
                name="😸 Kepribadianku:",
                value="• **Tsundere** - Malu-malu tapi perhatian\n• **Interactive** - Bereaksi dengan emoji\n• **Memory** - Ingat percakapan kita!\n• **Natural** - Chat biasa tanpa embed!",
                inline=False
            )
            
            if GAMIFICATION_ENABLED:
                try:
                    profile = gamification.get_user_profile(user_id)
                    level_title = get_level_title(profile.get("level", 1))
                    embed.add_field(
                        name="🎮 Your Progress:",
                        value=f"**Level:** {profile.get('level', 1)} - {level_title}\n**Chat Count:** {profile.get('miaw_interactions', 0)}\n**Achievements:** {len(profile.get('achievements', []))}",
                        inline=False
                    )
                except Exception as e:
                    print(f"Profile display error: {e}")
            
            embed.add_field(
                name="🎮 Try These Interactions:",
                value="• `!miaw hai miawka!` - Greetings\n• `!miaw kamu lucu banget!` - Compliments\n• `!miaw *pat head*` - Pat reactions\n• `!miaw aku sayang kamu` - Love reactions\n• `!miaw bye bye!` - Farewells",
                inline=False
            )
            
            embed.set_footer(text="Ayo chat sama aku! Natural responses! 😸💕")
            await ctx.reply(embed=embed)
            return
        
        if user_id not in conversation_histories['miaw']:
            conversation_histories['miaw'][user_id] = []

        # Add the user's message to the conversation history
        conversation_histories['miaw'][user_id].append({"role": "user", "content": message})

        # Get current mood and interactions
        mood = update_mood(user_id, 'miaw')
        interactions = detect_special_interactions(message)
        
        # Calculate EXP based on interaction type
        exp_reward = 10  # Base EXP
        if interactions['compliment']:
            exp_reward = 15
        elif interactions['pat']:
            exp_reward = 20
        elif interactions['love']:
            exp_reward = 25
        elif interactions['question']:
            exp_reward = 12
        
        enhanced_prompt = enhance_system_prompt_with_context(SYSTEM_PROMPT_MIAW, interactions, user_name)
        
        conversation = [
            {"role": "system", "content": enhanced_prompt},
            {"role": "system", "content": create_mood_prompt(mood)},
            {"role": "system", "content": f"User name: {user_name}. Use their name naturally in conversation sometimes. RESPOND WITH NATURAL TEXT - NO MARKDOWN, NO EMBEDS, just natural conversational text."},
            {"role": "user", "content": message}
        ]

        try:
            config = get_llm_config()
            
            async with ctx.typing():
                await add_interactive_elements(ctx, message, mood)
                
                client = openai.OpenAI(
                    api_key=config['api_key'],
                    base_url=config['base_url'] if config['base_url'] else "https://api.openai.com/v1",
                    timeout=30.0
                )

                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: client.chat.completions.create(
                        model=config['models']['miaw'],
                        messages=conversation,
                        max_tokens=2048,
                        temperature=0.9
                    )
                )
                answer = response.choices[0].message.content
                answer = clean_response(answer)
                
            # Send the main response
            if len(answer) <= 2000:
                await ctx.reply(answer)
            else:
                chunks = []
                current_chunk = ""
                
                for line in answer.split('\n'):
                    if len(current_chunk + line + '\n') <= 1900:
                        current_chunk += line + '\n'
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = line + '\n'
                
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                if chunks:
                    await ctx.reply(chunks[0])
                    for chunk in chunks[1:]:
                        await ctx.send(chunk)

            # Handle gamification rewards safely
            exp_result, new_achievements = handle_gamification_rewards(ctx, user_id, interactions, exp_reward)
            
            if exp_result:
                # Level up notification
                if exp_result.get("level_ups", 0) > 0:
                    level_title = get_level_title(exp_result["new_level"])
                    await ctx.send(f"🎉 **LEVEL UP!** {user_name} naik ke Level {exp_result['new_level']} - {level_title}! ✨")
                
                # Achievement notifications
                for achievement in new_achievements:
                    ach = achievement.get("achievement", {})
                    await ctx.send(f"🏆 **ACHIEVEMENT UNLOCKED!**\n{ach.get('icon', '🎉')} **{ach.get('name', 'Achievement')}**\n{ach.get('description', '')} (+{achievement.get('exp_reward', 0)} EXP)")
            
            # Show small reward indicator
            try:
                await ctx.message.add_reaction('💫')  # EXP indicator
            except:
                pass

            conversation_histories['miaw'][user_id].append({"role": "assistant", "content": answer})
            
            if random.random() < 0.1:
                cleanup_old_conversations()
                
        except asyncio.TimeoutError:
            # Natural error response
            error_reactions = ['⏱️', '😅', '💤']
            try:
                await ctx.message.add_reaction(random.choice(error_reactions))
            except:
                pass
            await ctx.reply("⏱️ Aduh, Miawka kelamaan mikir nih~ Coba lagi ya! 😸")
        except Exception as e:
            print(f"Miaw command error: {type(e).__name__}: {str(e)}")
            await ctx.reply(f"😿 Miawka error nih~ `{type(e).__name__}`. Coba lagi ya!")

    # Error handler for cooldown
    @chat_with_cat.error
    async def miaw_error(ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            # Natural cooldown message
            await ctx.reply(f"😤 Tunggu bentar! Miawka butuh istirahat {error.retry_after:.0f} detik lagi~")
        else:
            print(f"Miaw command error: {error}")
            await ctx.reply("😿 Ada error nih~ Coba lagi ya!")
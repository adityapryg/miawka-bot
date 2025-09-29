import openai
import re
import asyncio
import random
import discord
from discord.ext import commands
from core.globals import conversation_histories, SYSTEM_PROMPT_MIAW, create_mood_prompt, update_mood, get_llm_config, cleanup_old_conversations

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
    'confused': ['😵', '🤔', '❓', '😅', '🙃', '🤷\u200d♀️'],
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

def setup_miaw_command(bot):
    @bot.command(name='miaw')
    @commands.cooldown(rate=3, per=60, type=commands.BucketType.user)
    async def chat_with_cat(ctx, *, message=None):
        user_id = ctx.author.id
        user_name = ctx.author.display_name
        
        # Show help/explanation if no message provided (keep embed for important info)
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
            
            embed.add_field(
                name="� Try These Interactions:",
                value="• `!miaw hai miawka!` - Greetings\n• `!miaw kamu lucu banget!` - Compliments\n• `!miaw *pat head*` - Pat reactions\n• `!miaw aku sayang kamu` - Love reactions\n• `!miaw bye bye!` - Farewells",
                inline=False
            )
            
            embed.add_field(
                name="🔧 Commands Lainnya:",
                value="• `!sensei` - Belajar serius\n• `!vtubernews` - VTuber news\n• `!trending` - Viral topics\n• `!stats` - Your stats\n• `!reset` - Reset history",
                inline=False
            )
            
            embed.set_footer(text="Ayo chat sama aku! Natural text responses, no embeds! 😸�")
            await ctx.reply(embed=embed)
            return
        
        if user_id not in conversation_histories['miaw']:
            conversation_histories['miaw'][user_id] = []

        # Add the user's message to the conversation history
        conversation_histories['miaw'][user_id].append({"role": "user", "content": message})

        # Get current mood and interactions
        mood = update_mood(user_id, 'miaw')
        interactions = detect_special_interactions(message)
        
        # Enhanced system prompt with context
        enhanced_prompt = enhance_system_prompt_with_context(SYSTEM_PROMPT_MIAW, interactions, user_name)
        
        conversation = [
            {"role": "system", "content": enhanced_prompt},
            {"role": "system", "content": create_mood_prompt(mood)},
            {"role": "system", "content": f"User name: {user_name}. Use their name naturally in conversation sometimes. RESPOND WITH NATURAL TEXT - NO MARKDOWN, NO EMBEDS, just natural conversational text."},
            {"role": "user", "content": message}
        ]

        try:
            config = get_llm_config()
            
            # Show typing indicator while processing with interactive delay
            async with ctx.typing():
                # Add interactive typing delay and reaction
                await add_interactive_elements(ctx, message, mood)
                
                # Use OpenAI client with custom base_url for Perplexity
                client = openai.OpenAI(
                    api_key=config['api_key'],
                    base_url=config['base_url'] if config['base_url'] else "https://api.openai.com/v1",
                    timeout=30.0  # Set 30 second timeout
                )

                # Use asyncio to prevent blocking Discord's heartbeat
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: client.chat.completions.create(
                        model=config['models']['miaw'],
                        messages=conversation,
                        max_tokens=2048,
                        temperature=0.9  # High temperature for more personality
                    )
                )
                answer = response.choices[0].message.content
                
                # Clean up response - remove think tags and unwanted content
                answer = clean_response(answer)
                
            # Send natural text response (no embed for normal chat)
            if len(answer) <= 2000:
                await ctx.reply(answer)
            else:
                # Split into chunks if needed
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

            # Store the assistant's reply in history
            conversation_histories['miaw'][user_id].append({"role": "assistant", "content": answer})
            
            # Periodic cleanup (10% chance after each interaction)
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
            print(f"Miaw command error: {type(e).__name__}: {str(e)}")  # Debug logging
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
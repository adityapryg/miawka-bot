import openai
import re
import asyncio
import random
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

def setup_miaw_command(bot):
    @bot.command(name='miaw')
    @commands.cooldown(rate=3, per=60, type=commands.BucketType.user)
    async def chat_with_cat(ctx, *, message=None):
        user_id = ctx.author.id
        
        # Show help/explanation if no message provided
        if message is None:
            import discord
            embed = discord.Embed(
                title="🐱 Hai, aku Miawka!",
                description="Aku adalah kucing AI yang tsundere dan suka ngobrol!",
                color=0xff69b4
            )
            
            embed.add_field(
                name="💬 Cara Menggunakan:",
                value="`!miaw [pesan kamu]`\nContoh: `!miaw halo miawka!`",
                inline=False
            )
            
            embed.add_field(
                name="😸 Kepribadianku:",
                value="• Tsundere (malu-malu tapi perhatian)\n• Suka bercanda dan main-main\n• Bisa serius kalau perlu\n• Mood-ku selalu berubah-ubah!",
                inline=False
            )
            
            embed.add_field(
                name="🎯 Aku Bisa:",
                value="• Chat santai dan ngobrol\n• Jawab pertanyaan ringan\n• Kasih saran (meski tsundere)\n• Temani kamu saat bosan\n• Ingat percakapan kita!",
                inline=False
            )
            
            embed.add_field(
                name="🔧 Commands Lainnya:",
                value="• `!sensei` - Untuk belajar serius\n• `!stats` - Lihat statistik kamu\n• `!reset` - Reset chat history\n• `!switch` - Ganti AI provider (admin)",
                inline=False
            )
            
            embed.set_footer(text="Ayo ngobrol sama aku! Tapi... bukan karena aku lonely atau apa, baka! 😤")
            
            await ctx.reply(embed=embed)
            return
        
        if user_id not in conversation_histories['miaw']:
            conversation_histories['miaw'][user_id] = []

        # Add the user's message to the conversation history
        conversation_histories['miaw'][user_id].append({"role": "user", "content": message})

        mood = update_mood(user_id, 'miaw')

        conversation = [
            {"role": "system", "content": SYSTEM_PROMPT_MIAW},
            {"role": "system", "content": create_mood_prompt(mood)},
            {"role": "user", "content": message}
        ]

        try:
            config = get_llm_config()
            
            # Show typing indicator while processing
            async with ctx.typing():
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
                        temperature=0.8
                    )
                )
                answer = response.choices[0].message.content
                
                # Clean up response - remove think tags and unwanted content
                answer = clean_response(answer)
                
            # Handle long messages by chunking them (though Miaw should be brief)
            if len(answer) <= 2000:
                await ctx.reply(answer)
            else:
                # Split into chunks if needed (rare for Miaw due to 80-char limit in prompt)
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
            await ctx.reply("⏱️ Miawka kelamaan mikir nya~. Coba lagi ya!")
        except Exception as e:
            print(f"Miaw command error: {type(e).__name__}: {str(e)}")  # Debug logging
            await ctx.reply(f"Miawka error terjadi! ({type(e).__name__}: {str(e)})")

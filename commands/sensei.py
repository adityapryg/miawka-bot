import openai
import re
import asyncio
import random
from discord.ext import commands
from core.globals import conversation_histories, SYSTEM_PROMPT_TEACHER, create_mood_prompt, update_mood, get_llm_config, cleanup_old_conversations

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

def setup_sensei_command(bot):
    @bot.command(name='sensei')
    @commands.cooldown(rate=3, per=60, type=commands.BucketType.user)
    async def ask_tutor_to_cat(ctx, *, message=None):
        user_id = ctx.author.id
        
        # Show help/explanation if no message provided
        if message is None:
            import discord
            embed = discord.Embed(
                title="👨‍🏫 Halo! Saya Sensei",
                description="Saya adalah guru AI yang siap membantu pembelajaran Anda!",
                color=0x3498db
            )
            
            embed.add_field(
                name="📚 Cara Menggunakan:",
                value="`!sensei [pertanyaan atau topik]`\nContoh: `!sensei jelaskan photosynthesis`",
                inline=False
            )
            
            embed.add_field(
                name="🎯 Spesialisasi Saya:",
                value="• Menjelaskan konsep kompleks dengan sederhana\n• Membuat analogi yang mudah dipahami\n• Pembelajaran step-by-step\n• Memberikan contoh praktis\n• Menyesuaikan dengan gaya belajar Anda",
                inline=False
            )
            
            embed.add_field(
                name="📖 Mata Pelajaran:",
                value="• Sains (Fisika, Kimia, Biologi)\n• Matematika\n• Teknologi & Programming\n• Bahasa\n• Dan banyak lagi!",
                inline=False
            )
            
            embed.add_field(
                name="💡 Tips Bertanya:",
                value="• Jelaskan level pemahaman Anda\n• Sebutkan konteks/tujuan belajar\n• Tanya hal spesifik untuk hasil terbaik\n• Saya akan selalu tanya balik untuk memastikan!",
                inline=False
            )
            
            embed.add_field(
                name="🔧 Commands Lainnya:",
                value="• `!miaw` - Chat santai\n• `!stats` - Lihat statistik belajar\n• `!reset` - Reset riwayat pembelajaran",
                inline=False
            )
            
            embed.set_footer(text="Mari belajar bersama! Jangan ragu untuk bertanya apapun 🌟")
            
            await ctx.reply(embed=embed)
            return
        
        if user_id not in conversation_histories['sensei']:
            conversation_histories['sensei'][user_id] = []

        # Add the user's message to the conversation history
        conversation_histories['sensei'][user_id].append({"role": "user", "content": message})

        mood = update_mood(user_id, 'sensei')

        conversation = [
            {"role": "system", "content": SYSTEM_PROMPT_TEACHER},
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
                        model=config['models']['sensei'],
                        messages=conversation,
                        max_tokens=1500,
                        temperature=0.6
                    )
                )
                answer = response.choices[0].message.content
                
                # Clean up response - remove think tags and unwanted content
                answer = clean_response(answer)
            
            # Note: Citations would be in response metadata if available
            # Perplexity citations handling can be added when API supports it
            
            # Handle long messages by chunking them
            if len(answer) <= 2000:
                await ctx.reply(answer)
            else:
                # Split into chunks of 2000 characters or less
                chunks = []
                current_chunk = ""
                
                for line in answer.split('\n'):
                    if len(current_chunk + line + '\n') <= 1900:  # Leave room for safety
                        current_chunk += line + '\n'
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = line + '\n'
                
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # Send first chunk as reply, rest as follow-up messages
                if chunks:
                    await ctx.reply(chunks[0])
                    for chunk in chunks[1:]:
                        await ctx.send(chunk)

            # Store the assistant's reply in history
            conversation_histories['sensei'][user_id].append({"role": "assistant", "content": answer})
            
            # Periodic cleanup (10% chance after each interaction)
            if random.random() < 0.1:
                cleanup_old_conversations()
        except asyncio.TimeoutError:
            await ctx.reply("⏱️ Sensei membutuhkan waktu terlalu lama untuk berpikir. Coba lagi ya!")
        except Exception as e:
            print(f"Sensei command error: {type(e).__name__}: {str(e)}")  # Debug logging
            await ctx.reply(f"Sensei error terjadi! ({type(e).__name__})")

from datetime import datetime
import random
import openai
from core.globals import (
    conversation_histories, user_cooldowns, user_moods,
    COOLDOWN_DURATION, SYSTEM_PROMPT_MIAW, create_mood_prompt, update_mood
)

def setup_event_handlers(bot):
    @bot.event
    async def on_ready():
        print(f'{bot.user.name} has connected to Discord!')

    @bot.event
    async def on_message(message):
        if message.author.bot:
            return  # Ignore bot messages

        user_id = message.author.id
        now = datetime.now()

        # Handling cooldown for responses
        if user_id in user_cooldowns['miaw']:
            last_response_time = user_cooldowns['miaw'][user_id]
            if now - last_response_time < COOLDOWN_DURATION:
                return  # Ignore if still in cooldown
        
        # Update cooldown timer
        user_cooldowns['miaw'][user_id] = now

        # Add more complex logic here if needed
        # Example: Random responses
        if random.random() < 0.01:
            await message.channel.send()

        if random.random() < REPLY_PROBABILITY:
            response = "Meow~";
            if len(re.findall(r'[A-Z]', message.content)) > 7:  # Jika pesan memiliki lebih dari 5 huruf kapital
                response = "Wah, santai aja, gak perlu teriak-teriak."
            elif len(re.findall(r'[\U0001F600-\U0001F64F]', message.content)) > 3:  # Jika ada lebih dari 3 emoji
                response = "Banyak banget emotnya, koleksi lu?"

            # Simulate typing before replying
            async with message.channel.typing():
                await message.channel.send(response)

        # Process commands in on_message
        await bot.process_commands(message)

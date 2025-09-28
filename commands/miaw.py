import openai
from discord.ext import commands
from core.globals import conversation_histories, SYSTEM_PROMPT_MIAW, create_mood_prompt, update_mood, get_llm_config

def setup_miaw_command(bot):
    @bot.command(name='miaw')
    @commands.cooldown(rate=3, per=60, type=commands.BucketType.user)
    async def chat_with_cat(ctx, *, message):
        user_id = ctx.author.id
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
            
            # Use OpenAI client with custom base_url for Perplexity
            client = openai.OpenAI(
                api_key=config['api_key'],
                base_url=config['base_url'] if config['base_url'] else "https://api.openai.com/v1"
            )

            response = client.chat.completions.create(
                model=config['models']['miaw'],
                messages=conversation,
                max_tokens=2048,
                temperature=0.8
            )
            answer = response.choices[0].message.content
                
            await ctx.reply(answer)

            # Store the assistant's reply in history
            conversation_histories['miaw'][user_id].append({"role": "assistant", "content": answer})
        except Exception as e:
            print(f"Miaw command error: {type(e).__name__}: {str(e)}")  # Debug logging
            await ctx.reply(f"Miawka error terjadi! ({type(e).__name__})")

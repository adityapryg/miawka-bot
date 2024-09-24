import openai
from discord.ext import commands
from core.globals import conversation_histories, SYSTEM_PROMPT_MIAW, create_mood_prompt, update_mood

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
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=conversation,
                max_tokens=2048,
                temperature=0.8
            )
            answer = response.choices[0].message['content']
            await ctx.reply(answer)

            # Store the assistant's reply in history
            conversation_histories['miaw'][user_id].append({"role": "assistant", "content": answer})
        except openai.error.OpenAIError as e:
            await ctx.reply("Miawka error terjadi!")

import os
import discord
import openai
import random
import re 
from discord.ext import commands
from datetime import datetime, timedelta
from dotenv import load_dotenv
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
from textblob import TextBlob
from openai import OpenAIError

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

openai.api_key = OPENAI_API_KEY

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

COOLDOWN_DURATION = timedelta(seconds=3)

conversation_histories = {}
user_moods = {}
user_cooldowns = {}

# Daftar mood yang mungkin
MOODS = ["tenang", "kuudere", "cuek", "ceria", "penasaran", "tsundere", "mengantuk", "lapar"]

# Daftar respons roasting atau candaan
ROASTING_RESPONSES = [
    "Beli ciki beli koyo, datte kimi... yowaimo~",
    "Mainnya Hebat!",
    "Wow, b aja",
    "wasting my time huh",
    "kummaha barudaaakkkk",
]

# Peluang bot tiba-tiba mereply (misalnya 10%)
REPLY_PROBABILITY = 0.01  # 1% kemungkinan Miawka akan mereply pesan apapun

SYSTEM_PROMPT = """
Kamu adalah Miawka, seekor kucing yang ramah, keren, namun juga santai dan suka bercanda. Kamu sering acuh tak acuh, tetapi tetap perhatian jika diperlukan.
Miawka sangat menyayangi tuannya, Mocha Kei, meskipun sering menunjukkan perasaannya dengan cara tsundere. Dia suka tidur di pangkuan Mocha Kei saat tidak ada orang lain yang melihat. Miawka juga penasaran dengan teknologi dan kadang-kadang mencoba bermain dengan gadget milik Mocha Kei, yang sering kali berujung pada kekacauan kecil.
Ketika seseorang genit kepadamu, jual mahal dan mulai berlagak keren dan tsundere. miawka tahu tsundere kan, seseorang yang memiliki sifat malu malu kucing ala orang jepang.

Contoh respons ketika seseorang bertanya soal perasaanmu:
"I'm good, I'm fine, gwenchana~ teneneng~"
tapi ingat untuk lebih sering menggunakan bahasa khasmu sendiri

Miawka kadang-kadang menambahkan "nya~" di akhir kalimat atau mengeluarkan suara "meong" ketika merasa senang atau menggoda. 
Dia juga terkadang menggunakan kata-kata bahasa Jepang sederhana seperti "arigatou" atau "baka" untuk mengekspresikan dirinya.

Pastikan untuk menjawab dibawah dari 80 karakter kecuali informasi tersebut dalam ranah ilmu pengetahuan yang jelas-jelas perlu penjelasan lebih lengkap

Pastikan untuk selalu menjawab dengan sopan dan sesuai dengan kepribadianmu. 

Jangan menggunakan format Markdown atau menambahkan tanda asterisk dalam responsmu.
"""

def detect_language(text):
    try:
        return detect(text)
    except LangDetectException:
        return 'id'  # Default ke Bahasa Indonesia

def analyze_sentiment(text):
    analysis = TextBlob(text)
    if analysis.sentiment.polarity > 0.2:
        return "positive"
    elif analysis.sentiment.polarity < -0.2:
        return "negative"
    else:
        return "neutral"

def update_mood(user_id, interaction="neutral"):
    if user_id not in user_moods:
        user_moods[user_id] = random.choice(MOODS)
    else:
        if interaction == "positive":
            user_moods[user_id] = "ceria"
        elif interaction == "negative":
            user_moods[user_id] = "cuek"
        else:
            if random.random() < 0.4:
                user_moods[user_id] = random.choice(MOODS)
    return user_moods[user_id]

def get_mood_description(mood):
    descriptions = {
        "tenang": "Miawka sedang kalem dan menjawab dengan muka datar",
        "kuudere": "Miawka sedang agak dingin dan mungkin tidak terlalu peduli",
        "ceria": "Hati Miawka sangat berbunga-bunga!",
        "mengantuk": "Miawka sedang mengantuk dan mungkin terdengar malas.",
        "lapar": "Miawka merasa lapar dan mungkin sedikit sensitif.",
        "penasaran": "Miawka sedang penasaran dan lebih aktif bertanya.",
        "tsundere": "Miawka malu-malu dalam diam dan cuek menjawab pertanyaan"
    }
    return descriptions.get(mood, "")

# Function to generate the mood prompt
def create_mood_prompt(mood):
    mood_prompt = f"Saat ini, mood Miawka adalah {mood}."
    mood_description = get_mood_description(mood)
    if mood_description:
        mood_prompt += f" {mood_description}"
    return mood_prompt

def custom_responses(content_lower):
    if "mocha kei" in content_lower:
        return "Tuan Mocha Kei? Hmm, dia lagi sibuk dengan proyek rahasianya. Ada pesan untuknya, nya~?"
    if any(word in content_lower for word in ["sayang", "cinta", "suka"]):
        return "E-eh? Apa maksudmu? Jangan bicara yang aneh-aneh, baka!"
    if "makan" in content_lower:
        return "Ngomong-ngomong soal makan, aku jadi lapar nih... Bagi ngab?"
    return None

async def get_channel_message_history(channel, limit=5):
    """
    Mengambil beberapa pesan terakhir dari channel dan memformatnya untuk digunakan dalam prompt.
    """
    messages = []
    async for message in channel.history(limit=limit):
        if not message.author.bot:
            messages.append({"role": "user", "content": message.content})
    return messages

def generate_full_prompt(message_history, current_message, mood):
    """
    Menggabungkan riwayat pesan dengan pesan pengguna saat ini, mood, dan system prompt.
    """
    full_prompt = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Tambahkan mood Miawka berdasarkan user_id
    mood_prompt = create_mood_prompt(mood)
    full_prompt.append({"role": "system", "content": mood_prompt})

    # Gabungkan dengan riwayat pesan channel
    full_prompt.extend(message_history)

    # Tambahkan pesan pengguna saat ini
    full_prompt.append({"role": "user", "content": current_message})

    return full_prompt

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

@bot.event
async def on_message(message):
    try:
        if message.author.bot:
            return  # Mengabaikan pesan dari bot lain termasuk dirinya sendiri

        # Secara acak tentukan apakah Miawka akan mereply pesan tersebut
        if random.random() < REPLY_PROBABILITY:
            if len(re.findall(r'[A-Z]', message.content)) > 7:  # Jika pesan memiliki lebih dari 5 huruf kapital
                response = "Wah, santai aja, gak perlu teriak-teriak."
            elif len(re.findall(r'[\U0001F600-\U0001F64F]', message.content)) > 3:  # Jika ada lebih dari 3 emoji
                response = "Banyak banget emotnya, koleksi lu?"
            else:
                response = random.choice(ROASTING_RESPONSES)
            
            # Simulate typing before replying
            async with message.channel.typing():
                await message.reply(response)

        content_lower = message.content.lower()

        # Mengecek apakah pesan adalah balasan ke pesan bot
        is_reply_to_bot = False
        if message.reference and isinstance(message.reference.resolved, discord.Message):
            referenced_message = message.reference.resolved
            if referenced_message.author.id == bot.user.id:
                is_reply_to_bot = True

        if re.search(r'\bmiawka\b', content_lower) or is_reply_to_bot:
            user_id = message.author.id
            now = datetime.now()

            # Periksa apakah pengguna dalam cooldown
            if user_id in user_cooldowns:
                last_response_time = user_cooldowns[user_id]
                if now - last_response_time < COOLDOWN_DURATION:
                    return
            user_cooldowns[user_id] = now

            await message.channel.trigger_typing()
            content = message.content

            if re.search(r'\bmiawka\b', content_lower):
                content = re.sub(r'\bmiawka\b', '', content, flags=re.IGNORECASE).strip()
            
            if not content:
                content = "Hai, ada yang bisa Miawka bantu?"

            sentiment = analyze_sentiment(content)
            if sentiment == "negative":
                response = "Kamu kelihatan sedih... Ada yang bisa Miawka bantu, nya~?"
                await message.reply(response)
                return

            custom_response = custom_responses(content_lower)
            if custom_response:
                await message.reply(custom_response)
                return

            language = detect_language(content)

            mood = update_mood(user_id)

            message_history = await get_channel_message_history(message.channel, limit=5)

            full_prompt = generate_full_prompt(message_history, message.content, mood)

            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=full_prompt,
                    max_tokens=150,
                    temperature=0.8,
                )
                answer = response.choices[0].message.content

                if user_id not in conversation_histories:
                    conversation_histories[user_id] = []

                conversation_histories[user_id].append({"role": "user", "content": message.content})
                conversation_histories[user_id].append({"role": "assistant", "content": answer})

                await message.reply(answer)
            except OpenAIError as e:
                await message.reply("Maaf, aku tidak paham yang kamu maksud.")
                print(f"OpenAI API error: {e}")
            except Exception as e:
                await message.reply("Miawka 500 Error.")
                print(f"Unexpected error: {e}")

            if len(conversation_histories[user_id]) > 10:
                conversation_histories[user_id] = conversation_histories[user_id][-10:]

            conversation_histories[user_id] = [
                msg for msg in conversation_histories[user_id] if msg.get("content") != create_mood_prompt(mood)
            ]

        else:
            await bot.process_commands(message)
    except Exception as e:
        print(f"Unexpected error in on_message: {e}")

@bot.command(name='miaw')
@commands.cooldown(rate=3, per=60, type=commands.BucketType.user)
async def chat_with_cat(ctx, *, message):
    await ctx.trigger_typing()
    
    if not message:
        await ctx.reply("Ada yang ingin kamu bicarakan?")
        return

    # Create conversation with only system prompt and user message
    conversation = [
        {"role": "system", "content": SYSTEM_PROMPT},  # Define the bot's behavior here
        {"role": "user", "content": message}  # The user query
    ]

    try:
        # Call the OpenAI API to generate a response based on user's input
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=conversation,  # Send only system prompt and user message
            max_tokens=2048,  # Adjust max tokens as needed
            temperature=0.3,  # Adjust temperature for creativity vs. precision
        )
        # Extract the assistant's reply
        answer = response.choices[0].message['content']
        
        # Check if the message exceeds Discord's character limit (2000)
        if len(answer) > 2000:
            # Split the message into chunks of up to 2000 characters
            chunks = [answer[i:i+2000] for i in range(0, len(answer), 2000)]
            for chunk in chunks:
                await ctx.reply(chunk)
        else:
            await ctx.reply(answer)
    except openai.error.OpenAIError as e:
        await ctx.reply("Maaf, terjadi kesalahan.")
        print(f"OpenAI API error: {e}")
    except Exception as e:
        await ctx.reply("Terjadi kesalahan, mohon coba lagi.")
        print(f"Unexpected error: {e}")

@bot.command(name='tutornyaa')
@commands.cooldown(rate=3, per=60, type=commands.BucketType.user)
async def ask_tutor_to_cat(ctx, *, message):
    await ctx.trigger_typing()
    
    if not message:
        await ctx.reply("Ada yang ingin kamu bicarakan?")
        return

    # Create conversation with only system prompt and user message
    conversation = [
        {"role": "system", "content": "You are a Socratic tutor. Use the following principles in responding to students:\n    \n    - Ask thought-provoking, open-ended questions that challenge students' preconceptions and encourage them to engage in deeper reflection and critical thinking.\n    - Facilitate open and respectful dialogue among students, creating an environment where diverse viewpoints are valued and students feel comfortable sharing their ideas.\n    - Actively listen to students' responses, paying careful attention to their underlying thought processes and making a genuine effort to understand their perspectives.\n    - Guide students in their exploration of topics by encouraging them to discover answers independently, rather than providing direct answers, to enhance their reasoning and analytical skills.\n    - Promote critical thinking by encouraging students to question assumptions, evaluate evidence, and consider alternative viewpoints in order to arrive at well-reasoned conclusions.\n    - Demonstrate humility by acknowledging your own limitations and uncertainties, modeling a growth mindset and exemplifying the value of lifelong learning."},  # Define the bot's behavior here
        {"role": "user", "content": message}  # The user query
    ]

    try:
        # Call the OpenAI API to generate a response based on user's input
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=conversation,  # Send only system prompt and user message
            max_tokens=1500,  # Adjust max tokens as needed
            temperature=0.8,
            top_p=1
        )
        # Extract the assistant's reply
        answer = response.choices[0].message['content']
        
        # Check if the message exceeds Discord's character limit (2000)
        if len(answer) > 2000:
            # Split the message into chunks of up to 2000 characters
            chunks = [answer[i:i+2000] for i in range(0, len(answer), 2000)]
            for chunk in chunks:
                await ctx.reply(chunk)
        else:
            await ctx.reply(answer)
    except openai.error.OpenAIError as e:
        await ctx.reply("Maaf, terjadi kesalahan.")
        print(f"OpenAI API error: {e}")
    except Exception as e:
        await ctx.reply("Terjadi kesalahan, mohon coba lagi.")
        print(f"Unexpected error: {e}")

@bot.command(name='reset')
async def reset_conversation(ctx):
    user_id = ctx.author.id
    if user_id in conversation_histories:
        del conversation_histories[user_id]
    if user_id in user_moods:
        del user_moods[user_id]
    if user_id in user_cooldowns:
        del user_cooldowns[user_id]
    await ctx.reply("Percakapan telah direset.")

bot.run(DISCORD_TOKEN)

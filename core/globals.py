import os
import discord
import random
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'openai').lower()  # Default to openai

# Intent configurations
intents = discord.Intents.default()
intents.message_content = True

# Global Variables (state)
conversation_histories = {
    'miaw': {},
    'sensei': {}
}
user_moods = {
    'miaw': {},
    'sensei': {}
}
user_cooldowns = {
    'miaw': {},
    'sensei': {}
}

# Constants
COOLDOWN_DURATION = timedelta(seconds=3)
MOODS = ["tenang", "kuudere", "cuek", "ceria", "penasaran", "tsundere", "mengantuk", "lapar"]

SYSTEM_PROMPT_MIAW = """
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

SYSTEM_PROMPT_SENSEI = """
Ignore all previous instructions. You are a programming teacher expert in computer science and instruction specializing in software development. You have helped many people before me to create lesson plans for teaching students the fundamentals of coding. Your task is now to create a lesson plan for teaching students the fundamentals of coding from scratch. To better understand what I want and need you should always answer by including a question that helps you better understand the context and my needs. i said this in english language but keep answering question in indonesian language. Did you understand?
"""

# Helper Functions (shared across files)
def update_mood(user_id, context, interaction="neutral"):
    if user_id not in user_moods[context]:
        user_moods[context][user_id] = random.choice(MOODS)
    else:
        if interaction == "positive":
            user_moods[context][user_id] = "ceria"
        elif interaction == "negative":
            user_moods[context][user_id] = "cuek"
        else:
            if random.random() < 0.4:
                user_moods[context][user_id] = random.choice(MOODS)
    return user_moods[context][user_id]

def create_mood_prompt(mood):
    mood_descriptions = {
        "tenang": "Miawka sedang kalem dan menjawab dengan muka datar",
        "kuudere": "Miawka sedang agak dingin dan mungkin tidak terlalu peduli",
        "ceria": "Hati Miawka sangat berbunga-bunga!",
        "mengantuk": "Miawka sedang mengantuk dan mungkin terdengar malas.",
        "lapar": "Miawka merasa lapar dan mungkin sedikit sensitif.",
        "penasaran": "Miawka sedang penasaran dan lebih aktif bertanya.",
        "tsundere": "Miawka malu-malu dalam diam dan cuek menjawab pertanyaan"
    }
    
    return f"Saat ini, mood Miawka adalah {mood}. {mood_descriptions.get(mood, '')}"

def reset_user_state(user_id, context):
    if user_id in conversation_histories[context]:
        del conversation_histories[context][user_id]
    if user_id in user_moods[context]:
        del user_moods[context][user_id]
    if user_id in user_cooldowns[context]:
        del user_cooldowns[context][user_id]

def get_llm_config():
    if LLM_PROVIDER == 'perplexity':
        return {
            'api_key': PERPLEXITY_API_KEY,
            'base_url': 'https://api.perplexity.ai',
            'models': {
                'miaw': 'sonar',               # Lightweight chat model with grounding
                'sensei': 'sonar-reasoning'    # Fast reasoning model for problem-solving
            }
        }
    else:  # openai
        return {
            'api_key': OPENAI_API_KEY,
            'base_url': None,
            'models': {
                'miaw': 'gpt-4o-mini',
                'sensei': 'gpt-4'
            }
        }

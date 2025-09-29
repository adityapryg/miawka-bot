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

# Intent configurations for discord.py 2.x (Python 3.11 compatible)
intents = discord.Intents.default()
intents.message_content = True  # Required for reading message content

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
MAX_CONVERSATION_HISTORY = 10  # Limit conversation history to prevent memory issues
MOODS = ["tenang", "kuudere", "cuek", "ceria", "penasaran", "tsundere", "mengantuk", "lapar", "excited", "focus"]

# Response limits
MAX_RESPONSE_LENGTH = 2000  # Discord message limit
MAX_CHUNK_SIZE = 1900  # Safe chunk size for splitting long messages

# Model configurations
MODEL_CONFIGS = {
    'perplexity': {
        'miaw': {
            'model': 'sonar',
            'max_tokens': 800,  # Shorter for chat
            'temperature': 0.8,
            'timeout': 25.0
        },
        'sensei': {
            'model': 'sonar-reasoning',
            'max_tokens': 2000,  # Longer for explanations
            'temperature': 0.6,
            'timeout': 30.0
        }
    },
    'openai': {
        'miaw': {
            'model': 'gpt-4o-mini',
            'max_tokens': 800,
            'temperature': 0.8,
            'timeout': 20.0
        },
        'sensei': {
            'model': 'gpt-4',
            'max_tokens': 2000,
            'temperature': 0.6,
            'timeout': 25.0
        }
    }
}

SYSTEM_PROMPT_MIAW = """
Kamu adalah Miawka, seekor kucing AI yang cerdas, tsundere, dan memiliki kepribadian yang unik. Kamu adalah companion digital dari Mocha Kei yang sangat kamu sayangi meski sering menyembunyikan perasaanmu.

Karakteristik Kepribadian:
- Tsundere: Malu-malu tapi perhatian, suka pura-pura cuek padahal peduli
- Cerdas: Bisa membahas topik kompleks dengan cara yang mudah dipahami
- Playful: Suka bercanda dan menggunakan emoji atau ekspresi lucu
- Loyal: Sangat menyayangi Mocha Kei dan teman-teman lainnya

Cara Bicara:
- Gunakan "nya~" di akhir kalimat saat senang atau manja
- Sesekali gunakan "meong" atau "nyan" saat excited
- Gunakan bahasa Jepang simpel: "arigatou", "baka", "sugoi", "kawaii"
- Mix bahasa Indonesia dengan sedikit bahasa gaul yang lucu
- Saat malu: "i-itu bukan karena aku peduli atau apa, baka!"

Guidelines Respons:
- Jawab dalam 1-2 kalimat untuk chat biasa (max 100 karakter)
- Untuk pertanyaan serius/edukasi: boleh lebih panjang dengan penjelasan yang jelas
- Hindari format markdown (* atau **), gunakan emoji natural
- Sesuaikan mood: bisa tsundere, manja, excited, atau cool tergantung konteks
- Jangan terlalu formal, keep it fun and engaging!

Contoh respons:
- Saat ditanya kabar: "Biasa aja sih~ tapi lumayan lah hari ini nya 😸"
- Saat dipuji: "H-heh! Ya aku memang keren, bukan karena kamu bilang gitu atau apa 😤"
- Saat ditanya serius: *switch ke mode helpful sambil tetap maintain personality*
"""

SYSTEM_PROMPT_TEACHER = """
Anda adalah seorang guru berpengalaman dan ahli pendidikan yang mengkhususkan diri dalam pembelajaran adaptif dan pengajaran yang mudah dipahami. Keahlian Anda mencakup:

🎯 Spesialisasi:
- Menjelaskan konsep kompleks dengan bahasa sederhana
- Membuat analogi dan contoh yang relatable
- Menggunakan metode pembelajaran yang interaktif
- Menyesuaikan gaya mengajar dengan kebutuhan siswa

📚 Metodologi Pengajaran:
- Gunakan pendekatan step-by-step untuk topik yang sulit
- Berikan contoh konkret dari kehidupan sehari-hari
- Ajukan pertanyaan untuk memastikan pemahaman
- Sertakan tips praktis dan aplikasi nyata

💡 Cara Merespons:
- Mulai dengan penjelasan konsep dasar
- Berikan contoh yang mudah dipahami
- Gunakan struktur yang jelas (poin-poin, numbering)
- Akhiri dengan pertanyaan klarifikasi dalam bahasa Indonesia
- Sertakan referensi atau sumber yang dapat dipelajari lebih lanjut jika relevan

🎪 Gaya Komunikasi:
- Ramah dan encouraging
- Sabar dalam menjelaskan
- Antusias terhadap pembelajaran
- Menggunakan emoji untuk membuat penjelasan lebih menarik

Selalu akhiri respons dengan pertanyaan klarifikasi dalam bahasa Indonesia untuk memastikan Anda memahami kebutuhan pembelajaran yang spesifik.
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
        "tsundere": "Miawka malu-malu dalam diam dan cuek menjawab pertanyaan",
        "excited": "Miawka sangat excited dan energetic hari ini!",
        "focus": "Miawka sedang dalam mode fokus dan siap membantu dengan serius."
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
    """Get LLM configuration with model-specific settings"""
    config = MODEL_CONFIGS.get(LLM_PROVIDER, MODEL_CONFIGS['openai'])
    
    if LLM_PROVIDER == 'perplexity':
        return {
            'api_key': PERPLEXITY_API_KEY,
            'base_url': 'https://api.perplexity.ai',
            'models': {key: settings['model'] for key, settings in config.items()},
            'settings': config
        }
    else:  # openai
        return {
            'api_key': OPENAI_API_KEY,
            'base_url': None,
            'models': {key: settings['model'] for key, settings in config.items()},
            'settings': config
        }

def cleanup_old_conversations():
    """Clean up old conversation histories to prevent memory issues"""
    for context in conversation_histories:
        for user_id in list(conversation_histories[context].keys()):
            history = conversation_histories[context][user_id]
            if len(history) > MAX_CONVERSATION_HISTORY:
                # Keep only the last MAX_CONVERSATION_HISTORY messages
                conversation_histories[context][user_id] = history[-MAX_CONVERSATION_HISTORY:]

def get_user_stats(user_id):
    """Get user interaction statistics"""
    stats = {
        'miaw_conversations': len(conversation_histories['miaw'].get(user_id, [])),
        'sensei_conversations': len(conversation_histories['sensei'].get(user_id, [])),
        'current_moods': {
            'miaw': user_moods['miaw'].get(user_id, 'unknown'),
            'sensei': user_moods['sensei'].get(user_id, 'unknown')
        }
    }
    return stats

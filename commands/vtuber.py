import discord
import openai
import re
import asyncio
import random
from discord.ext import commands
from core.globals import get_llm_config, cleanup_old_conversations
from core.gamification import gamification, get_level_title

async def handle_vtuber_rewards(ctx, exp_result):
    """Handle gamification rewards for VTuber commands"""
    # Show level up notification
    if exp_result["level_ups"] > 0:
        level_title = get_level_title(exp_result["new_level"])
        level_up_msg = f"🎬 **VTUBER LEVEL UP!** 🎬\n⭐ {ctx.author.display_name} reached Level {exp_result['new_level']} - {level_title}! ⭐"
        try:
            await ctx.channel.send(level_up_msg)
        except:
            pass
    
    # Check for new achievements
    new_achievements = gamification.check_achievements(str(ctx.author.id))
    if new_achievements:
        for ach_id in new_achievements:
            achievement = gamification.achievements[ach_id]
            ach_msg = f"🏆 **ACHIEVEMENT UNLOCKED!** 🏆\n{achievement['icon']} **{achievement['name']}**\n{achievement['description']} (+{achievement['exp']} EXP)"
            try:
                await ctx.channel.send(ach_msg)
            except:
                pass

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

async def get_vtuber_response(prompt, context="vtuber"):
    """Get response from AI with VTuber-specific context"""
    try:
        config = get_llm_config()
        
        # Use OpenAI client with custom base_url for Perplexity
        client = openai.OpenAI(
            api_key=config['api_key'],
            base_url=config['base_url'] if config['base_url'] else "https://api.openai.com/v1",
            timeout=30.0
        )

        # Use asyncio to prevent blocking Discord's heartbeat
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=config['models']['sensei'],  # Use sensei model for research tasks
                messages=[
                    {"role": "system", "content": "You are a helpful assistant specializing in Indonesian VTuber industry and content creation. Always provide current, accurate information with sources when possible. Respond in Indonesian unless specifically asked otherwise."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.6
            )
        )
        
        answer = response.choices[0].message.content
        return clean_response(answer)
        
    except asyncio.TimeoutError:
        return "⏱️ Maaf, permintaan membutuhkan waktu terlalu lama. Coba lagi ya!"
    except Exception as e:
        print(f"VTuber command error: {type(e).__name__}: {str(e)}")
        return f"❌ Terjadi error: {type(e).__name__}"

def setup_vtuber_commands(bot):
    
    @bot.command(name='vtubernews')
    @commands.cooldown(rate=2, per=120, type=commands.BucketType.user)
    async def vtuber_news(ctx):
        """Get latest Indonesian VTuber news and updates"""
        
        prompt = """
        Berikan berita terbaru tentang VTuber Indonesia dalam 48 jam terakhir. Fokus pada:

        🎥 BERITA TERBARU:
        1. Debut VTuber baru dari agency Indonesia
        2. Pencapaian milestone penting (subscriber, monetization, dll)
        3. Kolaborasi menarik antar VTuber Indonesia
        4. Event VTuber atau pengumuman penting
        5. Kontroversi atau drama (jika ada, bahas dengan netral)

        📊 TRENDING TOPICS:
        - Apa yang sedang ramai dibicarakan di komunitas VTuber Indonesia
        - Hashtag atau topik yang viral
        - Game atau konten yang lagi trending

        Format jawaban dengan emoji dan struktur yang rapi untuk Discord. 
        Sertakan tanggal jika memungkinkan dan berikan konteks singkat untuk setiap berita.
        Maksimal 1500 karakter.
        """
        
        async with ctx.typing():
            response = await get_vtuber_response(prompt)
            
        # Handle long messages by chunking
        if len(response) <= 2000:
            embed = discord.Embed(
                title="📺 VTuber Indonesia News Update",
                description=response,
                color=0xff69b4
            )
            embed.set_footer(text="Use !trending untuk konten viral • !gametrends untuk game populer")
            await ctx.reply(embed=embed)
        else:
            # Split into chunks
            chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
            
            embed = discord.Embed(
                title="📺 VTuber Indonesia News Update",
                description=chunks[0],
                color=0xff69b4
            )
            await ctx.reply(embed=embed)
            
            for chunk in chunks[1:]:
                await ctx.send(chunk)
        
        # Add gamification rewards for VTuber command usage
        gamification.increment_stat(str(ctx.author.id), 'vtuber_commands')
        exp_result = gamification.add_exp(str(ctx.author.id), 12, "vtuber_news")
        
        # Check for level ups and achievements
        await handle_vtuber_rewards(ctx, exp_result)

    @bot.command(name='trending')
    @commands.cooldown(rate=2, per=120, type=commands.BucketType.user)
    async def trending_indonesia(ctx, platform: str = None):
        """Get trending topics in Indonesia for VTuber content"""
        
        # Default to X/Twitter since Indonesian VTubers primarily use it
        if not platform:
            platform = 'x'
        
        # Support both 'x' and 'twitter' for the same platform
        platform_lower = platform.lower()
        if platform_lower in ['twitter', 'x']:
            platform_display = "X (Twitter)"
            platform_search = "X/Twitter"
        elif platform_lower == 'tiktok':
            platform_display = "TikTok"
            platform_search = "TikTok"
        elif platform_lower == 'youtube':
            platform_display = "YouTube"
            platform_search = "YouTube"
        elif platform_lower == 'instagram':
            platform_display = "Instagram"
            platform_search = "Instagram"
        else:
            embed = discord.Embed(
                title="❌ Platform Tidak Valid",
                description="Platform yang didukung:\n• `x` atau `twitter` (default) - Platform utama VTuber Indonesia\n• `tiktok` - Konten short-form viral\n• `youtube` - Video content trends\n• `instagram` - Visual content trends",
                color=0xff0000
            )
            await ctx.reply(embed=embed)
            return
        
        prompt = f"""
        Apa yang sedang trending di {platform_search} Indonesia hari ini yang bisa dijadikan konten VTuber? 
        
        {"📱 FOKUS X/TWITTER - Platform utama VTuber Indonesia untuk:" if platform_lower in ['x', 'twitter'] else ""}
        {"- Announcement dan update dari VTuber lain" if platform_lower in ['x', 'twitter'] else ""}
        {"- Hashtag dan topik viral dalam komunitas VTuber" if platform_lower in ['x', 'twitter'] else ""}
        {"- Interaksi dan engagement dengan fans" if platform_lower in ['x', 'twitter'] else ""}
        {"" if platform_lower in ['x', 'twitter'] else ""}

        🔥 TRENDING TOPICS:
        1. Hashtag populer (#TrendingHashtag)
        2. Topik viral yang sedang ramai dibicarakan
        3. Meme terbaru yang lagi hits dan relate-able
        4. Challenge atau trend yang cocok untuk VTuber
        5. Berita atau kejadian yang jadi perbincangan hangat

        🎮 ENTERTAINMENT & VTUBER SPECIFIC:
        - Lagu atau musik yang lagi viral di kalangan VTuber
        - Anime/manga yang trending dan cocok untuk reaction content
        - Game yang lagi ramai dibahas VTuber Indonesia
        - Kolaborasi atau event VTuber yang lagi buzz

        💡 CONTENT IDEAS UNTUK VTUBER:
        Untuk setiap trend, berikan saran spesifik bagaimana VTuber bisa memanfaatkan:
        - Tweet/posting strategy untuk engagement
        - Stream topic yang relate dengan trend
        - Interactive content dengan audience
        - Collaboration opportunities yang muncul dari trend

        ⚠️ Hindari topik sensitif politik atau kontroversial yang bisa merugikan brand VTuber.
        Fokus pada konten yang safe untuk sponsorship dan family-friendly.
        Format dengan emoji dan maksimal 1500 karakter.
        """
        
        async with ctx.typing():
            response = await get_vtuber_response(prompt)
        
        embed = discord.Embed(
            title=f"🔥 Trending Indonesia - {platform_display}",
            description=response,
            color=0x1da1f2 if platform_lower in ['x', 'twitter'] else 0xff6b6b
        )
        
        # Add platform-specific footer
        if platform_lower in ['x', 'twitter']:
            embed.set_footer(text="💡 X/Twitter adalah platform utama VTuber Indonesia • !gametrends untuk game populer")
        else:
            embed.set_footer(text="Use !trending untuk X/Twitter trends • !gametrends untuk game populer")
        
        await ctx.reply(embed=embed)
        
        # Add gamification rewards
        gamification.increment_stat(str(ctx.author.id), 'vtuber_commands')
        exp_result = gamification.add_exp(str(ctx.author.id), 10, "trending_check")
        await handle_vtuber_rewards(ctx, exp_result)

    @bot.command(name='gametrends')
    @commands.cooldown(rate=2, per=120, type=commands.BucketType.user)
    async def game_trends(ctx, category: str = None):
        """Get trending games popular among Indonesian gamers and VTubers"""
        
        valid_categories = ['mobile', 'pc', 'horror', 'indie', 'collab']
        if category and category.lower() not in valid_categories:
            embed = discord.Embed(
                title="❌ Kategori Tidak Valid",
                description=f"Kategori yang tersedia: `{', '.join(valid_categories)}`",
                color=0xff0000
            )
            await ctx.reply(embed=embed)
            return
        
        category_text = f" kategori {category}" if category else ""
        
        prompt = f"""
        Game apa yang sedang trending di kalangan gamer Indonesia{category_text}, khususnya yang cocok untuk VTuber stream:

        🎮 GAME POPULER:
        1. Mobile games yang lagi hype (MLBB, CODM, Genshin, dll)
        2. PC games yang trending di Indonesia
        3. Game horror untuk variety content
        4. Game indie Indonesia yang baru release
        5. Game yang cocok untuk kolaborasi/multiplayer

        📊 ANALISIS TREND:
        - Mengapa game ini trending?
        - Audience target dan demografi
        - Potensi viewer engagement
        - Durasi trend yang diprediksi

        💡 STREAMING TIPS:
        - Format stream yang cocok (solo, collab, tournament)
        - Waktu streaming optimal
        - Cara memaksimalkan viewer interaction
        - Title dan thumbnail suggestions

        🎯 MONETIZATION:
        - Sponsor opportunities
        - Merchandise tie-ins
        - Community building potential

        Format dengan emoji dan struktur rapi. Maksimal 1500 karakter.
        """
        
        async with ctx.typing():
            response = await get_vtuber_response(prompt)
        
        embed = discord.Embed(
            title=f"🎮 Game Trends Indonesia{f' - {category.title()}' if category else ''}",
            description=response,
            color=0x00ff00
        )
        embed.set_footer(text="Use !collab untuk opportunities • !culture untuk konten budaya")
        await ctx.reply(embed=embed)
        
        # Add gamification rewards
        gamification.increment_stat(str(ctx.author.id), 'vtuber_commands')
        exp_result = gamification.add_exp(str(ctx.author.id), 10, "game_trends")
        await handle_vtuber_rewards(ctx, exp_result)

    @bot.command(name='culture', aliases=['budaya'])
    @commands.cooldown(rate=2, per=120, type=commands.BucketType.user)
    async def indonesian_culture(ctx, region: str = None):
        """Get Indonesian cultural content ideas for VTubers"""
        
        regions = ['jawa', 'sumatra', 'bali', 'kalimantan', 'sulawesi', 'papua', 'ntt', 'maluku']
        if region and region.lower() not in regions:
            embed = discord.Embed(
                title="🗺️ Pilih Daerah",
                description=f"Daerah yang tersedia:\n`{', '.join(regions)}` atau kosongkan untuk umum",
                color=0xffa500
            )
            await ctx.reply(embed=embed)
            return
        
        region_text = f" daerah {region}" if region else " Indonesia"
        
        prompt = f"""
        Ide konten budaya{region_text} yang menarik untuk VTuber:

        🏛️ KONTEN EDUKASI:
        1. Cerita rakyat dan legenda yang menarik untuk storytelling
        2. Tradisi dan festival yang bisa dijelaskan dengan fun
        3. Sejarah singkat yang engaging untuk audience muda
        4. Bahasa daerah atau slang yang unik
        5. Permainan tradisional yang bisa diadaptasi untuk stream

        🍲 FOOD CONTENT:
        - Makanan tradisional yang bisa untuk cooking stream
        - Street food yang viral dan unik
        - Minuman khas yang bisa direview
        - Food challenge dengan makanan lokal

        🎨 CREATIVE CONTENT:
        - Seni tradisional yang bisa distreaming (batik, lukis, dll)
        - Musik tradisional yang bisa diaransemen modern
        - Fashion tradisional untuk outfit showcase
        - Kerajinan tangan untuk DIY content

        🎭 INTERACTIVE IDEAS:
        - Quiz tentang budaya untuk audience
        - Storytelling session dengan cerita rakyat
        - Language lesson (bahasa daerah)
        - Cultural exchange dengan VTuber daerah lain

        💡 COLLABORATION OPPORTUNITIES:
        - Partnership dengan cultural institutions
        - Collab dengan local artists
        - Educational partnership potential

        Format engaging dengan emoji. Maksimal 1500 karakter.
        """
        
        async with ctx.typing():
            response = await get_vtuber_response(prompt)
        
        embed = discord.Embed(
            title=f"🏛️ Konten Budaya Indonesia{f' - {region.title()}' if region else ''}",
            description=response,
            color=0xffd700
        )
        embed.set_footer(text="Use !collab untuk networking • !trending untuk topik viral")
        await ctx.reply(embed=embed)
        
        # Add gamification rewards
        gamification.increment_stat(str(ctx.author.id), 'vtuber_commands')
        exp_result = gamification.add_exp(str(ctx.author.id), 10, "culture_content")
        await handle_vtuber_rewards(ctx, exp_result)

    @bot.command(name='collab')
    @commands.cooldown(rate=2, per=180, type=commands.BucketType.user)
    async def collaboration_opportunities(ctx, collab_type: str = None):
        """Get collaboration opportunities for Indonesian VTubers"""
        
        valid_types = ['vtuber', 'brand', 'agency', 'creator', 'event']
        if collab_type and collab_type.lower() not in valid_types:
            embed = discord.Embed(
                title="🤝 Tipe Kolaborasi",
                description=f"Tipe yang tersedia: `{', '.join(valid_types)}`",
                color=0xffa500
            )
            await ctx.reply(embed=embed)
            return
        
        collab_text = f" {collab_type}" if collab_type else ""
        
        prompt = f"""
        Peluang kolaborasi{collab_text} untuk VTuber Indonesia:

        🤝 NETWORKING OPPORTUNITIES:
        1. VTuber Indonesia yang open untuk kolaborasi
        2. Agency yang sedang mencari talent baru
        3. Brand Indonesia yang VTuber-friendly
        4. Content creator non-VTuber yang bisa diajak collab
        5. Event organizer yang butuh VTuber talent

        💼 CURRENT OPPORTUNITIES:
        - Audition yang sedang buka (agency, indie, corporate)
        - Brand campaign yang mencari VTuber endorser
        - Event mendatang yang butuh VTuber participation
        - Collaboration project yang sedang recruiting

        🎯 NETWORKING TIPS:
        - Platform terbaik untuk networking (Discord servers, Twitter, dll)
        - Cara approach yang professional
        - Portfolio yang dibutuhkan
        - Rate dan negotiation guidelines

        📊 COLLABORATION FORMATS:
        - Gaming collabs (tournament, casual play)
        - Music projects (cover, original songs)
        - Educational content partnerships
        - Variety show formats
        - Cross-platform content

        💰 MONETIZATION POTENTIAL:
        - Sponsor sharing arrangements
        - Merchandise collaborations
        - Event appearance fees
        - Long-term partnership benefits

        ⚠️ RED FLAGS:
        - Warning signs dari bad partnerships
        - Contract terms yang harus dihindari

        Format professional tapi engaging. Maksimal 1600 karakter.
        """
        
        async with ctx.typing():
            response = await get_vtuber_response(prompt)
        
        embed = discord.Embed(
            title=f"🤝 Collaboration Opportunities{f' - {collab_type.title()}' if collab_type else ''}",
            description=response,
            color=0x9b59b6
        )
        embed.set_footer(text="Use !vtubernews untuk update terbaru • Selalu verifikasi opportunities!")
        await ctx.reply(embed=embed)
        
        # Add gamification rewards
        gamification.increment_stat(str(ctx.author.id), 'vtuber_commands')
        exp_result = gamification.add_exp(str(ctx.author.id), 15, "collaboration_networking")  # Higher EXP for networking
        await handle_vtuber_rewards(ctx, exp_result)

    # Error handlers for all VTuber commands
    @vtuber_news.error
    @trending_indonesia.error
    @game_trends.error
    @indonesian_culture.error
    @collaboration_opportunities.error
    async def vtuber_command_error(ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(f"⏱️ Command ini masih cooldown. Coba lagi dalam {error.retry_after:.0f} detik.")
        else:
            print(f"VTuber command error: {error}")
            await ctx.reply("❌ Terjadi error saat memproses command. Coba lagi ya!")

    # Periodic cleanup (10% chance after each VTuber interaction)
    @bot.event
    async def on_command_completion(ctx):
        if ctx.command and ctx.command.name in ['vtubernews', 'trending', 'gametrends', 'culture', 'collab']:
            if random.random() < 0.1:
                cleanup_old_conversations()
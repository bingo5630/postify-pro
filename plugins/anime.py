import re
import time
import asyncio
import aiohttp
import urllib.parse
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto
from pyrogram.enums import ParseMode
from pyrogram import StopPropagation
from bot import Bot
from databases.database import db
from plugins.thumbnail_maker import generate_poster
from plugins.utils import apply_small_caps

user_data = {}

FANART_API_KEY = "dde00a3fdd2498bf1f664e686bd951ce"

# ==========================================
# 11 COLOUR TEMPLATES & HEX CODES
# ==========================================
COLORS = [
    # Orange Generation ke liye local transparent template hi rahega
    {"name": "ORANGE", "hex": "#FF6B00", "url": "assets/template.png"}, 
    {"name": "GREEN", "hex": "#28a745", "url": "https://ibb.co/G4GhnCsZ"},
    {"name": "TURQUOISE", "hex": "#40E0D0", "url": "https://ibb.co/1fVPgwqd"},
    {"name": "DARK YELLOW", "hex": "#DAA520", "url": "https://ibb.co/yTznRcZ"},
    {"name": "PINK", "hex": "#FF69B4", "url": "https://ibb.co/b5DVk3LR"},
    {"name": "BLUE", "hex": "#007BFF", "url": "https://ibb.co/pjz3Ts34"},
    {"name": "PALE GREEN", "hex": "#98FB98", "url": "https://ibb.co/C3jnf6sr"},
    {"name": "RED", "hex": "#DC143C", "url": "https://ibb.co/9m1V2CPM"},
    {"name": "TEAL BLUE", "hex": "#20B2AA", "url": "https://ibb.co/LXD0djss"},
    {"name": "DARK PURPLE", "hex": "#483D8B", "url": "https://ibb.co/FLqd5jt4"},
    {"name": "PURPLE", "hex": "#8A2BE2", "url": "https://ibb.co/yc8zYYYt"}
]

async def fetch_extra_images(title_eng, title_rom, mal_id=None):
    extra_images = []
    
    if mal_id:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://api.jikan.moe/v4/anime/{mal_id}/pictures") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if 'data' in data:
                            for pic in data['data']:
                                if 'large_image_url' in pic['jpg']:
                                    extra_images.append(pic['jpg']['large_image_url'])
        except Exception:
            pass

    if FANART_API_KEY:
        search_titles = []
        for t in [title_eng, title_rom]:
            if not t: continue
            search_titles.append(t) 
            if ':' in t:
                search_titles.append(t.split(':')[0].strip()) 
            search_titles.append(t.split()[0].strip()) 
                
        search_titles = list(dict.fromkeys(search_titles))
        
        try:
            async with aiohttp.ClientSession() as session:
                tv_id = None
                for t in search_titles:
                    encoded_title = urllib.parse.quote(t)
                    url = f"https://webservice.fanart.tv/v3/search/tv?api_key={FANART_API_KEY}&query={encoded_title}"
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data and isinstance(data, list) and len(data) > 0:
                                tv_id = data[0].get('tvdb_id')
                                if tv_id:
                                    break 
                
                if tv_id:
                    img_url = f"https://webservice.fanart.tv/v3/tv/{tv_id}?api_key={FANART_API_KEY}"
                    async with session.get(img_url) as img_resp:
                        if img_resp.status == 200:
                            img_data = await img_resp.json()
                            for key in ['tvposter', 'showbackground', 'characterart', 'hdclearart']:
                                for item in img_data.get(key, []):
                                    extra_images.append(item['url'])
        except Exception:
            pass
            
    return extra_images

async def fetch_anime_search(query, source="anilist"):
    if source == "mal":
        url = f"https://api.jikan.moe/v4/anime?q={query}&limit=5"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                if 'data' in data:
                    results = []
                    for item in data['data']:
                        results.append({
                            'id': item['mal_id'],
                            'mal_id': item['mal_id'],
                            'title': {
                                'romaji': item['title'],
                                'english': item.get('title_english', item['title'])
                            },
                            'genres': [g['name'] for g in item.get('genres', [])],
                            'description': item.get('synopsis', ''),
                            'coverImage': {'extraLarge': item['images']['jpg']['large_image_url']} if 'images' in item and 'jpg' in item['images'] else {},
                            'bannerImage': None 
                        })
                    return results
        return []

    url = "https://graphql.anilist.co"
    query_graphql = '''
    query ($search: String) {
      Page (page: 1, perPage: 5) {
        media (search: $search, type: ANIME) {
          id
          idMal
          title {
            romaji
            english
          }
          genres
          description(asHtml: false)
          coverImage {
            extraLarge
          }
          bannerImage
        }
      }
    }
    '''
    variables = {"search": query}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={'query': query_graphql, 'variables': variables}) as resp:
            data = await resp.json()
            if 'data' in data and 'Page' in data['data'] and 'media' in data['data']['Page']:
                results = []
                for item in data['data']['Page']['media']:
                    item['mal_id'] = item.get('idMal') 
                    results.append(item)
                return results
    return []

@Bot.on_message(filters.command("anime") & filters.private)
async def anime_cmd(client: Bot, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Please provide an anime name to search. Example: `/anime Naruto`")

    query = " ".join(message.command[1:])
    user_id = message.from_user.id

    user_data[user_id] = {
        'query': query,
        'results': [],
        'selected_anime': None,
        'crop_state': 0,
        'color_state': 0,
        'images': [],
        'current_image_idx': 0,
        'audio': None,
        'custom_image': None,
        'photo_msg_id': None,
        'timestamp': time.time()
    }

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(apply_small_caps("Anilist"), callback_data="search_anilist"),
         InlineKeyboardButton(apply_small_caps("MyAnimeList"), callback_data="search_mal")],
        [InlineKeyboardButton(apply_small_caps("Cancel"), callback_data="close_anime_menu")]
    ])

    await message.reply_text(f"SELECT SOURCE FOR: {query}", reply_markup=keyboard)


@Bot.on_callback_query(filters.regex("^search_anilist$"), group=-1)
async def handle_anilist_search(client: Bot, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in user_data:
        await callback_query.answer("Session expired.", show_alert=True)
        raise StopPropagation

    query = user_data[user_id]['query']
    await callback_query.answer("Fetching from AniList...")
    await callback_query.message.edit_text("Searching...")

    try:
        results = await fetch_anime_search(query, "anilist")
        user_data[user_id]['results'] = results
        if not results:
            await callback_query.message.edit_text("No results found.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(apply_small_caps("Cancel"), callback_data="close_anime_menu")]]))
            raise StopPropagation

        buttons = [[InlineKeyboardButton(anime['title']['english'] or anime['title']['romaji'], callback_data=f"sel_ani_{i}")] for i, anime in enumerate(results)]
        buttons.append([InlineKeyboardButton(apply_small_caps("Cancel"), callback_data="close_anime_menu")])

        await callback_query.message.edit_text(f"SEARCH RESULTS (ANILIST):", reply_markup=InlineKeyboardMarkup(buttons))
    except Exception as e:
        await callback_query.message.edit_text(f"❌ Error: {str(e)}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(apply_small_caps("Cancel"), callback_data="close_anime_menu")]]))
    raise StopPropagation


@Bot.on_callback_query(filters.regex("^search_mal$"), group=-1)
async def handle_mal_search(client: Bot, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in user_data:
        await callback_query.answer("Session expired.", show_alert=True)
        raise StopPropagation

    query = user_data[user_id]['query']
    await callback_query.answer("Fetching from MAL...")
    await callback_query.message.edit_text("Searching...")

    try:
        results = await fetch_anime_search(query, "mal")
        user_data[user_id]['results'] = results
        if not results:
            await callback_query.message.edit_text("No results found.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(apply_small_caps("Cancel"), callback_data="close_anime_menu")]]))
            raise StopPropagation

        buttons = [[InlineKeyboardButton(anime['title']['english'] or anime['title']['romaji'], callback_data=f"sel_mal_{i}")] for i, anime in enumerate(results)]
        buttons.append([InlineKeyboardButton(apply_small_caps("Cancel"), callback_data="close_anime_menu")])

        await callback_query.message.edit_text(f"SEARCH RESULTS (MAL):", reply_markup=InlineKeyboardMarkup(buttons))
    except Exception as e:
        await callback_query.message.edit_text(f"❌ Error: {str(e)}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(apply_small_caps("Cancel"), callback_data="close_anime_menu")]]))
    raise StopPropagation


@Bot.on_callback_query(filters.regex("^close_anime_menu$"), group=-1)
async def close_anime_menu(client: Bot, callback_query: CallbackQuery):
    await callback_query.answer()
    user_id = callback_query.from_user.id
    if user_id in user_data:
        try:
            if user_data[user_id].get('photo_msg_id'):
                await client.delete_messages(chat_id=user_id, message_ids=user_data[user_id]['photo_msg_id'])
        except: pass
        del user_data[user_id]
    await callback_query.message.delete()
    raise StopPropagation


def get_initial_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(apply_small_caps("Custom Img"), callback_data="anime_thumb_custom"),
         InlineKeyboardButton(apply_small_caps("Skip"), callback_data="anime_audio_menu")],
        [InlineKeyboardButton(apply_small_caps("Cancel"), callback_data="close_anime_menu")]
    ])


@Bot.on_callback_query(filters.regex(r"^sel_(ani|mal)_(\d+)"), group=-1)
async def handle_anime_select(client: Bot, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in user_data:
        await callback_query.answer("Session expired.", show_alert=True)
        raise StopPropagation

    await callback_query.message.edit_text("⏳ Fetching High-Res Posters & Fanart...")

    idx = int(callback_query.matches[0].group(2))
    selected_anime = user_data[user_id]['results'][idx]
    user_data[user_id]['selected_anime'] = selected_anime

    title_eng = selected_anime['title'].get('english', '')
    title_rom = selected_anime['title'].get('romaji', '')
    
    images = []
    if selected_anime.get('bannerImage'): images.append(selected_anime['bannerImage'])
    if selected_anime.get('coverImage', {}).get('extraLarge'): images.append(selected_anime['coverImage']['extraLarge'])
    
    extra = await fetch_extra_images(title_eng, title_rom, mal_id=selected_anime.get('mal_id'))
    images.extend(extra)
    
    images = list(dict.fromkeys(images))
    user_data[user_id]['images'] = images

    img_url = images[0] if images else "https://via.placeholder.com/1920x1080"
    msg_text = apply_small_caps("Poster selection ready. Send custom image or skip to proceed.")

    try:
        await callback_query.message.delete()
        await client.send_photo(chat_id=callback_query.message.chat.id, photo=img_url, caption=msg_text, reply_markup=get_initial_keyboard())
    except Exception as e:
        await client.send_message(chat_id=callback_query.message.chat.id, text=f"{msg_text} \n\n (Preview failed: {e})", reply_markup=get_initial_keyboard())
    raise StopPropagation


@Bot.on_callback_query(filters.regex("^anime_thumb_custom$"), group=-1)
async def handle_anime_thumb_custom(client: Bot, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in user_data:
        await callback_query.answer("Session expired.", show_alert=True)
        raise StopPropagation

    await callback_query.answer("Please send the custom photo now.")
    try:
        response = await client.ask(user_id, "Send the custom image for the poster now:", filters=filters.photo, timeout=60)
        photo_path = await response.download()
        user_data[user_id]['custom_image'] = photo_path
        await anime_audio_menu(client, callback_query)
    except asyncio.TimeoutError:
        await client.send_message(user_id, "Timeout occurred. Custom upload canceled.")
    raise StopPropagation


@Bot.on_callback_query(filters.regex("^anime_audio_menu$"), group=-1)
async def anime_audio_menu(client: Bot, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Hindi", callback_data="anime_audio_Hindi"), InlineKeyboardButton("English", callback_data="anime_audio_English")],
        [InlineKeyboardButton("Dual Audio", callback_data="anime_audio_Dual Audio"), InlineKeyboardButton("Multi Audio", callback_data="anime_audio_Multi Audio")],
        [InlineKeyboardButton("Jap & Eng", callback_data="anime_audio_Jap & Eng"), InlineKeyboardButton("Custom Text", callback_data="anime_audio_custom")],
        [InlineKeyboardButton(apply_small_caps("Cancel"), callback_data="close_anime_menu")]
    ])
    msg_text = "Select Audio Language or send custom text:"

    if callback_query.message.photo:
        await callback_query.message.delete()
        await client.send_message(user_id, msg_text, reply_markup=keyboard)
    else:
        await callback_query.message.edit_text(msg_text, reply_markup=keyboard)
    raise StopPropagation


@Bot.on_callback_query(filters.regex("^anime_audio_custom$"), group=-1)
async def handle_anime_audio_custom(client: Bot, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in user_data:
        await callback_query.answer("Session expired.", show_alert=True)
        raise StopPropagation

    await callback_query.answer("Please send the custom audio text now.")
    try:
        response = await client.ask(user_id, "Send the custom audio text:", timeout=60)
        user_data[user_id]['audio'] = response.text
        callback_query.data = f"anime_audio_{response.text}"
        await handle_anime_generate(client, callback_query)
    except asyncio.TimeoutError:
        await client.send_message(user_id, "Timeout occurred.")
    raise StopPropagation


async def build_final_poster(client, callback_query, user_id):
    anime = user_data[user_id]['selected_anime']
    title = anime['title']['english'] or anime['title']['romaji']
    
    # Space formatting for genres
    genres = "  ".join(anime.get('genres', [])[:3])
    
    synopsis = anime.get('description', '')
    if synopsis:
        synopsis = synopsis.replace('<br>', '').replace('<i>', '').replace('</i>', '').replace('<b>', '').replace('</b>', '')
    if synopsis and len(synopsis) > 300:
        synopsis = synopsis[:297] + "..."

    images = user_data[user_id]['images']
    img_idx = user_data[user_id]['current_image_idx']
    image_url = images[img_idx] if images else "https://via.placeholder.com/1920x1080"
    custom_image_path = user_data[user_id].get('custom_image')
    crop_state = user_data[user_id]['crop_state']
    color_state = user_data[user_id]['color_state']
    audio = user_data[user_id].get('audio', 'N/A')

    color_info = COLORS[color_state]

    try:
        from plugins.settings import font_toggles
        small_caps = font_toggles.get(user_id, {}).get("style_smallcaps", True)
    except: small_caps = False

    try:
        from databases.database import db
        if hasattr(db, 'get_anime_brand_text'):
            custom_text = await db.get_anime_brand_text(user_id)
            custom_logo = await db.get_anime_brand_logo(user_id)
        else:
            custom_text = await db.get_text(user_id)
            custom_logo = await db.get_logo(user_id)
    except Exception:
        custom_text = None
        custom_logo = None

    fallback_name = f"@{callback_query.from_user.username}" if callback_query.from_user.username else callback_query.from_user.first_name
    final_username = custom_text if custom_text else fallback_name

    poster_buf = await generate_poster(
        anime_img_url=image_url if not custom_image_path else None,
        custom_image_path=custom_image_path,
        title=title,
        genres=genres,
        synopsis=synopsis,
        username=final_username,
        logo_url=custom_logo,    
        crop_state=crop_state,
        small_caps=False,
        template_url=color_info['url'], 
        color_hex=color_info['hex']
    )

    try:
        caption_template = await db.get_caption(user_id)
    except: caption_template = None

    # ==========================================
    # CLEAN CAPTION WITH QUOTES & AUDIO
    # ==========================================
    if not caption_template:
        caption_template = "<blockquote><b>{title}</b></blockquote>\n» Type: <code>{type}</code>\n» Rating: <code>{rating}</code>\n» Status: <code>{status}</code>\n» Episodes: <code>{episodes}</code>\n» Audio: <code>{audio}</code>\n» Genre: {genres}\n<blockquote expandable>➤ Synopsis: {plot}</blockquote>"

    anime_type = str(anime.get('format', anime.get('type', 'TV')))
    rating = str(anime.get('averageScore', anime.get('score', 'N/A')))
    status = str(anime.get('status', 'FINISHED'))
    episodes = str(anime.get('episodes', 'N/A'))

    v_title = apply_small_caps(title) if small_caps else title
    v_type = apply_small_caps(anime_type) if small_caps else anime_type
    v_rating = apply_small_caps(rating) if small_caps else rating
    v_status = apply_small_caps(status) if small_caps else status
    v_episodes = apply_small_caps(episodes) if small_caps else episodes
    v_genres = apply_small_caps(genres) if small_caps else genres
    v_plot = apply_small_caps(synopsis) if small_caps else synopsis
    v_audio = apply_small_caps(audio) if small_caps else audio

    try:
        caption = caption_template.format(title=v_title, type=v_type, rating=v_rating, status=v_status, episodes=v_episodes, genres=v_genres, plot=v_plot, synopsis=v_plot, audio=v_audio, year="N/A", season="N/A")
    except Exception:
        caption = f"<blockquote><b>{v_title}</b></blockquote>\n» Audio: <code>{v_audio}</code>\n» Genres: {v_genres}"

    return poster_buf, caption

# ==========================================
# FINAL BUTTON LAYOUT
# ==========================================
def get_final_keyboard(color_state):
    color_name = COLORS[color_state]['name']
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("𝗠𝗢𝗩𝗘", callback_data="anime_final_move"),
         InlineKeyboardButton("𝗡𝗘𝗫𝗧 𝗜𝗠𝗔𝗚𝗘", callback_data="anime_final_next")],
        [InlineKeyboardButton(f"🎨 {color_name}", callback_data="anime_final_color")],
        [InlineKeyboardButton("𝗖𝗔𝗡𝗖𝗘𝗟", callback_data="close_anime_menu"),
         InlineKeyboardButton("𝗗𝗢𝗡𝗘", callback_data="final_done")]
    ])

@Bot.on_callback_query(filters.regex(r"^anime_audio_(.*)"), group=-1)
async def handle_anime_generate(client: Bot, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in user_data:
        await callback_query.answer("Session expired.", show_alert=True)
        raise StopPropagation

    if callback_query.data != "anime_audio_custom":
        audio = callback_query.matches[0].group(1) if hasattr(callback_query, 'matches') and callback_query.matches else callback_query.data.replace("anime_audio_", "")
        user_data[user_id]['audio'] = audio
    else:
        audio = user_data[user_id]['audio']

    await callback_query.message.edit_text("⏳ FETCHING METADATA...")
    await asyncio.sleep(1)
    await callback_query.message.edit_text("⏳ APPLYING ENHANCEMENTS AND GENERATING POSTER...")

    try:
        poster_buf, caption = await build_final_poster(client, callback_query, user_id)
        try:
            await callback_query.message.delete()
        except: pass
        
        photo_msg = await client.send_photo(
            chat_id=user_id,
            photo=poster_buf,
            caption=caption,
            parse_mode=ParseMode.HTML
        )
        
        user_data[user_id]['photo_msg_id'] = photo_msg.id
        
        await client.send_message(
            chat_id=user_id,
            text=f"⚙️ **{apply_small_caps('POSTER CONTROLS:')}**\nUse buttons below to modify your poster:",
            reply_markup=get_final_keyboard(user_data[user_id]['color_state'])
        )

    except Exception as e:
        await client.send_message(chat_id=user_id, text=f"Generation failed: {e}")

    raise StopPropagation

@Bot.on_callback_query(filters.regex("^anime_final_move$"), group=-1)
async def handle_anime_final_move(client: Bot, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in user_data:
        return await callback_query.answer("Session expired.", show_alert=True)

    user_data[user_id]['crop_state'] = (user_data[user_id]['crop_state'] + 1) % 3
    states = ["Center Focus", "Top Focus (Face)", "Bottom Focus"]
    await callback_query.answer(f"Position: {states[user_data[user_id]['crop_state']]}", show_alert=False)

    try:
        poster_buf, caption = await build_final_poster(client, callback_query, user_id)
        await client.edit_message_media(
            chat_id=user_id,
            message_id=user_data[user_id]['photo_msg_id'],
            media=InputMediaPhoto(poster_buf, caption=caption, parse_mode=ParseMode.HTML)
        )
    except Exception:
        pass
    raise StopPropagation

@Bot.on_callback_query(filters.regex("^anime_final_next$"), group=-1)
async def handle_anime_final_next(client: Bot, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in user_data:
        return await callback_query.answer("Session expired.", show_alert=True)

    user_data[user_id]['current_image_idx'] = (user_data[user_id]['current_image_idx'] + 1) % max(1, len(user_data[user_id]['images']))
    await callback_query.answer("Loading next image...", show_alert=False)

    try:
        poster_buf, caption = await build_final_poster(client, callback_query, user_id)
        await client.edit_message_media(
            chat_id=user_id,
            message_id=user_data[user_id]['photo_msg_id'],
            media=InputMediaPhoto(poster_buf, caption=caption, parse_mode=ParseMode.HTML)
        )
    except Exception:
        pass
    raise StopPropagation

@Bot.on_callback_query(filters.regex("^anime_final_color$"), group=-1)
async def handle_anime_final_color(client: Bot, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in user_data:
        return await callback_query.answer("Session expired.", show_alert=True)

    user_data[user_id]['color_state'] = (user_data[user_id]['color_state'] + 1) % len(COLORS)
    color_name = COLORS[user_data[user_id]['color_state']]['name']
    
    await callback_query.answer(f"Applying {color_name} template...", show_alert=False)

    try:
        poster_buf, caption = await build_final_poster(client, callback_query, user_id)
        
        await client.edit_message_media(
            chat_id=user_id,
            message_id=user_data[user_id]['photo_msg_id'],
            media=InputMediaPhoto(poster_buf, caption=caption, parse_mode=ParseMode.HTML)
        )
        
        await callback_query.edit_message_reply_markup(
            reply_markup=get_final_keyboard(user_data[user_id]['color_state'])
        )
    except Exception:
        pass
    raise StopPropagation

@Bot.on_callback_query(filters.regex("^final_done$"), group=-1)
async def handle_final_done(client: Bot, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    await callback_query.answer("Poster Done! Safe to share.")
    await callback_query.message.delete()
    
    if user_id in user_data:
        del user_data[user_id]
    raise StopPropagation

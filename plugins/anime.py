from bot import Bot
import re
import math
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto
from helper_func import is_subscribed
from databases.database import db
from plugins.thumbnail_maker import generate_poster
import aiohttp
from pyrogram.enums import ParseMode

user_data = {}

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
                            'title': {
                                'romaji': item['title'],
                                'english': item.get('title_english', item['title'])
                            },
                            'genres': [g['name'] for g in item.get('genres', [])],
                            'description': item.get('synopsis', ''),
                            'coverImage': {'extraLarge': item['images']['jpg']['large_image_url']} if 'images' in item and 'jpg' in item['images'] else {},
                            'bannerImage': None # MAL API v4 doesn't easily provide banner in search
                        })
                    return results
        return []

    # default to anilist
    url = "https://graphql.anilist.co"
    query_graphql = '''
    query ($search: String) {
      Page (page: 1, perPage: 5) {
        media (search: $search, type: ANIME) {
          id
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
                return data['data']['Page']['media']
    return []

@Bot.on_message(filters.command("anime") & filters.private)
async def anime_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Please provide an anime name to search. Example: `/anime Naruto`")

    query = " ".join(message.command[1:])
    user_id = message.from_user.id

    import time
    user_data[user_id] = {
        'query': query,
        'results': [],
        'selected_anime': None,
        'crop_state': 0,
        'images': [],
        'current_image_idx': 0,
        'audio': None,
        'timestamp': time.time()
    }

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("ᴀɴɪʟɪsᴛ", callback_data="anime_source_anilist"),
         InlineKeyboardButton("ᴍʏᴀɴɪᴍᴇʟɪsᴛ", callback_data="anime_source_mal")],
        [InlineKeyboardButton("ᴄᴀɴᴄᴇʟ", callback_data="anime_cancel")]
    ])

    await message.reply_text(f"SELECT SOURCE FOR: {query}", reply_markup=keyboard)

@Bot.on_callback_query(filters.regex(r"^anime_"))
async def anime_callbacks(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id

    if user_id not in user_data and data != "anime_cancel":
        return await callback_query.answer("Session expired. Please start again with /anime.", show_alert=True)

    if data == "anime_cancel":
        if user_id in user_data:
            del user_data[user_id]
        await callback_query.message.edit_text("Operation Cancelled.")
        return

    if data.startswith("anime_source_"):
        source = data.split("_")[2]
        query = user_data[user_id]['query']
        await callback_query.message.edit_text("Searching...")

        try:
            results = await fetch_anime_search(query, source)
        except Exception as e:
            return await callback_query.message.edit_text(f"API Error: Could not fetch data. ({e})", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄᴀɴᴄᴇʟ", callback_data="anime_cancel")]]))

        if not results:
            return await callback_query.message.edit_text("No results found. Please try another query.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄᴀɴᴄᴇʟ", callback_data="anime_cancel")]]))

        user_data[user_id]['results'] = results

        buttons = []
        for i, anime in enumerate(results):
            title = anime['title']['english'] or anime['title']['romaji']
            buttons.append([InlineKeyboardButton(title, callback_data=f"anime_select_{i}")])
        buttons.append([InlineKeyboardButton("ᴄᴀɴᴄᴇʟ", callback_data="anime_cancel")])

        source_name = "ANILIST" if source == "anilist" else "MAL"
        await callback_query.message.edit_text(f"SEARCH RESULTS ({source_name}) \n SELECT THE CORRECT TITLE FROM THE LIST BELOW:", reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("anime_select_"):
        idx = int(data.split("_")[2])
        selected_anime = user_data[user_id]['results'][idx]
        user_data[user_id]['selected_anime'] = selected_anime

        title = selected_anime['title']['english'] or selected_anime['title']['romaji']
        images = []
        if selected_anime.get('bannerImage'): images.append(selected_anime['bannerImage'])
        if selected_anime.get('coverImage', {}).get('extraLarge'): images.append(selected_anime['coverImage']['extraLarge'])

        user_data[user_id]['images'] = images

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("ɴᴇxᴛ ɪᴍɢ", callback_data="anime_thumb_next"),
             InlineKeyboardButton("sᴋɪᴘ", callback_data="anime_thumb_skip"),
             InlineKeyboardButton("ᴄᴀɴᴄᴇʟ", callback_data="anime_cancel")]
        ])

        await callback_query.message.edit_text(f"🖼 CUSTOM POSTER FOR '{title}' \n SEND ME A CUSTOM THUMBNAIL IMAGE, OR CLICK SKIP TO USE THIS POSTER.", reply_markup=keyboard)

    elif data == "anime_thumb_next":
        # Cycle logic: crop_state 0 -> 1 -> 2 -> next image
        user_data[user_id]['crop_state'] += 1
        if user_data[user_id]['crop_state'] > 2:
            user_data[user_id]['crop_state'] = 0
            user_data[user_id]['current_image_idx'] = (user_data[user_id]['current_image_idx'] + 1) % max(1, len(user_data[user_id]['images']))

        await callback_query.answer(f"Crop State: {['Center', 'Left', 'Right'][user_data[user_id]['crop_state']]} | Img: {user_data[user_id]['current_image_idx'] + 1}")

        # Regenerate the preview
        await callback_query.message.edit_text("⏳ GENERATING THUMBNAIL PREVIEW...")
        anime = user_data[user_id]['selected_anime']
        title = anime['title']['english'] or anime['title']['romaji']
        genres = ", ".join(anime.get('genres', [])[:3])
        synopsis = anime.get('description', '')
        if synopsis:
            synopsis = synopsis.replace('<br>', '').replace('<i>', '').replace('</i>', '')
        images = user_data[user_id]['images']
        img_idx = user_data[user_id]['current_image_idx']
        image_url = images[img_idx] if images else "https://via.placeholder.com/1920x1080"
        crop_state = user_data[user_id]['crop_state']
        username = f"@{callback_query.from_user.username}" if callback_query.from_user.username else callback_query.from_user.first_name
        try:
            from plugins.settings import font_toggles
            small_caps = font_toggles.get(user_id, {}).get("style_smallcaps", True)
        except:
            small_caps = False

        poster_buf = await generate_poster(
            anime_img_url=image_url,
            title=title,
            genres=genres,
            synopsis=synopsis,
            username=username,
            logo_url=None,
            crop_state=crop_state,
            small_caps=small_caps
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("ɴᴇxᴛ ɪᴍɢ", callback_data="anime_thumb_next"),
             InlineKeyboardButton("sᴋɪᴘ", callback_data="anime_thumb_skip"),
             InlineKeyboardButton("ᴄᴀɴᴄᴇʟ", callback_data="anime_cancel")]
        ])

        try:
            if callback_query.message.photo:
                await callback_query.edit_message_media(media=InputMediaPhoto(poster_buf, caption=f"🖼 CUSTOM POSTER FOR '{title}' \n SEND ME A CUSTOM THUMBNAIL IMAGE, OR CLICK SKIP TO USE THIS POSTER."), reply_markup=keyboard)
            else:
                await callback_query.message.delete()
                await client.send_photo(chat_id=callback_query.message.chat.id, photo=poster_buf, caption=f"🖼 CUSTOM POSTER FOR '{title}' \n SEND ME A CUSTOM THUMBNAIL IMAGE, OR CLICK SKIP TO USE THIS POSTER.", reply_markup=keyboard)
        except Exception as e:
            await callback_query.message.edit_text(f"🖼 CUSTOM POSTER FOR '{title}' \n SEND ME A CUSTOM THUMBNAIL IMAGE, OR CLICK SKIP TO USE THIS POSTER.", reply_markup=keyboard)

    elif data == "anime_thumb_skip":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Dual Audio", callback_data="anime_audio_Dual Audio"), InlineKeyboardButton("Multi Audio", callback_data="anime_audio_Multi Audio")],
            [InlineKeyboardButton("Hindi", callback_data="anime_audio_Hindi"), InlineKeyboardButton("English", callback_data="anime_audio_English")],
            [InlineKeyboardButton("Hindi & English", callback_data="anime_audio_Hindi & English"), InlineKeyboardButton("Japanese & Hindi", callback_data="anime_audio_Japanese & Hindi")],
            [InlineKeyboardButton("Japanese & English", callback_data="anime_audio_Japanese & English"), InlineKeyboardButton("Japanese & English Sub", callback_data="anime_audio_Japanese & English Sub")],
            [InlineKeyboardButton("Chinese & English", callback_data="anime_audio_Chinese & English"), InlineKeyboardButton("Chinese & (Esubs)", callback_data="anime_audio_Chinese & (Esubs)")],
            [InlineKeyboardButton("ᴄᴀɴᴄᴇʟ", callback_data="anime_cancel")]
        ])
        await callback_query.message.edit_text("☁ FONT SELECT AUDIO LANG OR SEND CUSTOM AUDIO TEXT", reply_markup=keyboard)

    elif data.startswith("anime_audio_"):
        audio = data.split("_", 2)[2]
        user_data[user_id]['audio'] = audio

        await callback_query.message.edit_text("⏳ FETCHING METADATA FROM SOURCE...")
        await asyncio.sleep(1)
        await callback_query.message.edit_text("⏳ GENERATING ANIME POSTER...")

        anime = user_data[user_id]['selected_anime']
        title = anime['title']['english'] or anime['title']['romaji']
        genres = ", ".join(anime.get('genres', [])[:3])
        synopsis = anime.get('description', '')
        if synopsis:
            synopsis = synopsis.replace('<br>', '').replace('<i>', '').replace('</i>', '')

        images = user_data[user_id]['images']
        img_idx = user_data[user_id]['current_image_idx']
        image_url = images[img_idx] if images else "https://via.placeholder.com/1920x1080"

        crop_state = user_data[user_id]['crop_state']

        username = f"@{callback_query.from_user.username}" if callback_query.from_user.username else callback_query.from_user.first_name

        # Check settings for small caps
        try:
            from plugins.settings import font_toggles
            small_caps = font_toggles.get(user_id, {}).get("style_smallcaps", True)
        except:
            small_caps = False

        poster_buf = await generate_poster(
            anime_img_url=image_url,
            title=title,
            genres=genres,
            synopsis=synopsis,
            username=username,
            logo_url=None, # Implement logo fetching from DB if needed
            crop_state=crop_state,
            small_caps=small_caps
        )

        caption = f"<b>{title}</b>\n\n<b>Audio:</b> {audio}\n<b>Genres:</b> {genres}"
        if small_caps:
            from plugins.thumbnail_maker import apply_small_caps
            caption = apply_small_caps(caption)

        await callback_query.message.delete()
        await client.send_photo(
            chat_id=user_id,
            photo=poster_buf,
            caption=caption,
            parse_mode=ParseMode.HTML
        )

        del user_data[user_id]

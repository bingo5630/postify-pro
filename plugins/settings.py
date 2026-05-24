from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from bot import Bot

MAIN_SETTINGS_TEXT = """HELLO 👤 {first_name} ✖️✖️,

I'M AN AUTO POST MAKER & AND THUMB MAKER BOT, BUILT WITH LOVE.

❝ IF YOU WERE TO WRITE A STORY WITH ME IN THE LEAD ROLE... IT WOULD CERTAINLY BE A TRAGEDY. ❞
— KEN KENEKI ❞

✖️ CHOOSE THE CATEGORY FOR WHICH YOU WANNA GET HELP. ASK YOUR DOUBTS AT SUPPORT CHAT

≡ CLICK BELOW BUTTONS TO CHANGE OR SET ITS CAPTION, BUTTONS AND TEMPLATE:"""

ANIME_SETTINGS_TEXT = """❝ ANIME SETTINGS

• TEMPLATE: animeposter8
• BRANDING: FOR MORE VISIT @ANIME_VERSE
• BUTTONS:
  🔸 JOIN NOW TO WATCH ▾ - {link}

• CAPTION:
HTML
<b>{title}</b>

» Type: <code>{type}</code>
» Average Rating: <code>{rating}</code>
» Status: <code>{status}</code>
» Episodes: <code>{episodes}</code>
» Genre: {genres}

<blockquote expandable>➤ Synopsis: {plot}</blockquote>"""

CAPTION_TEXT = """CURRENT CAPTION FORMAT:

<b>{title}</b>

» Type: <code>{type}</code>
» Average Rating: <code>{rating}</code>
» Status: <code>{status}</code>
» Episodes: <code>{episodes}</code>
» Genre: {genres}

<blockquote expandable>➤ Synopsis: {plot}</blockquote>

SEND THE NEW CAPTION FORMAT.
Available placeholders: {title}, {year}, {season}, {episodes}, {audio}, {genres}, {rating}, {status}, {plot}, {synopsis}."""

BUTTONS_TEXT = """Auto Buttons syntax:

Single Button: Button Name - {link}
Multiple Buttons: Button 1 - {link} && Button 2 - {link}
Colored Buttons: #g Green - {link}, #r Red - {link}, #p Primary - {link}."""

BRANDING_TEXT = """◉ BRANDING SETTINGS FOR ANIME

≡ Username: @ANIME_FURY
≡ Logo: branding.png

◉ CONFIGURE BRANDING OPTIONS BELOW: ❞"""

FONT_TEXT = """✨ FONT SETTINGS FOR ANIME

≡ Current Style: Small Caps
≡ Applied To: Title, Genres, Synopsis, Type, Category, Rating, Status, Episodes, Chapters, Pages, Year, Audio, Language

◉ CONFIGURE FONT OPTIONS BELOW: ❞"""

TEMPLATE_PIC = "https://envs.sh/ehW.jpg"

@Bot.on_message(filters.command('settings') & filters.private)
async def settings_command(client: Client, message: Message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("ᴀɴɪᴍᴇ", callback_data="set_anime"), InlineKeyboardButton("ᴍᴀɴɢᴀ", callback_data="set_manga")],
        [InlineKeyboardButton("ᴛᴠsʜᴏᴡs", callback_data="set_tvshows"), InlineKeyboardButton("ᴍᴏᴠɪᴇs", callback_data="set_movies")],
        [InlineKeyboardButton("ᴘᴏsᴛ sᴇᴛᴛɪɴɢ", callback_data="post_settings")],
        [InlineKeyboardButton("ᴀᴜᴛᴏ ꜰᴏʀᴡᴀʀᴅ", callback_data="auto_forward"), InlineKeyboardButton("ᴘᴏsᴛ sᴇᴀʀᴄʜ", callback_data="post_search")],
        [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="close")]
    ])
    await message.reply_text(MAIN_SETTINGS_TEXT.format(first_name=message.from_user.first_name), reply_markup=keyboard)

@Bot.on_callback_query(filters.regex('^settings_main$'))
async def settings_main_cb(client: Client, query: CallbackQuery):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("ᴀɴɪᴍᴇ", callback_data="set_anime"), InlineKeyboardButton("ᴍᴀɴɢᴀ", callback_data="set_manga")],
        [InlineKeyboardButton("ᴛᴠsʜᴏᴡs", callback_data="set_tvshows"), InlineKeyboardButton("ᴍᴏᴠɪᴇs", callback_data="set_movies")],
        [InlineKeyboardButton("ᴘᴏsᴛ sᴇᴛᴛɪɴɢ", callback_data="post_settings")],
        [InlineKeyboardButton("ᴀᴜᴛᴏ ꜰᴏʀᴡᴀʀᴅ", callback_data="auto_forward"), InlineKeyboardButton("ᴘᴏsᴛ sᴇᴀʀᴄʜ", callback_data="post_search")],
        [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="close")]
    ])
    try:
        if query.message.photo:
            await query.message.delete()
            await query.message.reply_text(MAIN_SETTINGS_TEXT.format(first_name=query.from_user.first_name), reply_markup=keyboard)
        else:
            await query.message.edit_text(MAIN_SETTINGS_TEXT.format(first_name=query.from_user.first_name), reply_markup=keyboard)
    except:
        await query.message.reply_text(MAIN_SETTINGS_TEXT.format(first_name=query.from_user.first_name), reply_markup=keyboard)

@Bot.on_callback_query(filters.regex('^set_anime$'))
async def anime_settings_cb(client: Client, query: CallbackQuery):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("ᴄᴀᴘᴛɪᴏɴ", callback_data="set_anime_caption"), InlineKeyboardButton("ʙᴜᴛᴛᴏɴs", callback_data="set_anime_buttons")],
        [InlineKeyboardButton("ᴛᴇᴍᴘʟᴀᴛᴇ", callback_data="set_anime_template"), InlineKeyboardButton("ʙʀᴀɴᴅɪɴɢ", callback_data="set_anime_branding")],
        [InlineKeyboardButton("ꜰᴏɴᴛ sᴛʏʟᴇ", callback_data="set_anime_font")],
        [InlineKeyboardButton("ᴏɴɢᴏɪɴɢ ᴀɴɪᴍᴇ", callback_data="set_anime_ongoing")],
        [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="settings_main")]
    ])
    try:
        if query.message.photo:
            await query.message.delete()
            await query.message.reply_text(ANIME_SETTINGS_TEXT, reply_markup=keyboard)
        else:
            await query.message.edit_text(ANIME_SETTINGS_TEXT, reply_markup=keyboard)
    except:
        await query.message.reply_text(ANIME_SETTINGS_TEXT, reply_markup=keyboard)

@Bot.on_callback_query(filters.regex('^set_anime_caption$'))
async def anime_caption_cb(client: Client, query: CallbackQuery):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="set_anime")]
    ])
    await query.message.edit_text(CAPTION_TEXT, reply_markup=keyboard)

@Bot.on_callback_query(filters.regex('^set_anime_buttons$'))
async def anime_buttons_cb(client: Client, query: CallbackQuery):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="set_anime")]
    ])
    await query.message.edit_text(BUTTONS_TEXT, reply_markup=keyboard)

@Bot.on_callback_query(filters.regex('^set_anime_template$'))
async def anime_template_cb(client: Client, query: CallbackQuery):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ ᴛᴇᴍᴘʟᴀᴛᴇ 1 (ᴍᴀɪɴ)", callback_data="set_anime_template_1")],
        [InlineKeyboardButton("ᴘᴏsᴛᴇʀ 2", callback_data="set_anime_template_2"), InlineKeyboardButton("ᴘᴏsᴛᴇʀ 3", callback_data="set_anime_template_3")],
        [InlineKeyboardButton("ᴘᴏsᴛᴇʀ 4", callback_data="set_anime_template_4"), InlineKeyboardButton("ᴘᴏsᴛᴇʀ 5", callback_data="set_anime_template_5")],
        [InlineKeyboardButton("ᴘᴏsᴛᴇʀ 6", callback_data="set_anime_template_6"), InlineKeyboardButton("ᴘᴏsᴛᴇʀ 7", callback_data="set_anime_template_7")],
        [InlineKeyboardButton("ᴘᴏsᴛᴇʀ 8", callback_data="set_anime_template_8"), InlineKeyboardButton("ᴘᴏsᴛᴇʀ 9", callback_data="set_anime_template_9")],
        [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="set_anime")]
    ])
    text = "◉ SELECT TEMPLATE FOR ANIME\n\n- CURRENT: animeposter8"
    try:
        await query.message.delete()
        await query.message.reply_photo(photo=TEMPLATE_PIC, caption=text, reply_markup=keyboard)
    except:
        pass

@Bot.on_callback_query(filters.regex('^set_anime_branding$'))
async def anime_branding_cb(client: Client, query: CallbackQuery):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("sᴇᴛ ᴛᴇxᴛ", callback_data="set_anime_brand_text"), InlineKeyboardButton("sᴇᴛ ʟᴏɢᴏ", callback_data="set_anime_brand_logo")],
        [InlineKeyboardButton("ᴜsᴇ ᴅᴇꜰᴀᴜʟᴛ", callback_data="set_anime_brand_default")],
        [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="set_anime")]
    ])
    await query.message.edit_text(BRANDING_TEXT, reply_markup=keyboard)

font_toggles = {}

@Bot.on_callback_query(filters.regex('^set_anime_font'))
async def anime_font_cb(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data

    if user_id not in font_toggles:
        font_toggles[user_id] = {
            "style_normal": False,
            "style_smallcaps": True,
            "title": False,
            "genres": True,
            "type": True,
            "rating": True,
            "status": True,
            "episodes": True,
            "synopsis": True,
            "audio": True,
            "year": True
        }

    t = font_toggles[user_id]

    if data.startswith("set_anime_font_toggle_"):
        key = data.replace("set_anime_font_toggle_", "")
        if key in t:
            if key == "style_normal":
                t["style_normal"] = True
                t["style_smallcaps"] = False
            elif key == "style_smallcaps":
                t["style_normal"] = False
                t["style_smallcaps"] = True
            else:
                t[key] = not t[key]

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{'✅' if t['style_normal'] else '❌'} ɴᴏʀᴍᴀʟ", callback_data="set_anime_font_toggle_style_normal"),
         InlineKeyboardButton(f"{'✅' if t['style_smallcaps'] else '❌'} sᴍᴀʟʟ ᴄᴀᴘs", callback_data="set_anime_font_toggle_style_smallcaps")],
        [InlineKeyboardButton(f"{'✅' if t['title'] else '❌'} ᴛɪᴛʟᴇ", callback_data="set_anime_font_toggle_title"),
         InlineKeyboardButton(f"{'✅' if t['genres'] else '❌'} ɢᴇɴʀᴇs", callback_data="set_anime_font_toggle_genres")],
        [InlineKeyboardButton(f"{'✅' if t['type'] else '❌'} ᴛʏᴘᴇ", callback_data="set_anime_font_toggle_type"),
         InlineKeyboardButton(f"{'✅' if t['rating'] else '❌'} ʀᴀᴛɪɴɢ", callback_data="set_anime_font_toggle_rating")],
        [InlineKeyboardButton(f"{'✅' if t['status'] else '❌'} sᴛᴀᴛᴜs", callback_data="set_anime_font_toggle_status"),
         InlineKeyboardButton(f"{'✅' if t['episodes'] else '❌'} ᴇᴘɪsᴏᴅᴇs", callback_data="set_anime_font_toggle_episodes")],
        [InlineKeyboardButton(f"{'✅' if t['synopsis'] else '❌'} sʏɴᴏᴘsɪs", callback_data="set_anime_font_toggle_synopsis"),
         InlineKeyboardButton(f"{'✅' if t['audio'] else '❌'} ᴀᴜᴅɪᴏ", callback_data="set_anime_font_toggle_audio")],
        [InlineKeyboardButton(f"{'✅' if t['year'] else '❌'} ʏᴇᴀʀ", callback_data="set_anime_font_toggle_year"),
         InlineKeyboardButton("sᴇᴛ ᴀʟʟ", callback_data="set_anime_font_toggle_all")],
        [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="set_anime")]
    ])

    try:
        await query.message.edit_text(FONT_TEXT, reply_markup=keyboard)
    except:
        pass

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto
from bot import Bot
from plugins.utils import apply_small_caps
import asyncio

MAIN_SETTINGS_TEXT = """I'M AN AUTO POST MAKER & AND THUMB MAKER BOT, BUILT WITH LOVE.

❝ IF YOU WERE TO WRITE A STORY WITH ME IN THE LEAD ROLE... IT WOULD CERTAINLY BE A TRAGEDY. ❞
— KEN KENEKI ❞

✖️ CHOOSE THE CATEGORY FOR WHICH YOU WANNA GET HELP. ASK YOUR DOUBTS AT SUPPORT CHAT

≡ CLICK BELOW BUTTONS TO CHANGE OR SET ITS CAPTION, BUTTONS AND TEMPLATE:"""

def get_anime_settings_text(current_template="animeposter8", current_branding="FOR MORE VISIT @ANIME_VERSE", current_buttons="🔸 JOIN NOW TO WATCH ▾ - {link}"):
    return f"""<blockquote expandable><b>❝ ᴀɴɪᴍᴇ sᴇᴛᴛɪɴɢs</b></blockquote>

• <b>ᴛᴇᴍᴘʟᴀᴛᴇ:</b> {current_template}
• <b>ʙʀᴀɴᴅɪɴɢ:</b> {current_branding}
• <b>ʙᴜᴛᴛᴏɴs:</b>
<pre>{current_buttons}</pre>

• <b>ᴄᴀᴘᴛɪᴏɴ:</b>
<pre><code class="language-html">HTML

&lt;b&gt;{{title}}&lt;/b&gt;

» Type: &lt;code&gt;{{type}}&lt;/code&gt;
» Average Rating: &lt;code&gt;{{rating}}&lt;/code&gt;
» Status: &lt;code&gt;{{status}}&lt;/code&gt;
» Episodes: &lt;code&gt;{{episodes}}&lt;/code&gt;
» Genre: {{genres}}

&lt;blockquote expandable&gt;➤ Synopsis: {{plot}}&lt;/blockquote&gt;</code></pre>

<blockquote><b>⧗ sᴇᴛ ᴛʜᴇ ғᴏʟʟᴏᴡɪɴɢ ᴏᴘᴛɪᴏɴs: ❞</b></blockquote>"""


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

BRANDING_TEXT = """≡ Username: @ANIME_FURY
≡ Logo: branding.png

◉ CONFIGURE BRANDING OPTIONS BELOW: ❞"""

FONT_TEXT = """≡ Current Style: Small Caps
≡ Applied To: Title, Genres, Synopsis, Type, Category, Rating, Status, Episodes, Chapters, Pages, Year, Audio, Language

◉ CONFIGURE FONT OPTIONS BELOW: ❞"""

TEMPLATE_PIC = "https://envs.sh/ehW.jpg"
WAIT_MSG = "<blockquote><b>> › > ᴡᴀɪᴛ ᴀ sᴇᴄᴏɴᴅ...</b></blockquote>"

def get_header(title, user_id=None, user_name=None):
    sc_title = apply_small_caps(title)
    res = f"<blockquote><b>⚙️ {sc_title}</b></blockquote>\n"
    if user_id and user_name:
        res += f"<blockquote><b>👤 ᴜsᴇʀ:</b> <a href=\"tg://user?id={user_id}\">{user_name}</a></blockquote>\n\n"
    else:
        res += "\n"
    return res

font_toggles = {}

@Bot.on_message(filters.command('settings') & filters.private)
async def settings_command(client: Client, message: Message):
    user = message.from_user
    header = get_header("General Settings", user.id, user.first_name)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(apply_small_caps("Anime"), callback_data="set_anime"), InlineKeyboardButton(apply_small_caps("Manga"), callback_data="set_manga")],
        [InlineKeyboardButton(apply_small_caps("TvShows"), callback_data="set_tvshows"), InlineKeyboardButton(apply_small_caps("Movies"), callback_data="set_movies")],
        [InlineKeyboardButton(apply_small_caps("Post Setting"), callback_data="post_settings")],
        [InlineKeyboardButton(apply_small_caps("Auto Forward"), callback_data="auto_forward"), InlineKeyboardButton(apply_small_caps("Post Search"), callback_data="post_search")],
        [InlineKeyboardButton(apply_small_caps("Back"), callback_data="close")]
    ])
    await message.reply_photo(photo=TEMPLATE_PIC, caption=header + MAIN_SETTINGS_TEXT, reply_markup=keyboard)

@Bot.on_callback_query(filters.regex('^settings_main$'))
async def settings_main_cb(client: Client, query: CallbackQuery):
    user = query.from_user
    await query.edit_message_caption(caption=WAIT_MSG)
    header = get_header("General Settings", user.id, user.first_name)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(apply_small_caps("Anime"), callback_data="set_anime"), InlineKeyboardButton(apply_small_caps("Manga"), callback_data="set_manga")],
        [InlineKeyboardButton(apply_small_caps("TvShows"), callback_data="set_tvshows"), InlineKeyboardButton(apply_small_caps("Movies"), callback_data="set_movies")],
        [InlineKeyboardButton(apply_small_caps("Post Setting"), callback_data="post_settings")],
        [InlineKeyboardButton(apply_small_caps("Auto Forward"), callback_data="auto_forward"), InlineKeyboardButton(apply_small_caps("Post Search"), callback_data="post_search")],
        [InlineKeyboardButton(apply_small_caps("Back"), callback_data="close")]
    ])
    try:
        await query.edit_message_media(media=InputMediaPhoto(TEMPLATE_PIC, caption=header + MAIN_SETTINGS_TEXT), reply_markup=keyboard)
    except:
        pass

@Bot.on_callback_query(filters.regex('^set_anime$'))
async def anime_settings_cb(client: Client, query: CallbackQuery):
    user = query.from_user
    await query.edit_message_caption(caption=WAIT_MSG)
    header = get_header("Anime Settings", user.id, user.first_name)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(apply_small_caps("Caption"), callback_data="set_anime_caption"), InlineKeyboardButton(apply_small_caps("Buttons"), callback_data="set_anime_buttons")],
        [InlineKeyboardButton(apply_small_caps("Template"), callback_data="set_anime_template"), InlineKeyboardButton(apply_small_caps("Branding"), callback_data="set_anime_branding")],
        [InlineKeyboardButton(apply_small_caps("Font Style"), callback_data="set_anime_font")],
        [InlineKeyboardButton(apply_small_caps("Ongoing Anime"), callback_data="set_anime_ongoing")],
        [InlineKeyboardButton(apply_small_caps("Back"), callback_data="settings_main")]
    ])
    try:
        await query.edit_message_media(media=InputMediaPhoto(TEMPLATE_PIC, caption=header + get_anime_settings_text()), reply_markup=keyboard)
    except:
        pass

@Bot.on_callback_query(filters.regex('^set_anime_caption$'))
async def anime_caption_cb(client: Client, query: CallbackQuery):
    await query.edit_message_caption(caption=WAIT_MSG)
    header = get_header("Caption Settings", query.from_user.id, query.from_user.first_name)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(apply_small_caps("Set Text"), callback_data="set_anime_caption_text")],
        [InlineKeyboardButton(apply_small_caps("Back"), callback_data="set_anime")]
    ])
    await query.edit_message_media(media=InputMediaPhoto(TEMPLATE_PIC, caption=header + CAPTION_TEXT), reply_markup=keyboard)

@Bot.on_callback_query(filters.regex('^set_anime_caption_text$'))
async def anime_caption_text_cb(client: Client, query: CallbackQuery):
    await query.answer("Please send the custom caption format now.")
    try:
        response = await client.ask(query.from_user.id, "Send the new caption format (HTML allowed):", timeout=60)
        # Store in DB here (pseudo-code depending on DB structure)
        # await db.set_anime_caption(query.from_user.id, response.text)
        await response.reply_text("Caption successfully set.")
        await anime_caption_cb(client, query)
    except asyncio.TimeoutError:
        await client.send_message(query.from_user.id, "Timeout occurred.")

@Bot.on_callback_query(filters.regex('^set_anime_buttons$'))
async def anime_buttons_cb(client: Client, query: CallbackQuery):
    await query.edit_message_caption(caption=WAIT_MSG)
    header = get_header("Buttons Settings", query.from_user.id, query.from_user.first_name)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(apply_small_caps("Back"), callback_data="set_anime")]
    ])
    await query.edit_message_media(media=InputMediaPhoto(TEMPLATE_PIC, caption=header + BUTTONS_TEXT), reply_markup=keyboard)

@Bot.on_callback_query(filters.regex('^set_anime_template$'))
async def anime_template_cb(client: Client, query: CallbackQuery):
    await query.edit_message_caption(caption=WAIT_MSG)
    header = get_header("Template Settings", query.from_user.id, query.from_user.first_name)

    # We will assume "✅ ᴛᴇᴍᴘʟᴀᴛᴇ 1 (ᴍᴀɪɴ)" has small caps applied via function
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(apply_small_caps("✅ Template 1 (Main)"), callback_data="set_anime_template_1")],
        [InlineKeyboardButton(apply_small_caps("Poster 2"), callback_data="set_anime_template_2"), InlineKeyboardButton(apply_small_caps("Poster 3"), callback_data="set_anime_template_3")],
        [InlineKeyboardButton(apply_small_caps("Poster 4"), callback_data="set_anime_template_4"), InlineKeyboardButton(apply_small_caps("Poster 5"), callback_data="set_anime_template_5")],
        [InlineKeyboardButton(apply_small_caps("Poster 6"), callback_data="set_anime_template_6"), InlineKeyboardButton(apply_small_caps("Poster 7"), callback_data="set_anime_template_7")],
        [InlineKeyboardButton(apply_small_caps("Poster 8"), callback_data="set_anime_template_8"), InlineKeyboardButton(apply_small_caps("Poster 9"), callback_data="set_anime_template_9")],
        [InlineKeyboardButton(apply_small_caps("Back"), callback_data="set_anime")]
    ])
    text = apply_small_caps("◉ Select Template For Anime") + "\n\n- " + apply_small_caps("Current: animeposter8")
    try:
        await query.edit_message_media(media=InputMediaPhoto(TEMPLATE_PIC, caption=header + text), reply_markup=keyboard)
    except:
        pass

@Bot.on_callback_query(filters.regex('^set_anime_branding$'))
async def anime_branding_cb(client: Client, query: CallbackQuery):
    await query.edit_message_caption(caption=WAIT_MSG)
    header = get_header("Branding Settings", query.from_user.id, query.from_user.first_name)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(apply_small_caps("Set Text"), callback_data="set_anime_brand_text"), InlineKeyboardButton(apply_small_caps("Set Logo"), callback_data="set_anime_brand_logo")],
        [InlineKeyboardButton(apply_small_caps("Use Default"), callback_data="set_anime_brand_default")],
        [InlineKeyboardButton(apply_small_caps("Back"), callback_data="set_anime")]
    ])
    await query.edit_message_media(media=InputMediaPhoto(TEMPLATE_PIC, caption=header + BRANDING_TEXT), reply_markup=keyboard)

@Bot.on_callback_query(filters.regex('^set_anime_brand_text$'))
async def anime_brand_text_cb(client: Client, query: CallbackQuery):
    await query.answer("Please send the custom text now.")
    try:
        response = await client.ask(query.from_user.id, "Send the custom text for branding now:", timeout=60)
        await response.reply_text(f"Text set to: {response.text}")
        await anime_branding_cb(client, query)
    except asyncio.TimeoutError:
        await client.send_message(query.from_user.id, "Timeout occurred.")

@Bot.on_callback_query(filters.regex('^set_anime_brand_logo$'))
async def anime_brand_logo_cb(client: Client, query: CallbackQuery):
    await query.answer("Please send the custom logo photo now.")
    try:
        response = await client.ask(query.from_user.id, "Send the custom logo photo for branding now:", filters=filters.photo, timeout=60)
        await response.reply_text("Logo successfully set.")
        await anime_branding_cb(client, query)
    except asyncio.TimeoutError:
        await client.send_message(query.from_user.id, "Timeout occurred.")

@Bot.on_callback_query(filters.regex('^set_anime_brand_default$'))
async def anime_brand_default_cb(client: Client, query: CallbackQuery):
    await query.answer("Reverted to default branding.", show_alert=True)
    await anime_branding_cb(client, query)

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

    await query.edit_message_caption(caption=WAIT_MSG)
    header = get_header("Font Settings", query.from_user.id, query.from_user.first_name)

    def btn_label(state, name):
        return apply_small_caps(f"{'✅' if state else '❌'} {name}")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(btn_label(t['style_normal'], "Normal"), callback_data="set_anime_font_toggle_style_normal"),
         InlineKeyboardButton(btn_label(t['style_smallcaps'], "Small Caps"), callback_data="set_anime_font_toggle_style_smallcaps")],
        [InlineKeyboardButton(btn_label(t['title'], "Title"), callback_data="set_anime_font_toggle_title"),
         InlineKeyboardButton(btn_label(t['genres'], "Genres"), callback_data="set_anime_font_toggle_genres")],
        [InlineKeyboardButton(btn_label(t['type'], "Type"), callback_data="set_anime_font_toggle_type"),
         InlineKeyboardButton(btn_label(t['rating'], "Rating"), callback_data="set_anime_font_toggle_rating")],
        [InlineKeyboardButton(btn_label(t['status'], "Status"), callback_data="set_anime_font_toggle_status"),
         InlineKeyboardButton(btn_label(t['episodes'], "Episodes"), callback_data="set_anime_font_toggle_episodes")],
        [InlineKeyboardButton(btn_label(t['synopsis'], "Synopsis"), callback_data="set_anime_font_toggle_synopsis"),
         InlineKeyboardButton(btn_label(t['audio'], "Audio"), callback_data="set_anime_font_toggle_audio")],
        [InlineKeyboardButton(btn_label(t['year'], "Year"), callback_data="set_anime_font_toggle_year"),
         InlineKeyboardButton(apply_small_caps("Set All"), callback_data="set_anime_font_toggle_all")],
        [InlineKeyboardButton(apply_small_caps("Back"), callback_data="set_anime")]
    ])

    try:
        await query.edit_message_media(media=InputMediaPhoto(TEMPLATE_PIC, caption=header + FONT_TEXT), reply_markup=keyboard)
    except:
        pass

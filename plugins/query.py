import random
import requests
import logging
import asyncio
import aiohttp 
from pyrogram import enums
from bot import Bot
from pyrogram import __version__
from plugins.FORMATS import *
from config import *
from pyrogram.enums import ParseMode, ChatAction
from plugins.autoDelete import convert_time
from databases.database import db
from datetime import timedelta
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto, ReplyKeyboardMarkup, ReplyKeyboardRemove


message_content = '''👋 Hey {first}\n
<blockquote><b>ᴘʀᴇᴍɪᴜᴍ ᴍᴇᴍʙᴇʀsʜɪᴘ ʙᴇɴᴇғɪᴛs:</b>
✨ ɴᴏ ᴀᴅs/ᴛᴏᴋᴇɴ ɴᴇᴇᴅᴇᴅ
✨ ᴜɴʟɪᴍɪᴛᴇᴅ ᴀᴄᴄᴇss
✨ ᴘʀɪᴏʀɪᴛʏ sᴜᴘᴘᴏʀᴛ
✨ ᴇxᴄʟᴜsɪᴠᴇ ғᴇᴀᴛᴜʀᴇs
</blockquote>

<b>💰 ᴀᴠᴀɪʟᴀʙʟᴇ ᴘʟᴀɴs:</b>

<blockquote>
🔹 <b>7 DAYS</b> - ₹39
🔹 <b>30 DAYS</b> - ₹99
🔹 <b>90 DAYS</b> - ₹299
🔹 <b>365 DAYS (1 YEAR)</b> - ₹999
</blockquote>
'''


logging.basicConfig(
    level=logging.INFO,  # Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

async def fileSettings(getfunc, setfunc=None, delfunc=False):
    btn_mode, txt_mode, pic_mode = '❌', off_txt, off_pic
    del_btn_mode = 'ᴇɴᴀʙʟᴇ ✅'
    try:
        if not setfunc:
            if await getfunc():
                txt_mode = on_txt
                btn_mode = '✅'
                del_btn_mode = 'ᴅɪsᴀʙʟᴇ ❌'

            return txt_mode, (del_btn_mode if delfunc else btn_mode)

        else:
            if await getfunc():
                await setfunc(False)
            else:
                await setfunc(True)
                pic_mode, txt_mode = on_pic, on_txt
                btn_mode = '✅'
                del_btn_mode = 'ᴅɪsᴀʙʟᴇ ❌'

            return pic_mode, txt_mode, (del_btn_mode if delfunc else btn_mode)

    except Exception as e:
        print(
            f"Error occured at [fileSettings(getfunc, setfunc=None, delfunc=False)] : {e}")


# Function to fetch anime data asynchronously
async def fetch_anime_data(api_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url) as response:
            response.raise_for_status()
            return await response.json()

# Function to get top anime asynchronously
async def get_top_anime():
    url = "https://api.jikan.moe/v4/top/anime"
    data = await fetch_anime_data(url)
    return data.get("data", [])

# Function to get weekly anime asynchronously
async def get_weekly_anime():
    url = "https://api.jikan.moe/v4/seasons/now"
    data = await fetch_anime_data(url)
    return data.get("data", [])

# Function to search for anime asynchronously
async def search_anime(query):
    url = f"https://api.jikan.moe/v4/anime?q={query}&page=1"
    data = await fetch_anime_data(url)
    return data.get("data", [])

# Cool font style for the anime title
def style_anime_title(title):
    return f"{title}".replace("A", "ᴀ").replace("B", "ʙ").replace("C", "ᴄ").replace("D", "ᴅ").replace("E", "ᴇ").replace("F", "ғ").replace("G", "ɢ").replace("H", "ʜ").replace("I", "ɪ").replace("J", "ᴊ").replace("K", "ᴋ").replace("L", "ʟ").replace("M", "ᴍ").replace("N", "ɴ").replace("O", "ᴏ").replace("P", "ᴘ").replace("Q", "ǫ").replace("R", "ʀ").replace("S", "s").replace("T", "ᴛ").replace("U", "ᴜ").replace("V", "ᴠ").replace("W", "ᴡ").replace("X", "x").replace("Y", "ʏ").replace("Z", "ᴢ")

# Get an emoji based on the anime title
def get_anime_emoji(title):
    emojis = ["✨", "🌟", "💫", "🔥", "💥", "🌸", "🎉", "🎇", "🎆", "⚡"]
    return emojis[hash(title) % len(emojis)]
# Provide or Make Button by takiing required modes and data

def buttonStatus(pc_data: str, hc_data: str, cb_data: str) -> list:
    button = [
        [
            InlineKeyboardButton(
                f'• ᴘᴄ: {pc_data}', callback_data='pc'),
            InlineKeyboardButton(
                f'• ʜᴄ: {hc_data}', callback_data='hc')
        ],
        [
            InlineKeyboardButton(
                f'• ᴄʙ: {cb_data}', callback_data='cb'),
            InlineKeyboardButton(f'sʙ •', callback_data='setcb')
        ],
        [
            InlineKeyboardButton('• ʀᴇғʀᴇsʜ', callback_data='files_cmd'),
            InlineKeyboardButton('ᴄʟᴏsᴇ •', callback_data='close')
        ],
    ]
    return button

# Verify user, if he/she is admin or owner before processing the query...


async def authoUser(query, id, owner_only=False):
    if not owner_only:
        if not any([id == OWNER_ID, await db.admin_exist(id)]):
            await query.answer("❌ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ ɪɴ ᴛʜɪs ʙᴏᴛ ʙᴀʙᴇʏʏʏ...!!!", show_alert=True)
            return False
        return True
    else:
        if id != OWNER_ID:
            await query.answer("❌ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴛʜᴇ ᴏᴡɴᴇʀ ᴏғ ᴛʜɪs ʙᴏᴛ ʙᴀʙᴇʏʏʏ...!!!", show_alert=True)
            return False
        return True


@Bot.on_callback_query()
async def cb_handler(client: Bot, query: CallbackQuery):
    data = query.data
    if data == "close":
        await query.message.delete()
        try:
            await query.message.reply_to_message.delete()
        except BaseException:
            pass

    elif data == "about":
        user = await client.get_users(OWNER_ID)
        user_link = f"https://t.me/{user.username}" if user.username else f"tg://openmessage?user_id={OWNER_ID}" 
        ownername = f"<a href={user_link}>{user.first_name}</a>" if user.first_name else f"<a href={user_link}>no name !</a>"
        await query.edit_message_media(
            InputMediaPhoto("https://graph.org/file/0c1deac4eae31f7919a9e-255eee8322a7fbecf1.jpg", 
                            ABOUT_TXT.format(
                                botname = client.name,
                                ownername = ownername, 
                            )
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('• ʙᴀᴄᴋ', callback_data='start'), InlineKeyboardButton('sᴛᴀᴛs •', callback_data='setting')]
            ]),
        )
                
    elif query.data == "plan":
        btn = [[InlineKeyboardButton("👨‍💼 ᴏᴡɴᴇʀ", url="https://t.me/DoraShin_hlo"),
                 InlineKeyboardButton("📧 ᴀᴅᴍɪɴ", url="https://t.me/DoraShin_hlo")],
            [
            InlineKeyboardButton(' ᴄʟᴏꜱᴇ ', callback_data='close')
        ]]
        reply_markup = InlineKeyboardMarkup(btn)
        await query.message.reply_photo(
            photo=("https://graph.org/file/0c1deac4eae31f7919a9e-255eee8322a7fbecf1.jpg"),
            caption=message_content.format(
                first = query.from_user.mention, 
                second = query.from_user.mention
        ),
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

        
    elif data == "close":
        await query.message.delete()
        try:
            await query.message.reply_to_message.delete()
        except:
            pass
            

    elif data == "setting":
        await query.edit_message_media(InputMediaPhoto(random.choice(PICS), "<b>» ᴘʟᴇᴀsᴇ wᴀɪᴛ ᴀ sᴇᴄᴏɴᴅ ʙᴀʙᴇʏʏ !!</b>"))
        try:
            total_fsub = len(await db.get_all_channels())
            total_admin = len(await db.get_all_admins())
            total_ban = len(await db.get_ban_users())
            autodel_mode = 'ᴇɴᴀʙʟᴇᴅ' if await db.get_auto_delete() else 'ᴅɪsᴀʙʟᴇᴅ'
            protect_content = 'ᴇɴᴀʙʟᴇᴅ' if await db.get_protect_content() else 'ᴅɪsᴀʙʟᴇᴅ'
            hide_caption = 'ᴇɴᴀʙʟᴇᴅ' if await db.get_hide_caption() else 'ᴅɪsᴀʙʟᴇᴅ'
            chnl_butn = 'ᴇɴᴀʙʟᴇᴅ' if await db.get_channel_button() else 'ᴅɪsᴀʙʟᴇᴅ'
            reqfsub = 'ᴇɴᴀʙʟᴇᴅ' if await db.get_request_forcesub() else 'ᴅɪsᴀʙʟᴇᴅ'

            await query.edit_message_media(
                InputMediaPhoto(random.choice(PICS),
                                SETTING_TXT.format(
                                    total_fsub=total_fsub,
                                    total_admin=total_admin,
                                    total_ban=total_ban,
                                    autodel_mode=autodel_mode,
                                    protect_content=protect_content,
                                    hide_caption=hide_caption,
                                    chnl_butn=chnl_butn,
                                    reqfsub=reqfsub
                )
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton('• ʙᴀᴄᴋ', callback_data='start'), InlineKeyboardButton(
                        'ᴄʟᴏsᴇ •', callback_data='close')]
                ]),
            )
        except Exception as e:
            print(f"! Error Occurred on callback data = 'setting' : {e}")

    elif data == "start":
        await query.edit_message_media(
            InputMediaPhoto(random.choice(PICS),
                            START_MSG.format(
                                first=query.from_user.first_name,
                                last=query.from_user.last_name,
                                username=None if not query.from_user.username else '@' + query.from_user.username,
                                mention=query.from_user.mention,
                                id=query.from_user.id
            )
            ),
            reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("• ᴄʟɪᴄᴋ ғᴏʀ ᴍᴏʀᴇ •", callback_data='about')],
                    [InlineKeyboardButton("• sᴇᴛᴛɪɴɢs", callback_data='setting'),
                     InlineKeyboardButton('ᴅᴇᴠᴇʟᴏᴘᴇʀ •', url='https://t.me/Urr_Sanjiii')],
                    [InlineKeyboardButton("• ᴏᴜʀ ᴀɴɪᴍᴇ ᴄᴏᴍᴍᴜɴɪᴛʏ •", url='https://t.me/Mugiwaras_Network')],
                ]),
        )

    elif data == "files_cmd":
        if await authoUser(query, query.from_user.id):
            await query.answer("♻️ Qᴜᴇʀʏ Pʀᴏᴄᴇssɪɴɢ....!!!")

            try:
                protect_content, pcd = await fileSettings(db.get_protect_content)
                hide_caption, hcd = await fileSettings(db.get_hide_caption)
                channel_button, cbd = await fileSettings(db.get_channel_button)
                name, link = await db.get_channel_button_link()

                await query.edit_message_media(
                    InputMediaPhoto(files_cmd_pic,
                                    FILES_CMD_TXT.format(
                                        protect_content=protect_content,
                                        hide_caption=hide_caption,
                                        channel_button=channel_button,
                                        name=name,
                                        link=link
                                    )
                                    ),
                    reply_markup=InlineKeyboardMarkup(
                        buttonStatus(pcd, hcd, cbd)),
                )
            except Exception as e:
                print(f"! Error Occurred on callback data = 'files_cmd' : {e}")

    elif data == "pc":
        if await authoUser(query, query.from_user.id):
            await query.answer("♻️ Qᴜᴇʀʏ Pʀᴏᴄᴇssɪɴɢ....!!!")

            try:
                pic, protect_content, pcd = await fileSettings(db.get_protect_content, db.set_protect_content)
                hide_caption, hcd = await fileSettings(db.get_hide_caption)
                channel_button, cbd = await fileSettings(db.get_channel_button)
                name, link = await db.get_channel_button_link()

                await query.edit_message_media(
                    InputMediaPhoto(pic,
                                    FILES_CMD_TXT.format(
                                        protect_content=protect_content,
                                        hide_caption=hide_caption,
                                        channel_button=channel_button,
                                        name=name,
                                        link=link
                                    )
                                    ),
                    reply_markup=InlineKeyboardMarkup(
                        buttonStatus(pcd, hcd, cbd))
                )
            except Exception as e:
                print(f"! Error Occurred on callback data = 'pc' : {e}")

    elif data == "hc":
        if await authoUser(query, query.from_user.id):
            await query.answer("♻️ Qᴜᴇʀʏ Pʀᴏᴄᴇssɪɴɢ....!!!")

            try:
                protect_content, pcd = await fileSettings(db.get_protect_content)
                pic, hide_caption, hcd = await fileSettings(db.get_hide_caption, db.set_hide_caption)
                channel_button, cbd = await fileSettings(db.get_channel_button)
                name, link = await db.get_channel_button_link()

                await query.edit_message_media(
                    InputMediaPhoto(pic,
                                    FILES_CMD_TXT.format(
                                        protect_content=protect_content,
                                        hide_caption=hide_caption,
                                        channel_button=channel_button,
                                        name=name,
                                        link=link
                                    )
                                    ),
                    reply_markup=InlineKeyboardMarkup(
                        buttonStatus(pcd, hcd, cbd))
                )
            except Exception as e:
                print(f"! Error Occurred on callback data = 'hc' : {e}")

    elif data == "cb":
        if await authoUser(query, query.from_user.id):
            await query.answer("♻️ Qᴜᴇʀʏ Pʀᴏᴄᴇssɪɴɢ....!!!")

            try:
                protect_content, pcd = await fileSettings(db.get_protect_content)
                hide_caption, hcd = await fileSettings(db.get_hide_caption)
                pic, channel_button, cbd = await fileSettings(db.get_channel_button, db.set_channel_button)
                name, link = await db.get_channel_button_link()

                await query.edit_message_media(
                    InputMediaPhoto(pic,
                                    FILES_CMD_TXT.format(
                                        protect_content=protect_content,
                                        hide_caption=hide_caption,
                                        channel_button=channel_button,
                                        name=name,
                                        link=link
                                    )
                                    ),
                    reply_markup=InlineKeyboardMarkup(
                        buttonStatus(pcd, hcd, cbd))
                )
            except Exception as e:
                print(f"! Error Occurred on callback data = 'cb' : {e}")

    elif data == "setcb":
        id = query.from_user.id
        if await authoUser(query, id):
            await query.answer("♻️ Qᴜᴇʀʏ Pʀᴏᴄᴇssɪɴɢ....!!!")

            try:
                button_name, button_link = await db.get_channel_button_link()

                button_preview = [[InlineKeyboardButton(
                    text=button_name, url=button_link)]]
                set_msg = await client.ask(chat_id=id, text=f'<b>ᴛᴏ ᴄʜᴀɴɢᴇ ᴛʜᴇ ʙᴜᴛᴛᴏɴ, ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴠᴀʟɪᴅ ᴀʀɢᴜᴍᴇɴᴛs ᴡɪᴛʜɪɴ 1 ᴍɪɴᴜᴛᴇ.\nғᴏʀ ᴇxᴀᴍᴘʟᴇ:\n<blockquote><code>»  ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ  « - https://t.me/Mugiwaras_Network</code></blockquote>\n\n<i>» ʙᴇʟᴏᴡ ɪs ʙᴜᴛᴛᴏɴ ᴘʀᴇᴠɪᴇᴡ ⬇️</i></b>', timeout=60, reply_markup=InlineKeyboardMarkup(button_preview), disable_web_page_preview=True)
                button = set_msg.text.split(' - ')

                if len(button) != 2:
                    markup = [[InlineKeyboardButton(
                        f'» sᴇᴛ ᴄʜᴀɴɴᴇʟ ʙᴜᴛᴛᴏɴ «', callback_data='setcb')]]
                    return await set_msg.reply("<b>ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴠᴀʟɪᴅ ᴀʀɢᴜᴍᴇɴᴛs.\n\nғᴏʀ ᴇxᴀᴍᴘʟᴇ:\n<blockquote><code>»  ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ  « - https://t.me/Mugiwaras_Network</code></blockquote>\n\nᴛʀʏ ᴀɢᴀɪɴ ʙʏ ᴄʟɪᴄᴋɪɴɢ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ..</b>", reply_markup=InlineKeyboardMarkup(markup), disable_web_page_preview=True)

                button_name = button[0].strip()
                button_link = button[1].strip()
                button_preview = [[InlineKeyboardButton(
                    text=button_name, url=button_link)]]

                await set_msg.reply("<b>ʙᴜᴛᴛᴏɴ ᴀᴅᴅᴇᴅ sᴜᴄcᴇssғᴜʟʟʏ ✅\n\n<blockquote>» sᴇᴇ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ ᴀs ᴘʀᴇᴠɪᴇᴡ ⬇️</blockquote></b>", reply_markup=InlineKeyboardMarkup(button_preview))
                await db.set_channel_button_link(button_name, button_link)
                return
            except Exception as e:
                try:
                    await set_msg.reply(f"<b>! ᴇʀʀᴏʀ ᴏᴄᴄᴜʀᴇᴅ..\n<blockquote>ʀᴇᴀsᴏɴ:</b> {e}</blockquote>")
                    print(f"! Error Occurred on callback data = 'setcb' : {e}")
                except BaseException:
                    await client.send_message(id, text=f"<b>! ᴇʀʀᴏʀ ᴏᴄᴄᴜʀᴇᴅ..\n\n<blockquote>ʀᴇᴀsᴏɴ: 1 minute Time out ..</b></blockquote>", disable_notification=True)
                    print(
                        f"! Error Occurred on callback data = 'setcb' -> Rᴇᴀsᴏɴ: 1 minute Time out ..")

    elif data == 'autodel_cmd':
        if await authoUser(query, query.from_user.id, owner_only=True):
            await query.answer("♻️ Qᴜᴇʀʏ Pʀᴏᴄᴇssɪɴɢ....!!!")

            try:
                timer = convert_time(await db.get_del_timer())
                autodel_mode, mode = await fileSettings(db.get_auto_delete, delfunc=True)

                await query.edit_message_media(
                    InputMediaPhoto(autodel_cmd_pic,
                                    AUTODEL_CMD_TXT.format(
                                        autodel_mode=autodel_mode,
                                        timer=timer
                                    )
                                    ),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(mode, callback_data='chng_autodel'), InlineKeyboardButton(
                            'sᴇᴛ ᴛɪᴍᴇʀ', callback_data='set_timer')],
                        [InlineKeyboardButton('ʀᴇғʀᴇsʜ', callback_data='autodel_cmd'), InlineKeyboardButton(
                            'ᴄʟᴏsᴇ', callback_data='close')]
                    ])
                )
            except Exception as e:
                print(
                    f"! Error Occurred on callback data = 'autodel_cmd' : {e}")

    elif data == 'chng_autodel':
        if await authoUser(query, query.from_user.id, owner_only=True):
            await query.answer("♻️ Qᴜᴇʀʏ Pʀᴏᴄᴇssɪɴɢ....!!!")

            try:
                timer = convert_time(await db.get_del_timer())
                pic, autodel_mode, mode = await fileSettings(db.get_auto_delete, db.set_auto_delete, delfunc=True)

                await query.edit_message_media(
                    InputMediaPhoto(pic,
                                    AUTODEL_CMD_TXT.format(
                                        autodel_mode=autodel_mode,
                                        timer=timer
                                    )
                                    ),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(mode, callback_data='chng_autodel'), InlineKeyboardButton(
                            'sᴇᴛ ᴛɪᴍᴇʀ', callback_data='set_timer')],
                        [InlineKeyboardButton('ʀᴇғʀᴇsʜ', callback_data='autodel_cmd'), InlineKeyboardButton(
                            'ᴄʟᴏsᴇ', callback_data='close')]
                    ])
                )
            except Exception as e:
                print(
                    f"! Error Occurred on callback data = 'chng_autodel' : {e}")

    elif data == 'set_timer':
        id = query.from_user.id
        if await authoUser(query, id, owner_only=True):
            try:

                timer = convert_time(await db.get_del_timer())
                set_msg = await client.ask(chat_id=id, text=f'<b><blockquote>» ᴄᴜʀʀᴇɴᴛ ᴛɪᴍᴇʀ: {timer}</blockquote>\n\n» ᴛᴏ ᴄʜᴀɴɢᴇ ᴛɪᴍᴇʀ, ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ ɪɴ sᴇᴄᴏɴᴅs ᴡɪᴛʜɪɴ 1 ᴍɪɴᴜᴛᴇ.\n\n<blockquote>ғᴏʀ ᴇxᴀᴍᴘʟᴇ: <code>300</code>, <code>600</code>, <code>900</code></b></blockquote>', timeout=60)
                del_timer = set_msg.text.split()

                if len(del_timer) == 1 and del_timer[0].isdigit():
                    DEL_TIMER = int(del_timer[0])
                    await db.set_del_timer(DEL_TIMER)
                    timer = convert_time(DEL_TIMER)
                    await set_msg.reply(f"<b>ᴛɪᴍᴇʀ ᴀᴅᴅᴇᴅ sᴜᴄcᴇssғᴜʟʟʏ ✅\n\n<blockquote>» ᴄᴜʀʀᴇɴᴛ ᴛɪᴍᴇʀ: {timer}</blockquote></b>")
                else:
                    markup = [[InlineKeyboardButton(
                        '» sᴇᴛ ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇʀ «', callback_data='set_timer')]]
                    return await set_msg.reply("<b>ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ ɪɴ sᴇᴄᴏɴᴅs.\n\n<blockquote>ғᴏʀ ᴇxᴀᴍᴘʟᴇ: <code>300</code>, <code>600</code>, <code>900</code></blockquote>\n\n» ᴛʀʏ ᴀɢᴀɪɴ ʙʏ ᴄʟɪᴄᴋɪɴɢ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ.</b>", reply_markup=InlineKeyboardMarkup(markup))

            except Exception as e:
                try:
                    await set_msg.reply(f"<b>! ᴇʀʀᴏʀ ᴏᴄᴄᴜʀᴇᴅ..\n\n<blockquote>ʀᴇᴀsᴏɴ:</b> {e}</blockquote>")
                    print(
                        f"! Error Occurred on callback data = 'set_timer' : {e}")
                except BaseException:
                    await client.send_message(id, text=f"<b>! ᴇʀʀᴏʀ ᴏᴄᴄᴜʀᴇᴅ..\n\n<blockquote>» ʀᴇᴀsᴏɴ: 1 ᴍɪɴᴜᴛᴇ ᴛɪᴍᴇ ᴏᴜᴛ...!!!</b></blockquote>", disable_notification=True)
                    print(
                        f"! Error Occurred on callback data = 'set_timer' -> Rᴇᴀsᴏɴ: 1 minute Time out ..")

    elif data == 'chng_req':
        if await authoUser(query, query.from_user.id, owner_only=True):
            await query.answer("♻️ Qᴜᴇʀʏ Pʀᴏᴄᴇssɪɴɢ....!!!")

            try:
                on = off = ""
                if await db.get_request_forcesub():
                    await db.set_request_forcesub(False)
                    off = "🔴"
                    texting = off_txt
                else:
                    await db.set_request_forcesub(True)
                    on = "🟢"
                    texting = on_txt

                button = [
                    [InlineKeyboardButton(f"{on} ᴏɴ", "chng_req"), InlineKeyboardButton(
                        f"{off} ᴏғғ", "chng_req")],
                    [InlineKeyboardButton(
                        "•  ᴍᴏʀᴇ sᴇᴛᴛɪɴɢs  •", "more_settings")]
                ]
                # 🎉)
                await query.message.edit_text(text=RFSUB_CMD_TXT.format(req_mode=texting), reply_markup=InlineKeyboardMarkup(button))

            except Exception as e:
                print(f"! Error Occurred on callback data = 'chng_req' : {e}")

    elif data == 'more_settings':
        if await authoUser(query, query.from_user.id, owner_only=True):
            # await query.answer("♻️ Qᴜᴇʀʏ Pʀᴏᴄᴇssɪɴɢ....")
            try:
                await query.message.edit_text("<b>» ᴘʟᴇᴀsᴇ wᴀɪᴛ ᴀ sᴇᴄᴏɴᴅ ʙᴀʙᴇʏʏ !!</b>")
                LISTS = "ᴇᴍᴘᴛʏ ʀᴇǫᴜᴇsᴛ ғᴏʀᴄᴇ-sᴜʙ ᴄʜᴀɴɴᴇʟ ʟɪsᴛ !?"

                REQFSUB_CHNLS = await db.get_reqChannel()
                if REQFSUB_CHNLS:
                    LISTS = ""
                    channel_name = "ᴜɴᴀʙʟᴇ ʟᴏᴀᴅ ɴᴀᴍᴇs..."
                    for CHNL in REQFSUB_CHNLS:
                        await query.message.reply_chat_action(ChatAction.TYPING)
                        try:
                            name = (await client.get_chat(CHNL)).title
                        except BaseException:
                            name = None
                        channel_name = name if name else channel_name

                        user = await db.get_reqSent_user(CHNL)
                        channel_users = len(user) if user else 0

                        link = await db.get_stored_reqLink(CHNL)
                        if link:
                            channel_name = f"<a href={link}>{channel_name}</a>"

                        LISTS += f"NAME: {channel_name}\n(ID: <code>{CHNL}</code>)\nUSERS: {channel_users}\n\n"

                buttons = [
                    [InlineKeyboardButton("• ᴄʟᴇᴀʀ ᴜsᴇʀs", "clear_users"), InlineKeyboardButton(
                        "cʟᴇᴀʀ cʜᴀɴɴᴇʟs •", "clear_chnls")],
                    [InlineKeyboardButton(
                        "•  ʀᴇғʀᴇsʜ sᴛᴀᴛᴜs  •", "more_settings")],
                    [InlineKeyboardButton("• ʙᴀᴄᴋ", "req_fsub"), InlineKeyboardButton(
                        "ᴄʟᴏsᴇ •", "close")]
                ]
                await query.message.reply_chat_action(ChatAction.CANCEL)
                await query.message.edit_text(text=RFSUB_MS_TXT.format(reqfsub_list=LISTS.strip()), reply_markup=InlineKeyboardMarkup(buttons))

            except Exception as e:
                print(
                    f"! Error Occurred on callback data = 'more_settings' : {e}")

        id = query.from_user.id

        if await authoUser(query, id, owner_only=True):
            await query.answer("♻️ Processing Request...!!!")

            try:
                # Fetch the current verified time from the database
                current_verify_time = await db.get_verified_time()
                time_display = f"{current_verify_time} sᴇᴄᴏɴᴅs" if current_verify_time else "ɴᴏᴛ sᴇᴛ"

                # Prompt the user to input a new verified time
                set_msg = await client.ask(
                    chat_id=id,
                    text=(
                        f"<b><blockquote>» Current Timer: {time_display}</blockquote>\n\n"
                        f"To change the timer, please send a valid number in seconds within 1 minute.\n\n"
                        f"<blockquote>For example: <code>300</code>, <code>600</code>, <code>900</code></blockquote></b>"
                    ),
                    timeout=60
                )

                # Validate the user input
                verify_time_input = set_msg.text.strip()
                if verify_time_input.isdigit():
                    verify_time = int(verify_time_input)

                    # Save the new verified time to the database
                    await db.set_verified_time(verify_time)
                    formatted_time = f"{verify_time} sᴇᴄᴏɴᴅs"

                    # Confirm the update to the user
                    await set_msg.reply(
                        f"<b>Timer updated successfully ✅\n\n"
                        f"<blockquote>» Current Timer: {formatted_time}</blockquote></b>"
                    )
                else:
                    # Handle invalid input
                    markup = [[InlineKeyboardButton('• ᴄʟɪᴄᴋ ᴛᴏ sᴇᴛ ᴠᴇʀɪғʏ ᴛɪᴍᴇʀ •', callback_data='set_verify_time')]]
                    return await set_msg.reply(
                        "<b>Please send a valid number in seconds.\n\n"
                        "<blockquote>For example: <code>300</code>, <code>600</code>, <code>900</code></blockquote>\n\n"
                        "Try again by clicking the button below...!!!</b>",
                        reply_markup=InlineKeyboardMarkup(markup)
                    )

            except asyncio.TimeoutError:
                # Handle timeout if user doesn't respond in time
                await client.send_message(
                    id,
                    text="<b>⚠️ Timeout occurred. You did not respond within the time limit.</b>",
                    disable_notification=True
                )
            except Exception as e:
                # Handle any other exceptions
                pass

import asyncio
from pyrogram.types import CallbackQuery
from pyrogram.enums import ParseMode

WAIT_MSG = "<blockquote><b>» ᴘʟᴇᴀsᴇ wᴀɪᴛ ᴀ sᴇᴄᴏɴᴅ ʙᴀʙᴇʏʏ ‼️</b></blockquote>"

async def show_wait(query: CallbackQuery):
    try:
        if query.message.photo or query.message.video or query.message.document:
            await query.edit_message_caption(caption=WAIT_MSG, parse_mode=ParseMode.HTML)
        else:
            await query.edit_message_text(text=WAIT_MSG, parse_mode=ParseMode.HTML)
        await asyncio.sleep(0.5)
    except Exception:
        pass

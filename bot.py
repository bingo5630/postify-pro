# +++ Made By Sanjiii [telegram username: @Urr_Sanjiii] +++

from aiohttp import web
from plugins import web_server

import asyncio
import pyromod.listen
from pyrogram import Client
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram.enums import ParseMode
import sys
from datetime import datetime

from config import API_HASH, APP_ID, LOGGER, TG_BOT_TOKEN, TG_BOT_WORKERS, PORT, OWNER_ID

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=APP_ID,
            plugins={
                "root": "plugins"
            },
            workers=TG_BOT_WORKERS,
            bot_token=TG_BOT_TOKEN
        )
        self.LOGGER = LOGGER
        self.scheduler = AsyncIOScheduler()

    async def start(self, *args, **kwargs):
        await super().start(*args, **kwargs)
        self.scheduler.start()
        bot_info = await self.get_me()
        self.name = bot_info.first_name
        self.username = bot_info.username
        self.uptime = datetime.now()

        # Start cleanup task for /anime user_data
        try:
            from plugins.clean_user_data import cleanup_task
            asyncio.create_task(cleanup_task())
        except Exception as e:
            self.LOGGER(__name__).error(f"Failed to start cleanup task: {e}")

        self.set_parse_mode(ParseMode.HTML)
        self.LOGGER(__name__).info(f"ᴀᴅᴠᴀɴᴄᴇ ғɪʟᴇ-sʜᴀʀɪɴɢ ʙᴏᴛ ᴡɪᴛʜ ᴛᴏᴋᴇɴ ғᴇᴀᴛᴜʀᴇ V5 ᴍᴀᴅᴇ ʙʏ ➪ @Urr_Sanjiii [Tᴇʟᴇɢʀᴀᴍ Usᴇʀɴᴀᴍᴇ]")
        self.LOGGER(__name__).info(f"{self.name} Bot Running..!")
        self.LOGGER(__name__).info(f"ʜᴏsᴛᴇᴅ sᴜᴄᴇssғᴜʟʟʏ ʙᴀʙᴇʏʏʏ !! ✅")
        #web-response
        app = web.AppRunner(await web_server())
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, PORT).start()

        try: await self.send_message(OWNER_ID, text = f"<b><blockquote>ʙᴏᴛ sᴜᴄᴇssғᴜʟʟʏ ʀᴇsᴛᴀʀᴛᴇᴅ ʙᴏss ✅\n\n» ᴍʏ ᴜɪ ɪs ᴍᴀᴅᴇ ʙʏ @urr_sanjiii\n\nᴄʟɪᴄᴋ ᴏɴ : /start ᴛᴏ ᴄʜᴇᴄᴋ ᴛʜᴇ ʙᴏᴛ...!!!</blockquote></b>")
        except: pass

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info(f"{self.name} Bot stopped.")

# +++ ᴜɪ ʙʏ ᴀʜᴍᴇᴅ [telegram username: @ᴜʀʀ_sᴀɴᴊɪɪɪ] +++

import asyncio
import base64
import logging
import os
import random
import sys
import re
import string 
import string as rohit
import time
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode, ChatAction
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from plugins.autoDelete import auto_del_notification, delete_message
from bot import Bot
from config import *
from helper_func import *
from databases.database import *
from plugins.FORMATS import *
from databases.database import db
from config import *
from pyrogram.errors.exceptions.bad_request_400 import PeerIdInvalid
from datetime import datetime, timedelta
from pytz import timezone


# +++ ᴜɪ ʙʏ ᴀʜᴍᴇᴅ [telegram username: @ᴜʀʀ_sᴀɴᴊɪɪɪ] +++

# Track (user_id, link_param) pairs who already saw /byt forcesub for a specific link
byt_fsub_seen = set()

@Bot.on_message(filters.command('start') & filters.private & subscribed)
async def start_command(client: Client, message: Message):
    id = message.from_user.id

    logging.info(f"Received /start command from user ID: {id}")

    # Check and add user to the database if not present
    if not await db.present_user(id):
        try:
            await db.add_user(id)
        except Exception as e:
            logging.error(f"Error adding user: {e}")
            return


    text = message.text        
    if len(text)>7:
        try:
            link_param = text.split(" ", 1)[1] if len(text.split(" ", 1)) > 1 else None
        except:
            link_param = None

        try:
            byt_links = await db.get_all_fsub_button_links()
            if byt_links and link_param:
                user_link_key = (id, link_param)
                if user_link_key not in byt_fsub_seen:
                    byt_fsub_seen.add(user_link_key)
                    byt_buttons = []
                    for link in byt_links:
                        byt_buttons.append([InlineKeyboardButton(text='»  ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ  «', url=link)])
                    try:
                        byt_buttons.append([InlineKeyboardButton(text='‼️ ɴᴏᴡ ᴄʟɪᴄᴋ ʜᴇʀᴇ ‼️', url=f"https://t.me/{client.username}?start={message.command[1]}")])
                    except IndexError:
                        pass
                    await client.send_photo(
                        chat_id=id,
                        photo=FORCE_PIC if FORCE_PIC else random.choice(PICS),
                        caption=FORCE_MSG.format(
                            first=message.from_user.first_name,
                            last=message.from_user.last_name,
                            username=None if not message.from_user.username else '@' + message.from_user.username,
                            mention=message.from_user.mention,
                            id=message.from_user.id
                        ),
                        reply_markup=InlineKeyboardMarkup(byt_buttons),
                        message_effect_id=5104841245755180586
                    )
                    return
        except Exception as e:
            logging.info(f"Error sending /byt force-sub message: {e}")

    reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("• ᴄʟɪᴄᴋ ғᴏʀ ᴍᴏʀᴇ •", callback_data='about')],
                [InlineKeyboardButton("• sᴇᴛᴛɪɴɢs", callback_data='setting'),
                 InlineKeyboardButton(' ᴅᴇᴠᴇʟᴏᴘᴇʀ •', url='https://t.me/DoraShin_hlo')],
                [InlineKeyboardButton("• ᴏᴜʀ ᴄᴏᴍᴍᴜɴɪᴛʏ •", url='https://t.me/Mugiwaras_Network')],
            ])
    await message.reply_photo(
        photo = random.choice(PICS),
        caption = START_MSG.format(
            first = message.from_user.first_name,
            last = message.from_user.last_name,
            username = None if not message.from_user.username else '@' + message.from_user.username,
            mention = message.from_user.mention,
            id = message.from_user.id
        ),
        reply_markup = reply_markup,
		has_spoiler = True,
	        message_effect_id=5104841245755180586 #🔥
    )
    try: await message.delete()
    except: pass

   
##===================================================================================================================##

#TRIGGRED START MESSAGE FOR HANDLE FORCE SUB MESSAGE AND FORCE SUB CHANNEL IF A USER NOT JOINED A CHANNEL

##===================================================================================================================##   


# Create a global dictionary to store chat data
chat_data_cache = {}

@Bot.on_message(filters.command('start') & filters.private & ~banUser)
async def not_joined(client: Client, message: Message):
    temp = await message.reply(f"<b>??</b>")

    user_id = message.from_user.id

    REQFSUB = await db.get_request_forcesub()
    buttons = []
    count = 0

    try:
        for total, chat_id in enumerate(await db.get_all_channels(), start=1):
            await message.reply_chat_action(ChatAction.PLAYING)

            # Show the join button of non-subscribed Channels.....
            if not await is_userJoin(client, user_id, chat_id):
                try:
                    # Check if chat data is in cache
                    if chat_id in chat_data_cache:
                        data = chat_data_cache[chat_id]  # Get data from cache
                    else:
                        data = await client.get_chat(chat_id)  # Fetch from API
                        chat_data_cache[chat_id] = data  # Store in cache

                    cname = data.title

                    # Handle private channels and links
                    if REQFSUB and not data.username: 
                        link = await db.get_stored_reqLink(chat_id)
                        await db.add_reqChannel(chat_id)

                        if not link:
                            link = (await client.create_chat_invite_link(chat_id=chat_id, creates_join_request=True)).invite_link
                            await db.store_reqLink(chat_id, link)
                    else:
                        link = data.invite_link

                    # Add button for the chat
                    buttons.append([InlineKeyboardButton(text='»  ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ  «', url=link)])
                    count += 1
                    await temp.edit(f"<b>{'! ' * count}</b>")

                except Exception as e:
                    print(f"Can't Export Channel Name and Link..., Please Check If the Bot is admin in the FORCE SUB CHANNELS:\nProvided Force sub Channel:- {chat_id}")
                    return await temp.edit(f"<b>! ᴇʀʀᴏʀ, ᴄᴏɴᴛᴀᴄᴛ ᴅᴇᴠᴇʟᴏᴘᴇʀ ᴛᴏ sᴏʟᴠᴇ ᴛʜᴇ ɪssᴜᴇs @urr_sanjiii</b>\n<blockquote expandable><b>ʀᴇᴀsᴏɴ:</b> {e}</blockquote>")

        # If user has joined all channels, delete temp and return (success - they're verified)
        if count == 0:
            await temp.delete()
            return 

        # Add /byt links (always show if they exist, regardless of REQFSUB)
        try:
            byt_links = await db.get_all_fsub_button_links()
            if byt_links:
                for link in byt_links:
                    buttons.append([InlineKeyboardButton(text='»  ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ  «', url=link)])
        except Exception as e:
            logging.info(f"No /byt links to add: {e}")

        # Add "now click here" button last
        try:
            buttons.append([InlineKeyboardButton(text='‼️ ɴᴏᴡ ᴄʟɪᴄᴋ ʜᴇʀᴇ ‼️', url=f"https://t.me/{client.username}?start={message.command[1]}")])
        except IndexError:
            pass

        await message.reply_photo(
            photo=random.choice(PICS),
            caption=FORCE_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=InlineKeyboardMarkup(buttons),
    message_effect_id=5104841245755180586  #🔥 Add the effect ID here
        )
    except Exception as e:
        print(f"Error: {e}")  # Print the error message for debugging
        # Optionally, send an error message to the user or handle further actions here
        await temp.edit(f"<b><i>! ᴇʀʀᴏʀ, ᴄᴏɴᴛᴀᴄᴛ ᴅᴇᴠᴇʟᴏᴘᴇʀ ᴛᴏ sᴏʟᴠᴇ ᴛʜᴇ ɪssᴜᴇs @urr_sanjiii</i></b>\n<blockquote expandable><b>ʀᴇᴀsᴏɴ:</b> {e}</blockquote>")


# +++ Customised By Rohit [telegram username: @rohit_1888] +++

#=====================================================================================##
#......... RESTART COMMAND FOR RESTARTING BOT .......#
#=====================================================================================##

@Bot.on_message(filters.command('restart') & filters.private & filters.user(OWNER_ID))
async def restart_bot(client: Client, message: Message):
    print("Restarting bot...")
    msg = await message.reply(text=f"<b><i>» {client.name} ɢᴏɪɴɢ ᴛᴏ ʀᴇsᴛᴀʀᴛ...\n\n» ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ ғᴏʀ 5 sᴇᴄᴏɴᴅs...!!!</i></b>")
    try:
        await asyncio.sleep(5)  # Wait for 5 seconds before restarting
        await msg.delete()
        args = [sys.executable, "main.py"]  # Adjust this if your start file is named differently
        os.execl(sys.executable, *args)
    except Exception as e:
        print(f"Error occured while Restarting the bot: {e}")
        return await msg.edit_text(f"<b>! ᴇʀʀᴏʀ, ᴄᴏɴᴛᴀᴄᴛ ᴅᴇᴠᴇʟᴏᴘᴇʀ ᴛᴏ sᴏʟᴠᴇ ᴛʜᴇ ɪssᴜᴇs @urr_sanjiii</b>\n<blockquote expandable><b>ʀᴇᴀsᴏɴ:</b> {e}</blockquote>")
    # Optionally, you can add cleanup tasks here
    #subprocess.Popen([sys.executable, "main.py"])  # Adjust this if your start file is named differently
    #sys.exit()

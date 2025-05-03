import requests
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import ChatAction
from . import app
from .block import block_dec

@app.on_message(filters.command("cosplay"))
@block_dec 
async def cosplay(_, msg):
    user_id = msg.from_user.id
    if temp_block(user_id):
        return
    bot_info = await app.get_me()
    bot_username = bot_info.username

    DRAGONS = [
        [
            InlineKeyboardButton(text="ᴀᴅᴅ ᴍᴇ ʙᴀʙʏ", url=f"https://t.me/{bot_username}?startgroup=true"),
        ],
    ]

    img = requests.get("https://waifu-api.vercel.app").json()
    await msg.reply_photo(img, caption=f"❅ ᴄᴏsᴘʟᴀʏ ʙʏ ➠ ๛ᴅ ʀ ᴀ ɢ ᴏ ɴ s ༗", reply_markup=InlineKeyboardMarkup(DRAGONS))


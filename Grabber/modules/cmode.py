from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB, InputMediaPhoto
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
from . import user_collection, app
from .block import block_dec, temp_block , block_cbq

FONT_PATH = "Fonts/font.ttf"
BG_IMAGE_PATH = "Images/cmode.jpg"

def create_cmode_image(username, user_id, current_rarity, dp_path=None):
    img = Image.open(BG_IMAGE_PATH).convert("RGBA")
    img = img.resize((275, 183))
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, 20)

    if not username:
        username = "None"
    text_lines = [
        f"Username: {username}",
        f"ID: {user_id}",
        f"Current Rarity: {current_rarity}"
    ]

    dp_size = (50, 50)
    dp_x = (img.width - dp_size[0]) // 2
    dp_y = 10

    if dp_path:
        user_dp = Image.open(dp_path).convert("RGBA")
        user_dp = user_dp.resize(dp_size, Image.ANTIALIAS)
        mask = Image.new("L", dp_size, 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, dp_size[0], dp_size[1]), fill=255)
        img.paste(user_dp, (dp_x, dp_y), mask)

    text_y = dp_y + dp_size[1] + 10

    for line in text_lines:
        text_width, text_height = d.textsize(line, font=font)
        text_x = (img.width - text_width) // 2
        d.text((text_x, text_y), line, fill=(0, 0, 0), font=font)
        text_y += text_height + 5

    img_path = f'/tmp/cmode_{user_id}.png'
    img.save(img_path)
    return img_path

@app.on_message(filters.command("cmode")& filters.group)
async def cmode(client, message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return
    username = message.from_user.username

    try:
        chat_member = await client.get_chat_member(message.chat.id, user_id)
        user_dp = chat_member.user.photo.big_file_id if chat_member.user.photo else None
    except Exception as e:
        user_dp = None

    user_data = await user_collection.find_one({'id': user_id})
    current_rarity = user_data.get('collection_mode', 'All') if user_data else 'All'

    dp_path = None
    if user_dp:
        try:
            dp_path = await client.download_media(user_dp)
        except Exception:
            dp_path = None

    img_path = create_cmode_image(username, user_id, current_rarity, dp_path)

    cmode_buttons = [
        [IKB("🟠 Rare", f"cmode:rare:{user_id}"), IKB("🥴 Special", f"cmode:special:{user_id}")],
        [IKB("💮 Exclusive", f"cmode:exclusive:{user_id}"), IKB("🍭 Cosplay", f"cmode:cosplay:{user_id}")],
        [IKB("🥵 Divine", f"cmode:divine:{user_id}"), IKB("🔮 Limited", f"cmode:limited:{user_id}")],
        [IKB("🪽 Celestial", f"cmode:celestial:{user_id}"), IKB("💎 Premium", f"cmode:premium:{user_id}")],
        [IKB("🔵 Medium", f"cmode:medium:{user_id}"), IKB("🟡 Legendary", f"cmode:legendary:{user_id}")],
        [IKB("💋 Aura", f"cmode:aura:{user_id}"), IKB("❄️ Winter", f"cmode:winter:{user_id}")],
        [IKB("⚡ Drip", f"cmode:drip:{user_id}"), IKB("🍥 Retro", f"cmode:retro:{user_id}")],
        [IKB("All", f"cmode:all:{user_id}")]
    ]
    reply_markup = IKM(cmode_buttons)

    await message.reply_photo(photo=img_path, caption="Choose your collection mode:", reply_markup=reply_markup)

@app.on_callback_query(filters.regex(r"^cmode:"))
async def cmode_callback(client, callback_query):
    data = callback_query.data
    rarity_modes = {
        'rare': '🟠 Rare',
        'special': '🥴 Special',
        'exclusive': '💮 Exclusive',
        'cosplay': '🍭 Cosplay',
        'divine': '🥵 Divine',
        'limited': '🔮 Limited',
        'celestial': '🪽 Celestial',
        'premium': '💎 Premium',
        'medium': '🔵 Medium',
        'legendary': '🟡 Legendary',
        'aura': '💋 Aura',
        'winter': '❄️ Winter',
        'all': 'All',
        'drip': '⚡ Drip',
        'retro': '🍥 Retro'
    }
    _, rarity, user_id = data.split(':')
    user_id = int(user_id)
    collection_mode = rarity_modes.get(rarity)

    if callback_query.from_user.id != user_id:
        await callback_query.answer("You cannot change someone else's collection mode.", show_alert=True)
        return

    user_data = await user_collection.find_one({'id': user_id})
    if not user_data:
        await callback_query.answer("User data not found.", show_alert=True)
        return

    if collection_mode == 'All':
        await user_collection.update_one({'id': user_id}, {'$set': {'collection_mode': 'All'}})
        username = callback_query.from_user.username

        try:
            chat_member = await client.get_chat_member(callback_query.message.chat.id, user_id)
            user_dp = chat_member.user.photo
            user_dp_url = user_dp.big_file_id if user_dp else None
        except Exception as e:
            user_dp_url = None

        if user_dp_url:
            dp_path = await client.download_media(user_dp_url)
        else:
            dp_path = None

        img_path = create_cmode_image(username, user_id, 'All', dp_path)

        await callback_query.edit_message_media(InputMediaPhoto(img_path))
        await callback_query.edit_message_caption(f"Collection mode set to: {collection_mode}")
        return

    characters = [char for char in user_data.get('characters', []) if char.get('rarity', '') == collection_mode]

    if collection_mode != 'All' and not characters:
        await callback_query.answer(f"You don't have any characters with the rarity: {collection_mode}.", show_alert=True)
        return

    await user_collection.update_one({'id': user_id}, {'$set': {'collection_mode': collection_mode}})
    username = callback_query.from_user.username

    try:
        chat_member = await client.get_chat_member(callback_query.message.chat.id, user_id)
        user_dp = chat_member.user.photo
        user_dp_url = user_dp.big_file_id if user_dp else None
    except Exception as e:
        user_dp_url = None

    if user_dp_url:
        dp_path = await client.download_media(user_dp_url)
    else:
        dp_path = None

    img_path = create_cmode_image(username, user_id, collection_mode, dp_path)
    await callback_query.edit_message_media(InputMediaPhoto(img_path))
    await callback_query.edit_message_caption(f"Rarity edited to: {collection_mode}")


@app.on_message(filters.command("cmode") & filters.private)
async def cmode_private(client, message):
    await message.reply_text("This command only works in groups.")
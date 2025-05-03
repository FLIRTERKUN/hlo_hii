import random
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM, CallbackQuery
from datetime import datetime, time, timedelta
import pytz
from . import user_collection, app, collection, capsify
from .block import block_dec, block_cbq

ags = {}

def is_allowed_time():
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz)
    if now.weekday() != 6:
        return False
    allowed_start = tz.localize(datetime.combine(now.date(), time(5, 30)))
    allowed_end = tz.localize(datetime.combine(now.date(), time(1, 30))) + timedelta(days=1)
    return allowed_start <= now <= allowed_end

@app.on_message(filters.command("gbuy"))
@block_dec
async def gbuy(client, message):
    if not is_allowed_time():
        await message.reply_text(capsify("This command can only be used on Sundays between 5:30 AM and 1:30 AM."))
        return

    user_id = message.from_user.id
    args = message.command[1:]
    if not args:
        await message.reply_text(capsify("Please provide a character ID to buy. Usage: /gbuy <character_id>"))
        return

    character_id = args[0]
    character = await collection.find_one({'id': character_id})

    if not character:
        await message.reply_text(capsify("Character not found. Please provide a valid character ID."))
        return

    restricted_rarities = ["❄️ Winter", "💋 Aura", "⚡ Drip"]
    if character.get('rarity') in restricted_rarities:
        await message.reply_text(capsify("This character cannot be purchased."))
        return

    price = random.randint(60000, 80000)

    keyboard = [
        [IKB(capsify("Buy"), callback_data=f"bg:{character_id}:{price}:{user_id}"),
         IKB(capsify("Cancel"), callback_data=f"cg:{character_id}:{user_id}")]
    ]
    reply_markup = IKM(keyboard)

    msg = await message.reply_photo(
        photo=character['img_url'],
        caption=capsify(f"Name: {character['name']}\nID: {character['id']}\nRarity: {character['rarity']}\nPrice: {price}"),
        reply_markup=reply_markup
    )

    ags[msg.message_id] = user_id

@app.on_callback_query(filters.regex(r"^(bg|cg):"))
#@block_cbq
async def hgq(client, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data.split(":")
    action = data[0]
    character_id = data[1]
    current_turn_id = int(data[3])
    price = int(data[2]) if action == "bg" else None

    if user_id != current_turn_id:
        await query.answer(capsify("This action is not for you."))
        return

    if action == "bg":
        user_data = await user_collection.find_one({'id': user_id})
        if user_data['gold'] < price:
            await query.answer(capsify("You don't have enough gold."))
            return

        character = await collection.find_one({'id': character_id})

        await user_collection.update_one(
            {'id': user_id}, 
            {'$inc': {'gold': -price}, '$push': {'characters': character}}
        )
        await query.message.edit_caption(caption=capsify(f"Purchase successful! You bought {character['name']}."))
        del ags[query.message.message_id]

    elif action == "cg":
        await query.message.edit_caption(caption=capsify("Purchase cancelled."))
        del ags[query.message.message_id]

    await query.answer()
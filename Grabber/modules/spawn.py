import random
import asyncio
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from . import collection, user_collection, group_user_totals_collection, top_global_groups_collection, app, capsify, show, deduct
from asyncio import Lock
from .watchers import character_watcher
from .block import temp_block, block_dec, block_cbq

message_counts = {}
spawn_locks = {}
spawned_characters = {}
chat_locks = {}

@app.on_message(filters.all & filters.group, group=character_watcher)
async def handle_message(_, message):
    chat_id = message.chat.id
    message_counts[chat_id] = message_counts.get(chat_id, 0) + 1
    chat_data = await group_user_totals_collection.find_one({'chat_id': chat_id})
    frequency = chat_data['message_frequency'] if chat_data and 'message_frequency' in chat_data else 100
    if chat_id in spawn_locks and spawn_locks[chat_id].locked():
        return
    if message_counts[chat_id] >= frequency:
        success = await spawn_character(chat_id)
        if success:
            message_counts[chat_id] = 0

async def spawn_character(chat_id):
    if chat_id not in spawn_locks:
        spawn_locks[chat_id] = Lock()
    async with spawn_locks[chat_id]:
        if chat_id in spawned_characters:
            return False
        chat_modes = await group_user_totals_collection.find_one({"chat_id": chat_id})
        if chat_modes is None:
            chat_modes = {"chat_id": chat_id, "character": True, "words": True, "maths": True}
            await group_user_totals_collection.update_one({"chat_id": chat_id}, {"$set": chat_modes}, upsert=True)
        if not chat_modes.get('character', True):
            return False
        rarity_map = {
            1: "🟢 Common",
            2: "🔵 Medium",
            3: "🟠 Rare",
            4: "🟡 Legendary",
            5: "🪽 Celestial",
            6: "🥵 Divine",
            7: "🥴 Special",
            8: "💎 Premium",
            9: "🔮 Limited",
        }
        allowed_rarities = [rarity_map[i] for i in range(1, 10)]
        all_characters = await collection.find({'rarity': {'$in': allowed_rarities}}).to_list(length=None)
        if not all_characters:
            return False
        character = random.choice(all_characters)
        spawned_characters[chat_id] = character
        keyboard = [[InlineKeyboardButton(capsify("NAME"), callback_data=f"name_{character['id']}")]]
        markup = InlineKeyboardMarkup(keyboard)
        caption = (
            f"🌟 {capsify('A NEW CHARACTER HAS APPEARED!')} 🌟\n"
            f"{capsify('USE ')}/pick {capsify('(NAME) TO CLAIM IT.')}\n\n"
            f"💰 {capsify('PRICE')}: {character['price']} {capsify('COINS')}\n"
            f"{capsify('💰 NOTE')}: {capsify('100 COINS WILL BE DEDUCTED FOR CLICKING NAME')}."
        )
        await app.send_photo(
            chat_id=chat_id,
            photo=character['img_url'],
            caption=caption,
            reply_markup=markup,
            has_spoiler=True
        )
        asyncio.create_task(remove_spawn_after_timeout(chat_id, character, timeout=300))
        return True

async def remove_spawn_after_timeout(chat_id, character, timeout):
    await asyncio.sleep(timeout)
    if chat_id in spawned_characters and spawned_characters[chat_id] == character:
        keyboard = [[InlineKeyboardButton(capsify("HOW MANY I HAVE"), callback_data=f"count_{character['id']}")]]
        await app.send_photo(
            chat_id,
            photo=character['img_url'],
            caption=capsify(
                f"❌ OOPS, THE CHARACTER JUST ESCAPED! 🏃‍♀️\n\n"
                f"👤 {capsify('NAME')}: {character['name']}\n"
                f"📺 {capsify('ANIME')}: {character['anime']}\n"
                f"⭐ {capsify('RARITY')}: {character['rarity']}\n"
                f"🆔 {capsify('ID')}: {character['id']}\n\n"
                f"🌌 {capsify('BETTER LUCK NEXT TIME!')} 🌌"
            ),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        del spawned_characters[chat_id]

@app.on_message(filters.command("pick"))
@block_dec
async def guess(_, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if chat_id not in chat_locks:
        chat_locks[chat_id] = Lock()
    async with chat_locks[chat_id]:
        args = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
        if not args or "()" in args or "&" in args:
            await message.reply_text(capsify("❌ INVALID INPUT. PLEASE AVOID USING SYMBOLS LIKE '()' OR '&'."))
            return
        guess = args.strip().lower()
        if chat_id not in spawned_characters:
            await message.reply_text(capsify("❌ NO CHARACTER HAS SPAWNED YET. PLEASE WAIT FOR THE NEXT SPAWN."))
            return
        character = spawned_characters[chat_id]
        character_name = character['name'].strip().lower()
        name_parts = character_name.split()
        if guess not in name_parts:
            await message.reply_text(
                capsify(f"❌ INCORRECT NAME. '{guess.upper()}' DOES NOT MATCH ANY PART OF THE CHARACTER'S NAME.")
            )
            return
        character_price = character['price']
        user_balance = await show(user_id)
        if user_balance < character_price:
            await message.reply_text(capsify("❌ NOT ENOUGH COINS TO CLAIM THIS CHARACTER."))
            return
        await user_collection.update_one({'id': user_id}, {'$push': {'characters': character}})
        await deduct(user_id, character_price)
        await group_user_totals_collection.update_one(
            {'user_id': user_id, 'group_id': chat_id},
            {'$inc': {'count': 1}},
            upsert=True
        )
        await top_global_groups_collection.update_one(
            {'group_id': chat_id},
            {'$inc': {'count': 1}, '$set': {'group_name': message.chat.title}},
            upsert=True
        )
        keyboard = [[InlineKeyboardButton(capsify("CHECK HAREM"), switch_inline_query_current_chat=f"collection.{user_id}")]]
        await message.reply_text(
            capsify(
                f"🎊 CONGRATULATIONS, {message.from_user.first_name}! 🎊\n"
                f"YOU'VE CLAIMED A NEW CHARACTER! 🎉\n\n"
                f"👤 NAME: {character['name']}\n"
                f"📺 ANIME: {character['anime']}\n"
                f"⭐ RARITY: {character['rarity']}\n\n"
                "👉 CHECK YOUR HAREM NOW!"
            ),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        del spawned_characters[chat_id]

@app.on_callback_query(filters.regex("^count_"))
@block_cbq
async def handle_count_button(_, callback_query):
    user_id = callback_query.from_user.id
    character_id = callback_query.data.split("_")[1]
    user_data = await user_collection.find_one({"id": user_id})
    if not user_data or "characters" not in user_data:
        await callback_query.answer(capsify("YOU DON'T OWN THIS CHARACTER."), show_alert=True)
        return
    count = sum(1 for char in user_data["characters"] if char["id"] == character_id)
    await callback_query.answer(capsify(f"YOU HAVE {count} OF THIS CHARACTER."), show_alert=True)



@app.on_callback_query(filters.regex("^name_"))
@block_cbq
async def handle_name_button(_, callback_query):
    chat_id = callback_query.message.chat.id
    character_id = callback_query.data.split("_")[1]
    character = spawned_characters.get(chat_id)
    if not character or str(character['id']) != character_id:
        await callback_query.answer("❌ Character not available anymore.", show_alert=True)
        return
    await callback_query.answer(f"👤 {character['name']}", show_alert=True)
import time
import asyncio
import random
from pyrogram import filters, Client, types as t
from pyrogram.errors import UserNotParticipant
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient
from . import user_collection, app, dev_filter
from .block import block_dec, temp_block

MUST_JOIN = "dragons_support"
cooldown_duration_shunt = 60

dungeon_sets = {
    "1": {
        "image_url": "https://te.legra.ph/file/400b73f9a6e48a227c7e5.jpg",
        "caption": "𝐘𝐨𝐮 𝐡𝐚𝐯𝐞 𝐟𝐨𝐮𝐧𝐝 𝐚𝐧 [ `𝐅` ] 𝐑𝐚𝐧𝐤 𝐆𝐨𝐛𝐥𝐢𝐧 𝐃𝐮𝐧𝐠𝐞𝐨𝐧.",
        "win_chance": 80,
        "loss_message": "You lost💀.\nAnd Goblin Fucked your Beast💀."
    },
    "2": {
        "image_url": "https://te.legra.ph/file/400b73f9a6e48a227c7e5.jpg",
        "caption": "𝐘𝐨𝐮 𝐡𝐚𝐯𝐞 𝐟𝐨𝐮𝐧𝐝 𝐚𝐧 [ `𝐄` ] 𝐑𝐚𝐧𝐤 𝐆𝐨𝐛𝐥𝐢𝐧 𝐃𝐮𝐧𝐠𝐞𝐨𝐧",
        "win_chance": 75,
        "loss_message": "You lost💀.\nAnd Goblin Fucked your Beast💀."
    },
    "3": {
        "image_url": "https://te.legra.ph/file/cc4b24dc0f54bc79ea998.jpg",
        "caption": "𝐘𝐨𝐮 𝐡𝐚𝐯𝐞 𝐟𝐨𝐮𝐧𝐝 𝐚𝐧 [ `𝐃` ] 𝐑𝐚𝐧𝐤 𝐖𝐨𝐥𝐟 𝐃𝐮𝐧𝐠𝐞𝐨𝐧.",
        "win_chance": 65,
        "loss_message": "You lost💀.\nAnd Wolf Fucked your Beast💀."
    },
    "4": {
        "image_url": "https://te.legra.ph/file/59bdd9842b4c98b75e5d2.jpg",
        "caption": "𝐘𝐨𝐮 𝐡𝐚𝐯𝐞 𝐟𝐨𝐮𝐧𝐝 𝐚𝐧 [ `𝐂` ] 𝐑𝐚𝐧𝐤 𝐒𝐧𝐨𝐰 𝐖𝐨𝐥𝐟 𝐃𝐮𝐧𝐠𝐞𝐨𝐧.",
        "win_chance": 45,
        "loss_message": "You lost💀.\nAnd Snow Wolf Fucked your Beast💀."
    },
    "5": {
        "image_url": "https://te.legra.ph/file/31ca2402a9309c3810a6b.jpg",
        "caption": "𝐘𝐨𝐮 𝐡𝐚𝐯𝐞 𝐟𝐨𝐮𝐧𝐝 𝐚𝐧 [ `𝐀` ] 𝐑𝐚𝐧𝐤 𝐑𝐞𝐝 𝐎𝐫𝐜 𝐃𝐮𝐧𝐠𝐞𝐨𝐧.",
        "win_chance": 5,
        "loss_message": "You lost💀.\nAnd Orc Fucked your Beast💀."
    },
    "6": {
        "image_url": "https://te.legra.ph/file/44df7f9ae15f9d543fec4.jpg",
        "caption": "𝐘𝐨𝐮 𝐡𝐚𝐯𝐞 𝐟𝐨𝐮𝐧𝐝 𝐚𝐧 [ `𝐀` ] 𝐑𝐚𝐧𝐤 𝐋𝐢𝐜𝐡 𝐤𝐢𝐧𝐠 𝐃𝐮𝐧𝐠𝐞𝐨𝐧",
        "win_chance": 5,
        "loss_message": "You lost💀.\nAnd Undead Fucked your Beast💀."
    },
}

last_usage_time_shunt = {}
user_last_command_times = {}

@app.on_message(filters.command(["shunt"]))
async def shunt_command(client, message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return
    current_time = time.time()

    if user_id in user_last_command_times and current_time - user_last_command_times[user_id] < 5:
        return await message.reply_text("You are sending commands too quickly. Please wait for a moment.")

    user_last_command_times[user_id] = current_time

    try:
        if user_id in last_usage_time_shunt:
            time_elapsed = current_time - last_usage_time_shunt[user_id]
            remaining_time = max(0, cooldown_duration_shunt - time_elapsed)
            if remaining_time > 0:
                return await message.reply_text(f"You're on cooldown. Please wait {int(remaining_time)} seconds before using this command again.")

        try:
            await app.get_chat_member(MUST_JOIN, user_id)
        except UserNotParticipant:
            link = f"https://t.me/{MUST_JOIN}"
            return await message.reply_text(
                f"You must join the support group/channel to use this command. Please join [here]({link}).",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Join", url=link)]]),
                disable_web_page_preview=True
            )

        user_data = await user_collection.find_one({'id': user_id}, projection={'beasts': 1})
        if not user_data or not user_data.get('beasts'):
            return await message.reply_text("You need a beast to hunt. Acquire a beast first using /beastshop.")

        dungeon_set = random.choice(list(dungeon_sets.values()))
        image_url = dungeon_set["image_url"]
        caption = dungeon_set["caption"]
        win_chance = dungeon_set["win_chance"]
        loss_message = dungeon_set["loss_message"]

        await message.reply_photo(photo=image_url, caption=caption)
        await asyncio.sleep(1)

        if random.randint(1, 100) <= win_chance:
            balance_to_award = random.randint(10, 150)
            await user_collection.update_one({'id': user_id}, {'$inc': {'gold': balance_to_award}})
            await message.reply_text(f"You won the fight! You got a gold of {balance_to_award}.")
        else:
            await message.reply_text(loss_message)

        last_usage_time_shunt[user_id] = current_time

    except Exception as e:
        await message.reply_text("An error occurred while processing your request. Please try again later.")

@app.on_message(filters.command(["rgold"]) & dev_filter)
@block_dec
async def reset_balance_command(client, message: t.Message):
    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id
        await user_collection.update_one({'id': user_id}, {'$set': {'gold': 0}})
        await message.reply_text(f"Gold reset for user {user_id}.")
    else:
        await message.reply_text("Please reply to the user's message to reset their balance.")
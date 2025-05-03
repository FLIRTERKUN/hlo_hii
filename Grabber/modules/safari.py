"""from pyrogram import Client, filters
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from pyrogram.types import CallbackQuery
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from pymongo import MongoClient
from datetime import datetime, timedelta
import random
import time
import asyncio
from Grabber import user_collection, collection, application, safari_cooldown_collection, safari_users_collection
from . import app

sessions = {}
safari_users = {}
allowed_group_id = -1002225496870
current_hunts = {}
current_engagements = {}

async def get_random_waifu():
    target_rarities = ['🔮 Limited', '🪽 Celestial', '💎 Premium', '🥴 Special']  # Example rarities
    selected_rarity = random.choice(target_rarities)
    try:
        pipeline = [
            {'$match': {'rarity': selected_rarity}},
            {'$sample': {'size': 1}}
        ]
        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=None)
        if characters:
            waifu = characters[0]
            waifu_id = waifu['id']
            sessions[waifu_id] = waifu
            return waifu
        else:
            return None
    except Exception as e:
        print(e)
        return None

async def load_safari_users():
    async for user_data in safari_users_collection.find():
        safari_users[user_data['user_id']] = {
            'safari_balls': user_data['safari_balls'],
            'hunt_limit': user_data['hunt_limit'],
            'used_hunts': user_data['used_hunts']
        }

async def save_safari_user(user_id):
    user_data = safari_users[user_id]
    await safari_users_collection.update_one(
        {'user_id': user_id},
        {'$set': user_data},
        upsert=True
    )

async def safe_edit_message(callback_query, new_text=None, new_markup=None):
    try:
        current_text = callback_query.message.text or callback_query.message.caption
        if current_text == new_text and callback_query.message.reply_markup == new_markup:
            return

        if callback_query.message.text:
            await callback_query.message.edit_text(text=new_text, reply_markup=new_markup)
        elif callback_query.message.caption:
            await callback_query.message.edit_caption(caption=new_text, reply_markup=new_markup)
        else:
            pass

    except pyrogram.errors.exceptions.bad_request_400.MessageNotModified as e:
        pass
    except Exception as e:
        pass

async def enter_safari(update: Update, context: CallbackContext):
    message = update.message
    user_id = message.from_user.id

    if user_id in safari_users:
        await message.reply_text("You are already in the slave zone!")
        return

    current_time = time.time()
    cooldown_doc = await safari_cooldown_collection.find_one({'user_id': user_id})

    if cooldown_doc:
        last_entry_time = cooldown_doc['last_entry_time']
    else:
        last_entry_time = 0

    cooldown_duration = 1 * 60 * 60  # 5 hours in seconds

    if current_time - last_entry_time < cooldown_duration:
        remaining_time = int(cooldown_duration - (current_time - last_entry_time))
        await message.reply_text(f"You can enter the slave zone again in {remaining_time // 3600} hours and {(remaining_time % 3600) // 60} minutes.")
        return

    user_data = await user_collection.find_one({'id': user_id})
    if user_data is None:
        await message.reply_text("Error: User data not found.")
        return

    entry_fee = 10000
    if user_data.get('gold', 0) < entry_fee:
        await message.reply_text("You don't have enough gold to enter the pick zone.\nNeed 10,000 gold.")
        return

    new_gold = user_data['gold'] - entry_fee
    await user_collection.update_one({'id': user_id}, {'$set': {'gold': new_gold}})

    await safari_cooldown_collection.update_one(
        {'user_id': user_id},
        {'$set': {'last_entry_time': current_time}},
        upsert=True
    )

    safari_users[user_id] = {
        'safari_balls': 30,
        'hunt_limit': 30,
        'used_hunts': 0
    }
    await save_safari_user(user_id)

    await message.reply_html(f"<b>Welcome to the pick Zone!\nEntry fee deducted: {entry_fee} Tokens\n\nBegin your /explore for rare slave.</b>")

async def exit_safari(update: Update, context: CallbackContext):
    message = update.message
    user_id = message.from_user.id

    if user_id not in safari_users:
        await message.reply_text("You are not in the slave zone!")
        return

    del safari_users[user_id]
    await safari_users_collection.delete_one({'user_id': user_id})

    await message.reply_text("You have now exited the slave Zone")

async def hunt(update: Update, context: CallbackContext):
    message = update.message
    user_id = message.from_user.id

    if user_id not in safari_users:
        await message.reply_text("Not in the pick zone. use /ptour first")
        return

    if user_id in current_hunts and current_hunts[user_id] is not None:
        if user_id not in current_engagements:
            await message.reply_text("You already have an ongoing hunt. Finish it first!")
            return

    user_data = safari_users[user_id]
    if user_data['used_hunts'] >= user_data['hunt_limit']:
        await message.reply_text("You have reached your hunt limit.")
        del safari_users[user_id]
        await safari_users_collection.delete_one({'user_id': user_id})
        return

    if user_data['safari_balls'] <= 0:
        await message.reply_text("You have run out of contract crystals.")
        del safari_users[user_id]
        await safari_users_collection.delete_one({'user_id': user_id})
        return

    waifu = await get_random_waifu()
    if not waifu:
        await message.reply_text("No slave available.")
        return

    waifu_name = waifu['name']
    waifu_img_url = waifu['img_url']
    waifu_id = waifu['id']
    waifu_rarity = waifu['rarity']

    if user_id in current_hunts:
        del current_hunts[user_id]

    current_hunts[user_id] = waifu_id

    user_data['used_hunts'] += 1
    safari_users[user_id] = user_data

    await save_safari_user(user_id)

    text = f"<b>A wild {waifu_name} ( {waifu_rarity} ) has appeared!</b>\n\n<b>/explore limit: {user_data['used_hunts']}/{user_data['hunt_limit']}\🔮 contract crystals: {user_data['safari_balls']}</b>"
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("contract", callback_data=f"engage_{waifu_id}_{user_id}")]
        ]
    )
    await message.reply_photo(photo=waifu_img_url, caption=text, reply_markup=keyboard, parse_mode='HTML')

    if user_id in current_engagements:
        del current_engagements[user_id]

async def typing_animation(callback_query, text):
    try:
        if random.random() < 0.25:
            duration = 3
        else:
            duration = random.choice([1, 2])

        for i in range(1, duration + 1):
            dots = "🔮" * i
            await callback_query.message.edit_caption(caption=text + dots)
            await asyncio.sleep(1)

        return dots
    except Exception as e:
        return "🔮🔮🔮"
async def throw_ball(callback_query):
    try:
        data = callback_query.data.split("_")
        waifu_id = data[1]
        user_id = int(data[2])

        if user_id != callback_query.from_user.id:
            await callback_query.answer("This hunt does not belong to you.", show_alert=True)
            return

        if user_id not in safari_users:
            await callback_query.answer("You are not in the safari zone!", show_alert=True)
            return

        if waifu_id not in sessions:
            await callback_query.answer("The wild pick has fled!", show_alert=True)
            return

        user_data = safari_users[user_id]
        user_data['safari_balls'] -= 1
        safari_users[user_id] = user_data

        await save_safari_user(user_id)

        outcome = await typing_animation(callback_query, "Attempting to capture the waifu.\n\n")

        if outcome == "🔮🔮🔮":
            await callback_query.message.edit_caption(caption=f"<b>âœ¨ congratulation âœ¨\nyou caught the wild slave!</b>", parse_mode="HTML")

            character = sessions[waifu_id]
            await user_collection.update_one({'id': user_id}, {'$push': {'characters': character}})

            del sessions[waifu_id]

        else:
            await callback_query.message.edit_caption(caption=f"<b>Your contract crystal failed.</b>\n<b>The wild slave fled.</b>", parse_mode="HTML")
            del sessions[waifu_id]

        if user_data['safari_balls'] <= 0:
            await callback_query.message.edit_caption(caption="You have run out of contract crystals.")
            del safari_users[user_id]
            await safari_users_collection.delete_one({'user_id': user_id})

        del current_hunts[user_id]

    except Exception as e:
        await callback_query.answer("An error occurred. Please try again later.")

async def run_away(callback_query):
    try:
        data = callback_query.data.split("_")
        waifu_id = data[1]
        user_id = int(data[2])

        if user_id != callback_query.from_user.id:
            await callback_query.answer("This hunt does not belong to you.", show_alert=True)
            return

        if user_id not in safari_users:
            await callback_query.answer("You are not in the safari zone!", show_alert=True)
            return

        del sessions[waifu_id]
        del current_hunts[user_id]

        await callback_query.message.edit_caption(caption="You escaped from the wild pick.")
        await callback_query.answer()

    except Exception as e:
        print(f"Error handling run_away: {e}")

async def engage(callback_query):
    try:
        data = callback_query.data.split("_")
        waifu_id = data[1]
        user_id = int(data[2])

        if user_id != callback_query.from_user.id:
            await callback_query.answer("This hunt does not belong to you.", show_alert=True)
            return

        if user_id not in safari_users:
            await callback_query.answer("You are not in the safari zone!", show_alert=True)
            return

        if waifu_id not in sessions:
            await callback_query.answer("The wild slave has fled!", show_alert=True)
            return

        if user_id in current_engagements:
            del current_engagements[user_id]

        if user_id in current_hunts and current_hunts[user_id] == waifu_id:
            waifu = sessions[waifu_id]
            text = f"Choose your action:"
            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Throw crystal", callback_data=f"throw_{waifu_id}_{user_id}"),
                        InlineKeyboardButton("Run", callback_data=f"run_{waifu_id}_{user_id}")
                    ]
                ]
            )
            await safe_edit_message(callback_query, new_text=text, new_markup=keyboard)

            current_engagements[user_id] = waifu_id

        else:
            await callback_query.answer("The wild pick has fled!", show_alert=True)

    except Exception as e:
        print(f"Error handling engage: {e}")

async def hunt_callback_query(update: Update, context: CallbackContext):
    callback_query = update.callback_query
    data = callback_query.data.split("_")
    action = data[0]
    waifu_id = data[1]
    user_id = int(data[2])

    if action == "engage":
        await engage(callback_query)
    elif action == "throw":
        await throw_ball(callback_query)
    elif action == "run":
        await run_away(callback_query)

async def dc_command(update: Update, context: CallbackContext):
    if not update.message.reply_to_message:
        await update.message.reply_text("You need to reply to a message to reset that user's cooldown.")
        return
    
    replied_user_id = update.message.reply_to_message.from_user.id
    authorized_user_id = 7185106962
    
    if update.message.from_user.id != authorized_user_id:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    try:
        result = await safari_cooldown_collection.delete_one({'user_id': replied_user_id})
        
        if result.deleted_count == 1:
            await update.message.reply_text(f"The tour cooldown for user {replied_user_id} has been reset.")
        else:
            await update.message.reply_text(f"The user {replied_user_id} doesn't have an active tour cooldown.")
    
    except Exception as e:
        print(f"Error resetting safari cooldown for user {replied_user_id}: {e}")
        await update.message.reply_text("An error occurred while resetting the tour cooldown. Please try again later.")

async def reset_hunt(update: Update, context: CallbackContext):
    message = update.message
    user_id = message.from_user.id

    if user_id not in safari_users:
        await message.reply_text("You are not in the safari zone! Use /ptour to enter.")
        return

    if user_id in current_hunts:
        del current_hunts[user_id]
    
    if user_id in current_engagements:
        del current_engagements[user_id]

    await message.reply_text("Your current hunt has been reset. You can now explore again!")

application.add_handler(CommandHandler("soja", reset_hunt))
application.add_handler(CommandHandler("dc", dc_command))
application.add_handler(CommandHandler("ptour", enter_safari))
application.add_handler(CommandHandler("exit", exit_safari))
application.add_handler(CommandHandler("explore", hunt))
application.add_handler(CallbackQueryHandler(hunt_callback_query, pattern="^(engage|throw|run)_", block=False))
"""


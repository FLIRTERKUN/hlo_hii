from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import random

from . import user_collection, clan_collection, join_requests_collection, app, db as database
from .block import block_dec, block_cbq

def generate_unique_numeric_code():
    return str(random.randint(1000000000, 9999999999))

def calculate_clan_level(clan_data):
    cxp = clan_data.get('cxp', 0)
    return cxp // 30 + 1

@app.on_message(filters.command("myclan"))
@block_dec
async def my_clan(client, message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return
    user_data = await user_collection.find_one({'id': user_id})

    if not user_data or 'clan_id' not in user_data:
        await message.reply_text("You are not in any clan. Create one with /createclan.")
        return

    clan_id = user_data['clan_id']
    clan_data = await clan_collection.find_one({'clan_id': clan_id})

    if not clan_data:
        await message.reply_text("Clan not found.")
        return

    member_count = len(clan_data['members'])
    message_text = (
        f"```\n"
        f"Clan ID: {clan_data['clan_id']}\n"
        f"Clan: {clan_data['name']} 🏆\n"
        f"Level: {calculate_clan_level(clan_data)}\n"
        f"XP: {clan_data.get('cxp', 0)}\n"
        f"Leader: {clan_data['leader_name']}\n"
        f"Members: {member_count}/20\n\n"
        f"Join our mighty clan and conquer the fantasy world together! 💪🌟"
        f"```"
    )

    if clan_data['leader_id'] != user_id:
        keyboard = [[InlineKeyboardButton("Leave Clan", callback_data=f"leave_clan:{clan_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message.reply_text(message_text, reply_markup=reply_markup)
    else:
        await message.reply_text(message_text)

@app.on_message(filters.command("createclan"))
@block_dec
async def create_clan(client, message):
    user_id = message.from_user.id
    #if temp_block(user_id):
        #return
    clan_name = ' '.join(message.command[1:])

    if not clan_name:
        await message.reply_text("Please provide a name for your clan.")
        return

    try:
        user_data = await user_collection.find_one({'id': user_id})
        if not user_data:
            await message.reply_text("Please start the bot first.")
            return

        current_gold = user_data.get('gold', 0)
        if current_gold < 10000:
            await message.reply_text(f"You need 10,000 gold to create a clan. Your current gold: {current_gold}")
            return

        new_gold_balance = current_gold - 10000
        await user_collection.update_one({'id': user_id}, {'$set': {'gold': new_gold_balance}})

        while True:
            clan_id = generate_unique_numeric_code()
            if await clan_collection.count_documents({'clan_id': clan_id}) == 0:
                break

        clan_data = {
            'clan_id': clan_id,
            'name': clan_name,
            'leader_id': user_id,
            'leader_name': message.from_user.first_name,
            'members': [user_id],
            'level': 1,
            'cxp': 0
        }

        await clan_collection.insert_one(clan_data)
        await user_collection.update_one({'id': user_id}, {'$set': {'clan_id': clan_id}})

        await message.reply_text(f"Clan '{clan_name}' created successfully with ID `{clan_id}!`")

    except Exception as e:
        await message.reply_text(f"Error creating clan: {str(e)}")

@app.on_message(filters.command("joinclan"))
@block_dec
async def join_clan(client, message):
    user_id = message.from_user.id
    #if temp_block(user_id):
        #return
    clan_id = ' '.join(message.command[1:])

    if not clan_id:
        await message.reply_text("Please provide a clan ID to join.")
        return

    user_data = await user_collection.find_one({'id': user_id})
    if user_data and 'clan_id' in user_data:
        await message.reply_text("You are already in a clan. Leave your current clan first.")
        return

    clan_data = await clan_collection.find_one({'clan_id': clan_id})
    if not clan_data:
        await message.reply_text("Clan not found.")
        return

    if len(clan_data['members']) >= 20:
        await message.reply_text("This clan is already full.")
        return

    join_request = {
        'user_id': user_id,
        'clan_id': clan_id,
        'user_name': message.from_user.first_name
    }
    await join_requests_collection.insert_one(join_request)

    leader_id = clan_data['leader_id']
    keyboard = [
        [InlineKeyboardButton("Accept", callback_data=f"aj:{user_id}:{clan_id}"),
         InlineKeyboardButton("Reject", callback_data=f"rj:{user_id}:{clan_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await client.send_message(chat_id=leader_id, text=f"{message.from_user.first_name} wants to join your clan.\nUser ID: {user_id}", reply_markup=reply_markup)
    await message.reply_text("Your request to join the clan has been sent to the leader.")

@app.on_message(filters.command("dclan"))
@block_dec
async def delete_clan(client, message):
    user_id = message.from_user.id
    #if temp_block(user_id):
        #return

    user_data = await user_collection.find_one({'id': user_id})
    if not user_data or 'clan_id' not in user_data:
        await message.reply_text("You are not in any clan.")
        return

    clan_id = user_data['clan_id']
    clan_data = await clan_collection.find_one({'clan_id': clan_id})

    if not clan_data:
        await message.reply_text("Clan not found.")
        return

    if clan_data['leader_id'] != user_id:
        await message.reply_text("Only the clan owner can delete the clan.")
        return

    await clan_collection.delete_one({'clan_id': clan_id})
    await user_collection.update_many({'clan_id': clan_id}, {'$unset': {'clan_id': ""}})

    await message.reply_text(f"`Clan '{clan_data['name']}' has been deleted.`")

@app.on_callback_query(filters.regex(r'^leave_clan:'))
@block_cbq
async def leave_clan_callback(client, callback_query):
    try:
        user_id = callback_query.from_user.id
        clan_id = callback_query.data.split(':')[1]  # Do not cast to int

        user_data = await user_collection.find_one({'id': user_id})
        if not user_data or user_data.get('clan_id') != clan_id:
            await callback_query.answer("You are not in this clan.", show_alert=True)
            return

        clan_data = await clan_collection.find_one({'clan_id': clan_id})
        if not clan_data or clan_data['leader_id'] == user_id:
            await callback_query.answer("Clan leader cannot leave the clan. Use /dclan to delete the clan.")
            return

        await clan_collection.update_one({'clan_id': clan_id}, {'$pull': {'members': user_id}})
        await user_collection.update_one({'id': user_id}, {'$unset': {'clan_id': ""}})

        await callback_query.answer("You have left the clan.", show_alert=True)
        await callback_query.edit_message_text("You have successfully left the clan.")

    except Exception as e:
        await callback_query.answer(f"An error occurred: {str(e)}", show_alert=True)

@app.on_callback_query(filters.regex(r'^aj:'))
async def accept_join_request(client, callback_query):
    try:
        _, user_id, clan_id = callback_query.data.split(':')

        await join_requests_collection.delete_one({'user_id': int(user_id), 'clan_id': clan_id})
        await clan_collection.update_one({'clan_id': clan_id}, {'$push': {'members': int(user_id)}})
        await user_collection.update_one({'id': int(user_id)}, {'$set': {'clan_id': clan_id}})

        await callback_query.answer("Join request accepted!", show_alert=True)
        await callback_query.edit_message_text("Join request accepted. Welcome to the clan!")

    except Exception as e:
        await callback_query.answer(f"An error occurred: {str(e)}", show_alert=True)

@app.on_callback_query(filters.regex(r'^rj:'))
async def reject_join_request(client, callback_query):
    try:
        _, user_id, clan_id = callback_query.data.split(':')

        await join_requests_collection.delete_one({'user_id': int(user_id), 'clan_id': clan_id})

        await callback_query.answer("Join request rejected.", show_alert=True)
        await callback_query.edit_message_text("Join request rejected.", show_alert=True)

    except Exception as e:
        await callback_query.answer(f"An error occurred: {str(e)}", show_alert=True)
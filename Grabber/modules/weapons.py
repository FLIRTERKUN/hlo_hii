from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
import uuid
import time
from . import app, user_collection
from .block import block_dec

weapons_data = [
    {'name': 'Sword', 'price': 500, 'damage': 10},
    {'name': 'Bow', 'price': 800, 'damage': 15},
    {'name': 'Staff', 'price': 1000, 'damage': 20},
    {'name': 'Knife', 'price': 200, 'damage': 5},
    {'name': 'Snipper', 'price': 5000, 'damage': 30}
]

async def weapons(client, message, user_id):
    user_data = await user_collection.find_one({'id': user_id})

    if not user_data:
        await message.reply_text("Please start the bot first.")
        return

    current_gold = user_data.get('gold', 0)
    owned_weapons = set(w['name'] for w in user_data.get('weapons', []))

    keyboard = []
    row = []
    for i, weapon in enumerate(weapons_data, start=1):
        button_text = f"{weapon['name']} - {weapon['price']} gold"
        if weapon['name'] in owned_weapons:
            button_text = f"{weapon['name']} (Owned)"
        row.append(InlineKeyboardButton(button_text, callback_data=f"buy_weapon:{weapon['name']}:{weapon['price']}"))
        
        # Add row every two items or at the end of the list
        if i % 2 == 0 or i == len(weapons_data):
            keyboard.append(row)
            row = []

    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text("Choose a weapon to buy:", reply_markup=reply_markup)

async def remove_expired_weapons(user_id: int):
    user_data = await user_collection.find_one({'id': user_id})
    if user_data and 'weapons' in user_data:
        current_time = time.time()
        updated_weapons = [w for w in user_data['weapons'] if (current_time - w.get('purchase_time', 0)) <= (7 * 24 * 60 * 60)]
        await user_collection.update_one({'id': user_id}, {'$set': {'weapons': updated_weapons}})

async def handle_buy_weapon(client, callback_query: CallbackQuery, user_id):
    data = callback_query.data.split(':')

    if len(data) != 3:
        await callback_query.answer("Invalid weapon selection.")
        return

    weapon_name = data[1]
    weapon_price = int(data[2])

    user_data = await user_collection.find_one({'id': user_id})
    if not user_data:
        await callback_query.answer("Please start the bot first.")
        return

    current_gold = user_data.get('gold', 0)
    if current_gold < weapon_price:
        await callback_query.answer("You don't have enough gold to buy this weapon.")
        return

    owned_weapons = set(w['name'] for w in user_data.get('weapons', []))
    if weapon_name in owned_weapons:
        await callback_query.answer("You already own this weapon.")
        return

    # Ensure the callback is for the current user
    if callback_query.from_user.id != user_id:
        await callback_query.answer("This is not your purchase.")
        return

    # Proceed with the purchase logic
    new_gold_balance = current_gold - weapon_price
    if new_gold_balance < 0:
        await callback_query.answer("Insufficient gold balance. Please earn more gold.")
        return

    await user_collection.update_one({'id': user_id}, {'$set': {'gold': new_gold_balance}})

    weapon_details = {
        'name': weapon_name,
        'damage': next((weapon['damage'] for weapon in weapons_data if weapon['name'] == weapon_name), 0),
        'purchase_time': time.time()  # Timestamp for purchase
    }
    await user_collection.update_one({'id': user_id}, {'$push': {'weapons': weapon_details}}, upsert=True)

    await callback_query.answer(f"You bought {weapon_name} for {weapon_price} gold.")
    await callback_query.edit_message_text(f"You bought {weapon_name} for {weapon_price} gold. Enjoy your new weapon!")

    await remove_expired_weapons(user_id)

@app.on_message(filters.command("weapons"))
@block_dec
async def cmd_weapons(client, message):
    user_id = message.from_user.id
    await weapons(client, message, user_id)

@app.on_callback_query(filters.regex(r'^buy_weapon:'))
async def cbk_buy_weapon(client, callback_query):
    user_id = callback_query.from_user.id
    await handle_buy_weapon(client, callback_query, user_id)
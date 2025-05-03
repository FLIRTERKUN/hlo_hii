import math
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pymongo import MongoClient
import random
import asyncio
from . import user_collection, clan_collection, app as application, Grabberu
from .block import block_dec, block_cbq

weapons_data = [
    {'name': 'Sword', 'price': 500, 'damage': 10},
    {'name': 'Bow', 'price': 800, 'damage': 15},
    {'name': 'Staff', 'price': 1000, 'damage': 20},
    {'name': 'Knife', 'price': 200, 'damage': 5},
    {'name': 'Snipper', 'price': 5000, 'damage': 30}
]

# Dictionary to store battle states and names
battles = {}
battle_names = {}

def custom_format_number(num):
    if int(num) >= 10**6:
        exponent = int(math.log10(num)) - 5
        base = num // (10 ** exponent)
        return f"{base:,.0f}({exponent:+})"
    return f"{num:,.0f}"

def format_timedelta(delta):
    minutes, seconds = divmod(delta.seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days = delta.days
    if days > 0:
        return f"{days}d {hours}m {minutes}s"
    elif hours > 0:
        return f"{hours}h {minutes}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

async def get_user_data(user_id):
    user_data = await user_collection.find_one({'id': user_id})
    if not user_data:
        user_data = {'id': user_id, 'first_name': 'Unknown', 'gold': 0, 'weapons': []}
    return user_data

@Grabberu.on_message(filters.command("battle") & filters.reply)
@block_dec
async def battle_command(client, message):
    user_a_id = message.from_user.id
    #if temp_block(user_a_id):
        #return
    user_a_data = await get_user_data(user_a_id)

    if not ('clan_id' in user_a_data or 'leader_id' in user_a_data):
        await message.reply_text("You need to be part of a clan or a clan leader to use this command.")
        return

    user_b_id = message.reply_to_message.from_user.id
    user_b_data = await get_user_data(user_b_id)

    # Check if both users are in the same clan
    user_a_clan_id = user_a_data.get('clan_id')
    user_b_clan_id = user_b_data.get('clan_id')

    if user_a_clan_id and user_b_clan_id and user_a_clan_id == user_b_clan_id:
        await message.reply_text("You cannot battle someone from the same clan.")
        return

    user_a_name = message.from_user.first_name
    user_b_name = message.reply_to_message.from_user.first_name

    # Store names in the battle_names dictionary
    battle_names[(user_a_id, user_b_id)] = (user_a_name, user_b_name)

    # Log attacker's weapons
    attacker_weapons = user_a_data.get('weapons', [])

    keyboard = [
        [InlineKeyboardButton("Fight", callback_data=f"battle_accept:{user_a_id}:{user_b_id}"),
         InlineKeyboardButton("Run", callback_data=f"battle_decline:{user_a_id}:{user_b_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await message.reply_to_message.reply_text(f"{user_b_name}, {user_a_name} challenged you: Do you fight or run?", reply_markup=reply_markup)

@Grabberu.on_callback_query(filters.regex(r'^battle_accept'))
@block_cbq
async def handle_battle_accept(client, query: CallbackQuery):
    data = query.data.split(':')
    user_a_id = int(data[1])
    user_b_id = int(data[2])

    if query.from_user.id != user_b_id:
        await query.answer("Only the challenged user can respond.", show_alert=True)
        return

    user_a_name, user_b_name = battle_names.get((user_a_id, user_b_id), ('User A', 'User B'))

    a_health = 100
    b_health = 100

    user_a_data = await get_user_data(user_a_id)
    user_a_weapons = user_a_data.get('weapons', [])

    # Split weapons into two rows
    num_weapons = len(user_a_weapons)
    half_index = num_weapons // 2

    a_weapon_buttons = [
        [InlineKeyboardButton(weapon['name'], callback_data=f"battle_attack:{weapon['name']}:{user_a_id}:{user_b_id}:{user_a_id}:{a_health}:{b_health}")]
        for weapon in user_a_weapons[:half_index]
    ]

    b_weapon_buttons = [
        [InlineKeyboardButton(weapon['name'], callback_data=f"battle_attack:{weapon['name']}:{user_a_id}:{user_b_id}:{user_a_id}:{a_health}:{b_health}")]
        for weapon in user_a_weapons[half_index:]
    ]
    print(a_weapon_buttons)
    print(b_weapon_buttons)

    reply_markup = InlineKeyboardMarkup(a_weapon_buttons + b_weapon_buttons)

    battle_message = await query.message.edit_text(
        f"{user_b_name} accepted the challenge!\n"
        f"{user_a_name}'s health: {a_health}/100\n"
        f"{user_b_name}'s health: {b_health}/100\n"
        f"{user_a_name}, choose your weapon:",
        reply_markup=reply_markup
    )

    # Initialize battle state
    battles[(user_a_id, user_b_id)] = {
        'a_health': a_health,
        'b_health': b_health,
        'current_turn_id': user_a_id
    }

@Grabberu.on_callback_query(filters.regex(r'^battle_decline'))
@block_cbq
async def handle_battle_decline(client, query: CallbackQuery):
    await query.answer("Challenge declined!")
    await query.message.edit_text("The battle challenge was declined.")

@Grabberu.on_callback_query(filters.regex(r'^battle_attack'))
@block_cbq
async def handle_battle_attack(client, query: CallbackQuery):
    data = query.data.split(':')
    weapon_name = data[1]
    user_a_id = int(data[2])
    user_b_id = int(data[3])
    current_turn_id = int(data[4])
    a_health = int(data[5])
    b_health = int(data[6])

    if query.from_user.id != current_turn_id:
        await query.answer("It's not your turn!", show_alert=True)
        return

    user_a_data = await get_user_data(user_a_id)
    user_b_data = await get_user_data(user_b_id)

    attacker_id = query.from_user.id
    defender_id = user_b_id if current_turn_id == user_a_id else user_a_id

    attacker_name, defender_name = battle_names.get((user_a_id, user_b_id), ('Attacker', 'Defender'))
    attacker_data = user_a_data if current_turn_id == user_a_id else user_b_data
    defender_data = user_b_data if current_turn_id == user_a_id else user_a_data

    attacker_weapons = attacker_data.get('weapons', [])
    defender_health = a_health if current_turn_id == user_b_id else b_health

    valid_weapon = next((w for w in weapons_data if w['name'] == weapon_name), None)
    if not valid_weapon or weapon_name not in [w['name'] for w in attacker_weapons]:
        await query.answer("Invalid weapon choice!", show_alert=True)
        return

    damage = valid_weapon['damage']
    defender_health -= damage
    if defender_health < 0:
        defender_health = 0

    if current_turn_id == user_a_id:
        b_health = defender_health
        next_turn_id = user_b_id
    else:
        a_health = defender_health
        next_turn_id = user_a_id

    if a_health == 0 or b_health == 0:
        winner_id = user_a_id if a_health > 0 else user_b_id
        loser_id = user_b_id if winner_id == user_a_id else user_a_id
        await end_battle(winner_id, loser_id)
        winner_name = battle_names.get((winner_id, loser_id), ('Winner', 'Loser'))[0]
        loser_name = battle_names.get((winner_id, loser_id), ('Winner', 'Loser'))[1]
        await query.message.edit_text(
            f"{attacker_name} attacked with {weapon_name}!\n"
            f"{defender_name} has {defender_health}/100 health left.\n"
            f"{winner_name} wins the battle!"
        )
        return

    next_turn_name = defender_name if next_turn_id == user_b_id else attacker_name

    defender_weapons = defender_data.get('weapons', [])
    weapon_buttons = [
        [InlineKeyboardButton(weapon['name'], callback_data=f"battle_attack:{weapon['name']}:{user_a_id}:{user_b_id}:{next_turn_id}:{a_health}:{b_health}")]
        for weapon in weapons_data if weapon['name'] in [w['name'] for w in defender_weapons]
    ]

    num_buttons = len(weapon_buttons)
    half_index = num_buttons // 2
    weapon_buttons_row1 = weapon_buttons[:half_index]
    weapon_buttons_row2 = weapon_buttons[half_index:]

    reply_markup = InlineKeyboardMarkup(weapon_buttons_row1 + weapon_buttons_row2)

    health_lines = (
        f"{attacker_name}: {a_health}/100\n"
        f"{defender_name}: {b_health}/100\n"
    )

    await query.message.edit_text(
        f"{health_lines if attacker_id == current_turn_id else ''}\n\n"
        f"{next_turn_name}, choose your weapon:",
        reply_markup=reply_markup
    )

async def end_battle(winner_id, loser_id):
    loser_data = await user_collection.find_one({'id': loser_id})
    if loser_data:
        loser_gold = loser_data.get('gold', 0)
        battle_cooldown_time = datetime.now() + timedelta(minutes=5)

        # Update winner's gold and set battle cooldown
        await user_collection.find_one_and_update(
            {'id': winner_id},
            {'$inc': {'gold': 300}, '$set': {'battle_cooldown': battle_cooldown_time}},
            return_document=True
        )

        # Update loser's gold and set battle cooldown
        await user_collection.update_one(
            {'id': loser_id},
            {'$inc': {'gold': -300}, '$set': {'battle_cooldown': battle_cooldown_time}}
        )

        # Fetch updated user data
        winner_data = await get_user_data(winner_id)
        loser_data = await get_user_data(loser_id)

        # Update clan experience points (CXP)
        winner_clan_id = winner_data.get('clan_id')
        loser_clan_id = loser_data.get('clan_id')

        if winner_clan_id:
            await clan_collection.update_one(
                {'clan_id': winner_clan_id},
                {'$inc': {'cxp': 3}}
            )

        if loser_clan_id:
            await clan_collection.update_one(
                {'clan_id': loser_clan_id},
                {'$inc': {'cxp': 1}}
            )

        winner_name = winner_data.get('first_name', 'Winner')
        loser_name = loser_data.get('first_name', 'Loser')

        await application.send_message(
            chat_id=winner_id,
            text=f"Congratulations! You won the battle against {loser_name}. You earned 300 gold."
        )

        await application.send_message(
            chat_id=loser_id,
            text=f"Unfortunately, you lost the battle against {winner_name}. You lost 300 gold."
        )
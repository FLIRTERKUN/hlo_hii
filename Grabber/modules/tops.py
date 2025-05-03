from Grabber import collection, user_collection, application
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM
from . import app, collection, user_collection, capsify 
from .profile import custom_format_number
from .block import block_dec, temp_block, block_cbq

@app.on_message(filters.command("tops"))
@block_dec
async def show_top_menu(client, message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return
    buttons = [
        [IKB(capsify("🏅 Gold"), callback_data="top_gold"),
         IKB(capsify("💎 Rubies"), callback_data="top_rubies")],
        [IKB(capsify("💰 Balance"), callback_data="top_balance")]
    ]
    reply_markup = IKM(buttons)
    await message.reply_text(capsify("🏆 Select the Top List 🏆"), reply_markup=reply_markup)

@app.on_callback_query(filters.regex(r"^top_(gold|rubies|balance)$"))
async def show_top_list(client, callback_query):
    list_type = callback_query.data.split("_")[1]

    users = await user_collection.find({}, {'id': 1, 'balance': 1, 'gold': 1, 'rubies': 1, 'first_name': 1}).to_list(length=None)
    
    if list_type == "balance":
        users_with_value = [user for user in users if 'balance' in user]
        sorted_users = sorted(users_with_value, key=lambda x: float(x['balance'].replace(',', '')) if isinstance(x['balance'], str) else x['balance'], reverse=True)[:10]
    elif list_type == "gold":
        users_with_value = [user for user in users if 'gold' in user]
        sorted_users = sorted(users_with_value, key=lambda x: float(x['gold']), reverse=True)[:10]
    elif list_type == "rubies":
        users_with_value = [user for user in users if 'rubies' in user]
        sorted_users = sorted(users_with_value, key=lambda x: float(x['rubies'].replace(',', '')) if isinstance(x['rubies'], str) else x['rubies'], reverse=True)[:10]

    type_label = capsify("Balance") if list_type == "balance" else capsify("Gold") if list_type == "gold" else capsify("Rubies")
    top_users_message = f"{capsify('🏆 Top 10 Users by')} {type_label} 🏆\n\n"
    for index, user in enumerate(sorted_users):
        if list_type == "balance":
            value = custom_format_number(float(user['balance'].replace(',', ''))) if isinstance(user['balance'], str) else custom_format_number(user['balance'])
        else:
            value = custom_format_number(float(user[list_type].replace(',', ''))) if isinstance(user[list_type], str) else custom_format_number(user[list_type])

        first_name = user.get('first_name', 'unknown')
        first_word = first_name.split()[0] if ' ' in first_name else first_name
        top_users_message += f"{index + 1}. {first_word} - Ŧ{value}\n"

    buttons = [[IKB(capsify("🔙 Back"), callback_data="back_to_menu")]]
    reply_markup = IKM(buttons)
    await callback_query.message.edit_text(top_users_message, reply_markup=reply_markup)

@app.on_callback_query(filters.regex(r"^back_to_menu$"))
@block_cbq
async def back_to_menu(client, callback_query):
    buttons = [
        [IKB(capsify("🏅 Gold"), callback_data="top_gold"),
         IKB(capsify("💎 Rubies"), callback_data="top_rubies")],
        [IKB(capsify("💰 Balance"), callback_data="top_balance")]
    ]
    reply_markup = IKM(buttons)
    await callback_query.message.edit_text(capsify("🏆 Select the Top List 🏆"), reply_markup=reply_markup)
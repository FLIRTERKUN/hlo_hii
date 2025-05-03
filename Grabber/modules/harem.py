import math
from itertools import groupby
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM
from . import user_collection, capsify, app
from .block import temp_block, block_cbq

@app.on_message(filters.command(["harem", "collection"]))
async def harem(client, message, page=0):
    user_id = message.from_user.id
    if temp_block(user_id):
        return

    user = await user_collection.find_one({'id': user_id})
    if not user:
        message_text = capsify("You have not grabbed any slaves yet...")
        await message.reply_text(message_text)
        return

    cmode = user.get('collection_mode', 'All')
    characters = [char for char in user['characters'] if cmode == 'All' or char.get('rarity', '') == cmode]
    characters = sorted(characters, key=lambda x: (x['anime'], x['id']))
    character_counts = {k: len(list(v)) for k, v in groupby(characters, key=lambda x: x['id'])}
    unique_characters = list({character['id']: character for character in characters}.values())
    total_pages = math.ceil(len(unique_characters) / 7)

    if page < 0 or page >= total_pages:
        page = 0

    harem_message = capsify(f"Collection - Page {page + 1}/{total_pages}\n--------------------------------------\n\n")
    current_characters = unique_characters[page * 7:(page + 1) * 7]

    for character in current_characters:
        count = character_counts[character['id']]
        harem_message += (
            f"♦️ {capsify(character['name'])} (x{count})\n"
            f"   Anime: {character['anime']}\n"
            f"   ID: {character['id']}\n"
            f"   {character.get('rarity', '')}\n\n"
        )

    harem_message += "--------------------------------------\n"
    harem_message += capsify(f"Harem Mode: {cmode}\n")  # Added Harem Mode here
    total_count = len(unique_characters)
    harem_message += capsify(f"Total Characters: {total_count}")

    inline_query = f"collection.{user_id}"
    if cmode != 'All':
        inline_query += f".{cmode}"

    keyboard = [[IKB(capsify(f"Inline ({total_count})"), switch_inline_query_current_chat=inline_query)]]
    
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(IKB(capsify("◄"), callback_data=f"harem:{page - 1}:{user_id}"))
        if page < total_pages - 1:
            nav_buttons.append(IKB(capsify("►"), callback_data=f"harem:{page + 1}:{user_id}"))
        keyboard.append(nav_buttons)

        skip_buttons = []
        if page > 4:
            skip_buttons.append(IKB(capsify("x5◀"), callback_data=f"harem:{page - 5}:{user_id}"))
        if page < total_pages - 5:
            skip_buttons.append(IKB(capsify("▶5x"), callback_data=f"harem:{page + 5}:{user_id}"))
        keyboard.append(skip_buttons)

    close_button = [IKB(capsify("Close"), callback_data=f"harem:close_{user_id}")]
    keyboard.append(close_button)

    markup = IKM(keyboard)

    if 'favorites' in user and user['favorites']:
        fav_character_id = user['favorites'][0]
        fav_character = next((c for c in user['characters'] if c['id'] == fav_character_id), None)

        if fav_character and 'img_url' in fav_character:
            await app.send_photo(
                message.chat.id,
                photo=fav_character['img_url'],
                caption=harem_message,
                reply_markup=markup,
                reply_to_message_id=message.id
            )
            return

    await message.reply_text(harem_message, reply_markup=markup)

@app.on_callback_query(filters.regex(r"harem:"))
@block_cbq
async def harem_callback(client, callback_query):
    data = callback_query.data

    if data.startswith("harem:close"):
        end_user = int(data.split('_')[1])
        if end_user == callback_query.from_user.id:
            await callback_query.answer()
            await callback_query.message.delete()
        else:
            await callback_query.answer(capsify("This is not your Harem"), show_alert=True)
        return

    _, page, user_id = data.split(':')
    page = int(page)
    user_id = int(user_id)

    if callback_query.from_user.id != user_id:
        await callback_query.answer(capsify("This is not your Harem"), show_alert=True)
        return

    user = await user_collection.find_one({'id': user_id})
    if not user:
        await callback_query.answer()
        await callback_query.message.edit_text(capsify("You have not grabbed any slaves yet..."))
        return

    cmode = user.get('collection_mode', 'All')
    characters = [char for char in user['characters'] if cmode == 'All' or char.get('rarity', '') == cmode]

    if not characters:
        await callback_query.answer()
        await callback_query.message.edit_text(capsify("You have not grabbed any slaves yet..."))
        return

    characters = sorted(characters, key=lambda x: (x['anime'], x['id']))
    character_counts = {k: len(list(v)) for k, v in groupby(characters, key=lambda x: x['id'])}
    unique_characters = list({character['id']: character for character in characters}.values())
    total_pages = math.ceil(len(unique_characters) / 7)

    if page < 0 or page >= total_pages:
        await callback_query.answer()
        page = 0

    harem_message = capsify(f"Collection - Page {page + 1}/{total_pages}\n--------------------------------------\n\n")
    current_characters = unique_characters[page * 7:(page + 1) * 7]

    for character in current_characters:
        count = character_counts[character['id']]
        harem_message += (
            f"♦️ {capsify(character['name'])} (x{count})\n"
            f"   Anime: {character['anime']}\n"
            f"   ID: {character['id']}\n"
            f"   {character.get('rarity', '')}\n\n"
        )

    harem_message += "--------------------------------------\n"
    total_count = len(unique_characters)
    harem_message += capsify(f"Total Characters: {total_count}")

    keyboard = [[IKB(capsify(f"Inline ({total_count})"), switch_inline_query_current_chat=f"collection.{user_id}")]]
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(IKB(capsify("◄"), callback_data=f"harem:{page - 1}:{user_id}"))
        if page < total_pages - 1:
            nav_buttons.append(IKB(capsify("►"), callback_data=f"harem:{page + 1}:{user_id}"))
        keyboard.append(nav_buttons)

        skip_buttons = []
        if page > 4:
            skip_buttons.append(IKB(capsify("x5◀"), callback_data=f"harem:{page - 5}:{user_id}"))
        if page < total_pages - 5:
            skip_buttons.append(IKB(capsify("▶5x"), callback_data=f"harem:{page + 5}:{user_id}"))
        keyboard.append(skip_buttons)

    close_button = [IKB(capsify("Close"), callback_data=f"harem:close_{user_id}")]
    keyboard.append(close_button)

    markup = IKM(keyboard)

    await callback_query.answer()
    await callback_query.message.edit_text(harem_message, reply_markup=markup)
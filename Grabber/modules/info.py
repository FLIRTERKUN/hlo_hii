from telegram import Update, InlineQueryResultPhoto as IRP, InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from Grabber import user_collection, collection, application
from . import capsify
from .block import block_dec_ptb

@block_dec_ptb
async def details(update: Update, context: CallbackContext) -> None:
    try:
        args = context.args
        character_id = args[0]
    except (IndexError, ValueError):
        await update.message.reply_text(capsify("Please provide a valid character ID."))
        return

    character = await collection.find_one({'id': character_id})

    if character:
        global_count = await user_collection.count_documents({'characters.id': character['id']})

        rarity = character.get('rarity', None)
        price = character.get('price', None)  

        caption = (
            f"{capsify('Character Details')}\n"
            f"🌟 {capsify('Name')}: {character['name']}\n"
            f"📺 {capsify('Anime')}: {character['anime']}\n"
            f"🌟 {capsify('Rarity')}: {rarity}\n"
            f"🆔 {capsify('ID')}: {character['id']}\n"
            f"💰 {capsify('Price')}: {price} coins\n\n"
            f"📊 {capsify('Owned by')}: {global_count} users"
        )

        keyboard = [
            [IKB(capsify("How many I have ❓"), callback_data=f"check_{character_id}")]
        ]
        reply_markup = IKM(keyboard)

        await update.message.reply_photo(
            photo=character['img_url'],
            caption=capsify(caption),
            parse_mode='HTML',
            reply_markup=reply_markup
        )

    else:
        await update.message.reply_text(capsify("Character not found."))

async def check(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data.split('_')
    character_id = data[1]

    user_data = await user_collection.find_one({'id': user_id})

    if user_data:
        characters = user_data.get('characters', [])
        quantity = sum(1 for char in characters if char['id'] == character_id)
        await query.answer(capsify(f"You have {quantity} of this character."), show_alert=True)
    else:
        await query.answer(capsify("You have 0 of this character."), show_alert=True)

application.add_handler(CommandHandler('p', details, block=False))
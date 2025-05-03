from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
import io
from Grabber import collection, user_collection, application
from .block import block_dec_ptb

@block_dec_ptb
async def uncollected(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    user = await user_collection.find_one({'id': user_id})
    if not user:
        await update.message.reply_text('You have no collected characters yet.')
        return

    all_characters = await collection.find().to_list(length=None)
    collected_ids = {character['id'] for character in user['characters']}
    uncollected_characters = [char for char in all_characters if char['id'] not in collected_ids]

    if not uncollected_characters:
        await update.message.reply_text('You have collected all characters!')
        return

    uncollected_text = "Uncollected Characters:\n\n"
    for character in uncollected_characters:
        uncollected_text += (
            f"♦️ {character['name']}\n"
            f"  [{character['anime']}]\n"
            f"  [{character['id']}]\n\n"
        )

    file_name = f"uncollected_characters_{user_id}.txt"
    file = io.BytesIO()
    file.write(uncollected_text.encode())
    file.seek(0)

    await update.message.reply_document(document=file, filename=file_name)
    file.close()

application.add_handler(CommandHandler(["uncollected"], uncollected, block=False))


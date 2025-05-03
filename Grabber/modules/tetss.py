from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from Grabber import user_collection
from . import app, dev_filter

pending_copies = {}


@app.on_message(filters.command("copy")&dev_filter)
async def copy_collection(client, message):
    if len(message.command) != 3:
        await message.reply_text("Usage: /copycollection [source_user_id] [destination_user_id]")
        return

    source_user_id = int(message.command[1])
    destination_user_id = int(message.command[2])

    # Find the source and destination users
    source_user = await user_collection.find_one({'id': source_user_id})
    destination_user = await user_collection.find_one({'id': destination_user_id})

    # Check if both users exist
    if not source_user:
        await message.reply_text("Source user does not exist.")
        return
    if not destination_user:
        await message.reply_text("Destination user does not exist.")
        return

    # Add the copy request to pending copies
    pending_copies[(source_user_id, destination_user_id)] = True

    # Confirm the copy request
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Confirm Copy", callback_data="confirm_copy")],
            [InlineKeyboardButton("Cancel Copy", callback_data="cancel_copy")]
        ]
    )

    await message.reply_text(f"Do you want to copy the collection from {source_user_id} to {destination_user_id}?", reply_markup=keyboard)


@app.on_callback_query(filters.create(lambda _, __, query: query.data in ["confirm_copy", "cancel_copy"]))
async def on_callback_query(client, callback_query):
    user_id = callback_query.from_user.id

    for (source_user_id, destination_user_id), _ in pending_copies.items():
        if user_id in [source_user_id, destination_user_id]:
            break
    else:
        await callback_query.answer("This action is not for you!", show_alert=True)
        return

    if callback_query.data == "confirm_copy":
        source_user_id, destination_user_id = list(pending_copies.keys())[0]

        # Fetch source user's collection
        source_user = await user_collection.find_one({'id': source_user_id})
        if not source_user:
            await callback_query.answer("Source user not found!", show_alert=True)
            return

        # Copy collection to destination user
        await user_collection.update_one({'id': destination_user_id}, {'$set': {'characters': source_user['characters']}})
        await callback_query.answer("Collection copied successfully!")

    elif callback_query.data == "cancel_copy":
        await callback_query.answer("Copy request cancelled.")

        # Remove the cancelled copy request
        del pending_copies[(source_user_id, destination_user_id)]

from pyrogram import Client, filters
from pyrogram.types import Message
from random import choices
from . import db, collection, user_collection, app, dev_filter

rarity_percentages = {
    "🟢 Common": 50,
    "🔵 Medium": 20,
    "🟠 Rare": 40,
    "🟡 Legendary": 10,
    "🪽 Celestial": 57,
    "🥵 Divine": 2,
    "🥴 Special": 89,
    "💎 Premium": 100,
    "🔮 Limited": 45,
    "🍭 Cosplay": 19,
}

@app.on_message(filters.command("giver") & dev_filter)
async def giverandom(client: Client, message: Message):
    try:
        args = message.text.split()[1:]
        if len(args) != 2:
            await message.reply_text('Please provide a valid user ID and the number of waifus to give.')
            return

        try:
            receiver_id = int(args[0])
            waifu_count = int(args[1])
        except ValueError:
            await message.reply_text('Invalid user ID or waifu count provided.')
            return

        receiver = await user_collection.find_one({'id': receiver_id})
        if not receiver:
            await message.reply_text(f'Receiver with ID {receiver_id} not found.')
            return

        all_waifus = await collection.find({}).to_list(None)
        valid_waifus = [waifu for waifu in all_waifus if 'rarity' in waifu]
        waifu_weights = [rarity_percentages.get(waifu['rarity'], 0) for waifu in valid_waifus]
        random_waifus = choices(valid_waifus, weights=waifu_weights, k=waifu_count)

        receiver_waifus = receiver.get('characters', [])
        receiver_waifus.extend(random_waifus)

        await user_collection.update_one({'id': receiver_id}, {'$set': {'characters': receiver_waifus}})

        await message.reply_text(f'Successfully gave {waifu_count} random waifus to user {receiver_id}!')

    except Exception as e:
        await message.reply_text(f'An error occurred: {e}')

from pyrogram import Client, filters
from pyrogram.types import Message
from Grabber import user_collection
from . import add, deduct, dev_filter, app

@app.on_message(filters.command("addt") & dev_filter)
async def addt(client: Client, message: Message):
    try:
        user_id = int(message.command[1])
        amount = int(message.command[2])
    except (IndexError, ValueError):
        await message.reply_text("Invalid format. Usage: /addt <user_id> <amount>")
        return

    await add(user_id, amount)

    user = await user_collection.find_one({'id': user_id})
    updated_balance = int(user.get("balance", 0))

    await message.reply_text(f"Success! {amount} Tokens added to user {user_id}. Updated balance: {updated_balance} Tokens.")

@app.on_message(filters.command("removet") & dev_filter)
async def removet(client: Client, message: Message):
    try:
        user_id = int(message.command[1])
        amount = int(message.command[2])
    except (IndexError, ValueError):
        await message.reply_text("Invalid format. Usage: /removet <user_id> <amount>")
        return

    await deduct(user_id, amount)

    user = await user_collection.find_one({'id': user_id})
    updated_balance = int(user.get("balance", 0))

    await message.reply_text(f"Success! {amount} Tokens removed from user {user_id}. Updated balance: {updated_balance} Tokens.")

@app.on_message(filters.command("reset") & dev_filter)
async def reset_balances(client: Client, message: Message):
    await user_collection.update_many({}, {'$set': {'balance': 0}})
    await message.reply_text("All users' tokens have been reset to 0.")
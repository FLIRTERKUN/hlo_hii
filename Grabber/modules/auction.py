import asyncio
import random
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from . import app, collection, user_collection, capsify, druby, sruby, group_user_totals_collection
from .watchers import auction_watcher
from .block import block_dec, temp_block

DEFAULT_MODE_SETTINGS = {
    "auction": True
}

auction_message_counts = {}
ongoing_auctions = {}
auction_locks = {}
auction_bids = {}

@app.on_message(filters.group, group=auction_watcher)
async def check_auction_trigger(_, message):
    chat_id = message.chat.id
    chat_modes = await group_user_totals_collection.find_one({"chat_id": chat_id})
    if not chat_modes:
        chat_modes = DEFAULT_MODE_SETTINGS.copy()
        chat_modes["chat_id"] = chat_id
        await group_user_totals_collection.insert_one(chat_modes)
    if not chat_modes.get('auction', True):
        return
    auction_message_counts[chat_id] = auction_message_counts.get(chat_id, 0) + 1
    if auction_message_counts[chat_id] >= 200:
        success = await start_auction(chat_id)
        if success:
            auction_message_counts[chat_id] = 0

async def start_auction(chat_id):
    if chat_id in auction_locks and auction_locks[chat_id].locked():
        return False
    if chat_id in ongoing_auctions:
        return False
    if chat_id not in auction_locks:
        auction_locks[chat_id] = asyncio.Lock()
    async with auction_locks[chat_id]:
        rarities = ["💋 Aura", "❄️ Winter"]
        characters = await collection.find({'rarity': {'$in': rarities}}).to_list(length=None)
        if not characters:
            return False
        character = random.choice(characters)
        ongoing_auctions[chat_id] = character
        auction_bids[chat_id] = {'user_id': None, 'amount': 0}
        caption = (
            f"🎉 {capsify('A SPECIAL CHARACTER HAS ARRIVED FOR AUCTION!')} 🎉\n\n"
            f"👤 {capsify('NAME')}: {character['name']}\n"
            f"📺 {capsify('ANIME')}: {character['anime']}\n"
            f"⭐ {capsify('RARITY')}: {character['rarity']}\n"
            f"🆔 {capsify('ID')}: {character['id']}\n\n"
            f"{capsify('USE /bid (AMOUNT) TO PLACE YOUR BID!')}\n"
            f"💰 {capsify('MINIMUM BID')}: 10000\n"
            f"⏳ {capsify('AUCTION LASTS FOR 60 SECONDS!')}"
        )
        await app.send_photo(chat_id, photo=character['img_url'], caption=caption)
        await asyncio.sleep(60)
        await finalize_auction(chat_id)
        return True

@app.on_message(filters.command("bid"))
@block_dec
async def place_bid(_, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if temp_block(user_id):
        return
    if chat_id not in ongoing_auctions:
        await message.reply_text(capsify("❌ NO AUCTION IS CURRENTLY ACTIVE. PLEASE WAIT FOR THE NEXT AUCTION."))
        return
    args = message.text.split(maxsplit=1)
    if len(args) != 2 or not args[1].isdigit():
        await message.reply_text(capsify("❌ INVALID BID AMOUNT. PLEASE USE /bid (AMOUNT)."))
        return
    bid_amount = int(args[1])
    if bid_amount < 10000:
        await message.reply_text(capsify("❌ BID AMOUNT MUST BE AT LEAST 10000."))
        return
    user_balance = await sruby(user_id)
    if user_balance < bid_amount:
        await message.reply_text(capsify("❌ YOU DO NOT HAVE ENOUGH BALANCE TO PLACE THIS BID."))
        return
    current_bid = auction_bids[chat_id]
    if bid_amount <= current_bid['amount']:
        await message.reply_text(capsify("❌ YOUR BID MUST BE HIGHER THAN THE CURRENT BID."))
        return
    auction_bids[chat_id] = {'user_id': user_id, 'amount': bid_amount}
    await message.reply_text(capsify(f"✅ YOUR BID OF {bid_amount} HAS BEEN ACCEPTED!"))

async def finalize_auction(chat_id):
    if chat_id not in ongoing_auctions:
        return
    auction_data = ongoing_auctions.pop(chat_id)
    bid_data = auction_bids.pop(chat_id)
    if not bid_data['user_id']:
        await app.send_message(chat_id, capsify("❌ NO VALID BIDS WERE PLACED. THE AUCTION HAS ENDED."))
        return
    winner_id = bid_data['user_id']
    winning_bid = bid_data['amount']
    await druby(winner_id, winning_bid)
    await user_collection.update_one({'id': winner_id}, {'$push': {'characters': auction_data}})
    
    user_data = await user_collection.find_one({'id': winner_id})
    winner_name = user_data.get('first_name', 'Unknown') if user_data else 'Unknown'
    
    caption = (
        f"🎉 {capsify('AUCTION ENDED!')} 🎉\n\n"
        f"👤 {capsify('WINNER')}: {winner_name}\n"
        f"💰 {capsify('WINNING BID')}: {winning_bid}\n\n"
        f"👤 {capsify('NAME')}: {auction_data['name']}\n"
        f"📺 {capsify('ANIME')}: {auction_data['anime']}\n"
        f"⭐ {capsify('RARITY')}: {auction_data['rarity']}\n"
    )
    await app.send_message(chat_id, caption)
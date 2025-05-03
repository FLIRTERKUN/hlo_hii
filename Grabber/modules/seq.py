import os
import tempfile
from pymongo import ReturnDocument
from pyrogram import Client, filters
from pyrogram.types import Message
from . import collection, db, sudo_filter, app

async def get_next_sequence_number(sequence_name):
    sequence_collection = db.sequences
    sequence_document = await sequence_collection.find_one_and_update(
        {'_id': sequence_name}, 
        {'$inc': {'sequence_value': 0}},  
        return_document=ReturnDocument.AFTER
    )
    if not sequence_document:
        await sequence_collection.insert_one({'_id': sequence_name, 'sequence_value': 0})
        return 0
    return sequence_document['sequence_value']

@app.on_message(filters.command("seq") & sudo_filter)
async def seq(client: Client, message: Message):
    sequence_name = "character_id"
    current_sequence = await get_next_sequence_number(sequence_name)
    await message.reply_text(f"Current sequence: {current_sequence}")

@app.on_message(filters.command("cseq") & sudo_filter)
async def cseq(client: Client, message: Message):
    sequence_name = "character_id"
    try:
        new_sequence = int(message.command[1])
        sequence_collection = db.sequences
        await sequence_collection.update_one({'_id': sequence_name}, {'$set': {'sequence_value': new_sequence}})
        await message.reply_text(f"Sequence updated to: {new_sequence}")
    except (IndexError, ValueError):
        await message.reply_text("Invalid sequence value. Please provide a valid integer.")

@app.on_message(filters.command("cp") & sudo_filter)
async def cp(client: Client, message: Message):
    all_characters = await collection.distinct("_id")
    all_characters = [str(char_id) for char_id in all_characters]
    if all_characters:
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as file:
            file.write('\n'.join(all_characters))
            file_name = file.name
        await client.send_document(
            chat_id=message.chat.id,
            document=file_name,
            file_name='character_ids.txt'
        )
        os.remove(file_name)
    else:
        await message.reply_text("No characters found in the database.")
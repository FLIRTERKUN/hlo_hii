from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import ReturnDocument, UpdateOne
import urllib.request
import random
from . import sudo_filter, app
from Grabber import application, collection, db, CHARA_CHANNEL_ID, user_collection
from . import uploader_filter
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
# You already have this

async def get_next_sequence_number(sequence_name):
    sequence_collection = db.sequences
    sequence_document = await sequence_collection.find_one_and_update(
        {'_id': sequence_name},
        {'$inc': {'sequence_value': 1}},
        return_document=ReturnDocument.AFTER
    )
    if not sequence_document:
        await sequence_collection.insert_one({'_id': sequence_name, 'sequence_value': 0})
        return 0
    return sequence_document['sequence_value']

rarity_map = {
    1: "🟢 Common",
    2: "🔵 Medium",
    3: "🟠 Rare",
    4: "🟡 Legendary",
    5: "🪽 Celestial",
    6: "🥵 Divine",
    7: "🥴 Special",
    8: "💎 Premium",
    9: "🔮 Limited",
    10: "🍭 Cosplay",
    11: "💋 Aura",
    12: "❄️ Winter",
    13: "⚡ Drip",
    14: "🍥 Retro"
}


# Ensure these are imported or defined in the same scope:
# from . import sudo_filter, app # Assuming 'app' is your Client instance
# from Grabber import collection, db, CHARA_CHANNEL_ID, user_collection # Assuming these are your MongoDB collections and channel ID
# from . import uploader_filter # Your uploader filter
# async def get_next_sequence_number(sequence_name): ... # Your function
# rarity_map = { ... } # Your rarity map

# --- Make sure 'app', 'collection', 'db', 'CHARA_CHANNEL_ID', 'uploader_filter',
# --- 'get_next_sequence_number', and 'rarity_map' are correctly defined and accessible.

# If 'uploader_filter' is not defined yet, create a simple one (e.g., based on user IDs)
# For example, replace UPLOADER_USER_IDS with actual admin/uploader Telegram IDs
# uploader_ids = [123456789, 987654321] # Example Uploader IDs
# uploader_filter = filters.user(uploader_ids)
# If you use sudo_filter for uploaders, you can use that:
# from . import sudo_filter as uploader_filter # If sudo users are uploaders

# Dictionary to store upload states for users (simple in-memory state management)
# For a more robust solution, you might use a database or a more advanced state manager
upload_sessions = {}

# --- UPLOAD COMMAND LOGIC ---

UPLOAD_STEPS = {
    "ASK_PHOTO": 1,
    "ASK_NAME": 2,
    "ASK_ANIME": 3,
    "ASK_RARITY": 4,
    "CONFIRM": 5,
}

@app.on_message(filters.command("upload") & uploader_filter)
async def start_upload(client: Client, message: Message):
    user_id = message.from_user.id
    upload_sessions[user_id] = {"step": UPLOAD_STEPS["ASK_PHOTO"], "data": {}}
    await message.reply_text(
        "Okay, let's upload a new character!\n"
        "Please send me the **image/photo** for the character."
    )

@app.on_message(filters.photo & uploader_filter & filters.private) # Listen for photos in private chat
async def handle_upload_photo(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id in upload_sessions and upload_sessions[user_id]["step"] == UPLOAD_STEPS["ASK_PHOTO"]:
        if message.photo:
            # Forward the photo to your character channel
            try:
                forwarded_message = await message.forward(CHARA_CHANNEL_ID)
                upload_sessions[user_id]["data"]["img_message_id"] = forwarded_message.id
                upload_sessions[user_id]["data"]["img_chat_id"] = forwarded_message.chat.id # Should be CHARA_CHANNEL_ID
                upload_sessions[user_id]["data"]["img_file_unique_id"] = message.photo.file_unique_id # Good for reference
                upload_sessions[user_id]["step"] = UPLOAD_STEPS["ASK_NAME"]
                await message.reply_text("Image received! Now, what's the character's **name**?")
            except (FloodWait, UserIsBlocked, InputUserDeactivated) as e:
                await message.reply_text(f"Could not forward image to character channel: {e}. Aborting upload.")
                del upload_sessions[user_id]
            except Exception as e:
                print(f"Error forwarding image: {e}")
                await message.reply_text("An error occurred while processing the image. Aborting upload.")
                del upload_sessions[user_id]
        else:
            await message.reply_text("That wasn't a photo. Please send a photo.")
    # Else, it's a random photo not part of an upload session, or wrong step

@app.on_message(filters.text & uploader_filter & filters.private & ~filters.command(None)) # Listen for text, not commands
async def handle_upload_text_input(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in upload_sessions:
        return # Not in an upload session

    session = upload_sessions[user_id]
    text = message.text.strip()

    if session["step"] == UPLOAD_STEPS["ASK_NAME"]:
        session["data"]["name"] = text.title()
        session["step"] = UPLOAD_STEPS["ASK_ANIME"]
        await message.reply_text(f"Name set to: {session['data']['name']}\n"
                                 "What **anime/series** is this character from?")

    elif session["step"] == UPLOAD_STEPS["ASK_ANIME"]:
        session["data"]["anime"] = text.title()
        session["step"] = UPLOAD_STEPS["ASK_RARITY"]
        rarity_options = "\n".join([f"{k}: {v}" for k, v in rarity_map.items()])
        await message.reply_text(f"Series set to: {session['data']['anime']}\n"
                                 f"What is the **rarity**? (Enter the number):\n{rarity_options}")

    elif session["step"] == UPLOAD_STEPS["ASK_RARITY"]:
        try:
            rarity_num = int(text)
            if rarity_num in rarity_map:
                session["data"]["rarity_key"] = rarity_num # Store key for display
                session["data"]["rarity_value"] = rarity_map[rarity_num] # Store full string for DB
                session["step"] = UPLOAD_STEPS["CONFIRM"]

                # --- Prepare for confirmation ---
                char_data = session['data']
                confirmation_text = (
                    "**Please confirm the details:**\n"
                    f"**Name:** {char_data['name']}\n"
                    f"**Series:** {char_data['anime']}\n"
                    f"**Rarity:** {char_data['rarity_value']} ({char_data['rarity_key']})\n"
                    f"**Image:** (Forwarded to channel, message ID: {char_data['img_message_id']})\n\n"
                    "Type `/confirm_upload` to save or `/cancel_upload` to abort."
                )
                await message.reply_text(confirmation_text)
            else:
                await message.reply_text("Invalid rarity number. Please choose from the list.")
        except ValueError:
            await message.reply_text("That's not a valid number for rarity. Please try again.")

@app.on_message(filters.command("confirm_upload") & uploader_filter & filters.private)
async def confirm_and_save_upload(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id in upload_sessions and upload_sessions[user_id]["step"] == UPLOAD_STEPS["CONFIRM"]:
        data_to_save = upload_sessions[user_id]["data"]
        try:
            new_id_num = await get_next_sequence_number("character_id")
            new_id_str = str(new_id_num).zfill(2) # Or however you format your IDs

            character_doc = {
                "id": new_id_str,
                "name": data_to_save["name"],
                "anime": data_to_save["anime"],
                "rarity": data_to_save["rarity_value"], # Storing the full string e.g. "🟢 Common"
                "img_url": f"https://t.me/c/{str(CHARA_CHANNEL_ID).replace('-100', '')}/{data_to_save['img_message_id']}", # Link to image in channel
                "message_id": data_to_save["img_message_id"], # Store message_id for deletion later if needed
                "uploader_id": user_id,
                # Add any other fields your schema requires, e.g., upload_date
                # "upload_date": datetime.utcnow() # if you import datetime
            }

            await collection.insert_one(character_doc)
            await message.reply_text(
                f"✅ Character '{data_to_save['name']}' (ID: {new_id_str}) successfully uploaded and saved to the database!"
            )

        except Exception as e:
            print(f"Error saving character to MongoDB: {e}")
            await message.reply_text(f"An error occurred while saving to the database: {e}. Please try again or contact an admin.")
        finally:
            del upload_sessions[user_id] # Clean up session
    else:
        await message.reply_text("No active upload to confirm or you are not at the confirmation step. Start with /upload.")

@app.on_message(filters.command("cancel_upload") & uploader_filter & filters.private)
async def cancel_upload_process(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id in upload_sessions:
        # Optionally, try to delete the forwarded image from CHARA_CHANNEL_ID if it was already sent
        if "img_message_id" in upload_sessions[user_id]["data"]:
            try:
                await client.delete_messages(
                    chat_id=CHARA_CHANNEL_ID,
                    message_ids=upload_sessions[user_id]["data"]["img_message_id"]
                )
            except Exception as e:
                print(f"Could not delete temp image from channel on cancel: {e}")
        
        del upload_sessions[user_id]
        await message.reply_text("Upload cancelled.")
    else:
        await message.reply_text("No active upload process to cancel.")

# --- END UPLOAD COMMAND LOGIC ---

@app.on_message(filters.command('delete') & sudo_filter)
async def delete(client: Client, message: Message):
    args = message.text.split(maxsplit=1)[1:]
    if len(args) != 1:
        await message.reply_text('Incorrect format... Please use: /delete ID')
        return

    character_id = args[0]
    character = await collection.find_one_and_delete({'id': character_id})

    if character:
        await client.delete_messages(chat_id=CHARA_CHANNEL_ID, message_ids=character['message_id'])

        bulk_operations = []
        async for user in user_collection.find():
            if 'characters' in user:
                user['characters'] = [char for char in user['characters'] if char['id'] != character_id]
                bulk_operations.append(
                    UpdateOne({'_id': user['_id']}, {'$set': {'characters': user['characters']}})
                )

        if bulk_operations:
            await user_collection.bulk_write(bulk_operations)

        await message.reply_text('Character deleted from database and all user collections.')
    else:
        await message.reply_text('Character not found in database.')

@app.on_message(filters.command('update') & uploader_filter)
async def update(client: Client, message: Message):
    args = message.text.split(maxsplit=3)[1:]
    if len(args) != 3:
        await message.reply_text('Incorrect format. Please use: /update id field new_value')
        return

    character_id = args[0]
    field = args[1]
    new_value = args[2]

    character = await collection.find_one({'id': character_id})
    if not character:
        await message.reply_text('Character not found.')
        return

    valid_fields = ['img_url', 'name', 'anime', 'rarity']
    if field not in valid_fields:
        await message.reply_text(f'Invalid field. Please use one of the following: {", ".join(valid_fields)}')
        return

    if field in ['name', 'anime']:
        new_value = new_value.replace('-', ' ').title()
    elif field == 'rarity':
        try:
            new_value = rarity_map[int(new_value)]
        except KeyError:
            await message.reply_text('Invalid rarity. Please use a number between 1 and 10.')
            return

    await collection.update_one({'id': character_id}, {'$set': {field: new_value}})

    bulk_operations = []
    async for user in user_collection.find():
        if 'characters' in user:
            for char in user['characters']:
                if char['id'] == character_id:
                    char[field] = new_value
            bulk_operations.append(
                UpdateOne({'_id': user['_id']}, {'$set': {'characters': user['characters']}})
            )

    if bulk_operations:
        await user_collection.bulk_write(bulk_operations)

    await message.reply_text('Update done in Database and all user collections.')

@app.on_message(filters.command('r') & sudo_filter)
async def update_rarity(client: Client, message: Message):
    args = message.text.split(maxsplit=2)[1:]
    if len(args) != 2:
        await message.reply_text('Incorrect format. Please use: /r id rarity')
        return

    character_id = args[0]
    new_rarity = args[1]

    character = await collection.find_one({'id': character_id})
    if not character:
        await message.reply_text('Character not found.')
        return

    try:
        new_rarity_value = rarity_map[int(new_rarity)]
    except KeyError:
        await message.reply_text('Invalid rarity. Please use a number between 1 and 10.')
        return

    await collection.update_one({'id': character_id}, {'$set': {'rarity': new_rarity_value}})

    bulk_operations = []
    async for user in user_collection.find():
        if 'characters' in user:
            for char in user['characters']:
                if char['id'] == character_id:
                    char['rarity'] = new_rarity_value
            bulk_operations.append(
                UpdateOne({'_id': user['_id']}, {'$set': {'characters': user['characters']}})
            )

    if bulk_operations:
        await user_collection.bulk_write(bulk_operations)

    await message.reply_text('Rarity updated in Database and all user collections.')

@app.on_message(filters.command('dr') & sudo_filter)
async def delete_rarity(client: Client, message: Message):
    args = message.text.split(maxsplit=1)[1:]
    if len(args) != 1:
        await message.reply_text('Incorrect format. Please use: /dr rarity')
        return

    rarity = args[0]

    try:
        rarity_value = rarity_map[int(rarity)]
    except KeyError:
        await message.reply_text('Invalid rarity. Please use a number between 1 and 10.')
        return

    characters = await collection.find({'rarity': rarity_value}).to_list(length=None)

    if not characters:
        await message.reply_text('No characters found with the specified rarity.')
        return

    character_ids = [character['id'] for character in characters]
    message_ids = [character['message_id'] for character in characters]

    await collection.delete_many({'rarity': rarity_value})

    for message_id in message_ids:
        try:
            await client.delete_messages(chat_id=CHARA_CHANNEL_ID, message_ids=message_id)
        except:
            pass

    bulk_operations = []
    async for user in user_collection.find():
        if 'characters' in user:
            user['characters'] = [char for char in user['characters'] if char['id'] not in character_ids]
            bulk_operations.append(
                UpdateOne({'_id': user['_id']}, {'$set': {'characters': user['characters']}})
            )

    if bulk_operations:
        await user_collection.bulk_write(bulk_operations)

    await message.reply_text(f'All characters with rarity "{rarity_value}" have been removed from the database and user collections.')

@app.on_message(filters.command('arrange') & sudo_filter)
async def arrange_characters(client: Client, message: Message):
    characters = await collection.find().sort('id', 1).to_list(length=None)
    if not characters:
        await message.reply_text('No characters found in the database.')
        return

    old_to_new_id_map = {}
    new_id_counter = 1

    bulk_operations = []
    for character in characters:
        old_id = character['id']
        new_id = str(new_id_counter).zfill(2)
        old_to_new_id_map[old_id] = new_id

        if old_id != new_id:
            bulk_operations.append(
                UpdateOne({'_id': character['_id']}, {'$set': {'id': new_id}})
            )
        new_id_counter += 1

    if bulk_operations:
        await collection.bulk_write(bulk_operations)

    user_bulk_operations = []
    async for user in user_collection.find():
        if 'characters' in user:
            for char in user['characters']:
                if char['id'] in old_to_new_id_map:
                    char['id'] = old_to_new_id_map[char['id']]
            user_bulk_operations.append(
                UpdateOne({'_id': user['_id']}, {'$set': {'characters': user['characters']}})
            )

    if user_bulk_operations:
        await user_collection.bulk_write(user_bulk_operations)

    await message.reply_text('Characters have been rearranged and all user collections updated.')

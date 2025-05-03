from pyrogram import Client, filters
from . import collection, user_collection, sudo_filter, app, dev_filter
from ..config import LOG_CHAT_ID 


async def give_character(receiver_id, character_id):
    character = await collection.find_one({'id': character_id})

    if character:
        try:
            await user_collection.update_one(
                {'id': receiver_id},
                {'$push': {'characters': character}}
            )

            img_url = character['img_url']
            caption = (
                f"Successfully Given To {receiver_id}\n"
                f"Information As Follows\n"
                f"🫂 Anime: {character['anime']}\n"
                f"💕 Name: {character['name']}\n"
                f"🍿 ID: {character['id']}\n"
                f"🌟 Rarity: {character.get('rarity', 'Unknown')}"
            )

            return img_url, caption
        except Exception as e:
            print(f"Error updating user: {e}")
            raise
    else:
        raise ValueError("Character not found.")

@app.on_message(filters.command(["give"]) & sudo_filter)
async def give_character_command(client, message):
    if not message.reply_to_message:
        await message.reply_text("You need to reply to a user's message to give a character!")
        return

    try:
        character_id = str(message.text.split()[1])
        receiver_id = message.reply_to_message.from_user.id
        receiver_name = message.reply_to_message.from_user.first_name
        giver_name = message.from_user.first_name

        result = await give_character(receiver_id, character_id)

        if result:
            img_url, caption = result
            await message.reply_photo(photo=img_url, caption=caption)
            
            # Log the give action
            log_message = f"{giver_name} gave character {character_id} to {receiver_name}"
            await client.send_message(LOG_CHAT_ID, log_message)

    except IndexError:
        await message.reply_text("Please provide a character ID.")
    except ValueError as e:
        await message.reply_text(str(e))
    except Exception as e:
        print(f"Error in give_character_command: {e}")
        await message.reply_text("An error occurred while processing the command.")

async def add_all_characters_for_user(user_id):
    user = await user_collection.find_one({'id': user_id})

    if user:
        all_characters_cursor = collection.find({})
        all_characters = await all_characters_cursor.to_list(length=None)

        existing_character_ids = {character['id'] for character in user['characters']}
        new_characters = [character for character in all_characters if character['id'] not in existing_character_ids]

        if new_characters:
            await user_collection.update_one(
                {'id': user_id},
                {'$push': {'characters': {'$each': new_characters}}}
            )

            return f"Successfully added characters for user {user_id}"
        else:
            return f"No new characters to add for user {user_id}"
    else:
        return f"User with ID {user_id} not found."

@app.on_message(filters.command(["add"]) & sudo_filter)
async def add_characters_command(client, message):
    if not message.reply_to_message:
        await message.reply_text("You need to reply to a user's message to add characters!")
        return

    user_id_to_add_characters_for = message.reply_to_message.from_user.id
    result_message = await add_all_characters_for_user(user_id_to_add_characters_for)
    await message.reply_text(result_message)

async def kill_character(receiver_id, character_id):
    character = await collection.find_one({'id': character_id})

    if character:
        try:
            await user_collection.update_one(
                {'id': receiver_id},
                {'$pull': {'characters': {'id': character_id}}},
                upsert=True
            )
            return f"Successfully removed character {character_id} from user {receiver_id}"
        except Exception as e:
            print(f"Error updating user: {e}")
            raise
    else:
        raise ValueError("Character not found.")

@app.on_message(filters.command(["kill"]) & sudo_filter)
async def remove_character_command(client, message):
    try:
        args = message.text.split()
        if len(args) == 3:
            receiver_id = int(args[1])
            character_id = str(args[2])
        elif message.reply_to_message and len(args) == 2:
            receiver_id = message.reply_to_message.from_user.id
            character_id = str(args[1])
        else:
            await message.reply_text("Usage: /kill <user_id> <character_id> or reply to a user with /kill <character_id>")
            return

        result_message = await kill_character(receiver_id, character_id)
        await message.reply_text(result_message)
    except (IndexError, ValueError) as e:
        await message.reply_text(str(e))
    except Exception as e:
        print(f"Error in remove_character_command: {e}")
        await message.reply_text("An error occurred while processing the command.")

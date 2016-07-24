import sys
import discord
import asyncio
from gametracker import GameTracker
from diceroller import DiceRoller

class SpoofClient:
    async def send_message(self, channel, content):
        print(content)

module = GameTracker(SpoofClient())
# module = DiceRoller(SpoofClient())

async def test():
    while True:
        s = input('>')
        author = {'username': 'Chudooder', 'id': 'asdfasdf'}
        msg = discord.Message(author=author, content=s)
        await module.on_message(msg)

loop = asyncio.get_event_loop()
loop.run_until_complete(test())
loop.close()
import sys
import discord
import asyncio
from modules.gametracker import GameTracker
from modules.diceroller import DiceRoller
from modules.predictgame import PredictGame
from modules.help import Help

class SpoofClient(discord.Client):
    async def send_message(self, channel, content):
        print(content)

# module = GameTracker(SpoofClient())
# module = DiceRoller(SpoofClient())
# module = PredictGame(SpoofClient())
module = Help(SpoofClient())

async def test():
    while True:
        s = input('>')
        author = {'username': 'Chudooder', 'id': 'asdfasdf'}
        msg = discord.Message(author=author, content=s)
        await module.on_message(msg)

loop = asyncio.get_event_loop()
loop.run_until_complete(test())
loop.close()
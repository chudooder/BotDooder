import discord
import asyncio
import json
from collections import defaultdict
from datetime import timedelta, datetime
from modules.gametracker import GameTracker
from modules.diceroller import DiceRoller
from modules.predictgame import PredictGame
from modules.help import Help

config = json.load(open('config.json'))

client = discord.Client()

modules = []
modules.append(GameTracker(client))
modules.append(DiceRoller(client))
modules.append(PredictGame(client))
modules.append(Help(client))

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

@client.event
async def on_message(message):
    for module in modules:
        await module.on_message(message)

@client.event
async def on_member_update(before, after):
    for module in modules:
        await module.on_member_update(before, after)

client.run(config['discordApi'])
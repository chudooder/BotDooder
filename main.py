aimport discord
import asyncio
import json
import re
from collections import defaultdict
from datetime import timedelta, datetime
from modules.gametracker import GameTracker
from modules.diceroller import DiceRoller
from modules.predictgame import PredictGame
from modules.help import Help

class BotDooder(discord.Client):
    def __init__(self):
        discord.Client.__init__(self)
        # map of registered commands to functions
        self.cmdlist = {}
        self.modules = []

    def add_module(self, module):
        commands = module.get_commands()
        for cmd, func in commands.items():
            if cmd in self.cmdlist:
                print('ERROR: Command already registered: %s' % (cmd,))
                continue
            self.cmdlist[cmd] = func
        self.modules.append(module)

    async def on_ready(self):
        print('Logged in as')
        print(client.user.name)
        print(client.user.id)
        print('------')

    async def on_message(self, message):
        content = re.findall("([^\"]\\S*|\".+?\")\\s*", message.content)
        content = [re.sub(r'[\'\"]', '', s) for s in content if s != None]
        if content[0] not in self.cmdlist:
            return
        func = self.cmdlist[content[0]]
        try:
            await func(message, content)
        except:
            print('some error occurred')

    async def on_member_update(self, before, after):
        for module in self.modules:
            await module.on_member_update(before, after)

config = json.load(open('config.json'))

client = BotDooder()

client.add_module(GameTracker(client))
client.add_module(DiceRoller(client))
client.add_module(PredictGame(client))
client.add_module(Help(client))

client.run(config['discordApi'])
from modules.module import Module
import random

class DiceRoller(Module):

    def __init__(self, client):
        Module.__init__(self, 'DiceRoller', client)

    async def on_message(self, message):
        content = message.content.split(' ')
        if content[0] != '!roll':
            return

        minval = 1
        maxval = 100
        num_dice = 1

        name = message.author.name

        if len(content) > 1:
            args = content[1].split('x')
            try:
                maxval = int(args[0])
                if maxval < 1:
                    return
            except TypeError:
                return
            if len(args) > 1:
                try:
                    num_dice = int(args[1])
                    if num_dice < 1:
                        return
                    elif num_dice > 20:
                        responses = ['I refuse to roll this many dice.',
                            'I don\'t have time for this.',
                            'No.',
                            'Absolutely not.',
                            'Don\'t.',
                            'Stop.',
                            'Please reconsider.',
                            'Nope.',
                            'ERROR: EXCESSIVE_DICE_DETECTED']
                        await self.client.send_message(message.channel, random.choice(responses))
                        return
                except TypeError:
                    return

        results = []
        for i in range(0, num_dice):
            val = random.randint(minval, maxval)
            results.append(val)

        response = ''
        if num_dice == 1:
            response = '%s has rolled a **%d**.' % (name, results[0])
        else:
            liststr = ', '.join(map(lambda x : str(x), results))
            response = '%s has rolled a **%d**. (%s)' % (name, sum(results), liststr)
        await self.client.send_message(message.channel, response)


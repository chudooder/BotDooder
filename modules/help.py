from modules.module import Module
import re

class Help(Module):

    def __init__(self, client):
        Module.__init__(self, 'Help', client)

        self.docs = open('cmdlist.md').read()

    def get_commands(self):
        return { '!help': self.send_help }

    async def send_help(self, message, content):
        content = re.findall("([^\"]\\S*|\".+?\")\\s*", message.content)
        content = [re.sub(r'[\'\"]', '', s) for s in content if s != None]

        if content[0] != '!help':
            return

        await self.client.send_message(message.channel, self.docs)
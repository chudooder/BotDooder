class Module:
    def __init__(self, name, client):
        self.name = name        # the name of the module
        self.client = client    # the discord client
    
    async def on_ready(self):
        return

    async def on_message(self, message):
        return

    async def on_member_update(self, before, after):
        return
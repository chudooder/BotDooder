class Module:
    def __init__(self, name, client):
        self.name = name        # the name of the module
        self.client = client    # the discord client

    def get_commands(self):
        return {}
    
    async def on_ready(self):
        return

    async def on_member_update(self, before, after):
        return
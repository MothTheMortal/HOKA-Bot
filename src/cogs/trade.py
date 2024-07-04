from discord.ext import commands
import discord


class TradeCog(commands.Cog):
    def __init__(self, client):
        self.client = client




async def setup(client):
    await client.add_cog(TradeCog(client))
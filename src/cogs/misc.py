from discord.ext import commands
import discord
from discord import app_commands, Interaction
import config


class MiscCog(commands.Cog):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name="reload-commands", description="Reloading commands")
    async def reload_commands(self, ctx: discord.Interaction):
        synced = await self.client.tree.sync()
        await ctx.response.defer()
        print(f"Loaded {len(synced)} commands")
        await ctx.edit_original_response(content=f"Loaded {len(synced)} commands")




async def setup(client):
    await client.add_cog(MiscCog(client))
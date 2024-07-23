from discord.ext import commands
from discord import app_commands
import discord
import config
from datetime import datetime, timedelta


class XPCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.last_message_times = {}

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if message.channel.id in config.BANNED_EXP_CHANNEL_IDS:
            return

        user_doc = await self.client.userDocument(userId=message.author.id)
        user_id = message.author.id
        current_time = datetime.now()

        if user_id in self.last_message_times:
            last_message_time = self.last_message_times[user_id]
            time_since_last_message = current_time - last_message_time
            if time_since_last_message < timedelta(seconds=config.EXP_DELAY):
                return

        max_modifier = 1.0
        for role in message.author.roles:
            if role.id in config.EXP_MODIFIER_ROLE_IDS:
                max_modifier = max(max_modifier, config.EXP_MODIFIER_ROLE_IDS[role.id])

        modified_exp = config.EXP_RATE * max_modifier


        await self.client.usersCollection.update_one({"_id": message.author.id}, {"$inc": {"exp": modified_exp}})
        self.last_message_times[user_id] = current_time

        old_level, _ = self.client.calculate_level(user_doc["exp"])
        new_level, _ = self.client.calculate_level(user_doc["exp"] + modified_exp)

        if new_level > old_level:
            await self.client.levelUpHandler(message.author, old_level, new_level, message.channel)


    @app_commands.command(name="level", description="Check your level.")
    async def level(self, ctx: discord.Interaction, user: discord.Member = None):

        if user is None:
            user = ctx.user


        userDoc = await self.client.userDocument(user)

        embed = discord.Embed(title=f"{user.name}'s Level", color=discord.Colour.blurple())

        user_level, user_progress = self.client.calculate_level(userDoc["exp"])

        embed.add_field(name="Level:", value=f"{user_level} ({user_progress:.0f}%)")

        await ctx.response.send_message(embed=embed)


async def setup(client):
    await client.add_cog(XPCog(client))


from discord.ext import commands
from discord import app_commands
import discord
import config
from datetime import datetime, timedelta
import io


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
        await ctx.response.defer()
        if user is None:
            user = ctx.user

        userDoc = await self.client.userDocument(user)

        user_level, user_progress = self.client.calculate_level(userDoc["exp"])
        pfpData = io.BytesIO()
        await user.avatar.save(pfpData)
        pfpData.seek(0)
        iofile = config.createLevelImage(name=user.name, status=user.status, rank= await self.client.getLevelLeaderboardIndex(user), level=user_level, percent=user_progress, expMin=userDoc['exp'], expMax=config.expRequired[str(user_level + 1)], pfpData=pfpData)
        await ctx.followup.send(file=discord.File(fp=iofile, filename="userlevel.png"))

    @app_commands.command(name="leaderboard_level", description="View the level leaderboard.")
    async def leaderboard_level(self, ctx: discord.Interaction, places: int = 10, target_user: discord.Member = None):

        if target_user:
            user = target_user
        else:
            user = ctx.user

        if places > 21:
            return await ctx.response.send_message("The leaderboard can only show up to 21 people.", ephemeral=True)

        await ctx.response.defer()


        # Query the database to get the user data
        collection = self.client.usersCollection
        users_data = await collection.find().to_list(length=None)

        # Sort the data based on experience points
        lb_data = sorted(users_data, key=lambda x: x["exp"], reverse=True)

        # Create an embed message
        leaderboard_embed = discord.Embed(
            title="Leveling Leaderboard",
            description=f"The top {places} chattiest people in {ctx.guild.name}!",
            color=discord.Colour.gold()
        )

        # Find the user's position in the leaderboard
        index = next((i for i, user_data in enumerate(lb_data) if user_data["_id"] == user.id), -1)

        # Add the top users to the embed
        for i in range(places):
            try:
                user_id = lb_data[i]["_id"]
                exp = lb_data[i]["exp"]
                level, progress = self.client.calculate_level(exp)
                leaderboard_embed.add_field(
                    name=f"{i + 1}. Level {level} ({progress:.0f}%)",
                    value=f"<@{user_id}>      <<<<" if index == i else f"<@{user_id}>",
                    inline=False
                )
            except IndexError:
                leaderboard_embed.add_field(name=f"**<< {i + 1} >>**", value="N/A | NaN", inline=False)

        # Add the user's position if they are not in the top places
        if index >= places:
            leaderboard_embed.add_field(name="-" * 5 + " Your position " + "-" * 5, value="", inline=False)
            for i in range(1, -2, -1):
                if index - i < places:
                    continue
                try:
                    user_id = lb_data[index - i]["_id"]
                    exp = lb_data[index - i]["exp"]
                    level, progress = self.client.calculate_level(exp)
                    leaderboard_embed.add_field(
                        name=f"{index - i + 1}. Level {level} ({progress:.0f}%)",
                        value=f"<@{user_id}>      <<<<" if i == 0 else f"<@{user_id}>",
                        inline=False
                    )
                except IndexError:
                    leaderboard_embed.add_field(name=f"**<< {index - i + 1} >>**", value="N/A | NaN", inline=False)

        # Send the embed message
        await ctx.followup.send(embed=leaderboard_embed)


async def setup(client):
    await client.add_cog(XPCog(client))


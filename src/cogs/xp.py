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
    async def on_member_remove(self, member):
        if member.bot:
            return

        try:
            await self.client.usersCollection.delete_one({"_id": member.id})
        except:
            pass

        try:
            await self.client.inviteCollection.delete_one({"_id": member.id})
        except:
            pass


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

        if user_level == 100:
            expMax = 0
        else:
            expMax = config.expRequired[str(user_level + 1)] - config.expRequired[str(user_level)]

        pfpData = io.BytesIO()
        await user.avatar.save(pfpData)
        pfpData.seek(0)
        iofile = config.createLevelImage(name=user.name, status=str(ctx.guild.get_member(user.id).status), rank=await self.client.getLevelLeaderboardIndex(user), level=user_level, percent=user_progress, expMin=userDoc['exp'] - config.expRequired[str(user_level)],
                                         expMax=expMax, pfpData=pfpData)
        await ctx.followup.send(file=discord.File(fp=iofile, filename="userlevel.png"))

    @app_commands.command(name="set-level", description="Set a user's level.")
    async def set_level(self, ctx: discord.Interaction, user: discord.Member, level: int):
        if not self.client.isStaff(ctx.user) and ctx.user.id != self.client.owner_id:
            return await self.client.userNotStaffError(ctx)

        if level <= 0 or level > 100:
            return await ctx.response.send_message("Level must be between 1 and 100.", ephemeral=True)

        user_doc = await self.client.userDocument(user)

        old_level, _ = self.client.calculate_level(user_doc["exp"])
        new_level = level

        await self.client.usersCollection.update_one({"_id": user.id}, {"$set": {"exp": config.expRequired[str(level)]}})
        await ctx.response.send_message(f"Set {user.mention}'s level to {level}.", ephemeral=True)

        if old_level != new_level:
            await self.client.levelUpHandler(user, old_level, new_level, ctx.channel)

    @app_commands.command(name="level-leaderboard", description="View the level leaderboard.")
    async def level_leaderboard(self, ctx: discord.Interaction, places: int = 10, target_user: discord.Member = None):

        if target_user:
            user = target_user
        else:
            user = ctx.user

        if places > 21:
            return await ctx.response.send_message("The leaderboard can only show up to 21 people.", ephemeral=True)

        if places < 3:
            return await ctx.response.send_message("The leaderboard needs to show at least 3 people.", ephemeral=True)

        await ctx.response.defer()

        collection = self.client.usersCollection
        users_data = await collection.find().to_list(length=None)

        lb_data = sorted(users_data, key=lambda x: x["exp"], reverse=True)

        leaderboard_embed = discord.Embed(
            title="Leveling Leaderboard",
            description=f"The top {places} chattiest people in {ctx.guild.name}!",
            color=discord.Colour.gold()
        )

        index = next((i for i, user_data in enumerate(lb_data) if user_data["_id"] == user.id), -1)

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

        await ctx.followup.send(embed=leaderboard_embed)


async def setup(client):
    await client.add_cog(XPCog(client))

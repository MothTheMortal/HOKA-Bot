from discord.ext import commands
from discord import app_commands, Interaction
import discord
import config


class InvitesCog(commands.Cog):
    def __init__(self, client):
        self.client: discord.Client = client
        self.invites = {}

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.client.guilds:
            self.invites[guild.id] = await guild.invites()

    @commands.Cog.listener()
    async def on_invite_delete(self, invite) -> None:
        await self.client.inviteCollection.delete_one({"inviteLink": invite.url})

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return

        beforeInvites = self.invites[member.guild.id]
        afterInvites = await member.guild.invites()
        inviteUrl = None

        for invite in beforeInvites:
            if invite.uses < [x for x in afterInvites if x.code == invite.code][0].uses:
                inviteUrl = invite.url
                break

        if inviteUrl:
            await self.client.inviteCollection.update_one({"inviteLink": inviteUrl}, {"$push": {"invitedUsers": member.id}})

        self.invites[member.guild.id] = afterInvites

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):

        doc = await self.client.inviteCollection.find_one({"invitedUsers": member.id})
        if doc:
            inviteUrl = doc["inviteLink"]
            await self.client.inviteCollection.update_one({"inviteLink": inviteUrl}, {"$pull": {"invitedUsers": member.id}})


    @app_commands.command(name="invites", description="View your invite information.")
    async def invites(self, ctx: Interaction):
        await ctx.response.defer()

        inviteDocument = await self.client.userInviteDocument(ctx.user)

        self.invites[ctx.guild.id] = await ctx.guild.invites()

        rolesDict = {roleId: 0 for _, roleId in config.levelsToCheckInvite.items()}

        for userId in inviteDocument['invitedUsers']:
            userDoc = await self.client.userDocument(userId=userId)
            userLevel, _ = self.client.calculate_level(userDoc['exp'])
            for key in config.levelsToCheckInvite:
                if userLevel >= key:
                    rolesDict[config.levelsToCheckInvite[key]] += 1

        text = ""
        for key, val in rolesDict.items():
            text += f"{'<@&' + key + '>' if ctx.guild.get_role(key) else '**Level ' + str({v: k for k, v in config.levelsToCheckInvite.items()}[key]) + '**'}: {val}\n"

        description = (f"**Total Invites:** {len(inviteDocument['invitedUsers'])}\n**Your Invite Link:** {inviteDocument['inviteLink']}\n"
                       f"**Invitees:** {' '.join([f'<@{i}>' for i in inviteDocument['invitedUsers']]) if inviteDocument['invitedUsers'] else 'None'}\n**Levels Reached:  **\n{text}")

        inviteEmbed = discord.Embed(title="Invite Tracker", description=description)

        await ctx.followup.send(embed=inviteEmbed)


    @app_commands.command(name="invites-leaderboard", description="View the top 10 inviters.")
    async def invites_leaderboard(self, ctx: Interaction, places: int = 10, target_user: discord.Member = None):

        if target_user:
            user = target_user
        else:
            user = ctx.user

        if places > 21:
            return await ctx.response.send_message("The leaderboard can only show up to 21 people.", ephemeral=True)

        if places < 3:
            return await ctx.response.send_message("The leaderboard needs to show at least 3 people.", ephemeral=True)

        await ctx.response.defer()

        collection = self.client.inviteCollection
        users_data = await collection.find().to_list(length=None)

        lb_data = sorted(users_data, key=lambda x: len(x["invitedUsers"]), reverse=True)

        leaderboard_embed = discord.Embed(
            title="Leveling Leaderboard",
            description=f"The top {places} inviters in {ctx.guild.name}!",
            color=discord.Colour.gold()
        )

        index = next((i for i, user_data in enumerate(lb_data) if user_data["_id"] == user.id), -1)

        for i in range(places):
            try:
                user_id = lb_data[i]["_id"]
                invitedUsers = len(lb_data[i]["invitedUsers"])
                leaderboard_embed.add_field(
                    name=f"{i + 1}. {invitedUsers} Invites",
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
                    invitedUsers = lb_data[index - i]["invitedUsers"]
                    leaderboard_embed.add_field(
                        name=f"{index - i + 1}. {invitedUsers} Invites",
                        value=f"<@{user_id}>      <<<<" if i == 0 else f"<@{user_id}>",
                        inline=False
                    )
                except IndexError:
                    leaderboard_embed.add_field(name=f"**<< {index - i + 1} >>**", value="N/A | NaN", inline=False)

        await ctx.followup.send(embed=leaderboard_embed)


async def setup(client):
    await client.add_cog(InvitesCog(client))

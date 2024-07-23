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
            print(member.name, inviteUrl)
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


async def setup(client):
    await client.add_cog(InvitesCog(client))

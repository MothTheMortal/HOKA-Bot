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


        # bot = 0
        # rolesDict = {ctx.guild.get_role(roleId): 0 for roleId in config.roleIdsToCheckInvites}
        #
        # users = []
        # for userId in inviteDocument['invitedUsers']:
        #     user = await ctx.guild.fetch_member(userId)
        #
        #     if user.bot:
        #         bot += 1
        #         continue
        #
        #     for role in roleDict.keys():
        #         if role in user.roles:
        #             rolesDict[role] += 1
        #     users.append(user)

        description = (f"**Total Invites:** {len(inviteDocument['invitedUsers'])}\n**Your Invite Link:** {inviteDocument['inviteLink']}\n"
                       f"**Invitees:** {' '.join([f'<@{i}>' for i in inviteDocument['invitedUsers']]) if inviteDocument['invitedUsers'] else 'None'}")

        inviteEmbed = discord.Embed(title="Invite Tracker", description=description)

        await ctx.followup.send(embed=inviteEmbed)


async def setup(client):
    await client.add_cog(InvitesCog(client))

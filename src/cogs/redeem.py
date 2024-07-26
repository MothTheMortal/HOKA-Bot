from discord.ext import commands
from discord import app_commands, Interaction
from discord.app_commands import Choice
import discord
import config
import random


class RedeemCog(commands.Cog):
    def __init__(self, client):
        self.client = client


    @app_commands.command(name="create-code", description="Create a redeem code")
    @app_commands.choices(
        action=[
            Choice(name="Give Role", value="role"),
            Choice(name="Give EXP", value="xp"),
            Choice(name="Create a Channel", value="ticket")
        ]
    )
    async def create_code(self, ctx: Interaction, action: Choice[str], uses: int, role: discord.Role = None, exp: int = None, channel_title: str = ""):
        if not self.client.isStaff(ctx.user) and ctx.user.id != self.client.owner_id:
            return await self.client.userNotStaffError(ctx)

        await ctx.response.defer()

        if sum(bool(value) for value in [role, exp, channel_title]) != 1:
            return await ctx.followup.send("You must provide exactly one of the following: roleGiven, expGiven, or ticket.", ephemeral=True)
        if action.value == "xp" and exp is None:
            return await ctx.followup.send("You must provide an exp value when choosing the 'xp' action.", ephemeral=True)
        elif action.value == "role" and role is None:
            return await ctx.followup.send("You must provide a role when choosing the 'role' action.", ephemeral=True)
        elif action.value == "ticket" and channel_title is False:
            return await ctx.followup.send("You must provide a channel Title when choosing the 'ticket' action.", ephemeral=True)

        if uses < 1:
            return await ctx.followup.send("You must provide a valid number of uses.", ephemeral=True)

        code = await self.client.generate_code()

        logMsg = ""
        if action.value == "role":
            data = [role.id]
            logMsg = f"**Role:** {role.mention}"
        elif action.value == "xp":
            data = exp
            logMsg = f"**Exp:** +{exp}"
        else:
            data = channel_title
            logMsg = f"**Ticket:** {channel_title}"

        await ctx.followup.send(f"**Created Redeem Code:**\n**Code:** {code}\n**Action:** {action.name}", ephemeral=True)

        await self.client.createRedeemDocument(code, action.value, uses, ctx.user, data)

        logChannel = await ctx.guild.fetch_channel(config.REDEEM_LOG_CHANNEL_ID)
        embed = discord.Embed(title=f"{ctx.user.name} created a code", description=f"**Code:** {code}\n**Action:** {action.name}\n{logMsg}", color=discord.Colour.blurple())
        await logChannel.send(embed=embed)


    @app_commands.command(name="delete-code", description="Delete a redeem code")
    async def delete_code(self, ctx: Interaction, code: str):

        if not self.client.isStaff(ctx.user) and ctx.user.id != self.client.owner_id:
            return await self.client.userNotStaffError(ctx)

        x = await self.client.redeemCollection.delete_one({"_id": code})
        if x.deleted_count == 1:
            await ctx.response.send_message(f"**Deleted Redeem Code:** {code}", ephemeral=True)
        else:
            await ctx.response.send_message("Redeem Code not found.", ephemeral=True)

        logChannel = await ctx.guild.fetch_channel(config.REDEEM_LOG_CHANNEL_ID)
        embed = discord.Embed(title=f"{ctx.user.name} deleted a code", description=f"**Code:** {code}", color=discord.Colour.dark_red())
        await logChannel.send(embed=embed)


    @app_commands.command(name="redeem", description="Redeem a code")
    async def redeem(self, ctx: Interaction, code: str):

        redeemDocument = await self.client.redeemCollection.find_one({"_id": code})

        if not redeemDocument:
            return await ctx.response.send_message("Redeem Code not found.", ephemeral=True)

        if ctx.user.id in redeemDocument['claimedUsers']:
            return await ctx.response.send_message("You have already claimed this code.", ephemeral=True)

        if redeemDocument['uses'] < 1:
            return await ctx.response.send_message("Redeem Code has expired.", ephemeral=True)


        logMsg = ""

        if redeemDocument["actionType"] == "role":
            await ctx.response.send_message(f"You have redeemed:\nRole: <@&{redeemDocument['data'][0]}>", ephemeral=True)
            await ctx.user.add_roles(ctx.guild.get_role(redeemDocument["data"][0]))

            logMsg = f"**Role:** <@&{redeemDocument['data'][0]}>"

        elif redeemDocument["actionType"] == "xp":
            await ctx.response.send_message(f"You have redeemed:\nEXP: +{redeemDocument['data']}", ephemeral=True)
            logMsg = f"**Exp:** +{redeemDocument['data']}"

            user_doc = await self.client.userDocument(ctx.user)

            await self.client.usersCollection.update_one({"_id": ctx.user.id}, {"$inc": {"exp": int(redeemDocument['data'])}})

            old_level, _ = self.client.calculate_level(user_doc["exp"])
            new_level, _ = self.client.calculate_level(user_doc["exp"] + int(redeemDocument['data']))

            if new_level > old_level:
                await self.client.levelUpHandler(ctx.user, old_level, new_level, ctx.channel)


        elif redeemDocument["actionType"] == "ticket":
            await ctx.response.send_message(f"You have redeemed a ticket!.", ephemeral=True)
            logMsg = f"**Ticket:** {redeemDocument['data']}"

            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False, view_channel=False),
                ctx.user: discord.PermissionOverwrite(read_messages=True, view_channel=True)
            }
            for roleId in config.STAFF_ROLE_IDS:
                role = ctx.guild.get_role(roleId)
                if role:
                    overwrites[role] = discord.PermissionOverwrite(read_messages=True, view_channel=True)

            ticketCategory = await ctx.guild.fetch_channel(config.TICKET_CATEGORY_ID)
            await ticketCategory.create_text_channel(name=f"{ctx.user.name}{random.randint(100000, 999999)}", topic=redeemDocument['data'], overwrites=overwrites)

        await self.client.redeemCollection.update_one({"_id": code}, {"$inc": {"uses": -1}})
        await self.client.redeemCollection.update_one({"_id": code}, {"$push": {"claimedUsers": ctx.user.id}})

        logChannel = await ctx.guild.fetch_channel(config.REDEEM_LOG_CHANNEL_ID)
        embed = discord.Embed(title=f"{ctx.user.name} redeemed a code", description=f"**Code:** {code}\n**Action:** {redeemDocument['actionType']}\n{logMsg}", color=discord.Colour.green())
        await logChannel.send(embed=embed)


    @app_commands.command(name="view-codes", description="View all redeem codes")
    async def view_codes(self, ctx: Interaction):

        if not self.client.isStaff(ctx.user) and ctx.user.id != self.client.owner_id:
            return await self.client.userNotStaffError(ctx)

        codes_cursor = self.client.redeemCollection.find({"uses": {"$gt": 0}})
        codes = await codes_cursor.to_list(length=None)

        if not codes:
            return await ctx.response.send_message("No codes found.", ephemeral=True)

        text = ""
        for doc in codes:
            text += f"**Code:** {doc['_id']}\n**Action:** {doc['actionType']}\n**Uses:** {doc['uses']}\n\n"
        await ctx.response.send_message(text, ephemeral=True)


async def setup(client):
    await client.add_cog(RedeemCog(client))

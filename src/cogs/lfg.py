from discord.ext import commands, tasks
import discord
from discord import app_commands, Interaction, Embed, Button, ui
import config
import asyncio
from datetime import datetime, timedelta
import time
import logging

logging.basicConfig(level=logging.INFO)


class LFGCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.active_lfg = []
        self.post_vc = []
        self.post: discord.Message = None
        self.party_locks = {}

    @commands.Cog.listener()
    async def on_ready(self):
        self.refreshLFG.start()
        self.voiceHandler.start()

        channel: discord.TextChannel = self.client.get_channel(config.LFG_POST_CHANNEL_ID)
        last50Msg = channel.history(limit=50)
        async for msg in last50Msg:
            if msg.embeds:
                if "HOKA LFG" in msg.embeds[0].title:
                    await msg.delete()

        self.post = await self.lfg_post()
        self.stickyPost.start()

    @tasks.loop(seconds=60)
    async def refreshLFG(self):
        current_time = datetime.now()
        inactive_lfg = []

        for entry in self.active_lfg:
            party_msg, voice_channel, party_leader, last_interaction_time, _ = entry

            # Check for inactivity (30 minutes)
            if current_time - last_interaction_time > timedelta(seconds=config.PARTY_INVALIDITY_LIMIT):
                inactive_lfg.append(entry)
                continue

            try:
                await party_msg.edit(attachments=[])
            except Exception as e:
                print(e)

        # Handle inactive LFGs
        for entry in inactive_lfg:
            party_msg, voice_channel, party_leader, _, _ = entry
            party_leader: discord.Member
            await party_msg.delete()
            if voice_channel:
                await voice_channel.delete()
            try:
                await party_leader.send("Your LFG party has been deleted due to 30 minutes of inactivity.")
            except Exception as e:
                print("Invalidity Notice Error", e)
            self.active_lfg.remove(entry)

    @tasks.loop(seconds=60)
    async def voiceHandler(self):
        current_time = datetime.now()
        inactive_vcs = []

        for vc, last_active_time in self.post_vc:
            if len(vc.members) == 0 and (current_time - last_active_time).total_seconds() > config.VC_INVALIDITY_LIMIT:  # 30 minutes
                inactive_vcs.append((vc, last_active_time))

        for vc, _ in inactive_vcs:
            try:
                await vc.delete()
            except Exception as e:
                logging.error(f"Error deleting voice channel {vc.id}: {e}")
            self.post_vc.remove((vc, _))

    @tasks.loop(seconds=10)
    async def stickyPost(self):
        channel: discord.TextChannel = self.client.get_channel(config.LFG_POST_CHANNEL_ID)
        last5Msg = channel.history(limit=5)
        sticky = False
        async for msg in last5Msg:
            if msg == self.post:
                sticky = True

        if not sticky:
            await self.post.delete()
            self.post = await self.lfg_post()

    async def lfg_post(self) -> discord.Message:
        startEmbed = Embed(title="HOKA LFG", description="Create a LFG")
        startEmbed.set_thumbnail(url=config.THUMBNAIL_URL)

        firstView = ui.View(timeout=None)
        button = ui.Button(label="Create Group", style=discord.ButtonStyle.green, emoji="<:add:1257611423358652439>")

        async def buttonCallBack(ctx: Interaction):

            for party in self.active_lfg:
                if ctx.user in party:
                    return await ctx.response.send_message(f"You already have an active party: {party[0].jump_url}", ephemeral=True)

            return await self.lfg(ctx)

        button.callback = buttonCallBack

        firstView.add_item(button)

        channel = self.client.get_channel(config.LFG_POST_CHANNEL_ID)
        message = await channel.send(embed=startEmbed, view=firstView)
        return message

    async def lfg(self, ctx: Interaction):
        view = ui.View(timeout=None)
        dropdown = ui.Select(placeholder="Select rank(s)", options=[discord.SelectOption(label=key, value=key, emoji=value) for key, value in config.HOK_RANKS.items()], max_values=3)

        async def dropDownCallback(ctx: Interaction):
            if not dropdown.values:
                return await ctx.response.send_message("Please select a rank", ephemeral=True)

            hasRank = False

            for rankNames in dropdown.values:
                roleId = config.HOK_RANKS_ROLE_IDS[rankNames]
                role = ctx.guild.get_role(roleId)

                if role in ctx.user.roles:
                    hasRank = True
                    break

            if not hasRank:
                return await ctx.response.send_message("You don't have the required rank. Please select them in Channels & Roles", ephemeral=True)

            ranks = dropdown.values
            modal = ui.Modal(title="Lobby Details", timeout=None)
            lobbyTextInput = ui.TextInput(label="Enter a message for your LFG", placeholder="Example: mic only", style=discord.TextStyle.short, required=False)
            lobbyCodeInput = ui.TextInput(label="Enter lobby code", placeholder="Example: 42341", style=discord.TextStyle.short, required=False)

            async def modalCallback(ctx: Interaction):
                if not lobbyCodeInput.value.isdigit() and lobbyCodeInput.value != '':
                    return await ctx.response.send_message("Please enter a valid lobby code", ephemeral=True)

                view = ui.View(timeout=None)
                dropdown2 = ui.Select(placeholder="Select Party Size", options=[discord.SelectOption(label=key, value=val) for key, val in config.TEAM_SIZES.items()])

                async def dropDownCallback(ctx: Interaction):
                    if not dropdown2.values:
                        return await ctx.response.send_message("Please select a size", ephemeral=True)

                    size = str(int(float(dropdown2.values[0])))

                    view = ui.View(timeout=None)

                    roleSet = []

                    dropdown = ui.Select(placeholder="Select your role", max_values=1, min_values=1, options=[discord.SelectOption(label=key, value=key) for key in config.HOK_ROLES])

                    async def callback(ctx: Interaction):
                        userRole = dropdown.values[0]
                        return await self.partyHandler(ctx, size, ranks, lobbyTextInput.value, lobbyCodeInput.value, userRole)

                    dropdown.callback = callback
                    view.add_item(dropdown)

                    return await ctx.response.send_message(view=view, ephemeral=True)

                dropdown2.callback = dropDownCallback

                view.add_item(dropdown2)

                await ctx.response.send_message(view=view, ephemeral=True)

            async def modalError(ctx: Interaction, *e):
                return await ctx.response.send_message("Error Occurred", ephemeral=True)

            modal.add_item(lobbyTextInput)
            modal.add_item(lobbyCodeInput)
            modal.on_submit = modalCallback
            modal.on_timeout = modalError
            modal.on_error = modalError
            await ctx.response.send_modal(modal)

        dropdown.callback = dropDownCallback
        view.add_item(dropdown)

        await ctx.response.send_message(view=view, ephemeral=True)

    async def partyHandler(self, ctx: Interaction, size, ranks, message, code, userRole):
        await ctx.response.send_message("Creating party... :timer:", ephemeral=True)
        messageContent = " ".join(["<@&" + config.HOK_RANKS_ROLE_IDS[rank] + ">" for rank in ranks])

        if message:
            message += "\n"

        imgHistory = []
        partyLeader = ctx.user
        users = [partyLeader]
        userRoles = {
            ctx.user: userRole
        }
        voiceChannel = None  # Local variable initialization

        party_id = f"{partyLeader.id}-{int(ctx.created_at.timestamp())}"
        self.party_locks[party_id] = asyncio.Lock()
        last_interaction_time = datetime.now()  # Initialize last interaction time

        description = f""
        for user in users:
            description += config.HOK_RANKS["Master"] + user.mention + f"** - {userRoles[user]}**\n"

        partyEmbed = Embed(title=f"(1/{size})", description=description)
        partyEmbed.set_author(name=partyLeader.name, icon_url=partyLeader.avatar.url if partyLeader.avatar else partyLeader.default_avatar)

        start_time = time.time()
        imgUrl = await self.client.drawRoles(partyLeader, userRole)
        logging.info(f"Image URL generated in {time.time() - start_time:.4f} seconds")

        imgHistory.append(imgUrl)
        partyEmbed.set_image(url=imgUrl)
        view = ui.View(timeout=None)
        joinButton = ui.Button(label="Join", style=discord.ButtonStyle.green)
        leaveButton = ui.Button(label="Leave", style=discord.ButtonStyle.red)
        startButton = ui.Button(label="Start", style=discord.ButtonStyle.blurple)
        vcButton = ui.Button(label="Create VC", style=discord.ButtonStyle.grey)

        async def refreshEmbed(picUrl=None):
            nonlocal last_interaction_time
            last_interaction_time = datetime.now()  # Update last interaction time
            if "Group" in partyEmbed.title:
                return
            description = f""
            for user in users:
                description += config.HOK_RANKS["Master"] + user.mention + f"** - {userRoles[user]}**\n"

            if picUrl:
                img = await self.client.drawRoles(users[-1], userRoles[users[-1]], bannerUrl=imgHistory[-1])
                imgHistory.append(img)
                partyEmbed.set_image(url=img)
            else:
                imgHistory.pop()
                img = imgHistory[-1]
                partyEmbed.set_image(url=img)

            partyEmbed.description = description
            partyEmbed.title = f"({len(users)}/{size})"
            await partyMessage.edit(embed=partyEmbed)

        async def startCallback(ctx: Interaction):
            nonlocal last_interaction_time
            last_interaction_time = datetime.now()  # Update last interaction time
            async with self.party_locks[party_id]:  # Acquire the lock for this party
                if ctx.user == partyLeader:
                    for x in self.active_lfg:
                        if partyMessage in x:
                            self.active_lfg.remove(x)
                            break
                    partyEmbed.title = f"**Group Started** ({len(users)}/{size})"

                    if voiceChannel:
                        self.post_vc.append((voiceChannel, datetime.now()))

                    return await ctx.response.edit_message(view=None, embed=partyEmbed)
                return await ctx.response.edit_message(attachments=[])

        async def leaveCallback(ctx: Interaction):
            nonlocal last_interaction_time
            last_interaction_time = datetime.now()  # Update last interaction time
            async with self.party_locks[party_id]:  # Acquire the lock for this party
                if ctx.user not in users:
                    return await ctx.response.edit_message(attachments=[])
                if ctx.user == partyLeader:
                    await ctx.response.edit_message(attachments=[])
                    for party in self.active_lfg:
                        if partyMessage in party:
                            self.active_lfg.remove(party)
                            break

                    if voiceChannel:
                        await voiceChannel.delete()

                    return await partyMessage.delete()



                if voiceChannel:
                    overwrites = voiceChannel.overwrites
                    try:
                        overwrites.pop(ctx.user)
                    except Exception as e:
                        print("Overwriting Leaving Party Member Error", e)

                    await voiceChannel.edit(overwrites=overwrites)

                users.remove(ctx.user)

                await ctx.response.edit_message(attachments=[])
                await refreshEmbed()

        async def joinCallback(ctx: Interaction):
            nonlocal last_interaction_time
            last_interaction_time = datetime.now()  # Update last interaction time
            async with self.party_locks[party_id]:  # Acquire the lock for this party
                if ctx.user in users or not len(users) < int(size):
                    return await ctx.response.edit_message(attachments=[])

                for party in self.active_lfg:
                    if ctx.user in party[4]:
                        return await ctx.response.send_message("You are already in an active party.", ephemeral=True)


                eligible = False
                for rank in ranks:
                    rankRole = ctx.guild.get_role(int(config.HOK_RANKS_ROLE_IDS[rank]))
                    if rankRole in ctx.user.roles:
                        eligible = True
                        break

                if not eligible:
                    return await ctx.response.send_message("You do not have the required rank role to join this party. Please select them in Channels & Roles", ephemeral=True)

                roleDropdown = ui.Select(placeholder="Select Role", options=[discord.SelectOption(label=key, value=key) for key in config.HOK_ROLES])

                async def roleCallback(ctx: Interaction):
                    nonlocal last_interaction_time
                    last_interaction_time = datetime.now()  # Update last interaction time
                    async with self.party_locks[party_id]:  # Acquire the lock for this party
                        roleSelected = roleDropdown.values[0]
                        if roleSelected in userRoles.values():
                            return await ctx.response.send_message("This role has already been selected.", ephemeral=True)

                        if not len(users) < int(size):
                            return await ctx.response.send_message("The party is already full", ephemeral=True)

                        if voiceChannel:
                            overwrites = voiceChannel.overwrites
                            overwrites[ctx.user] = discord.PermissionOverwrite(connect=True, view_channel=True)
                            await voiceChannel.edit(overwrites=overwrites)

                        await ctx.response.send_message(f"**Party code: {code if code else f'Contact {partyLeader.mention}'}**\n{'**VC:** ' + voiceChannel.mention if voiceChannel else ''}",
                                                        ephemeral=True)

                        users.append(ctx.user)
                        userRoles[ctx.user] = roleSelected
                        await refreshEmbed(picUrl=True)

                roleDropdown.callback = roleCallback

                view = ui.View(timeout=None)
                view.add_item(roleDropdown)

                await ctx.response.send_message(view=view, ephemeral=True)

        async def createVcCallback(ctx: Interaction):
            nonlocal voiceChannel, last_interaction_time
            last_interaction_time = datetime.now()  # Update last interaction time
            async with self.party_locks[party_id]:  # Acquire the lock for this party
                if ctx.user != partyLeader:
                    return await ctx.response.edit_message(attachments=[])

                if voiceChannel:  # Check if voiceChannel is already set
                    return await ctx.response.edit_message(attachments=[])

                category = await ctx.guild.fetch_channel(config.PARTY_VC_CATEGORY_ID)

                overwrites = {
                    ctx.guild.default_role: discord.PermissionOverwrite(connect=False, view_channel=False),
                }

                for user in users:
                    overwrites[user] = discord.PermissionOverwrite(connect=True, view_channel=True)

                voiceChannel = await category.create_voice_channel(name=f"{partyLeader.name}'s Party VC", user_limit=int(size), overwrites=overwrites)

                for user in users:
                    if user != partyLeader:
                        await user.send(content=f"A voice channel has been created for your party: {voiceChannel.mention}")

                await ctx.response.send_message(f"Voice Channel has been created: {voiceChannel.mention}", ephemeral=True)

        joinButton.callback = joinCallback
        leaveButton.callback = leaveCallback
        startButton.callback = startCallback
        vcButton.callback = createVcCallback

        view.add_item(joinButton)
        view.add_item(leaveButton)
        view.add_item(startButton)
        view.add_item(vcButton)

        lfgChannel: discord.TextChannel = ctx.guild.get_channel(config.LFG_MSG_CHANNEL_ID)
        partyMessage = await lfgChannel.send(content=f"**{message}{messageContent}**", embed=partyEmbed, view=view)
        self.active_lfg.append((partyMessage, voiceChannel, partyLeader, last_interaction_time, users))  # Store the party message, voice channel, party leader, last interaction time and users
        await ctx.edit_original_response(content=F"**LFG Created** {partyMessage.jump_url}", view=None)


async def setup(client):
    await client.add_cog(LFGCog(client))

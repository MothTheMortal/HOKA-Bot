from discord.ext import commands, tasks
import discord
from discord import app_commands, Interaction, Embed, Button, ui
import config


class LFGCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.active_lfg = []
        self.post: discord.Message = None

    @commands.Cog.listener()
    async def on_ready(self):
        self.refreshLFG.start()

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
        for msg in self.active_lfg:
            try:
                await msg.edit(attachments=[])
            except Exception as e:
                print(e)
        # print(f"Refreshed {len(self.active_lfg)} LFG Messages.")

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




        # if not sticky:
        #     await stickyMsg.delete()
        #     stickyMsg = await self.lfg_post()


    async def lfg_post(self) -> discord.Message:
        startEmbed = Embed(title="HOKA LFG", description="Create a LFG")
        startEmbed.set_thumbnail(url=config.THUMBNAIL_URL)


        firstView = ui.View(timeout=None)
        button = ui.Button(label="Create Group", style=discord.ButtonStyle.green, emoji="<:add:1257611423358652439>")
        notificationButton = ui.Button(label="Toggle", style=discord.ButtonStyle.blurple, emoji="🔔")

        async def notificationCallback(ctx: Interaction):
            if not self.client.hasHOKRank(ctx.user, ctx.user.roles):
                return await ctx.response.send_message("Please assign yourself a HOK rank first.", ephemeral=True)
            await ctx.response.send_message("Enabled Notifications!", ephemeral=True)

        async def buttonCallBack(ctx: Interaction):
            return await self.lfg(ctx)

        button.callback = buttonCallBack
        notificationButton.callback = notificationCallback

        firstView.add_item(button)
        firstView.add_item(notificationButton)

        channel = self.client.get_channel(config.LFG_POST_CHANNEL_ID)
        message = await channel.send(embed=startEmbed, view=firstView)
        return message
        # await ctx.response.send_message(embed=startEmbed, view=firstView)

    async def lfg(self, ctx: Interaction):
        view = ui.View(timeout=None)
        dropdown = ui.Select(placeholder="Select rank(s)", options=[discord.SelectOption(label=key, value=key, emoji=value) for key, value in config.HOK_RANKS.items()], max_values=2)

        async def dropDownCallback(ctx: Interaction):
            if not dropdown.values:
                return await ctx.response.send_message("Please select a rank", ephemeral=True)
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

                    dropdown = ui.Select(placeholder="Select role", max_values=1, min_values=1, options=[discord.SelectOption(label=key, value=key) for key in config.HOK_ROLES])

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
        await ctx.response.defer()
        messageContent = " ".join(["<@&" + config.HOK_RANKS_ROLE_IDS[rank] + ">" for rank in ranks])
        imgHistory = []
        partyLeader = ctx.user
        users = [partyLeader]
        userRoles = {
            ctx.user: userRole
        }

        description = f""
        for user in users:
            description += config.HOK_RANKS["Master"] + user.mention + f"** - {userRoles[user]}**\n"

        partyEmbed = Embed(title=f"(1/{size})", description=description)
        partyEmbed.set_author(name=partyLeader.name, icon_url=partyLeader.avatar.url if partyLeader.avatar else partyLeader.default_avatar)

        imgUrl = await self.client.drawRoles(partyLeader, userRole)
        imgHistory.append(imgUrl)
        partyEmbed.set_image(url=imgUrl)
        view = ui.View(timeout=None)
        joinButton = ui.Button(label="Join", style=discord.ButtonStyle.green)
        leaveButton = ui.Button(label="Leave", style=discord.ButtonStyle.red)
        startButton = ui.Button(label="Start", style=discord.ButtonStyle.blurple)

        async def refreshEmbed(picUrl=None):
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
            if ctx.user == partyLeader:
                self.active_lfg.remove(partyMessage)
                partyEmbed.title = f"**Group Started** ({len(users)}/{size})"
                return await ctx.response.edit_message(view=None, embed=partyEmbed)
            return await ctx.response.edit_message(attachments=[])

        async def leaveCallback(ctx: Interaction):
            if ctx.user not in users:
                return await ctx.response.edit_message(attachments=[])
            if ctx.user == partyLeader:
                self.active_lfg.remove(partyMessage)
                return await partyMessage.delete()
            users.remove(ctx.user)

            await ctx.response.edit_message(attachments=[])
            await refreshEmbed()

        async def joinCallback(ctx: Interaction):

            if ctx.user in users or not len(users) < int(size):
                return await ctx.response.edit_message(attachments=[])

            roleDropdown = ui.Select(placeholder="Select Role", options=[discord.SelectOption(label=key, value=key) for key in config.HOK_ROLES])

            async def roleCallback(ctx: Interaction):
                roleSelected = roleDropdown.values[0]
                if roleSelected in userRoles.values():
                    return await ctx.response.send_message("This role has already been selected.", ephemeral=True)

                if not len(users) < int(size):
                    return await ctx.response.send_message("The party is already full", ephemeral=True)


                await ctx.response.send_message(f"The party code is **{code}**" if code else f"You have joined the Group, Contact {partyLeader.mention} for the party code", ephemeral=True)
                users.append(ctx.user)
                userRoles[ctx.user] = roleSelected
                await refreshEmbed(picUrl=True)

            roleDropdown.callback = roleCallback

            view = ui.View(timeout=None)
            view.add_item(roleDropdown)

            await ctx.response.send_message(view=view, ephemeral=True)

        joinButton.callback = joinCallback
        leaveButton.callback = leaveCallback
        startButton.callback = startCallback

        view.add_item(joinButton)
        view.add_item(leaveButton)
        view.add_item(startButton)

        lfgChannel: discord.TextChannel = ctx.guild.get_channel(config.LFG_MSG_CHANNEL_ID)
        partyMessage = await lfgChannel.send(content=f"**{message}**" if message else "" + "\n" + messageContent, embed=partyEmbed, view=view)
        await ctx.edit_original_response(content=F"**LFG Created** {partyMessage.jump_url}", view=None)
        self.active_lfg.append(partyMessage)



async def setup(client):
    await client.add_cog(LFGCog(client))

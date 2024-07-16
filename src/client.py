from discord.ext import commands
import discord
import mongoengine
import config
from typing import List, Dict
from PIL import Image, ImageDraw
import io
import requests
import motor.motor_asyncio


class HOKABot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.databaseClient = client = motor.motor_asyncio.AsyncIOMotorClient(kwargs['mongodb_uri'])
        self.database = self.databaseClient["HOKA"]
        self.usersCollection = self.database["users"]
        self.inviteCollection = self.database["invites"]

    async def on_ready(self):
        print(f"Logged in as {self.user}")

    async def setup_hook(self):
        for cog in config.cogs:
            await self.load_extension(f"cogs.{cog}")

    async def userInviteDocument(self, user: discord.User) -> Dict:
        userDoc = await self.inviteCollection.find_one({"_id": user.id})

        if not userDoc:
            inviteChannel = await self.fetch_channel(config.INVITE_LINK_CHANNEL_ID)
            invite = await inviteChannel.create_invite(reason=f"{user.name}'s Unique Invite Link")

            data = {
                "_id": user.id,
                "inviteLink": invite.url,
                "invitedUsers": []
            }
            await self.inviteCollection.insert_one(data)
            userDoc = data

        return userDoc


    # async def userDocument(self, user: discord.User) -> dict:


    async def uploadFile(self, data) -> str:
        storageChannel = self.get_channel(config.STORAGE_ID)
        message = await storageChannel.send(file=discord.File(fp=data, filename="role_positioning.png"))

        return message.attachments[0].url

    async def drawRoles(self, user: discord.Member, role, bannerUrl: str = "https://cdn.discordapp.com/attachments/1255756712925859940/1258336558709473300/1040x460.png?ex=6687acbe&is=66865b3e&hm=8c67df8f151d3d727fc33ea6db588e6b60fc27cbc83800eb6348797bd2db4e80&") -> None:
        banner_response = requests.get(bannerUrl)
        banner_response.raise_for_status()
        banner = Image.open(io.BytesIO(banner_response.content))

        if user.avatar:
            pfpUrl = user.avatar.url
        else:
            pfpUrl = user.default_avatar

        pfp_response = requests.get(pfpUrl)
        pfp_response.raise_for_status()

        pfp = Image.open(io.BytesIO(pfp_response.content))

        pfp = pfp.resize((90, 90))

        mask = Image.new('L', pfp.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + pfp.size, fill=255)
        pfp.putalpha(mask)

        icon_x, icon_y = config.COORDS[role]


        paste_location = (icon_x - pfp.width // 2, icon_y - pfp.height // 2)
        if pfp.mode in ('RGBA', 'LA') or (pfp.mode == 'P' and 'transparency' in pfp.info):
            banner.paste(pfp, paste_location, pfp)
        else:
            banner.paste(pfp, paste_location)

        bannerData = io.BytesIO()
        banner.save(bannerData, format="PNG")
        bannerData.seek(0)
        return await self.uploadFile(bannerData)



    @staticmethod
    def hasHOKRank(user: discord.User, roles: List[discord.Role]) -> bool:

        for role in roles:
            if role.name.title() in config.HOK_RANKS.keys():
                return True
        return False

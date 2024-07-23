from discord.ext import commands
import discord
import config
from typing import List, Dict
from PIL import Image, ImageDraw
import io
import requests
import motor.motor_asyncio
import string
import random


class HOKABot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.databaseClient = client = motor.motor_asyncio.AsyncIOMotorClient(kwargs['mongodb_uri'])
        self.database = self.databaseClient["HOKA"]
        self.usersCollection = self.database["users"]
        self.inviteCollection = self.database["invites"]
        self.redeemCollection = self.database["redeems"]
        self.redeemCollection.find()

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

    async def createRedeemDocument(self, code: str, action_type: str, uses: int, created_by: discord.User, data) -> Dict:
        doc = {
            "_id": code,
            "actionType": action_type,
            "createdBy": created_by.id,
            "data": data,
            "claimedUsers": [],
            "uses": uses
        }

        await self.redeemCollection.insert_one(doc)

    async def userDocument(self, user: discord.User=None, userId=None) -> Dict:
        if userId:
            user = userId
        else:
            user = user.id

        userDoc = await self.usersCollection.find_one({"_id": user})

        if userDoc:
            return userDoc

        doc = {
            "_id": user,
            "exp": 0,
        }
        await self.usersCollection.insert_one(doc)

        return doc

    async def uploadFile(self, data) -> str:
        storageChannel = self.get_channel(config.STORAGE_ID)
        message = await storageChannel.send(file=discord.File(fp=data, filename="role_positioning.png"))

        return message.attachments[0].url

    async def drawRoles(self, user: discord.Member, role, bannerUrl: str = config.TEAM_URL) -> None:
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

    async def generate_code(self, length=12) -> str:
        characters = string.ascii_letters + string.digits
        code = ''.join(random.choice(characters) for _ in range(length))
        while await self.redeemCollection.find_one({"_id": code}):
            code = ''.join(random.choice(characters) for _ in range(length))
        return code

    @staticmethod
    async def levelUpHandler(user: discord.Member, oldLevel, newLevel, channel):
        if config.ASSIGN_ROLE_ON_LEVEL_UP.get(newLevel):
            role = user.guild.get_role(config.ASSIGN_ROLE_ON_LEVEL_UP.get(newLevel))
            await user.add_roles(role)

        await channel.send(config.LEVEL_UP_MSG.format(
                user=user.mention,
                newLevel=newLevel,
                oldLevel=oldLevel)
        )

    @staticmethod
    async def userNotStaffError(ctx: discord.Interaction):
        embed = discord.Embed(title="You don't have the necessary permissions", color=discord.Colour.dark_red())
        await ctx.response.send_message(embed=embed, ephemeral=True)

    @staticmethod
    def isStaff(user: discord.Member) -> bool:
        for role in user.roles:
            if role.id in config.STAFF_ROLE_IDS:
                return True
        return False

    @staticmethod
    def hasHOKRank(user: discord.User, roles: List[discord.Role]) -> bool:
        for role in roles:
            if role.name.title() in config.HOK_RANKS.keys():
                return True
        return False

    @staticmethod
    def calculate_level(exp: int) -> (int, float):
        level = 1
        for lvl, required_exp in config.expRequired.items():
            if exp >= required_exp:
                level = int(lvl)
            else:
                break

        if level == 50:
            return level, 100.0

        current_level_exp = config.expRequired[str(level)]
        next_level_exp = config.expRequired[str(level + 1)]

        progress = (exp - current_level_exp) / (next_level_exp - current_level_exp) * 100
        return level, progress

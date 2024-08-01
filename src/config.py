from PIL import Image, ImageDraw, ImageOps, ImageFont
import io

# Do not change
cogs = ["lfg", "invites", "redeem", "xp", "misc"]
HOK_ROLES = ["Clash Lane", "Farm Lane", "Mid Lane", "Jungler", "Roamer"]
THUMBNAIL_URL = "https://i.postimg.cc/VsSnmbYb/355880079-692682859537191-2670861757827348493-n.jpg"
TEAM_URL = "https://i.postimg.cc/WzBVv8QN/1035x460.png"
TEAM_SIZES = {"Duo": "2", "Trio": "3", "5-men": "5"}
COORDS = {
    'Roamer': (102, 178),
    'Jungler': (286, 322),
    'Mid Lane': (499, 175),
    'Farm Lane': (706, 321),
    'Clash Lane': (892, 178)
}
expRequired = {
    "1": 1,
    "2": 200,
    "3": 450,
    "4": 800,
    "5": 1250,
    "6": 1800,
    "7": 2450,
    "8": 3200,
    "9": 4050,
    "10": 5000,
    "11": 6050,
    "12": 7200,
    "13": 8450,
    "14": 9800,
    "15": 11250,
    "16": 12800,
    "17": 14450,
    "18": 16200,
    "19": 18050,
    "20": 20000,
    "21": 22050,
    "22": 24200,
    "23": 26450,
    "24": 28800,
    "25": 31250,
    "26": 33800,
    "27": 36450,
    "28": 39200,
    "29": 42050,
    "30": 45000,
    "31": 48050,
    "32": 51200,
    "33": 54450,
    "34": 57800,
    "35": 61250,
    "36": 64800,
    "37": 68450,
    "38": 72200,
    "39": 76050,
    "40": 80000,
    "41": 84050,
    "42": 88200,
    "43": 92450,
    "44": 96800,
    "45": 101250,
    "46": 105800,
    "47": 110450,
    "48": 115200,
    "49": 120050,
    "50": 125000,
    "51": 130050,
    "52": 135200,
    "53": 140450,
    "54": 145800,
    "55": 151250,
    "56": 156800,
    "57": 162450,
    "58": 168200,
    "59": 174050,
    "60": 180000,
    "61": 186050,
    "62": 192200,
    "63": 198450,
    "64": 204800,
    "65": 211250,
    "66": 217800,
    "67": 224450,
    "68": 231200,
    "69": 238050,
    "70": 245000,
    "71": 252050,
    "72": 259200,
    "73": 266450,
    "74": 273800,
    "75": 281250,
    "76": 288800,
    "77": 296450,
    "78": 304200,
    "79": 312050,
    "80": 320000,
    "81": 328050,
    "82": 336200,
    "83": 344450,
    "84": 352800,
    "85": 361250,
    "86": 369800,
    "87": 378450,
    "88": 387200,
    "89": 396050,
    "90": 405000,
    "91": 414050,
    "92": 423200,
    "93": 432450,
    "94": 441800,
    "95": 451250,
    "96": 460800,
    "97": 470450,
    "98": 480200,
    "99": 490050,
    "100": 500000,
}  # Exp required to reach each level
color_scheme = {  # Color Scheme for the level boxes
    1: "#2B4663",
    2: "#29445F",
    3: "#283D5A",
    4: "#3E4B75",
    5: "#485482",
    6: "#4F598A",
    7: "#535D90",
    8: "#62679F",
    9: "#6969A1",
    10: "#7469A1"
}

# Modify values below!

STAFF_ROLE_IDS = [1253221573465346100]
DATABASE_NAME = 'HOKA'

# LFG
HOK_RANKS = {"Bronze": "<:bronze:1255772551322402857>", "Silver": "<:rank_2_silver:1255773186667319347>", "Gold": "<:rank_3_gold:1255773184620363796>",
             "Platinum": "<:rank_4_platinum:1255773181696807004>", "Diamond": "<:rank_5_diamond:1255773180094844938>", "Master": "<:rank_6_master:1255773177531859006>",
             "Grandmaster": "<:rank_7_grandmaster:1255773175749283912>",
             "Mythic Grandmaster": "<:rank_7_grandmaster:1255773175749283912>",
             "Epic Grandmaster": "<:epicgrandmaster:1268462905511252068>",
             "Legend Grandmaster": "<:epicgrandmaster:1268462905511252068>",
             }

HOK_RANKS_ROLE_IDS = {  # Rank: Rank Role ID
    'Bronze': '1256128781266063452',
    'Silver': '1256128782759366770',
    'Gold': '1256128784093155369',
    'Platinum': '1256128785644916809',
    'Diamond': '1256128787221839944',
    'Master': '1256128788685656154',
    'Grandmaster': '1256128790132686858',
    'Mythic Grandmaster': '1256128790132686858',
    'Epic Grandmaster': '1256128790132686858',
    'Legend Grandmaster': '1256128790132686858',
}

PARTY_VC_CATEGORY_ID = 1266283672030416906
PARTY_INVALIDITY_LIMIT = 30 * 60  # Seconds
VC_INVALIDITY_LIMIT = 10 * 60  # Seconds

# URL for the thumbnail that will appear on the LFG Embed
DEV_GUILD_ID = 1248544817357787168
LFG_REMINDER_SECONDS = 60 * 5
LFG_POST_CHANNEL_ID = 1258347247117008947
LFG_MSG_CHANNEL_ID = 1266305363897094184
STORAGE_ID = 1257950603649486905


# Invites
INVITE_LINK_CHANNEL_ID = 1248544817806315585  # Channel ID where invited users will be first sent (like #annoucement or #general)
levelsToCheckInvite = {  # Levels that will be displayed on /invites
    # Level - level Role ID
    10: 1261984637375352000
}

# Redeem Codes
REDEEM_LOG_CHANNEL_ID = 1262646876038103182  # Channel ID where logs for redeem codes will be sent
TICKET_CATEGORY_ID = 1264083281369104414  # Category ID where ticket channels will be created

# EXP & Leveling
EXP_RATE = 9  # Exp per MSG
EXP_DELAY = 30  # How many seconds before letting user earn xp again
BANNED_EXP_CHANNEL_IDS = []  # Channels that will not give users EXP
EXP_MODIFIER_ROLE_IDS = {
    #  Role ID: Modifier
    # 1253221573465346100 : 1.5 -> Means that this role's user will get 1.5x the EXP
    1253221573465346100: 1.5
}
ASSIGN_ROLE_ON_LEVEL_UP = {
    #  Level - Role ID
    10: 1261984637375352872,
    5: 1268470471272431649,
    15: 1268470401730740277
}

LEVEL_UP_MSG = "Congratulations {user}, you have reached level **{newLevel}** from level **{oldLevel}**!"


def mainFont(size):
    return ImageFont.truetype("data/mainfont.otf", size)


def nameFont(size):
    return ImageFont.truetype("data/namefont.ttf", size)


def fontSizeFilter(text, size=35, max_length=486):
    # Load the font
    font = ImageFont.truetype("data/namefont.ttf", size)

    # Create a dummy image to get a drawing context
    dummy_image = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(dummy_image)

    # Calculate the size of the text
    text_width = draw.textlength(text, font=font)

    # Truncate the text if it exceeds the maximum length
    if text_width > max_length:
        truncated_text = ""
        for char in text:
            if draw.textlength(truncated_text + char, font=font) <= max_length:
                truncated_text += char
            else:
                break
        text = truncated_text

    return text


def rgb(hex_color):
    """Convert a hex color code to an RGB tuple."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    elif len(hex_color) == 3:
        return tuple(int(hex_color[i] * 2, 16) for i in range(3))
    else:
        raise ValueError("Invalid hex color code")


def add_outline(image, outline_width, color):
    # Ensure the image has an alpha channel
    image = image.convert("RGBA")

    if "#" in color:
        color = tuple(int(color[i:i + 2], 16) for i in (1, 3, 5)) + (255,)

    # Create a mask to create a circular outline
    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)
    width, height = image.size
    radius = min(width, height) // 2

    # Draw a filled circle in the mask
    draw.ellipse(
        [(outline_width, outline_width), (width - outline_width, height - outline_width)],
        fill=255
    )

    # Create a new image for the outline
    outline_image = Image.new("RGBA", (width + 2 * outline_width, height + 2 * outline_width), (0, 0, 0, 0))
    draw = ImageDraw.Draw(outline_image)

    # Draw the outer circle with the outline color
    draw.ellipse(
        [(0, 0), (width + 2 * outline_width, height + 2 * outline_width)],
        fill=color
    )

    # Paste the original image onto the outline image using the mask
    outline_image.paste(image, (outline_width, outline_width), mask)

    return outline_image  # Example usage


def makeCircle(image_path, output_path):
    image = Image.open(image_path).convert("RGBA")
    width, height = image.size
    square_size = min(width, height)
    new_image = Image.new('RGBA', (square_size, square_size), (0, 0, 0, 0))
    left = (square_size - width) // 2
    top = (square_size - height) // 2
    new_image.paste(image, (left, top))
    mask = Image.new('L', (square_size, square_size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, square_size, square_size), fill=255)
    new_image.putalpha(mask)
    new_image.save(output_path)


def draw_text_with_outline(image, text, position, font, text_color, outline_color, outline_width):
    draw = ImageDraw.Draw(image)

    x, y = position

    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=outline_color)

    draw.text((x, y), text, font=font, fill=text_color)


def drawStatus(status_color, image):
    leftMargin = 40
    outlineColor = "#C6BCD1"
    topMargin = 32
    status_size = 60
    status_circle = Image.new("RGBA", (status_size, status_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(status_circle)
    draw.ellipse((0, 0, status_size, status_size), fill=status_color)
    status_circle = add_outline(status_circle, 1, outlineColor)
    balancer = 0
    image.paste(status_circle, box=(leftMargin + 128 + status_size + balancer, 128 + topMargin + status_size + balancer), mask=status_circle)


def drawBackgroundWithPfp(pfpData):
    leftMargin = 40
    topMargin = 32
    width, height = 1024, 320
    background_color = (215, 223, 242, 255)

    image = Image.new("RGBA", (width, height), background_color)
    pfp = Image.open(pfpData).convert("RGBA")  # 256x256
    pfp = pfp.resize((256, 256), Image.LANCZOS)

    outlineWidth = 5
    outlineColor = "#C6BCD1"
    pfp = add_outline(pfp, outlineWidth, outlineColor)
    leftMargin = 40
    topMargin = 32
    image.paste(pfp, (leftMargin, topMargin - outlineWidth), pfp)
    return image


def draw_box(draw, box, color):
    x0, y0, x1, y1 = box
    width = x1 - x0
    height = y1 - y0

    r1, g1, b1 = color
    r2, g2, b2 = color
    dr = (r2 - r1) / width
    dg = (g2 - g1) / width
    db = (b2 - b1) / width

    for i in range(width):
        r = int(r1 + dr * i)
        g = int(g1 + dg * i)
        b = int(b1 + db * i)
        draw.line([(x0 + i, y0), (x0 + i, y1)], fill=(r, g, b))


def drawName(text, image):
    text = fontSizeFilter(text)

    draw_text_with_outline(image, text, (355, 130), nameFont(35), "white", "#506978", 2)


def drawRank(text, image):
    draw = ImageDraw.Draw(image)
    draw.text((860, 135), fill="#295372", font=mainFont(32), text="RANK")
    draw_text_with_outline(image, f"#{text}", (915, 120), mainFont(45), "white", "#506978", 1)


def drawLevel(text, image):
    draw = ImageDraw.Draw(image)
    draw.text((365, 230), fill="#295372", font=mainFont(30), text="LVL")
    draw.text((400, 220), fill="#295372", font=mainFont(45), text=text)


def drawLevelBoxes(percent, image):
    box_width, box_height = 55, 55
    gap = 5
    emptyColor = "#C5BCD1"
    num_boxes = 10
    x, y = 350, 170
    num_full_boxes = int(num_boxes * percent / 100)
    num_partial_boxes = 1 if percent % 10 >= 5 else 0
    num_empty_boxes = num_boxes - num_full_boxes - num_partial_boxes

    draw = ImageDraw.Draw(image)

    for i in range(num_boxes):

        color = rgb(color_scheme[i + 1])

        x0 = x + (box_width + gap) * i
        y0 = y
        x1 = x0 + box_width
        y1 = y0 + box_height
        box = (x0, y0, x1, y1)

        if i < num_full_boxes:
            draw_box(draw, box, color)

        elif i == num_full_boxes and num_partial_boxes:
            draw_box(draw, (x0, y0, x0 + int(box_width * 0.5), y1), color)
            draw.rectangle([(x0 + int(box_width * 0.5), y0), (x1, y1)], fill=emptyColor)
        else:
            draw.rectangle([(x0, y0), (x1, y1)], fill=emptyColor)


def numFormat(num):
    if num < 1000:
        return str(num)
    elif num < 1_000_000:
        return f"{num / 1_000:.3g}K"
    elif num < 1_000_000_000:
        return f"{num / 1_000_000:.3g}M"
    else:
        return str(num)


def expLine(expMin, expMax, image):
    img = Image.open("data/img.png")
    draw = ImageDraw.Draw(image)

    draw.text((820, 237), fill="#295372", font=mainFont(25), text=f"{numFormat(expMin)}/{numFormat(expMax)}")
    draw.text((910, 220), fill="#295372", font=mainFont(45), text="XP")

    image.paste(img, (445, 230))


def createLevelImage(name, status, rank, level, percent, expMin, expMax, pfpData):
    image = drawBackgroundWithPfp(pfpData)

    if status == "online":
        drawStatus("#23A55A", image)
    elif status == "offline" or status == "invisible":
        drawStatus("#80848E", image)
    elif status == "idle":
        drawStatus("#D39C2C", image)
    else:
        drawStatus("#F23F43", image)

    drawName(name, image)
    drawRank(rank, image)
    drawLevel(str(level), image)
    drawLevelBoxes(percent, image)
    expLine(expMin, expMax, image)

    imageIo = io.BytesIO()
    image.save(imageIo, format="PNG")
    imageIo.seek(0)
    return imageIo

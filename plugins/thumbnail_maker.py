import os
import aiohttp
import asyncio
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import textwrap
import io

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")

TEMPLATE_PATH = os.path.join(ASSETS_DIR, "template.png")
# We assume hex_mask.png is already created by our analysis step and placed in ASSETS_DIR.
# For robustness, if it doesn't exist, we will create it on the fly.
HEX_MASK_PATH = os.path.join(ASSETS_DIR, "hex_mask.png")

FONT_TITLE = os.path.join(FONTS_DIR, "Montserrat-Black.ttf")
FONT_BODY = os.path.join(FONTS_DIR, "Roboto-Medium.ttf")

def get_hex_mask():
    if os.path.exists(HEX_MASK_PATH):
        return Image.open(HEX_MASK_PATH).convert('L')

    img = Image.open(TEMPLATE_PATH).convert('RGBA')
    mask = Image.new('L', img.size, 0)
    pixels = img.load()
    mask_pixels = mask.load()

    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = pixels[x, y]
            if x > 800 and r > 240 and g > 240 and b > 240:
                mask_pixels[x, y] = 255
    mask.save(HEX_MASK_PATH)
    return mask

def crop_image(img, target_size, crop_state):
    """
    Crops the image based on crop_state:
    0: Center
    1: Left
    2: Right
    """
    target_width, target_height = target_size
    img_ratio = img.width / img.height
    target_ratio = target_width / target_height

    if img_ratio > target_ratio:
        # Image is wider than target, crop horizontally
        new_width = int(target_ratio * img.height)
        if crop_state == 0: # Center
            left = (img.width - new_width) // 2
        elif crop_state == 1: # Left
            left = 0
        else: # Right
            left = img.width - new_width

        img = img.crop((left, 0, left + new_width, img.height))
    elif img_ratio < target_ratio:
        # Image is taller than target, crop vertically (always center vertically for simplicity)
        new_height = int(img.width / target_ratio)
        top = (img.height - new_height) // 2
        img = img.crop((0, top, img.width, top + new_height))

    return img.resize(target_size, Image.Resampling.LANCZOS)

def apply_small_caps(text):
    # Simple small caps mapping for A-Z
    normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    smallcaps = "ᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ"
    trans = str.maketrans(normal, smallcaps)
    return text.translate(trans)

async def generate_poster(anime_img_url, title, genres, synopsis, username, logo_url=None, crop_state=0, small_caps=False):
    # Fetch anime image
    async with aiohttp.ClientSession() as session:
        async with session.get(anime_img_url) as resp:
            anime_img_data = await resp.read()
            anime_img = Image.open(io.BytesIO(anime_img_data)).convert('RGBA')

        # Fetch logo if provided
        logo_img = None
        if logo_url:
            try:
                async with session.get(logo_url) as resp:
                    if resp.status == 200:
                        logo_data = await resp.read()
                        logo_img = Image.open(io.BytesIO(logo_data)).convert('RGBA')
            except Exception as e:
                print(f"Failed to fetch logo: {e}")

    # Load template and mask
    template = Image.open(TEMPLATE_PATH).convert('RGBA')
    hex_mask = get_hex_mask()

    # Get mask bounding box to know exact size of the masked area
    bbox = hex_mask.getbbox()
    if not bbox:
        bbox = (0, 0, template.width, template.height)

    # We resize the anime image to cover the entire template area for simplicity,
    # but strictly crop it to the template aspect ratio first.
    cropped_anime = crop_image(anime_img, template.size, crop_state)

    # Create an empty image for the masked anime
    masked_anime = Image.new('RGBA', template.size, (0, 0, 0, 0))
    masked_anime.paste(cropped_anime, (0, 0))
    masked_anime.putalpha(hex_mask)

    # Composite the masked anime onto the template
    final_img = Image.alpha_composite(template, masked_anime)

    draw = ImageDraw.Draw(final_img)

    # Typography logic
    if small_caps:
        title = apply_small_caps(title)
        genres = apply_small_caps(genres)
        synopsis = apply_small_caps(synopsis)
        username = apply_small_caps(username)

    # Title
    font_title = ImageFont.truetype(FONT_TITLE, 80)
    # Wrap title
    wrapped_title = textwrap.fill(title, width=20)
    title_lines = wrapped_title.split('\n')

    # Genres
    font_genres = ImageFont.truetype(FONT_BODY, 35)

    # Synopsis
    font_synopsis = ImageFont.truetype(FONT_BODY, 30)
    if len(synopsis) > 150:
        synopsis = synopsis[:150] + "...read more"
    wrapped_synopsis = textwrap.fill(synopsis, width=50)

    # Branding (Logo + Username)
    font_brand = ImageFont.truetype(FONT_BODY, 40)

    # Define positions
    x_offset = 80
    y_offset = 250

    # Draw Title
    for line in title_lines:
        draw.text((x_offset, y_offset), line, font=font_title, fill="white")
        y_offset += 90

    y_offset += 20

    # Draw Genres
    draw.text((x_offset, y_offset), genres, font=font_genres, fill="#FF6B00") # Orange

    y_offset += 60

    # Draw Synopsis
    draw.text((x_offset, y_offset), wrapped_synopsis, font=font_synopsis, fill="#D3D3D3") # Light Gray

    # Draw Branding (Top Left)
    brand_x = 80
    brand_y = 60
    if logo_img:
        logo_img = logo_img.resize((80, 80), Image.Resampling.LANCZOS)
        # Create circular mask for logo
        circle_mask = Image.new('L', (80, 80), 0)
        circle_draw = ImageDraw.Draw(circle_mask)
        circle_draw.ellipse((0, 0, 80, 80), fill=255)
        logo_img.putalpha(circle_mask)
        final_img.paste(logo_img, (brand_x, brand_y), logo_img)
        brand_x += 100
        brand_y += 15

    draw.text((brand_x, brand_y), username, font=font_brand, fill="white")

    # Save to buffer
    buf = io.BytesIO()
    final_img.save(buf, format='PNG')
    buf.seek(0)
    return buf

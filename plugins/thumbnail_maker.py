import os
import aiohttp
import asyncio
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import textwrap
import io

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")

TEMPLATE_PATH = os.path.join(ASSETS_DIR, "template.png")
# FIX: Corrected mask name to match your folder
HEX_MASK_PATH = os.path.join(ASSETS_DIR, "hex_mask.png") 

FONT_TITLE = os.path.join(FONTS_DIR, "Montserrat-Black.ttf")
FONT_BODY = os.path.join(FONTS_DIR, "Roboto-Medium.ttf")

def crop_image(img, target_size, crop_state):
    target_width, target_height = target_size
    img_ratio = img.width / img.height
    target_ratio = target_width / target_height

    if img_ratio > target_ratio:
        new_width = int(target_ratio * img.height)
        if crop_state == 0: 
            left = (img.width - new_width) // 2
        elif crop_state == 1: 
            left = 0
        else: 
            left = img.width - new_width

        img = img.crop((left, 0, left + new_width, img.height))
    elif img_ratio < target_ratio:
        new_height = int(img.width / target_ratio)
        top = (img.height - new_height) // 2
        img = img.crop((0, top, img.width, top + new_height))

    return img.resize(target_size, Image.Resampling.LANCZOS)

def apply_small_caps(text):
    if not text: return text
    normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    smallcaps = "ᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ"
    trans = str.maketrans(normal, smallcaps)
    return text.translate(trans)

async def generate_poster(anime_img_url=None, custom_image_path=None, title="", genres="", synopsis="", username="", logo_url=None, crop_state=0, small_caps=False):

    if custom_image_path:
        anime_img = Image.open(custom_image_path).convert('RGBA')
    elif anime_img_url:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(anime_img_url) as resp:
                    anime_img_data = await resp.read()
                    anime_img = Image.open(io.BytesIO(anime_img_data)).convert('RGBA')
            except Exception:
                anime_img = Image.new('RGBA', (1920, 1080), (100, 100, 100, 255))
    else:
        anime_img = Image.new('RGBA', (1920, 1080), (100, 100, 100, 255))

    logo_img = None
    if logo_url:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(logo_url) as resp:
                    if resp.status == 200:
                        logo_data = await resp.read()
                        logo_img = Image.open(io.BytesIO(logo_data)).convert('RGBA')
        except Exception as e:
            pass

    base_template = Image.open(TEMPLATE_PATH).convert('RGBA')

    try:
        fetched_mask = Image.open(HEX_MASK_PATH).convert('RGBA')
    except:
        fetched_mask = Image.new('RGBA', base_template.size, (0, 0, 0, 0))

    fetched_mask = fetched_mask.resize(base_template.size, Image.Resampling.LANCZOS)
    hex_mask = fetched_mask.convert('L')

    anime_artwork = crop_image(anime_img, hex_mask.size, crop_state)
    anime_artwork.putalpha(hex_mask)

    final_img = base_template.copy()
    final_img.paste(anime_artwork, (0, 0), hex_mask)

    draw = ImageDraw.Draw(final_img)

    if small_caps:
        title = apply_small_caps(title)
        genres = apply_small_caps(genres)
        synopsis = apply_small_caps(synopsis)
        username = apply_small_caps(username)

    # Safe Font Loading
    try:
        font_title = ImageFont.truetype(FONT_TITLE, 80)
        font_genres = ImageFont.truetype(FONT_BODY, 35)
        font_synopsis = ImageFont.truetype(FONT_BODY, 30)
        font_brand = ImageFont.truetype(FONT_BODY, 40)
    except:
        font_title = font_genres = font_synopsis = font_brand = ImageFont.load_default()

    wrapped_title = textwrap.fill(title, width=22)
    title_lines = wrapped_title.split('\n')

    # FIX: Increased length for synopsis so it doesn't cut off too early
    if len(synopsis) > 280:
        synopsis = synopsis[:277] + "..."
    wrapped_synopsis = textwrap.fill(synopsis, width=55)

    # ==========================================
    # FIX: MOVED EVERYTHING TO THE RIGHT SIDE
    # ==========================================
    x_offset = 950  # Shifted from 80 to 950 (Right side of 1920x1080 canvas)
    y_offset = 250

    for line in title_lines:
        draw.text((x_offset, y_offset), line, font=font_title, fill="white")
        y_offset += 90

    y_offset += 20
    draw.text((x_offset, y_offset), genres, font=font_genres, fill="#FF6B00")

    y_offset += 60
    draw.text((x_offset, y_offset), wrapped_synopsis, font=font_synopsis, fill="#D3D3D3")

    # Branding (Top Right)
    brand_x = 950
    brand_y = 100
    if logo_img:
        logo_img = logo_img.resize((80, 80), Image.Resampling.LANCZOS)
        grayscale_mask = logo_img.convert('L')
        rgba_logo = logo_img.convert('RGBA')
        rgba_logo.putalpha(grayscale_mask)
        final_img.paste(rgba_logo, (brand_x, brand_y), rgba_logo)
        brand_x += 100
        brand_y += 15

    draw.text((brand_x, brand_y), username, font=font_brand, fill="white")

    buf = io.BytesIO()
    final_img.save(buf, format='PNG')
    buf.seek(0)
    return buf

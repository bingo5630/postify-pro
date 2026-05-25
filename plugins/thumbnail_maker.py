import os
import aiohttp
import asyncio
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import textwrap
import io

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")

TEMPLATE_PATH = os.path.join(ASSETS_DIR, "template.png")
HEX_MASK_PATH = os.path.join(ASSETS_DIR, "hex_mask_remote.png")

FONT_TITLE = os.path.join(FONTS_DIR, "Montserrat-Black.ttf")
FONT_BODY = os.path.join(FONTS_DIR, "Roboto-Medium.ttf")

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
    if not text: return text
    normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    smallcaps = "ᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ"
    trans = str.maketrans(normal, smallcaps)
    return text.translate(trans)

async def generate_poster(anime_img_url=None, custom_image_path=None, title="", genres="", synopsis="", username="", logo_url=None, crop_state=0, small_caps=False):

    # Load anime image (API or custom upload)
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

    # Fetch logo if provided
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

    # Load template and mask
    base_template = Image.open(TEMPLATE_PATH).convert('RGBA')

    # Step 1: Fetch the specific ImgBB Mask logic
    try:
        fetched_mask = Image.open(HEX_MASK_PATH).convert('RGBA')
    except:
        fetched_mask = Image.new('RGBA', base_template.size, (0, 0, 0, 0))

    # Resize fetched mask to template dimensions (in case it differs slightly)
    fetched_mask = fetched_mask.resize(base_template.size, Image.Resampling.LANCZOS)

    # Step 2: Prepare the Mask (grayscale mode for alpha stencil)
    hex_mask = fetched_mask.convert('L')

    # Step 3: Resize Artwork exactly to the dimensions of hex_mask
    anime_artwork = crop_image(anime_img, hex_mask.size, crop_state)

    # Optional: Apply stencil strictly directly on artwork (as requested, but paste does it too)
    anime_artwork.putalpha(hex_mask)

    # Step 4: Paste strictly inside the Hexagon
    final_img = base_template.copy()
    final_img.paste(anime_artwork, (0, 0), hex_mask)

    draw = ImageDraw.Draw(final_img)

    # Typography logic
    if small_caps:
        title = apply_small_caps(title)
        genres = apply_small_caps(genres)
        synopsis = apply_small_caps(synopsis)
        username = apply_small_caps(username)

    # Title
    font_title = ImageFont.truetype(FONT_TITLE, 80)
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
        # Remove solid background dynamically using Grayscale mask
        grayscale_mask = logo_img.convert('L')
        rgba_logo = logo_img.convert('RGBA')
        rgba_logo.putalpha(grayscale_mask)
        final_img.paste(rgba_logo, (brand_x, brand_y), rgba_logo)
        brand_x += 100
        brand_y += 15

    draw.text((brand_x, brand_y), username, font=font_brand, fill="white")

    # Save to buffer
    buf = io.BytesIO()
    final_img.save(buf, format='PNG')
    buf.seek(0)
    return buf

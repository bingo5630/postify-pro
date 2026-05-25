import os
import aiohttp
import asyncio
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import textwrap
import io

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")

TEMPLATE_PATH = os.path.join(ASSETS_DIR, "template.png")
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
            if logo_url.startswith("http"):
            if os.path.exists(logo_url):
                logo_img = Image.open(logo_url).convert('RGBA')
            else:
                async with aiohttp.ClientSession() as session:
                    async with session.get(logo_url) as resp:
                        if resp.status == 200:
                            logo_data = await resp.read()
                            logo_img = Image.open(io.BytesIO(logo_data)).convert('RGBA')
 cleanup-poster-bot-refactor-17135537001999441390
            elif os.path.exists(logo_url):
                logo_img = Image.open(logo_url).convert('RGBA')
        except Exception as e:

        except Exception:
 main
            pass

    base_template = Image.open(TEMPLATE_PATH).convert('RGBA')

    try:
        fetched_mask = Image.open(HEX_MASK_PATH).convert('RGBA')
    except:
        fetched_mask = Image.new('RGBA', base_template.size, (0, 0, 0, 0))

    fetched_mask = fetched_mask.resize(base_template.size, Image.Resampling.LANCZOS)
    
    # Pure Alpha Extract (Removes White Halo)
    try:
        hex_mask = fetched_mask.split()[3] 
    except IndexError:
        hex_mask = fetched_mask.convert('L')

    anime_artwork = crop_image(anime_img, hex_mask.size, crop_state)
    
    final_img = base_template.copy()
    final_img.paste(anime_artwork, (0, 0), hex_mask)

    draw = ImageDraw.Draw(final_img)

    if small_caps:
        genres = apply_small_caps(genres)
        synopsis = apply_small_caps(synopsis)
        username = apply_small_caps(username)

    try:
        font_title = ImageFont.truetype(FONT_TITLE, 80)
        font_genres = ImageFont.truetype(FONT_BODY, 35)
        font_synopsis = ImageFont.truetype(FONT_BODY, 30)
        font_brand = ImageFont.truetype(FONT_BODY, 40)
    except:
        font_title = font_genres = font_synopsis = font_brand = ImageFont.load_default()

    # Force ALL-CAPS & Tighter 16-Char Wrap
    wrapped_title = textwrap.fill(title.upper(), width=16) 
    title_lines = wrapped_title.split('\n')

    if len(synopsis) > 280:
        synopsis = synopsis[:277] + "..."
    wrapped_synopsis = textwrap.fill(synopsis, width=45)

    x_offset = 80 
    y_offset = 280

    # ==========================================
    # FIX: FIRST LINE WHITE, SECOND LINE ORANGE
    # ==========================================
    for i, line in enumerate(title_lines):
        # Agar pehli line hai (0) toh white, warna Orange (#FF6B00)
        text_color = "white" if i == 0 else "#FF6B00"
        draw.text((x_offset, y_offset), line, font=font_title, fill=text_color)
        y_offset += 90

    y_offset += 20
    draw.text((x_offset, y_offset), genres, font=font_genres, fill="#FF6B00")

    y_offset += 60
    draw.text((x_offset, y_offset), wrapped_synopsis, font=font_synopsis, fill="#D3D3D3")

    brand_x = 80
    brand_y = 60
    
    if logo_img:
        try:
            logo_img = logo_img.resize((80, 80), Image.Resampling.LANCZOS).convert('RGBA')
            final_img.paste(logo_img, (brand_x, brand_y), logo_img)
            brand_x += 100 
        except Exception:
            pass 

    draw.text((brand_x, brand_y + 15), username, font=font_brand, fill="white")

    buf = io.BytesIO()
    final_img.save(buf, format='PNG')
    buf.seek(0)
    return buf

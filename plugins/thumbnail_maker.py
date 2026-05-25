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

# ==========================================
# SMART LOGO CLEANER (Removes Black BG for B&W Logos)
# ==========================================
def clean_logo(img):
    img = img.convert("RGBA")
    if img.getextrema()[3][0] < 255:
        return img
    
    tiny = img.convert("RGB").resize((32, 32))
    for r, g, b in tiny.getdata():
        if abs(r-g) > 25 or abs(r-b) > 25:
            return img 
            
    white_img = Image.new("RGBA", img.size, (255, 255, 255, 255))
    white_img.putalpha(img.convert("L"))
    return white_img

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

    base_template = Image.open(TEMPLATE_PATH).convert('RGBA')

    try:
        fetched_mask = Image.open(HEX_MASK_PATH).convert('RGBA')
    except:
        fetched_mask = Image.new('RGBA', base_template.size, (0, 0, 0, 0))
        
    fetched_mask = fetched_mask.resize(base_template.size, Image.Resampling.LANCZOS)
    
    # ==========================================
    # ARTIFACT KILLER: ALPHA CLAMPING + COMPOSITE CANVAS
    # ==========================================
    
    # 1. Mask ko strict Black & White mein convert karna
    strict_l_mask = fetched_mask.convert('L')
    binary_mask_full = strict_l_mask.point(lambda p: 255 if p > 128 else 0)

    # 2. Anime Artwork ko crop karna
    crop_artwork_full = crop_image(anime_img, base_template.size, crop_state)

    # 3. Ek blank transparent canvas banana
    clean_cutout_layer = Image.new('RGBA', base_template.size, (0, 0, 0, 0))

    # 4. Artwork ko sharp mask ke sath transparent canvas par paste karna (White line yaheen khatam ho jayegi)
    clean_cutout_layer.paste(crop_artwork_full, (0, 0), binary_mask_full)

    # 5. Us clean cutout ko final template par paste karna
    final_img = base_template.copy()
    final_img.paste(clean_cutout_layer, (0, 0), clean_cutout_layer)

    draw = ImageDraw.Draw(final_img)

    logo_img = None
    if logo_url:
        try:
            if logo_url.startswith("http"):
                async with aiohttp.ClientSession() as session:
                    async with session.get(logo_url) as resp:
                        if resp.status == 200:
                            logo_data = await resp.read()
                            logo_img = Image.open(io.BytesIO(logo_data)).convert('RGBA')
            elif os.path.exists(logo_url):
                logo_img = Image.open(logo_url).convert('RGBA')
        except Exception: 
            pass

    genres_caps = genres.upper() if genres else ""

    if small_caps:
        genres_caps = apply_small_caps(genres_caps)
        synopsis = apply_small_caps(synopsis)
        username = apply_small_caps(username)

    try:
        font_title = ImageFont.truetype(FONT_TITLE, 85)
        font_genres = ImageFont.truetype(FONT_BODY, 35)
        font_synopsis = ImageFont.truetype(FONT_BODY, 30)
        font_brand = ImageFont.truetype(FONT_BODY, 40)
        font_title_orange = ImageFont.truetype(FONT_TITLE, 65)
    except:
        font_title = font_genres = font_synopsis = font_brand = font_title_orange = ImageFont.load_default()

    wrapped_title = textwrap.fill(title.upper(), width=17) 
    title_lines = wrapped_title.split('\n')

    x_offset = 80
    y_dynamic_offset = 280

    for i, line in enumerate(title_lines):
        if i == 0:
            draw.text((x_offset, y_dynamic_offset), line, font=font_title, fill="white")
            y_dynamic_offset += 100 
        else:
            draw.text((x_offset, y_dynamic_offset), line, font=font_title_orange, fill="#FF6B00")
            y_dynamic_offset += 75 

    y_dynamic_offset += 20
    draw.text((x_offset, y_dynamic_offset), genres_caps, font=font_genres, fill="#FF6B00")

    synopsis_dynamic_max_chars = 220 - ((len(title_lines) - 1) * 60) 
    
    if len(synopsis) > synopsis_dynamic_max_chars:
        synopsis = synopsis[:synopsis_dynamic_max_chars].rsplit(' ', 1)[0] + "...read more"
    wrapped_synopsis = textwrap.fill(synopsis, width=45)

    y_dynamic_offset += 60
    draw.text((x_offset, y_dynamic_offset), wrapped_synopsis, font=font_synopsis, fill="#D3D3D3")

    brand_x = 80
    brand_y = 60
    
    if logo_img:
        try:
            logo_img = clean_logo(logo_img)
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

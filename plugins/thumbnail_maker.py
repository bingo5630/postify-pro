import os
import aiohttp
import asyncio
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageChops, ImageEnhance
import textwrap
import io

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")

TEMPLATE_PATH = os.path.join(ASSETS_DIR, "template.png")
HEX_MASK_PATH = os.path.join(ASSETS_DIR, "hex_mask.png")

FONT_TITLE = os.path.join(FONTS_DIR, "Montserrat-Black.ttf")
FONT_BODY = os.path.join(FONTS_DIR, "Roboto-Medium.ttf")

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

def enhance_image(img):
    img = img.convert("RGB")
    img = ImageEnhance.Sharpness(img).enhance(2.0)
    img = ImageEnhance.Contrast(img).enhance(1.2)
    img = ImageEnhance.Color(img).enhance(1.2)
    return img.convert("RGBA")

def apply_small_caps(text):
    if not text: return text
    normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    smallcaps = "ᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ"
    trans = str.maketrans(normal, smallcaps)
    return text.translate(trans)

# Ab crop_state wapas aagaya hai 2 styles handle karne ke liye
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
        fetched_mask = Image.open(HEX_MASK_PATH).convert('L')
    except:
        fetched_mask = Image.new('L', base_template.size, 0)

    fetched_mask = fetched_mask.resize(base_template.size, Image.Resampling.LANCZOS)
    
    # White Border Killer (Hole punch technique)
    strict_mask = fetched_mask.point(lambda p: 255 if p > 128 else 0)
    expanded_mask = strict_mask.filter(ImageFilter.MaxFilter(7))
    inverse_mask = ImageOps.invert(expanded_mask)
    
    r, g, b, a = base_template.split()
    punched_alpha = ImageChops.darker(a, inverse_mask) 
    base_template.putalpha(punched_alpha)
    
    # ==========================================
    # TUMHARA 2-STEP LOGIC YAHAN HAI:
    # ==========================================
    if crop_state == 0:
        # STYLE 1: Full Fit (Pehle wala - Screen bhar dega, par face kat sakta hai vertical hone par)
        anime_artwork = ImageOps.fit(anime_img, base_template.size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    else:
        # STYLE 2: TUMHARA MANUAL IDEA (Center Fit with Background)
        # 1. Background ko blur kar diya (Black se better look ke liye)
        blurred_bg = ImageOps.fit(anime_img, base_template.size, method=Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(25))
        anime_artwork = blurred_bg.convert('RGBA')
        
        # 2. Original image ko chhota (shrink) karke beech mein chipka diya (Koi face nahi katega)
        fitted = ImageOps.contain(anime_img, base_template.size, method=Image.Resampling.LANCZOS)
        offset_x = (base_template.size[0] - fitted.size[0]) // 2
        offset_y = (base_template.size[1] - fitted.size[1]) // 2
        anime_artwork.paste(fitted, (offset_x, offset_y), fitted if fitted.mode == 'RGBA' else None)

    anime_artwork = enhance_image(anime_artwork)
    
    final_img = Image.new('RGBA', base_template.size, (0, 0, 0, 255))
    final_img.paste(anime_artwork, (0, 0)) 
    final_img.paste(base_template, (0, 0), base_template) 

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

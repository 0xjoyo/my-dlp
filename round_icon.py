import sys
from PIL import Image, ImageDraw

def add_corners(im, rad):
    circle = Image.new('L', (rad * 2, rad * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, rad * 2 - 1, rad * 2 - 1), fill=255)
    alpha = Image.new('L', im.size, 255)
    w, h = im.size
    alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
    alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
    alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
    alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
    im.putalpha(alpha)
    return im

try:
    img_path = r"C:\Users\fgggg\.gemini\antigravity\brain\4c852d65-babb-4a00-8008-1dc94ae6919f\modern_downloader_icon_1782027898987.png"
    img = Image.open(img_path).convert("RGBA")
    
    # Assuming the image is 1024x1024, radius 200 gives nice soft squircle edges
    w, h = img.size
    radius = int(w * 0.22) 
    
    img_rounded = add_corners(img, radius)
    img_rounded.save("assets/icon.ico", format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (32, 32)])
    print("Successfully rounded the icon corners.")
except Exception as e:
    print(f"Error: {e}")

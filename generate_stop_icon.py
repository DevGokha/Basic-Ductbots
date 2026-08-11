from PIL import Image, ImageDraw

def create_icon(filename, draw_func):
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw_func(draw)
    img.save(filename)
    print(f"Generated {filename}")

def draw_stop(draw):
    # A square
    draw.rectangle([(16, 16), (48, 48)], fill="white")

create_icon("icons/stop_icon.png", draw_stop)

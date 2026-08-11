from PIL import Image, ImageDraw
import math

def create_icon(filename, draw_func):
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw_func(draw)
    img.save(filename)
    print(f"Generated {filename}")

def draw_playback(draw):
    # Triangle pointing right
    points = [(20, 16), (20, 48), (48, 32)]
    draw.polygon(points, fill="white")

def draw_record(draw):
    # Circle
    draw.ellipse([(16, 16), (48, 48)], fill="white")

def draw_flip(draw):
    # Two arrows or a simple flip icon
    draw.arc([(12, 24), (36, 48)], start=90, end=270, fill="white", width=4)
    draw.arc([(28, 16), (52, 40)], start=270, end=90, fill="white", width=4)
    # arrows
    draw.polygon([(36, 44), (28, 48), (36, 52)], fill="white")
    draw.polygon([(28, 20), (36, 16), (28, 12)], fill="white")

def draw_lane(draw):
    # Two converging lines
    draw.line([(20, 56), (28, 16)], fill="white", width=4)
    draw.line([(44, 56), (36, 16)], fill="white", width=4)
    # middle dashed line
    draw.line([(32, 50), (32, 42)], fill="white", width=4)
    draw.line([(32, 34), (32, 26)], fill="white", width=4)

def draw_export(draw):
    # Arrow pointing down to a line
    draw.line([(32, 12), (32, 40)], fill="white", width=6)
    draw.polygon([(20, 36), (44, 36), (32, 48)], fill="white")
    draw.line([(16, 52), (48, 52)], fill="white", width=6)

create_icon("icons/playback_icon.png", draw_playback)
create_icon("icons/record_icon.png", draw_record)
create_icon("icons/flip_icon.png", draw_flip)
create_icon("icons/lane_icon.png", draw_lane)
create_icon("icons/export_icon.png", draw_export)

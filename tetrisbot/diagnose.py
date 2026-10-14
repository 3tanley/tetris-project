"""`python -m tetrisbot --locate`: one-shot check that the board is found and read."""
import os

from . import vision
from .controller import Screen, screen_access_ok


def locate_once(save_dir="debug"):
    if not screen_access_ok(prompt=True):
        print("Screen Recording permission is missing; the capture will only show the desktop.")
    scr = Screen()
    img = scr.full()
    geo = vision.locate(img)
    os.makedirs(save_dir, exist_ok=True)
    try:
        from PIL import Image
        Image.fromarray(img).save(os.path.join(save_dir, "screen.png"))
    except Exception:
        pass
    if geo is None:
        print(f"Board NOT found. Screenshot saved to {save_dir}/screen.png")
        return
    print("Board found:", geo)
    board, letters = vision.read_board(img, geo)
    p, cells = vision.read_active(img, geo, board)
    print("falling piece:", p, cells)
    print("hold:", vision.read_hold(img, geo))
    print("next:", "".join(vision.read_queue(img, geo)))
    for y in range(19, -1, -1):
        print("|" + "".join(letters.get((x, y), ".") for x in range(10)) + "|")

#  Copyright (c) 2025. Salim Janji. All rights reserved.
#  Unauthorized copying, distribution, or modification of this file is strictly prohibited.
from PIL import Image, ImageOps
import numpy as np
import cv2


def remove_white_background(image_path):
    """Loads an image and removes the white background."""
    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)  #Threshold adjust
    mask_inv = cv2.bitwise_not(mask)
    bgra = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
    bgra[:, :, 3] = mask_inv
    overlay_image = Image.fromarray(bgra)

    return overlay_image


def overlay_image(background_path, overlay_path, position=(100, 100), resize=(44, 44)):
    """Overlays the processed image on the background at the specified position."""
    background = Image.open(background_path).convert("RGBA")
    overlay = remove_white_background(overlay_path)
    overlay = overlay.resize(resize)
    background.paste(overlay, position, overlay)

    return background


def remove_duplicate_sentences(text):
    """Removes duplicate sentences from a string."""
    sentences = text.split("\n")
    unique_sentences = set(sentences)
    return "\n".join(unique_sentences)

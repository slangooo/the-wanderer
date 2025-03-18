#  Copyright (c) 2025. Salim Janji. All rights reserved.
#  Unauthorized copying, distribution, or modification of this file is strictly prohibited.

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_ID = "Janus-Pro-7B"  # Change for other models
MODEL_PATH = BASE_DIR / "models" / "janus" / MODEL_ID
MODEL_NAME = "deepseek-ai/"+MODEL_ID
WANDERER_IMG_PATH = BASE_DIR / "images" / "wanderer_white_bkg.jpg"
ENTITY_IMG_PATH = BASE_DIR / "images" / "entity_white_bkg.jpg"
ENV_IMG_PATH = BASE_DIR / "images" / "env.jpg"
FINAL_IMG_PATH = BASE_DIR / "images" / "final.png" #Final image to be shown on the GUI

"""LLM Text GEN"""
TEXT_GEN_MAX_TOKENS = 512
CFG_WEIGHT_IMG = 5

if __name__ == '__main__':
    print(MODEL_PATH.parent)

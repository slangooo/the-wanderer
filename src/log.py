#  Copyright (c) 2025. Salim Janji. All rights reserved.
#  Unauthorized copying, distribution, or modification of this file is strictly prohibited.

import logging

logger = logging.getLogger("WandererLogger")
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))

file_handler = logging.FileHandler("app.log", mode="w")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Prevent duplicate logs if `log.py` is imported multiple times
logger.propagate = False

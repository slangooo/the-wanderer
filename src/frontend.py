#  Copyright (c) 2025. Salim Janji. All rights reserved.
#  Unauthorized copying, distribution, or modification of this file is strictly prohibited.

import tkinter as tk
from tkinter import Text, Scrollbar, filedialog
from PIL import Image, ImageTk
from configs.config import FINAL_IMG_PATH
from src.game_backend import TheWandererGame
import threading
import time

class WandererGameUI:
    def __init__(self, root):
        self.root = root
        self.root.title("The Wanderer")

        # Set window size
        self.root.geometry("800x600")

        # === Image Display Area ===
        self.image_label = tk.Label(self.root, text="No Image Loaded", bg="gray", width=50, height=15)
        self.image_label.pack(pady=10)

        # === Chat Display (Scrollable) ===
        self.chat_frame = tk.Frame(self.root)
        self.chat_frame.pack(pady=5, fill=tk.BOTH, expand=True)

        self.chat_text = Text(self.chat_frame, wrap=tk.WORD, height=10, state=tk.DISABLED)
        self.chat_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.chat_scroll = Scrollbar(self.chat_frame, command=self.chat_text.yview)
        self.chat_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_text.config(yscrollcommand=self.chat_scroll.set)

        # === User Input Field ===
        self.input_frame = tk.Frame(self.root)
        self.input_frame.pack(fill=tk.X, padx=10, pady=5)

        self.input_entry = tk.Entry(self.input_frame, width=80)
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.input_entry.bind("<Return>", self.process_input)  # Enter key triggers submission

        self.submit_button = tk.Button(self.input_frame, text="Submit", command=self.process_input)
        self.submit_button.pack(side=tk.RIGHT, padx=5)

        # === Example Usage ===
        self.update_chat("Game started. Welcome to The Wanderer game!")
        self.load_image()
        self.game_ctrl = TheWandererGame()
        self.update_chat(f"Environment description: {self.game_ctrl.get_env_desc()}")
        self.update_chat(f"'{self.game_ctrl.generate_entity_exchange()}'")

    def update_chat(self, message):
        """Appends a message to the chat display."""
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, message + "\n")
        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.yview(tk.END)  # Auto-scroll to the bottom

    def process_input(self, event=None):
        """Handles user input and appends it to the chat."""
        user_input = self.input_entry.get().strip()
        if user_input:
            self.update_chat(f"You: '{user_input}'")
            self.input_entry.delete(0, tk.END)  # Clear input field
            self.handle_game_logic(user_input)

    def handle_game_logic(self, user_input):
        """Process the user input and generate a game response."""
        threading.Thread(target=self.process_game_logic, args=(user_input,), daemon=True).start()

    def process_game_logic(self, user_input):
        """Runs the backend logic without blocking the UI."""
        new_env, entity_exchange = self.game_ctrl.wanderer_input(user_input)
        if new_env:
            self.root.after(0, self.update_chat, f"You have arrived at a new location. Environment description:"
                                                 f" \n {new_env}")
            self.root.after(0, self.load_image)
        self.root.after(0, self.update_chat, f"'{entity_exchange}'")


    def load_image(self):
        """Loads an image and displays it."""
        file_path = FINAL_IMG_PATH
        if file_path:
            image = Image.open(file_path)
            new_size = (image.width * 1, image.height * 1)
            upscaled_image = image.resize(new_size, Image.LANCZOS)
            self.img = ImageTk.PhotoImage(upscaled_image)
            self.image_label.config(image=self.img, text="")  # Remove text
            self.image_label.config(width=new_size[0], height=new_size[1])


if __name__ == "__main__":
    root = tk.Tk()
    game_ui = WandererGameUI(root)
    root.mainloop()

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

root = ttk.Window(themename="superhero")
root.title("Universal Skin Mod Manager")
root.iconbitmap("controller.ico")

main_frame = ttk.Frame(root, padding="3 3 12 12")
main_frame.grid(column=0, row=0, sticky=(N, W, E, S))
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

# business logic

# button to add game
b_add_game = ttk.Button(main_frame, text="Add Game", bootstyle=SUCCESS)
b_add_game.pack(side=LEFT, padx=5, pady=10)

    # add game via dialog box form
    # config file for app?
    # db for games, characters, notes
    # crud functionality for games and notes since characters are determined by read folder content
# button to remove game
# display list of games
# display list of characters/skinable objects once game is selected
# display list of mods for character from the skin closet folder

game_frame = ttk.Frame(main_frame, padding="3 3 12 12")

# write function to pull list of games from db or config file
games = ["Genshin", "Honkai", "Wuthering", "SF6", "ZZZ"]

def set_game_list():
    for game in games:
        # default toolbutton style
        select_game = ttk.Radiobutton(main_frame, text=game, bootstyle="toolbutton")
        select_game.pack(side=TOP, padx=5, pady=10)

set_game_list()


root.mainloop()
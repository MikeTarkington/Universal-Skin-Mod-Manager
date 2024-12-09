from tkinter import *
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
b_add_game = ttk.Button(main_frame, text="Add Game")
b_add_game.pack(side=TOP, padx=5, pady=10)

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
mods = ["Raiden","Shenhe", "Jean", "Barbara", "Keqing", "Chasca"]

# def set_game_list():
#     for game in games:
#         # default toolbutton style
#         select_game = ttk.Radiobutton(main_frame, text=game)
#         select_game.pack(side=BOTTOM, padx=5, pady=10)

# set_game_list()

game_listb = Listbox(main_frame, listvariable=games, selectmode=SINGLE, height=10)

def set_game_list():
    i = 0
    for game in games:
        i += 1
        game_listb.insert(i, game)

set_game_list()
# game_listb.grid()
game_listb.pack(side=BOTTOM, padx=5, pady=10)

mod_listb = Listbox(main_frame, listvariable=mods, selectmode=SINGLE, height=10)
mod_listb.pack(side=RIGHT, padx=5, pady=10)

def display_mods(game):
    i = 0
    for mod in mods:
        i += 1
        mod_listb.insert(i, mod)

l = ttk.Label(root, text="Starting...")
# l.pack(side=BOTTOM, padx=5, pady=10)
game_listb.bind('<<ListboxSelect>>', display_mods)


root.mainloop()

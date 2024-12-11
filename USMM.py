from tkinter import *
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

# Dev notes/planning:
    # add game via dialog box form
    # config file for app?
    # db for games, characters, notes
    # crud functionality for games and notes since characters are determined by read folder content
    # game needs stored path to applied mods folder and unapplied storage folder
# button to remove game
# display list of games
# display list of characters/skinable objects once game is selected
# display list of mods for character from the skin closet folder
# re-read mod folder button
# delete mod folder button?
# Associations: game has many modables and modables have many mods

root = ttk.Window(themename="superhero")
root.title("Universal Skin Mod Manager")
root.iconbitmap("controller.ico")

main_frame = ttk.Frame(root, padding="3 3 12 12")
main_frame.grid(column=0, row=0, padx=5, pady=5, sticky=(N, W, E, S))
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

# temporary variables for testing in dev
games = ["Genshin", "Honkai", "Wuthering", "SF6", "ZZZ"]
modables = ["Raiden","Shenhe", "Jean", "Barbara", "Keqing", "Chasca"]

# business logic

def set_game_list():
    i = 0
    for game in games:
        i += 1
        game_listb.insert(i, game)

def display_modables(game):
    i = 0
    for modable in modables:
        i += 1
        modable_listb.insert(i, modable)


# display content:

# button to add game
b_add_game = ttk.Button(main_frame, text="Add Game")
b_add_game.grid(column=1, row=3, padx=5, pady=5)

game_frame = ttk.Frame(main_frame, padding="3 3 12 12").grid()
game_list_l = ttk.Label(main_frame, text='Game List')
game_list_l.grid(column=1, row=1, padx=5, pady=5)
game_listb = Listbox(main_frame, listvariable=games, selectmode=SINGLE, height=10)
game_listb.grid(column=1, row=2, padx=5, pady=5)

# pupulate the games list by finding them in db (WIP)
set_game_list()

modable_listb = Listbox(main_frame, listvariable=modables, selectmode=SINGLE, height=10)
modable_listb.grid(column=2, row=2, padx=5, pady=5)

# click a game to show modables for that game in its corresponding listbox
game_listb.bind('<<ListboxSelect>>', display_modables)

root.mainloop()

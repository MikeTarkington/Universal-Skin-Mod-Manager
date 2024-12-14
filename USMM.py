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

class Game:
    def __init__(self, title, applied_path, store_path):
        self.title = title
        self.applied_path = applied_path
        self.store_path = store_path

def add_game():
    title = game_t.get()
    applied_path = game_mods_path.get()
    store_path = game_modables_path.get()
    game = Game(title, applied_path, store_path)
    print(vars(game))
    games.append(game.title) # will eventually write to db or conf file
    # need to update the game list page somehow to show the newly added game

# consider refactor to join with display_modables**
def set_game_list():
    i = 0
    for game in games:
        i += 1
        game_listb.insert(i, game)

# consider refactor to join with set_game_list**
def display_modables(game):
    i = 0
    for modable in modables:
        i += 1
        modables_list_lb.insert(i, modable)


# display content:

# game list display
game_frame = ttk.Frame(main_frame, padding="3 3 12 12").grid()
game_list_l = ttk.Label(main_frame, text='Games')
game_list_l.grid(column=1, row=1, padx=5, pady=5)
game_listb = Listbox(main_frame, listvariable=games, selectmode=SINGLE, height=10)
game_listb.grid(column=1, row=2, padx=5, pady=5)

# pupulate the games list by finding them in db (WIP)
set_game_list()

# form to add game
game_title_l = ttk.Label(main_frame, text='Game Title')
game_title_l.grid(column=1, row=3, padx=5, pady=5)
game_t = StringVar()
game_t = ttk.Entry(main_frame, textvariable=game_t)
game_t.grid(column=1, row=4, padx=5, pady=5)
game_path_l = ttk.Label(main_frame, text='Path to Applied Mods Folder')
game_path_l.grid(column=1, row=5, padx=5, pady=5)
# add browse button option for entering path**
game_modables_path = StringVar()
game_modables_path = ttk.Entry(main_frame, textvariable=game_modables_path)
game_modables_path.grid(column=1, row=6, padx=5, pady=5)
game_path_l = ttk.Label(main_frame, text='Path to Mod Storage Folder')
game_path_l.grid(column=1, row=7, padx=5, pady=5)
# add browse button option for entering path**
game_mods_path = StringVar()
game_mods_path = ttk.Entry(main_frame, textvariable=game_mods_path)
game_mods_path.grid(column=1, row=8, padx=5, pady=5)
# submit form
b_add_game = ttk.Button(main_frame, text="Add Game", command=add_game)
b_add_game.grid(column=1, row=9, padx=5, pady=5)

# modable list display
modables_listl = ttk.Label(main_frame, text='Assets (Char Skins, etc)')
modables_listl.grid(column=2, row=1, padx=5, pady=5)
modables_list_lb = Listbox(main_frame, listvariable=modables, selectmode=SINGLE, height=10)
modables_list_lb.grid(column=2, row=2, padx=5, pady=5)

# click a game to show modables for that game in its corresponding listbox
game_listb.bind('<<ListboxSelect>>', display_modables)

root.mainloop()

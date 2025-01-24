import os
import shutil
import sqlite3
import ttkbootstrap as ttk
from tkinter import *
from tkinter import filedialog
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

# tkinter setup
root = ttk.Window(themename="superhero")
root.title("Universal Skin Mod Manager")
root.iconbitmap("controller.ico")

main_frame = ttk.Frame(root, padding="3 3 12 12")
main_frame.grid(column=0, row=0, padx=5, pady=5, sticky=(N, W, E, S))
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
main_frame.columnconfigure((1, 2, 3, 4), minsize=250)

# setup default example data for db and create local folders for the game paths
curr_path = f"{os.getcwd()}"
ex_applied_path = curr_path + "\\Example_Applied_Mods"
ex_stored_path = curr_path + "\\Example_Stored_Mods"
ex_modable_name = "Example_Modable_Char_or_Wep_etc"


if os.path.exists(curr_path + "\\usmm.db") == False:
    os.mkdir("Example_Applied_Mods")
    os.mkdir("Example_Stored_Mods")
    os.mkdir(os.path.join(ex_stored_path, ex_modable_name))

# sqlite3 db setup
con = sqlite3.connect("usmm.db")
cur = con.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS game(title, appliedPath, storePath)")

if cur.execute("SELECT 1 FROM game LIMIT 1").fetchone() == None:
    print(cur.execute("SELECT 1 FROM game LIMIT 1").fetchone() == None)
    cur.execute("INSERT INTO game VALUES (?, ?, ?)",
                    ("Example Title", ex_applied_path, ex_stored_path))
    con.commit()


# BUSINESS LOGIC
current_selected_game = []
current_selected_modable = ""


class Game:
    def __init__(self, title, applied_path, store_path):
        self.title = title
        self.applied_path = applied_path
        self.store_path = store_path

def add_game():
    title = game_t.get() #validate string
    applied_path = game_modables_path.get() #add validation for path and error dialog flow
    store_path = game_mods_path.get() #add validation for path and error dialog flow
    game = Game(title, applied_path, store_path)
    # print(vars(game))
    cur.execute("INSERT INTO game VALUES (?, ?, ?)",
                (title, applied_path, store_path))
    con.commit()
    game_list_lb.insert(ttk.END, game.title)
    return game
    # - may need to close the db connection at some point after committing but
    #  would have reopen later for other tasks potentially so not sure yet
    # con.close()
    # - clear form fields after submission or make a separate dialog that closes

def delete_game():
    print("delete game")

# write this function to fill in the entry fields of the add game form with paths
def browse_folder():
    folder_path = filedialog.askdirectory()
    if folder_path:
        print(folder_path)
        # entry.delete(0, tk.END)
        # entry.insert(0, folder_path)

def set_game_list():
    games_l_query = cur.execute("SELECT title FROM game").fetchall()
    game_list_b = []
    i = 0
    for game in games_l_query:
        game_list_b.insert(i, game[0])
        i += 1
    game_titles = ttk.Variable(value=game_list_b)
    return game_titles

# Returns a list of file paths for folders within the specified directory
def get_folder_paths(folder_path):
    paths = []
    for modable in os.scandir(folder_path):
        if modable.is_dir(): #after adding form validation should be able to remove condition
            paths.append(modable.path)
    return paths

def display_modables(selected_game=()):
    modables_list_lb.delete(0, ttk.END)
    mods_list_lb.delete(0, ttk.END)
    selected_game = game_list_lb.curselection()
    if selected_game == (): #consider whether this is still necessary if using default selection
        selected_title = game_list_lb.get(0)
    else:
        selected_title = game_list_lb.get(selected_game)
    game = cur.execute("SELECT storePath, appliedPath FROM game WHERE title=?", (selected_title,)).fetchone()
    modables = get_folder_paths(game[0])
    i = 0
    for modable in modables:
        modables_list_lb.insert(i, modable.rsplit("\\", 1)[-1])
        i += 1
    modables_list = ttk.Variable(value=modables_list_lb)
    global current_selected_game
    current_selected_game = game
    active_mods_display(current_selected_game[1])
    return modables_list

def refresh_modables():
    print("refresh please")

def display_mods(selected_modable=()):
    mods_list_lb.delete(0, ttk.END)
    selected_modable = modables_list_lb.curselection()
    if selected_modable == (): #consider whether this is still necessary if using default selection
        selected_modable = modables_list_lb.get(0)
    else:
        selected_modable = modables_list_lb.get(selected_modable)
    print(selected_modable)
    modable_path = f"{current_selected_game[0]}\\{selected_modable}"
    print(modable_path)
    mods = get_folder_paths(modable_path)
    i = 0
    for mod in mods:
        mods_list_lb.insert(i, mod.rsplit("\\", 1)[-1])
        i += 1
    mods_list = ttk.Variable(value=mods_list_lb)
    global current_selected_modable
    current_selected_modable = modable_path
    return mods_list
    
def activate_mod(mod=()):
    # print(current_selected_modable)
    active_path = current_selected_game[1]
    # print(active_path)
    mod_selection = mods_list_lb.curselection()
    mod = mods_list_lb.get(mod_selection[0])
    mod_path = f"{current_selected_modable}\\{mod}"
    print(mod_path)
    active = active_mod(current_selected_modable, active_path)
    print("**********")
    print(active)
    # stuff here to activate game by removing the currently active one and copying in the selected
    if os.path.exists(active):
        shutil.rmtree(active)
    else:
        print(active) # consider error handling
    destination_path = f"{active_path}\\{mod}"
    print("+++++++++++++")
    print(destination_path)
    shutil.copytree(mod_path, destination_path)
    active_mods_display(active_path)
    return "activated"


def active_mod(modables_path, active_mods_path):
    active_mod = "no active mod for modable"
    mod_folder_name = ""
    check_path = ""
    for mod in os.scandir(modables_path):
        mod_folder_name = mod.path.rsplit("\\", 1)[-1]
        check_path = f"{active_mods_path}\\{mod_folder_name}"
        if os.path.exists(check_path):
            active_mod = check_path
    return active_mod

def active_mods_display(active_mods_path):
    active_mods_list_lb.delete(0, ttk.END)
    mod_paths = get_folder_paths(active_mods_path)
    i = 0
    for path in mod_paths:
        active_mods_list_lb.insert(i, path.rsplit("\\", 1)[-1])
        i += 1
    mods_list = ttk.Variable(value=mods_list_lb)
    return mods_list

def deactivate_mod(event):
    print("deactive modable")

def display_mod_info(mod=()):
    print("mod info")



# DISPLAY CONTENT

# form to add game
# look into adding entry field validation
    # https://tkdocs.com/tutorial/widgets.html#entry:~:text=leads%20us%20to...-,Validation,-Users%20can%20type
add_game_frame = ttk.Frame(main_frame, padding="3 3 10 3")
add_game_frame.grid(column=1, row=4)
game_title_l = ttk.Label(add_game_frame, text='Game Title')
game_title_l.grid(column=1, sticky=(W), columnspan=2, row=1, padx=5, pady=5)
game_t = StringVar()
game_t = ttk.Entry(add_game_frame, textvariable=game_t) #add validatecommand= param with function
game_t.grid(column=1, row=2, padx=5, pady=5)
game_path_l = ttk.Label(add_game_frame, text='Path to Applied Mods Folder')
game_path_l.grid(column=1, sticky=(W), columnspan=2, row=3, padx=5, pady=1)
# add browse button option for entering path**
game_modables_path_browse_btn = ttk.Button(add_game_frame, text="Browse", command=browse_folder)
game_modables_path_browse_btn.grid(column=2, row=4, sticky=(W), pady=5)
game_modables_path = StringVar()
game_modables_path = ttk.Entry(add_game_frame, textvariable=game_modables_path) #add validatecommand= param with function
game_modables_path.grid(column=1, sticky=(E), row=4, padx=5, pady=5)
game_path_l = ttk.Label(add_game_frame, text='Path to Mod Storage Folder')
game_path_l.grid(column=1, sticky=(W), columnspan=2, row=5, padx=5, pady=1)
# add browse button option for entering path**
game_modable_mods_path_browse_btn = ttk.Button(add_game_frame, text="Browse", command=browse_folder)
game_modable_mods_path_browse_btn.grid(column=2, row=6, sticky=(W), pady=5)
game_mods_path = StringVar()
game_mods_path = ttk.Entry(add_game_frame, textvariable=game_mods_path) #add validatecommand= param with function
game_mods_path.grid(column=1, sticky=(E),row=6, padx=5, pady=5)
# submit form
    # use validation to enable the button when the form is correctly complete
b_add_game = ttk.Button(add_game_frame, text="Add Game", command=add_game)
b_add_game.grid(column=1, row=7, padx=5, pady=5)

# game list display
game_titles = set_game_list()
# game_frame = ttk.Frame(main_frame, padding="3 3 12 12")
# game_frame.grid()
game_list_l = ttk.Label(main_frame, text='Games')
game_list_l.grid(column=1, row=1, padx=5, pady=5)
game_list_lb = Listbox(main_frame, 
                       listvariable=game_titles, 
                       selectmode=SINGLE, 
                       height=10,
                       exportselection=False
                       )
game_list_lb.grid(column=1, row=2, padx=5, pady=5)
game_list_lb.selection_set(first=0)
game_list_lb.bind('<<ListboxSelect>>', display_modables)
remove_game = ttk.Button(main_frame, text="Remove Game", command=delete_game)
remove_game.grid(column=1, row=3, padx=5, pady=5, sticky=N)

# modable list display
modables_list = ttk.Variable(value=[])
modables_listl = ttk.Label(main_frame, text='Modable Assets (Char Skins, etc)')
modables_listl.grid(column=2, row=1, padx=5, pady=5)
modables_list_lb = Listbox(main_frame,
                           listvariable=modables_list,
                           selectmode=SINGLE,
                           height=10,
                           exportselection=False
                           )
modables_list_lb.grid(column=2, row=2, padx=5, pady=5)
modables_list_lb.selection_set(first=0)
modables_list_lb.bind('<<ListboxSelect>>', display_mods)
refresh_modables_b = ttk.Button(main_frame, text="Refresh List", command=refresh_modables)
refresh_modables_b.grid(column=2, row=3, padx=5, pady=5, sticky=N)

# mods for modable list display
mods_list = ttk.Variable(value=[])
mods_listl = ttk.Label(main_frame, text='Mods for Asset')
mods_listl.grid(column=3, row=1, padx=5, pady=5)
mods_list_lb = Listbox(main_frame,
                           listvariable=mods_list,
                           selectmode=SINGLE,
                           height=10,
                           exportselection=False
                           )
mods_list_lb.grid(column=3, row=2, padx=5, pady=5)
mods_list_lb.selection_set(first=0)
mods_list_lb.bind('<<ListboxSelect>>', display_mod_info)
activate_mod_b = ttk.Button(main_frame, text="Activate", command=activate_mod)
activate_mod_b.grid(column=3, row=3, padx=5, pady=5, sticky=NW)
deactivate_b = ttk.Button(main_frame, text="Deactivate", command=deactivate_mod)
deactivate_b.grid(column=3, row=3, padx=5, pady=5, sticky=NE)

# active mods for game list display
active_mods_list = ttk.Variable(value=[])
active_mods_list_l = ttk.Label(main_frame, text='Active Mods')
active_mods_list_l.grid(column=4, row=1, padx=5, pady=5)
active_mods_list_lb = Listbox(main_frame, 
                       listvariable=active_mods_list, 
                       selectmode=SINGLE, 
                       height=10,
                       exportselection=False
                       )
active_mods_list_lb.grid(column=4, row=2, padx=5, pady=5)
active_mods_list_lb.selection_set(first=0)
active_mods_list_lb.bind('<<ListboxSelect>>', display_mod_info)

root.mainloop()

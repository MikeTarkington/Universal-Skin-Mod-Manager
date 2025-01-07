import os
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

    # may need to close the db connection at some point after committing but
    #  would have reopen later for other tasks potentially so not sure yet
    # con.close()
    
    # how I might call on a particular game using its title:
    # game_query = cur.execute("""SELECT title, appliedPath, storePath 
    #                          FROM game WHERE title=?""", (title,))
    # print(game_query.fetchone())
    
    # need to update the game list page somehow to show the newly added game
    # clear form fields after submission or make a separate dialog that closes

# consider refactor to join with display_modables**
def set_game_list():
    games_l_query = cur.execute("SELECT title FROM game").fetchall()
    game_list_b = []
    i = 0 #consider refactor of insertions to use ttk.END insead of index
    for game in games_l_query:
        game_list_b.insert(i, game[0])
        i += 1
    game_titles = ttk.Variable(value=game_list_b)
    return game_titles

# Returns a list of file paths for folders within the specified directory
def get_modables_paths(folder_path):
    modables_paths = []
    for modable in os.scandir(folder_path):
        if modable.is_dir(): #after adding form validation should be able to remove condition
            modables_paths.append(modable.path)
    return modables_paths

def display_modables(selected_game=()):
    modables_list_lb.delete(0, ttk.END)
    selected_game = game_list_lb.curselection()
    if selected_game == (): #consider whether this is still necessary if we have default selection
        selected_title = game_list_lb.get(0)
    else:
        selected_title = game_list_lb.get(selected_game)
    print("*&*&*&*&*&*&*&")
    print(selected_game)
    print(selected_title)
    game = cur.execute("SELECT appliedPath FROM game WHERE title=?", (selected_title,)).fetchone()
    modables = get_modables_paths(game[0])
    i = 0 #consider refactor of insertions to use ttk.END insead of index
    for modable in modables:
        modables_list_lb.insert(i, modable.rsplit("\\", 1)[-1])
        i += 1
    print("*&*&*&*&*&*&*&")
    print(modables_list_lb)
    modables_list = ttk.Variable(value=modables_list_lb)
    return modables_list

def browse_folder():
    folder_path = filedialog.askdirectory()
    if folder_path:
        print(folder_path)
        # entry.delete(0, tk.END)
        # entry.insert(0, folder_path)



# DISPLAY CONTENT

# form to add game
# look into adding entry field validation
    # https://tkdocs.com/tutorial/widgets.html#entry:~:text=leads%20us%20to...-,Validation,-Users%20can%20type
add_game_frame = ttk.Frame(main_frame, padding="3 3 10 3")
add_game_frame.grid(column=1, row=3)
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
game_list_lb = Listbox(main_frame, listvariable=game_titles, selectmode=SINGLE, height=10)
game_list_lb.grid(column=1, row=2, padx=5, pady=5)
# click a game to show modables for that game in its corresponding listbox
game_list_lb.selection_set( first = 0 )
game_list_lb.bind('<<ListboxSelect>>', display_modables)

# modable list display
modables_list = ttk.Variable(value=[])
modables_listl = ttk.Label(main_frame, text='Assets (Char Skins, etc)')
modables_listl.grid(column=2, row=1, padx=5, pady=5)
modables_list_lb = Listbox(main_frame,
                           listvariable=modables_list,
                             selectmode=SINGLE, height=10)
modables_list_lb.grid(column=2, row=2, padx=5, pady=5)


root.mainloop()

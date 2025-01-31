import os
import shutil
import sqlite3
import configparser
from tkinter import *
from tkinter import filedialog
import ttkbootstrap as ttk
from ttkbootstrap import Style
from ttkbootstrap.constants import *
from PIL import ImageTk, Image

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
main_frame.grid(column=0, row=0, padx=10, pady=10, sticky=(N, W, E, S))
root.columnconfigure(0, weight=1, pad=10) 
root.rowconfigure(0, weight=1)
main_frame.columnconfigure(4, minsize=250)

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
    cur.execute("INSERT INTO game VALUES (?, ?, ?)",
                (title, applied_path, store_path))
    con.commit()
    game_list_lb.insert(ttk.END, game.title)
    game_t.delete(0, ttk.END)
    game_mods_path.delete(0, ttk.END)
    game_modables_path.delete(0, ttk.END)
    return game
    # - may need to close the db connection at some point after committing but
    #  would have reopen later for other tasks potentially so not sure yet
    # con.close()
    # - clear form fields after submission or make a separate dialog that closes

def delete_game(title=()):
    active_dir = current_selected_game[1]
    cur.execute("DELETE FROM game WHERE appliedPath=?", (active_dir,))
    con.commit()
    game_list_lb.delete(0, ttk.END)
    global game_titles
    game_titles = set_game_list()
    game_list_lb.config(listvariable=game_titles)
    modables_list_lb.delete(0, ttk.END)
    mods_list_lb.delete(0, ttk.END)
    active_mods_list_lb.delete(0, ttk.END)
    return f"{active_dir} deleted"


# write this function to fill in the entry fields of the add game form with paths
def browse_folder(entry):
    folder_path = filedialog.askdirectory()
    if folder_path:
        entry.delete(0, ttk.END)
        entry.insert(0, folder_path)

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

def display_mods(selected_modable=()):
    mods_list_lb.delete(0, ttk.END)
    selected_modable = modables_list_lb.curselection()
    if selected_modable == (): #consider whether this is still necessary if using default selection
        selected_modable = modables_list_lb.get(0)
    else:
        selected_modable = modables_list_lb.get(selected_modable)
    modable_path = f"{current_selected_game[0]}\\{selected_modable}"
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
    active_path = current_selected_game[1]
    mod_selection = mods_list_lb.curselection()
    mod = mods_list_lb.get(mod_selection[0])
    mod_path = f"{current_selected_modable}\\{mod}"
    active = active_mod(current_selected_modable, active_path)
    if os.path.exists(active):
        shutil.rmtree(active)
    else:
        print(active) # consider error handling
    destination_path = f"{active_path}\\{mod}"
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

def deactivate_mod(event=()):
    active_path = current_selected_game[1]
    active = active_mod(current_selected_modable, active_path)
    if os.path.exists(active):
        shutil.rmtree(active)
        active_mods_display(active_path)
    else:
        print("unable to deactivate") # consider error handling
    return f"deactivated {active}"
    
def add_mod_info(mod=()):
    mod_selection = mods_list_lb.curselection()
    mod = mods_list_lb.get(mod_selection[0])
    mod_path = f"{current_selected_modable}\\{mod}"
    url = mod_url.get()
    notes = mod_notes.get("1.0", "end-1c")
    mod_info_config = configparser.ConfigParser()
    mod_info_config['Mod Info'] = {'URL': url, 'Notes': notes}
    with open(f"{mod_path}\\usmm_mod_info.ini", 'w') as configfile:
        mod_info_config.write(configfile)

def display_mod_info(mod=()):
    # read stored ini file for the selected mod from modables or active list
    mod_selection = mods_list_lb.curselection()
    mod = mods_list_lb.get(mod_selection[0])
    mod_path = f"{current_selected_modable}\\{mod}"
    global mod_url, mod_notes
    mod_url.delete(0, ttk.END)
    mod_notes.delete("1.0", "end-1c")
    # add some conditional logic to prevent KeError when no ini file is present
    mod_info_config = configparser.ConfigParser()
    mod_info_config.read(f"{mod_path}\\usmm_mod_info.ini")
    url = mod_info_config['Mod Info']['URL']
    notes = mod_info_config['Mod Info']['Notes']
    mod_url.insert(0, url)
    mod_notes.insert("1.0", notes)
    preview_image()
    return mod_info_config

def preview_image(mod=()):
    mod_selection = mods_list_lb.curselection()
    global mod_preview_img
    mod = mods_list_lb.get(mod_selection[0])
    mod_path = f"{current_selected_modable}\\{mod}"
    if os.path.exists(f"{mod_path}\\preview.jpg") == False:
        print("default image")
        img = Image.open("controller.ico")
        mod_preview_img = ImageTk.PhotoImage(img, size=(50, 50))
        mod_img_lb.config(image=mod_preview_img)
    else:
        print("image preview rather than default")
        img = Image.open(f"{mod_path}\\preview.jpg")
        mod_preview_img = ImageTk.PhotoImage(img, size=(50, 50))
        mod_img_lb.config(image=mod_preview_img)
    return mod_preview_img


# DISPLAY CONTENT

# form to add game
# look into adding entry field validation
    # https://tkdocs.com/tutorial/widgets.html#entry:~:text=leads%20us%20to...-,Validation,-Users%20can%20type
ttk.Style().configure("control_frame.TFrame", relief="solid", border=1, bordercolor="#3e5059")
add_game_frame = ttk.Frame(main_frame, padding="20 20 20 20", style="control_frame.TFrame")
add_game_frame.grid(column=1, row=4, sticky=W, padx=10, pady=10)
game_title_l = ttk.Label(add_game_frame, text='Game Title')
game_title_l.grid(column=1, sticky=(W), columnspan=2, row=1, padx=5, pady=5)
game_t = StringVar()
game_t = ttk.Entry(add_game_frame, textvariable=game_t) #add validatecommand= param with function
game_t.grid(column=1, row=2, padx=5, pady=5)
game_path_l = ttk.Label(add_game_frame, text='Path to Applied Mods Folder')
game_path_l.grid(column=1, sticky=(W), columnspan=2, row=3, padx=5, pady=1)
# add browse button option for entering path**
game_modables_path_browse_btn = ttk.Button(add_game_frame, text="Browse",
                                           command= lambda: browse_folder(game_modables_path)
                                           )
game_modables_path_browse_btn.grid(column=2, row=4, sticky=(W), pady=5)
game_modables_path = StringVar()
game_modables_path = ttk.Entry(add_game_frame, textvariable=game_modables_path) #add validatecommand= param with function
game_modables_path.grid(column=1, sticky=(E), row=4, padx=5, pady=5)
game_path_l = ttk.Label(add_game_frame, text='Path to Mod Storage Folder')
game_path_l.grid(column=1, sticky=(W), columnspan=2, row=5, padx=5, pady=1)
# add browse button option for entering path**
game_modable_mods_path_browse_btn = ttk.Button(add_game_frame, text="Browse", command=lambda: browse_folder(game_mods_path))
game_modable_mods_path_browse_btn.grid(column=2, row=6, sticky=(W), pady=5)
game_mods_path = StringVar()
game_mods_path = ttk.Entry(add_game_frame, textvariable=game_mods_path) #add validatecommand= param with function
game_mods_path.grid(column=1, sticky=(E),row=6, padx=5, pady=5)
# submit form
    # use validation to enable the button when the form is correctly complete
b_add_game = ttk.Button(add_game_frame, text="Add Game", command=add_game)
b_add_game.grid(column=1, row=7, padx=5, pady=5)

# game list display
control_frame = ttk.Frame(main_frame, padding="20 20 20 20", style="control_frame.TFrame")
control_frame.grid(column=1, row=1, columnspan=3)
game_titles = set_game_list()
game_list_l = ttk.Label(control_frame, text='Games')
game_list_l.grid(column=1, row=1, padx=5, pady=5)
game_list_lb = Listbox(control_frame, 
                       listvariable=game_titles, 
                       selectmode=SINGLE, 
                       height=10,
                       exportselection=False
                       )
game_list_lb.grid(column=1, row=2, padx=5, pady=5)
game_list_lb.selection_set(first=0)
game_list_lb.bind('<<ListboxSelect>>', display_modables)
remove_game = ttk.Button(control_frame, text="Remove Game", command=delete_game)
remove_game.grid(column=1, row=3, padx=5, pady=5, sticky=N)

# modable list display
modables_list = ttk.Variable(value=[])
modables_listl = ttk.Label(control_frame, text='Modable Assets (Char Skins, etc)')
modables_listl.grid(column=2, row=1, padx=5, pady=5)
modables_list_lb = Listbox(control_frame,
                           listvariable=modables_list,
                           selectmode=SINGLE,
                           height=10,
                           exportselection=False
                           )
modables_list_lb.grid(column=2, row=2, padx=5, pady=5)
modables_list_lb.selection_set(first=0)
modables_list_lb.bind('<<ListboxSelect>>', display_mods)
refresh_modables_b = ttk.Button(control_frame, text="Refresh List", command=display_modables)
refresh_modables_b.grid(column=2, row=3, padx=5, pady=5, sticky=N)

# mods for modable list display
mods_list = ttk.Variable(value=[])
mods_listl = ttk.Label(control_frame, text='Mods for Asset')
mods_listl.grid(column=3, row=1, padx=5, pady=5)
mods_list_lb = Listbox(control_frame,
                           listvariable=mods_list,
                           selectmode=SINGLE,
                           height=10,
                           exportselection=False
                           )
mods_list_lb.grid(column=3, row=2, padx=5, pady=5)
mods_list_lb.selection_set(first=0)
mods_list_lb.bind('<<ListboxSelect>>', display_mod_info)
activate_mod_b = ttk.Button(control_frame, text="Activate", command=activate_mod)
activate_mod_b.grid(column=3, row=3, padx=5, pady=5, sticky=NW)
deactivate_b = ttk.Button(control_frame, text="Deactivate", command=deactivate_mod)
deactivate_b.grid(column=3, row=3, padx=5, pady=5, sticky=NE)

# active mods for game list display
active_games_frame = ttk.Frame(main_frame, padding="20 20 20 20", style="control_frame.TFrame")
active_games_frame.grid(column=4, row=1, padx=10, pady=10)
active_mods_list = ttk.Variable(value=[])
active_mods_list_l = ttk.Label(active_games_frame, text='Active Mods')
active_mods_list_l.grid(column=1, row=1, padx=5, pady=5, sticky=N)
active_mods_list_lb = Listbox(active_games_frame, 
                       listvariable=active_mods_list, 
                       selectmode=SINGLE, 
                       height=10,
                       exportselection=False,
                       )
active_mods_list_lb.grid(column=1, row=2, padx=5, pady=5)
active_mods_list_lb.selection_set(first=0)
active_mods_list_lb.bind('<<ListboxSelect>>', display_mod_info)

# mod info form
add_mod_inf = ttk.Frame(main_frame, padding="20 20 20 20", style="control_frame.TFrame")
add_mod_inf.grid(column=2, row=4, sticky=W, padx=10, pady=10)
mod_url_l = ttk.Label(add_mod_inf, text='Mod URL')
mod_url_l.grid(column=1, sticky=(W), row=1, padx=5, pady=5)
mod_url = StringVar()
mod_url = ttk.Entry(add_mod_inf, textvariable=mod_url) #add validatecommand= param with function
mod_url.grid(column=1, row=2, padx=5, pady=5)
mod_notes_add_l = ttk.Label(add_mod_inf, text='Notes (toggles, etc)')
mod_notes_add_l.grid(column=1, sticky=(W), row=3, padx=5, pady=1)
mod_notes = StringVar()
mod_notes = ttk.Text(add_mod_inf, width=25, height=10) #add validatecommand= param with function
mod_notes.grid(column=1, row=4, padx=5, pady=5)
# submit form
    # use validation to enable the button when the form is correctly complete
b_add_mod_info = ttk.Button(add_mod_inf, text="Save Mod Info", command=add_mod_info)
b_add_mod_info.grid(column=1, row=7, padx=5, pady=5)

# mod preview image display
mod_img_frame = ttk.Frame(main_frame, padding="20 20 20 20", style="control_frame.TFrame")
mod_img_frame.grid(column=3, row=4, sticky=W, padx=10, pady=10)
mod_img_l = ttk.Label(mod_img_frame, text='Mod Image')
mod_img_l.grid(column=1, sticky=(W), row=1, padx=5, pady=5)
mod_default_preview_img = Image.open("controller.ico")
mod_preview_img = ImageTk.PhotoImage(mod_default_preview_img, size=(50, 50))
mod_img_lb = ttk.Label(mod_img_frame, image=mod_preview_img)
mod_img_lb.grid(column=1, row=2, padx=5, pady=5)

root.mainloop()

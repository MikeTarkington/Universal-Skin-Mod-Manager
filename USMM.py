import os
import shutil
import sqlite3
import re
import configparser
from tkinter import *
from tkinter import filedialog
import ttkbootstrap as ttk
from ttkbootstrap import Style
from ttkbootstrap.constants import *
from PIL import ImageTk, Image


# tkinter setup
root = ttk.Window(themename="superhero")
root.title("Universal Skin Mod Manager")
root.iconbitmap("controller.ico")

main_frame = ttk.Frame(root, padding="10 10 10 10")
main_frame.grid(column=0, row=0, padx=10, pady=10, sticky=(N, W, E, S))
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

def check_game_form():
    if game_t.get() and game_modables_path.get() and game_mods_path.get():
        b_add_game.config(state="normal")
    else:
        b_add_game.config(state="disabled")

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
    check_game_form()
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

def browse_folder(entry):
    folder_path = filedialog.askdirectory()
    if folder_path:
        entry.delete(0, ttk.END)
        entry.insert(0, folder_path)
    check_game_form()
    return folder_path

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
    b_add_mod_info.config(state="disabled")
    activate_mod_b.config(state="disabled")
    deactivate_b.config(state="disabled")
    explore_modable.config(state="disabled")
    explore_mod.config(state="disabled")
    explore_storage.config(state="normal")
    explore_applied.config(state="normal")
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
    b_add_mod_info.config(state="disabled")
    activate_mod_b.config(state="disabled")
    deactivate_b.config(state="normal")
    explore_mod.config(state="disabled")
    explore_modable.config(state="normal")
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
    return "mod info saved"

def display_mod_info(mod=()):
    b_add_mod_info.config(state="normal")
    activate_mod_b.config(state="normal")
    deactivate_b.config(state="normal")
    explore_mod.config(state="normal")
    mod_selection = mods_list_lb.curselection()
    mod = mods_list_lb.get(mod_selection[0])
    mod_path = f"{current_selected_modable}\\{mod}"
    global mod_url, mod_notes
    mod_url.delete(0, ttk.END)
    mod_notes.delete("1.0", "end-1c")
    # add some conditional logic to prevent KeyError when no ini file is present
    if os.path.exists(f"{mod_path}\\usmm_mod_info.ini"):        
        mod_info_config = configparser.ConfigParser()
        mod_info_config.read(f"{mod_path}\\usmm_mod_info.ini")
        url = mod_info_config['Mod Info']['URL']
        notes = mod_info_config['Mod Info']['Notes']
        mod_url.insert(0, url)
        mod_notes.insert("1.0", notes)
    preview_image()
    return [mod_url, mod_notes]

def preview_image(mod=()):
    mod_selection = mods_list_lb.curselection()
    global mod_preview_img
    mod = mods_list_lb.get(mod_selection[0])
    mod_path = f"{current_selected_modable}\\{mod}"
    img_found = False
    ext = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"]
    for e in ext:
        if os.path.exists(f"{mod_path}\\preview{e}"):
            img = Image.open(f"{mod_path}\\preview{e}")
            img.thumbnail((500, 500))
            mod_preview_img = ImageTk.PhotoImage(img)
            mod_img_lb.config(image=mod_preview_img)
            img_found = True
            break
    if img_found == False:
        img = Image.open("defaultpreview.jpg")
        img.thumbnail((500, 500))
        mod_preview_img = ImageTk.PhotoImage(img)
        mod_img_lb.config(image=mod_preview_img)
    return mod_preview_img

def explore_folder(path_type):
    if path_type == "storage":
        path = current_selected_game[0]
    elif path_type == "applied":
        path = current_selected_game[1]
    elif path_type == "modable":
        path = current_selected_modable
    elif path_type == "mod":
        mod_selection = mods_list_lb.curselection()
        mod = mods_list_lb.get(mod_selection[0])
        path = f"{current_selected_modable}\\{mod}"
    else:
        print("invalid path type")
    os.startfile(path)
    return f"{path} opened"


# DISPLAY CONTENT

# style for the control frame
ttk.Style().configure("control_frame.TFrame", relief="solid", border=1, bordercolor="#3e5059")
ttk.Style().configure("main_btn.TButton", background="teal")
ttk.Style().configure("alt_btn.TButton", background="slateblue")
ttk.Style().configure("dull_btn.TButton", background="gray")

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
                        width=28,
                        exportselection=False
                       )
game_list_lb.grid(column=1, row=2, padx=5, pady=5)
game_list_lb.selection_set(first=0)
game_list_lb.bind('<<ListboxSelect>>', display_modables)
remove_game = ttk.Button(control_frame, text="Remove Game", style="dull_btn.TButton", command=delete_game)
remove_game.grid(column=1, row=3, padx=5, pady=5, sticky=N)

# modable list display
modables_list = ttk.Variable(value=[])
modables_listl = ttk.Label(control_frame, text='Modable Assets (Char Skins, etc)')
modables_listl.grid(column=2, row=1, padx=5, pady=5)
modables_list_lb = Listbox(control_frame,
                            listvariable=modables_list,
                            selectmode=SINGLE,
                            height=10,
                            width=28,
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
                           width=28,
                           exportselection=False
                           )
mods_list_lb.grid(column=3, row=2, padx=5, pady=5)
mods_list_lb.selection_set(first=0)
mods_list_lb.bind('<<ListboxSelect>>', display_mod_info)
activate_mod_b = ttk.Button(control_frame, text="Activate", style="main_btn.TButton", command=activate_mod)
activate_mod_b.grid(column=3, row=3, padx=5, pady=5, sticky=NW)
activate_mod_b.config(state="disabled")
deactivate_b = ttk.Button(control_frame, text="Deactivate", command=deactivate_mod)
deactivate_b.grid(column=3, row=3, padx=5, pady=5, sticky=NE)
deactivate_b.config(state="disabled")

# active mods for game list display
active_games_frame = ttk.Frame(main_frame, padding="20 20 20 20", style="control_frame.TFrame")
active_games_frame.grid(column=4, row=1, padx=10, pady=10)
active_mods_list = ttk.Variable(value=[])
active_mods_list_l = ttk.Label(active_games_frame, text='Active Mods')
active_mods_list_l.grid(column=1, row=1, padx=5, pady=5, sticky=N)
active_mods_list_lb = Listbox(active_games_frame, 
                       listvariable=active_mods_list, 
                       selectmode=SINGLE, 
                       height=12,
                       width=28,
                       exportselection=False
                       )
active_mods_list_lb.grid(column=1, row=2, padx=5, pady=5)
active_mods_list_lb.selection_set(first=0)
active_mods_list_lb.bind('<<ListboxSelect>>', display_mod_info) #give an argument to display mod info from active vs storage?

# utility buttons
utility_frame = ttk.Frame(main_frame, padding="20 10 20 10", style="control_frame.TFrame")
utility_frame.grid(column=1, row=4, sticky=N, padx=10, pady=10)
utility_frame.columnconfigure(0, weight=1)
utility_frame.rowconfigure(0, weight=1)
utility_btn_l = ttk.Label(utility_frame, text='Explore Selection Folders')
utility_btn_l.grid(column=1, row=1, sticky=EW)
explore_storage = ttk.Button(utility_frame,
                            text="Game Mod Storage",
                            style="alt_btn.TButton",
                            command= lambda: explore_folder("storage")
                            )
explore_storage.grid(column=1, row=2, sticky=EW, pady=5)
explore_storage.config(width=28, state="disabled")
explore_applied = ttk.Button(utility_frame,
                             text="Game Applied Mods",
                             style="alt_btn.TButton",
                             command= lambda: explore_folder("applied")
                             )
explore_applied.grid(column=1, row=3, sticky=EW, pady=5)
explore_applied.config(width=28, state="disabled")
explore_modable = ttk.Button(utility_frame,
                             text="Modable Asset Storage",
                             style="alt_btn.TButton",
                             command= lambda: explore_folder("modable")
                             )
explore_modable.grid(column=1, row=4, sticky=EW, pady=5)
explore_modable.config(width=28, state="disabled")
explore_mod = ttk.Button(utility_frame,
                         text="Mod",
                         style="alt_btn.TButton",
                         command= lambda: explore_folder("mod")
                         )
explore_mod.grid(column=1, row=5, sticky=EW, pady=5)
explore_mod.config(width=28, state="disabled")

# add game form
add_game_frame = ttk.Frame(main_frame, padding="20 10 20 10", style="control_frame.TFrame")
add_game_frame.grid(column=1, row=4, sticky=SW, padx=10, pady=10)
game_title_l = ttk.Label(add_game_frame, text='Game Title')
game_title_l.grid(column=1, sticky=W, columnspan=2, row=1, padx=5, pady=5)
game_t = StringVar()
game_t = ttk.Entry(add_game_frame, textvariable=game_t) #add validatecommand= param with function
game_t.grid(column=1, row=2, padx=5, pady=5)
# game_t.bind("<KeyRelease>", lambda e: check_game_form())
game_path_l = ttk.Label(add_game_frame, text='Path to Applied Mods Folder')
game_path_l.grid(column=1, sticky=W, columnspan=2, row=3, padx=5, pady=1)
game_modables_path_browse_btn = ttk.Button(add_game_frame,
                                           text="Browse",
                                           command= lambda: browse_folder(game_modables_path)
                                           )
game_modables_path_browse_btn.grid(column=2, row=4, sticky=W, pady=5)
game_modables_path = StringVar()
game_modables_path = ttk.Entry(add_game_frame, textvariable=game_modables_path) #add validatecommand= param with function
game_modables_path.grid(column=1, sticky=E, row=4, padx=5, pady=5)
# game_modables_path.bind("<KeyRelease>", lambda e: check_game_form())
game_path_l = ttk.Label(add_game_frame, text='Path to Mod Storage Folder')
game_path_l.grid(column=1, sticky=W, columnspan=2, row=5, padx=5, pady=1)
game_modable_mods_path_browse_btn = ttk.Button(add_game_frame, text="Browse", 
                                               command=lambda: browse_folder(game_mods_path)
                                               )
game_modable_mods_path_browse_btn.grid(column=2, row=6, sticky=W, pady=5)
game_mods_path = StringVar()
game_mods_path = ttk.Entry(add_game_frame, textvariable=game_mods_path) #add validatecommand= param with function
game_mods_path.grid(column=1, sticky=E,row=6, padx=5, pady=5)
# game_mods_path.bind("<KeyRelease>", lambda e: check_game_form())
# submit form
    # use validation to enable the button when the form is correctly complete
b_add_game = ttk.Button(add_game_frame, text="Add Game", style="main_btn.TButton", command=add_game)
b_add_game.grid(column=1, row=7, padx=5, pady=5)
b_add_game.config(state="disabled")

# mod info form
add_mod_inf = ttk.Frame(main_frame, padding="20 20 20 20", style="control_frame.TFrame")
add_mod_inf.grid(column=2, row=4, sticky=W, padx=10, pady=10)
mod_url_l = ttk.Label(add_mod_inf, text='Mod URL')
mod_url_l.grid(column=1, sticky=W, row=1, padx=5, pady=5)
mod_url = StringVar()
mod_url = ttk.Entry(add_mod_inf, textvariable=mod_url) #add validatecommand= param with function
mod_url.grid(column=1, row=2, sticky=W, padx=5, pady=5)
mod_notes_add_l = ttk.Label(add_mod_inf, text='Notes (toggles, etc)')
mod_notes_add_l.grid(column=1, sticky=W, row=3, padx=5, pady=1)
mod_notes = StringVar()
mod_notes = ttk.Text(add_mod_inf, width=25, height=14, wrap=ttk.WORD) #add validatecommand= param with function
mod_notes.grid(column=1, row=4, padx=5, pady=5)
# submit form
    # use validation to enable the button when the form is correctly complete
b_add_mod_info = ttk.Button(add_mod_inf, text="Save Mod Info", style="main_btn.TButton", command=add_mod_info)
b_add_mod_info.grid(column=1, row=7, padx=5, pady=5)
b_add_mod_info.config(state="disabled")

# mod preview image display
mod_img_frame = ttk.Frame(main_frame, padding="20 20 20 20", style="control_frame.TFrame")
mod_img_frame.grid(column=3, columnspan=3, row=4, sticky=W, padx=10, pady=10)
mod_img_frame.columnconfigure(1, weight=1, minsize=501)
mod_img_frame.rowconfigure(2, weight=1, minsize=501)
mod_img_l = ttk.Label(mod_img_frame, text='Mod Preview Image')
mod_img_l.grid(column=1, sticky=(N, W, E, S), row=1, padx=5, pady=5)
mod_default_preview_img = Image.open("defaultpreview.jpg")
mod_default_preview_img.thumbnail((500, 500))
mod_preview_img = ImageTk.PhotoImage(mod_default_preview_img)
mod_img_lb = ttk.Label(mod_img_frame, image=mod_preview_img)
mod_img_lb.grid(column=1, row=2)

root.mainloop()

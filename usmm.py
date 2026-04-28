import extractor
import logging
import logging.config

import os
import shutil
import sqlite3
import re
import json
import webbrowser
import threading
import functools
import traceback
import mimetypes
# import send2trash
from pythonjsonlogger.json import JsonFormatter
from urllib.parse import urlparse
from pathlib import Path
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap import Style
from ttkbootstrap.constants import *
from PIL import ImageTk, Image

# Note to self: Command to bundle exe was `pyinstaller --onefile --windowed --hidden-import=pythonjsonlogger usmm.py`

# potential additional "nice-to-have" features
# - script runner that can target a specific directory, storage, modable, mod, active
# - explore potential api integrations for gamebanana and nexusmods
# - copy readme content to mod info notes by default?
# - custom template creation to switch between mod sets
# - storage of mods in archives for a bit of space saving and ease of use
# - store config for last selected game and modable etc
# - mod versioning and update checking
# - confict checking for active mods
# - mod reload integration for games that support it?
# - option to handle mods of various file types rather than just folders ie .pak, .zip, etc (remove requirement that a mod in the asset list be a dir path? get_folder_paths())
#   - for this to work might be good to add a parameter to the game class that would indicate the mod file/folder type
#   - consider that some games are modded by having files unpacked into a dir where they are overwritten so perhaps we store a backup of the originals and a record of unpacked files in order to remove them on deactivation
# - cycle through lists with up/down arrow keypress?
# - is there a way to save toggled configs into storage?

# ISSUES DISCOVERED FROM USAGE
# - button to add mod info section from readme
# - button to open mod info json file in default text editor
# - add edit game functionality similar to saving mod info where the form fields are populataed or by having a button and dialog popup for the form instead
# - find better way to adjust image size to  cell so that proportions of are maintained or consider setting image sizes based on screen resolution
# - consider scaling UI based on screen resolution?
# - frames in bottom row same height and N alignment
# - investigate issue of game not having its storage or applied mods folder sizes shown in the status bar (inspect the db on main system)
# - active mods list box might need fixed size matching the main control frame
# - deactivate/reactivate all button for active mods getting fresh versions from storage?
# DONE - when activating a mod that is already active, it seems the progress bar is stuck and that perhaps the mod is deactivated but not properly activated... investigate and allow for reactivating of a mod
# DONE - logging for debugging
# DONE - make sure that if game folders are moved or deleted it doesn't break operations such as displaying active or stored mods and deleting games... os.path.exists() might be a good option. ensure titles are unique and use them for deletions?
# DONE(changed to json)- ensure ini file edits are taken as string values or at least not able to affect the code. Receiving errors blocking saves when using some unusual characters like "down arrow" or ":""
# DONE - storage space consumption display
    # DONE - write myself a script to convert all ini files by the name usmm_mod_info.ini under a certain directory, and its sub ini file to json
# DONE - stop the "open" button from opening another isntance of the app when there is no URL
# DONE - refresh button for "mods for asset" list
# DONE- refresh and deactivate buttons get disabled when selecting from active mod list but not renabled when selecting from mods list
# DONE - add confirmation popup when someone clicks "remove game"
# DONE - indicate active mod in the "mods for asset" list (hightlight when box is in focus?, edit the title to say "ACTIVE"?)
# DONE - show progress bar for local actions of the app
# DONE - show message for confirmation of actions outcome next to progress bar
# DONE - when mod is activated highlight it in the active list?  NOT IMPORTANT NOW SINCE "ACTIVE" moves it to top due to alpha ordering

# setup logging with json configs and non-blocking handlers added via decorator
with open('logging_config.json', 'r') as f:
    logging_config = json.load(f)
logging.config.dictConfig(logging_config)
logger = logging.getLogger()

def log_this(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            threading.Thread(target=logger.info, args=(f"Running {func.__name__}",)).start()
            return func(*args, **kwargs)
        except Exception as e:
            threading.Thread(
                target=logger.error, args=(
                    f"Exception in {func.__name__}: {e}\n{traceback.format_exc()}",
                    )
                ).start()
            raise

    return wrapper

# Function to center the window after its widgets have determined its natural size
def center_and_finalize_window(window, parent=None):
    """
    Calculates the required size of the window using its layout managers (pack/grid) 
    and then centers it on the screen.
    """
    # 1. Force the window to calculate its natural size based on its contents (Pass 1)
    # We must run an update/update_idletasks to ensure layout managers have done their job.
    window.update_idletasks() 
    
    # 2. Get the size determined by the layout manager
    window_width = window.winfo_reqwidth()
    window_height = window.winfo_reqheight()

    # 3. Get screen dimensions
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    # 4. Calculate center coordinates
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2

    # 5. Set the final geometry (This repositions it without destroying the content)
    window.geometry(f'{window_width}x{window_height}+{x}+{y}')
    window.lift() # Bring to front

# tkinter setup
root = ttk.Window(themename="superhero")
root.title("Universal Skin Mod Manager")
root.iconbitmap("controller.ico")
root.resizable(False, False)
main_frame = ttk.Frame(root, padding="10 10 10 10")
main_frame.grid(column=0, row=0, padx=10, pady=10, sticky=(N, W, E, S))
main_frame.columnconfigure(4, minsize=250)
main_frame.rowconfigure(4, minsize=250)
main_frame.rowconfigure(5, weight=0)

# setup default example data for db with local folders for the game paths
curr_path = f"{os.getcwd()}"
ex_applied_path = curr_path + "\\Example_Applied_Mods-can-delete"
ex_stored_path = curr_path + "\\Example_Stored_Mods-can-delete"

# sqlite3 db setup
con = sqlite3.connect("usmm.db")
cur = con.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS game(title, appliedPath, storePath)")

if cur.execute("SELECT 1 FROM game LIMIT 1").fetchone() == None:
    cur.execute("INSERT INTO game VALUES (?, ?, ?)",
                    ("Example Title *CLICK* (remove when done)", ex_applied_path, ex_stored_path))
    con.commit()
cur.close()

# BUSINESS LOGIC
current_selected_game = []
current_selected_modable = ""

class Game:
    def __init__(self, title, applied_path, store_path):
        self.title = title
        self.applied_path = applied_path
        self.store_path = store_path

@log_this
def save_game(modal):
    con = sqlite3.connect("usmm.db")
    cur = con.cursor()
    check_game_form()
    title = game_t.get()
    applied_path = game_modables_path.get()
    store_path = game_mods_path.get()
    if game_validation():
        game = Game(title, applied_path, store_path)
        cur.execute("INSERT INTO game VALUES (?, ?, ?)",
                    (title, applied_path, store_path))
        con.commit()
        game_title = game.title
        game_list_lb.delete(0, ttk.END)
        global game_titles
        game_titles = set_game_list()
        game_list_lb.config(listvariable=game_titles)
        game_t.set("")
        game_mods_path.delete(0, ttk.END)
        game_modables_path.delete(0, ttk.END)
    con.close()

    modal.event_generate("<<CloseAddGameModal>>")

    return f"{game_title} added/updated"

def check_game_form():
    if game_t.get() and game_modables_path.get() and game_mods_path.get():
        b_add_game.config(state="normal")
    else:
        b_add_game.config(state="disabled")

def game_validation():
    # if i keep validation for title being unique, i don't think i need to have 
        # the db connect again, rather i can pass arguments to the validation
        # function when i call it to use the same db connection otherwise there
        # might be threading issues with sqlite
    # con = sqlite3.connect("usmm.db")
    # cur = con.cursor()
    # game = cur.execute("SELECT title FROM game WHERE title=?", (game_t.get(),)).fetchone()
    # con.close()
    if len(game_t.get()[0]) < 1:
        msg = "Game title must be at least 1 character"
        show_error(msg)
    # elif game != None:
    #     msg = "Game title already exists"
    #     show_error(msg)
    elif os.path.exists(game_modables_path.get()) == False:
        msg = "Path to Applied Mods Folder does not exist"
        show_error(msg)
    elif os.path.exists(game_mods_path.get()) == False:
        msg = "Path to Mod Storage Folder does not exist"
        show_error(msg)
    else:
        return True

def show_error(msg):
    messagebox.showerror("Error", msg, icon="error")

@log_this
def display_game_info():
    con = sqlite3.connect("usmm.db")
    cur = con.cursor()
    title = game_list_lb.get(game_list_lb.curselection())
    cur.execute("SELECT * FROM game WHERE title=?", (title,))
    game = cur.fetchone()
    con.close()
    set_game_list()

@log_this
def delete_game(title=()):
    con = sqlite3.connect("usmm.db")
    cur = con.cursor()
    title = game_list_lb.get(game_list_lb.curselection())
    if messagebox.askyesno("Delete Game", f"Delete {title} from USMM?"):
        # active_dir = current_selected_game[1]
        cur.execute("DELETE FROM game WHERE title=?", (title,))
        con.commit()
        game_list_lb.delete(0, ttk.END)
        global game_titles
        game_titles = set_game_list()
        game_list_lb.config(listvariable=game_titles)
        modables_list_lb.delete(0, ttk.END)
        mods_list_lb.delete(0, ttk.END)
        active_mods_list_lb.delete(0, ttk.END)
    else:
        return "game deletion cancelled"
    con.close()
    return f"{title} removed from USMM"

def browse_folder(entry):
    folder_path = filedialog.askdirectory()
    if folder_path:
        entry.delete(0, ttk.END)
        entry.insert(0, folder_path)
    check_game_form()
    return folder_path

@log_this
def set_game_list():
    con = sqlite3.connect("usmm.db")
    cur = con.cursor()
    games_l_query = cur.execute("SELECT title FROM game ORDER BY title").fetchall()
    game_list_b = []
    i = 0
    for game in games_l_query:
        game_list_b.insert(i, game[0])
        i += 1
    game_titles = ttk.Variable(value=game_list_b)
    con.close()
    return game_titles

@log_this
def display_modables(selected_game=()):
    display_game_info()
    modables_list_lb.delete(0, ttk.END)
    mods_list_lb.delete(0, ttk.END)
    clear_mod_info()
    add_mod_info_b.config(state="disabled")
    activate_mod_b.config(state="disabled")
    refresh_mods_b.config(state="disabled")
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
    con = sqlite3.connect("usmm.db")
    cur = con.cursor()
    game = cur.execute("SELECT storePath, appliedPath FROM game WHERE title=?", (selected_title,)).fetchone()
    con.close()
    if path_exists(game[0]):
        modables = get_folder_paths(game[0])
        i = 0
        for modable in modables:
            modables_list_lb.insert(i, modable.rsplit("\\", 1)[-1])
            i += 1
        modables_list = ttk.Variable(value=modables_list_lb)
        global current_selected_game
        current_selected_game = game
        active_mods_display(current_selected_game[1])
        explore_storage.config(text=f"Game Storage: {get_dir_size_in_mb(current_selected_game[0])}")
        explore_applied.config(text=f"Applied: {get_dir_size_in_mb(current_selected_game[1])}")
        explore_modable.config(text=f"Modable: NA")
        explore_mod.config(text=f"Mod: NA")
    return modables_list

def get_folder_paths(folder_path):
    paths = []
    for f in os.scandir(folder_path):
        if f.is_dir():
            paths.append(f.path)
    return paths

@log_this
def display_mods(selected_modable=()):
    mods_list_lb.delete(0, ttk.END)
    clear_mod_info()
    add_mod_info_b.config(state="disabled")
    activate_mod_b.config(state="disabled")
    refresh_mods_b.config(state="normal")
    deactivate_b.config(state="normal")
    explore_mod.config(state="disabled")
    explore_modable.config(state="normal")
    add_mod_b.config(state="normal")
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
    explore_modable.config(text=f"Modable Storage: {get_dir_size_in_mb(modable_path)}")
    explore_mod.config(text=f"Mod: NA")
    return mods_list

@log_this
def activate_mod(mod=()):
    remove_active_tag()
    active_path = current_selected_game[1]
    mod_selection = mods_list_lb.curselection()
    mod = mods_list_lb.get(mod_selection[0])
    if mod.startswith("ACTIVE-"):
        mod = mod[len("ACTIVE-"):]
    mod_path = f"{current_selected_modable}\\{mod}"
    active = active_mod(current_selected_modable, active_path)
    if os.path.exists(active):
        shutil.rmtree(active)
    destination_path = f"{active_path}\\{mod}"
    shutil.copytree(mod_path, destination_path)
    shutil.move(mod_path, f"{current_selected_modable}\\ACTIVE-{mod}")
    active_mods_display(active_path)
    display_mods()
    return f"Activated {mod}"

def remove_active_tag():
    for mod in os.scandir(current_selected_modable):
        mod_folder_name = mod.path.rsplit("\\", 1)[-1]
        dest_path = f"{current_selected_modable}\\{mod_folder_name[len("ACTIVE-"):]}"
        if mod_folder_name.startswith("ACTIVE-"):
            shutil.move(mod.path, dest_path)

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

@log_this
def active_mods_display(active_mods_path):
    active_mods_list_lb.delete(0, ttk.END)
    if path_exists(active_mods_path):
        mod_paths = get_folder_paths(active_mods_path)
        i = 0
        for path in mod_paths:
            active_mods_list_lb.insert(i, path.rsplit("\\", 1)[-1])
            i += 1
        mods_list = ttk.Variable(value=mods_list_lb)
    return mods_list

@log_this
def deactivate_mod(event=()):
    remove_active_tag()
    active_path = current_selected_game[1]
    active = active_mod(current_selected_modable, active_path)
    if os.path.exists(active):
        shutil.rmtree(active)
        active_mods_display(active_path)
    else:
        show_error("No active mod to deactivate for modable")
    display_mods()
    return f"Deactivated {active.rsplit("\\", 1)[-1]}"
    
@log_this
def add_mod():
    game = game_list_lb.get(game_list_lb.curselection())
    open_add_mod_modal(game, current_selected_modable)

@log_this
def add_mod_to_storage(modal):
    game = game_list_lb.get(game_list_lb.curselection())
    src_path = mod_src_path_e.get()
    name = mod_name_e.get()
    destined_path = current_selected_modable  
    url = mod_url_e.get()
    notes = mod_notes_modal_e.get("1.0", "end-1c")
    img_found = False
    archive_found = False

    if not os.path.exists(src_path):
        show_error("Mod source path does not exist")
    elif name is None or name == "":
        show_error("Mod name cannot be empty")
    else:
        archive_types = {'.zip', '.rar', '.tar', '.gz', '.7z', '.bz2'}
        destined_path = destined_path + "\\" + name
        os.makedirs(destined_path, exist_ok=True)
        src_path = Path(src_path)
        for file in src_path.iterdir():
            if file.is_file():
                mime_type, _ = mimetypes.guess_type(file)
                is_image = mime_type and mime_type.startswith('image/')
                extension = file.suffix.lower()
                is_archive = extension in archive_types
            
                if is_image:
                    shutil.move(file, f"{destined_path}\\preview.png") #shutil.move(file, destined_path)
                    # send2trash.send2trash(file)
                    img_found = True
                elif is_archive:
                    extractor.extract_archives(src_path, destined_path)
                    archive_found = True
        
        if img_found == False and archive_found == False:
            show_error("No images or archives found")
        elif archive_found == False:
           show_error("No archives found")

        if url or notes is not None:
            data = {"mod_info": {"url": url, "notes": notes}}
            with open(f"{destined_path}\\usmm_mod_info.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

        display_mods()
        modal.event_generate("<<CloseAddModModal>>")
        
    return f"Extracted archive, saved image, and added {name}"
    

@log_this
def add_mod_info(mod=()):
    mod_selection = mods_list_lb.curselection()
    mod = mods_list_lb.get(mod_selection[0])
    mod_path = f"{current_selected_modable}\\{mod}"
    url = mod_url.get()
    notes = mod_notes.get("1.0", "end-1c")
    data = {"mod_info": {"url": url, "notes": notes}}
    with open(f"{mod_path}\\usmm_mod_info.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return f"Saved {mod} info"

@log_this
def display_mod_info_storage(mod=()):
    add_mod_info_b.config(state="normal")
    activate_mod_b.config(state="normal")
    explore_mod.config(state="normal")
    mod_selection = mods_list_lb.curselection()
    mod = mods_list_lb.get(mod_selection[0])
    mod_path = f"{current_selected_modable}\\{mod}"
    populate_mod_info(mod_path)
    explore_mod.config(text=f"Mod: {get_dir_size_in_mb(mod_path)}")
    preview_image("storage")

@log_this
def display_mod_info_active(mod=()):
    add_mod_info_b.config(state="disabled")
    activate_mod_b.config(state="disabled")
    mod_selection = active_mods_list_lb.curselection()
    mod = active_mods_list_lb.get(mod_selection[0])
    mod_path = f"{current_selected_game[1]}\\{mod}"
    populate_mod_info(mod_path)
    preview_image("active")

def populate_mod_info(mod_path):
    clear_mod_info()
    if os.path.exists(f"{mod_path}\\usmm_mod_info.json"):        
        global mod_url, mod_notes
        mod_url.delete(0, ttk.END)
        mod_notes.delete("1.0", "end-1c")
        with open(f"{mod_path}\\usmm_mod_info.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            url = data["mod_info"]["url"]
            notes = data["mod_info"]["notes"]
        mod_url.insert(0, url)
        mod_notes.insert("1.0", notes)

@log_this
def preview_image(selection):
    if selection == "storage":
        mod_selection = mods_list_lb.curselection()
        mod = mods_list_lb.get(mod_selection[0])
        mod_path = f"{current_selected_modable}\\{mod}"
    elif selection == "active":
        mod_selection = active_mods_list_lb.curselection()
        mod = active_mods_list_lb.get(mod_selection[0])
        mod_path = f"{current_selected_game[1]}\\{mod}"
    global mod_preview_img
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

def clear_mod_info():
    mod_url.delete(0, ttk.END)
    mod_notes.delete("1.0", "end-1c")
    img = Image.open("defaultpreview.jpg")
    img.thumbnail((500, 500))
    mod_preview_img = ImageTk.PhotoImage(img)
    mod_img_lb.config(image=mod_preview_img)
    return "mod info cleared"

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

def mod_web(url):
    parsed_url = urlparse(url)
    if all([parsed_url.scheme, parsed_url.netloc]):
        webbrowser.open(url, new=2)
    else:
        show_error("Invalid URL")

def progress_thread(command):
    threading.Thread(target=run_with_progress, args=(command,)).start()

def run_with_progress(arg):
    progress_bar["maximum"] = 100
    progress_bar["value"] = 0
    progress_bar.start()
    status_label.config(text="Processing...")
    if type(arg) is dict:
        command = arg["cmd"]
        modal = arg["modal"]
    else:
        command = arg

    if arg == "activate":
        status_label.config(text=activate_mod())
    elif command == "deactivate":
        status_label.config(text=deactivate_mod())
    elif command == "save_game":
        status_label.config(text=save_game(modal))
    elif command == "remove_game":
        status_label.config(text=delete_game())
    elif command == "save_mod_info":
        status_label.config(text=add_mod_info())
    elif command == "add_mod_to_strg":
        status_label.config(text=add_mod_to_storage(modal))
    progress_bar["value"] = 100
    progress_bar.stop()

def get_dir_size_in_mb(dir_path):
    total_size_bytes = 0
    for dirpath, dirnames, filenames in os.walk(dir_path):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            total_size_bytes += os.path.getsize(file_path)
    return f"{round(total_size_bytes / (1024 * 1024)):,}mb"

def path_exists(path):
    if os.path.exists(path):
        return True
    else:
        messagebox.showerror("Error", f"Path {path} does not exist. Remove and reenter the selected game")
        return False


# DISPLAY CONTENT

# style for the control frame
ttk.Style().configure("control_frame.TFrame", relief="solid", border=1, bordercolor="#3e5059")
ttk.Style().configure("footer_frame.TFrame", background="gray")
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
add_game = ttk.Button(control_frame,
                         text="Add Game",
                         style="main_btn.TButton",
                         command=lambda: open_add_game_modal()
                         )
add_game.grid(column=1, row=3, padx=5, pady=5, sticky=NW)

remove_game = ttk.Button(control_frame,
                         text="Remove Game",
                         style="dull_btn.TButton",
                         command=lambda: progress_thread("remove_game")
                         )
remove_game.grid(column=1, row=3, padx=5, pady=5, sticky=NE)
explore_storage = ttk.Button(control_frame,
                            text="Game Mod Storage",
                            style="alt_btn.TButton",
                            command= lambda: explore_folder("storage")
                            )
explore_storage.grid(column=1, row=4, sticky=EW, padx=5, pady=5)
explore_storage.config(state="disabled")

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
add_mod_b = ttk.Button(control_frame,
                       text="Add Mod",
                       style="main_btn.TButton",
                       command=add_mod
                       )
add_mod_b.grid(column=2, row=3, padx=5, pady=5, sticky=NW)
add_mod_b.config(state="disabled")
refresh_modables_b = ttk.Button(control_frame, text="Refresh", command=display_modables)
refresh_modables_b.grid(column=2, row=3, padx=5, pady=5, sticky=NE)
explore_modable = ttk.Button(control_frame,
                             text="Modable Asset Storage",
                             style="alt_btn.TButton",
                             command= lambda: explore_folder("modable")
                             )
explore_modable.grid(column=2, row=4, sticky=EW, padx=5, pady=5)
explore_modable.config(state="disabled")

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
mods_list_lb.bind('<<ListboxSelect>>', display_mod_info_storage)
mod_button_frame = ttk.Frame(control_frame)
mod_button_frame.grid(column=3, row=3, sticky=N)
activate_mod_b = ttk.Button(mod_button_frame,
                            text="Activate",
                            style="main_btn.TButton",
                            command=lambda: progress_thread("activate")
                            )
activate_mod_b.grid(column=1, row=1, padx=2, pady=5, sticky=N)
activate_mod_b.config(state="disabled")
refresh_mods_b = ttk.Button(mod_button_frame, text="Refresh", command=display_mods)
refresh_mods_b.grid(column=2, row=1, padx=2, pady=5, sticky=N)
refresh_mods_b.config(state="disabled")
deactivate_b = ttk.Button(mod_button_frame,
                          text="Deactivate",
                          command=lambda: progress_thread("deactivate")
                          )
deactivate_b.grid(column=3, row=1, padx=2, pady=5, sticky=N)
deactivate_b.config(state="disabled")
explore_mod = ttk.Button(control_frame,
                         text="Mod",
                         style="alt_btn.TButton",
                         command= lambda: explore_folder("mod")
                         )
explore_mod.grid(column=3, row=4, sticky=EW, padx=5, pady=5)
explore_mod.config( state="disabled")

# active mods for game display
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
active_mods_list_lb.bind('<<ListboxSelect>>', display_mod_info_active)
explore_applied = ttk.Button(active_games_frame,
                             text="Game Applied Mods",
                             style="alt_btn.TButton",
                             command= lambda: explore_folder("applied")
                             )
explore_applied.grid(column=1, row=3, sticky=EW, padx=5, pady=5)
explore_applied.config(state="disabled")

# mod info form/display
add_mod_inf = ttk.Frame(main_frame, padding="20 20 20 20", style="control_frame.TFrame")
add_mod_inf.grid(column=1, row=4, sticky=NW)
mod_url_l = ttk.Label(add_mod_inf, text='Mod URL')
mod_url_l.grid(column=1, sticky=W, row=1, padx=5, pady=5)
mod_url = StringVar()
mod_url = ttk.Entry(add_mod_inf, textvariable=mod_url, width=17)
mod_url.grid(column=1,row=2, sticky=W, padx=5, pady=5)
mod_url_b = ttk.Button(add_mod_inf, text="Open",
                       command= lambda: mod_web(mod_url.get())
                       )
mod_url_b.grid(column=1, row=2, sticky=E)
mod_notes_add_l = ttk.Label(add_mod_inf, text='Notes (toggles, install info, etc)')
mod_notes_add_l.grid(column=1, sticky=W, row=3, padx=5, pady=1)
mod_notes = StringVar()
mod_notes = ttk.Text(add_mod_inf, width=63, height=14, wrap=ttk.WORD)
mod_notes.grid(column=1, columnspan=2, row=4, padx=5, pady=5)
add_mod_info_b = ttk.Button(add_mod_inf,
                            text="Save Mod Info",
                            style="main_btn.TButton",
                            command=lambda: progress_thread("save_mod_info")
                            )
add_mod_info_b.grid(column=1, columnspan=2, row=7, padx=5, pady=5)
add_mod_info_b.config(state="disabled")

# mod preview image display
mod_img_frame = ttk.Frame(main_frame, padding="20 20 20 20", style="control_frame.TFrame")
mod_img_frame.grid(column=2, columnspan=3, row=4, sticky=NW)
mod_img_frame.columnconfigure(1, weight=1, minsize=501) #weight values creating extra spaces?
mod_img_frame.rowconfigure(2, weight=1, minsize=501)
mod_img_l = ttk.Label(mod_img_frame, text="Mod Preview Image")
mod_img_l.grid(column=1, sticky=(N, W, E, S), row=1, padx=5, pady=5)
mod_default_preview_img = Image.open("defaultpreview.jpg")
mod_default_preview_img.thumbnail((500, 500))
mod_preview_img = ImageTk.PhotoImage(mod_default_preview_img)
mod_img_lb = ttk.Label(mod_img_frame, image=mod_preview_img)
mod_img_lb.grid(column=1, row=2)

# progress bar and status info
status_frame = ttk.Frame(main_frame, height=20, style="control_frame.TFrame")
status_frame.grid(column=1, row=5, columnspan=4, sticky="sew", pady=10)
status_frame.columnconfigure(2, minsize=400)
status_frame.columnconfigure((3, 4, 5, 6), minsize=65)
progress_bar = ttk.Progressbar(status_frame, orient="horizontal", length=100, mode="determinate")
progress_bar.grid(column=1, row=1, padx=10, pady=10)
status_label = ttk.Label(status_frame, text="Idle")
status_label.grid(column=2, row=1, sticky=W, padx=10, pady=10)# max size? or weight approach?

# center main window after all elements are placed in base frames 
center_and_finalize_window(root)

# display for "add game" modal
game_t = StringVar()
game_modables_path = StringVar()
game_mods_path = StringVar()

# frame for add game form
explore_add_frame = ttk.Frame(main_frame)
explore_add_frame.grid(column=1, row=4, sticky=N)
explore_add_frame.columnconfigure(1, weight=1, minsize=250) #weight values creating extra spaces?
explore_add_frame.rowconfigure((1, 2), weight=1)

def open_add_game_modal():
    global game_t, game_modables_path, game_mods_path
    add_game_modal = ttk.Toplevel(root)
    add_game_modal.title("Add Game")
    add_game_modal.resizable(False, False)
    add_game_modal.transient(root)
    add_game_modal.grab_set()
    add_game_modal.bind("<<CloseAddGameModal>>", lambda event: add_game_modal.destroy())

    # add/edit game form
    add_game_frame = ttk.Frame(add_game_modal, padding="20 10 20 10", style="control_frame.TFrame")
    add_game_frame.grid(column=1, row=3, sticky=SW, padx=10, pady=10)
    game_title_l = ttk.Label(add_game_frame, text='Game Title')
    game_title_l.grid(column=1, sticky=W, columnspan=2, row=1, padx=5, pady=5)
    game_t_e = ttk.Entry(add_game_frame, textvariable=game_t)
    game_t_e.grid(column=1, row=2, padx=5, pady=5)
    game_path_l = ttk.Label(add_game_frame, text='Path to Applied Mods Folder')
    game_path_l.grid(column=1, sticky=W, columnspan=2, row=3, padx=5, pady=1)
    game_modables_path_browse_btn = ttk.Button(add_game_frame,
                                            text="Browse",
                                            command= lambda: browse_folder(game_modables_path)
                                            )
    game_modables_path_browse_btn.grid(column=2, row=4, sticky=W, pady=5)
    game_modables_path = ttk.Entry(add_game_frame, textvariable=game_modables_path)
    game_modables_path.grid(column=1, sticky=E, row=4, padx=5, pady=5)
    game_path_l = ttk.Label(add_game_frame, text='Path to Mod Storage Folder')
    game_path_l.grid(column=1, sticky=W, columnspan=2, row=5, padx=5, pady=1)
    game_modable_mods_path_browse_btn = ttk.Button(add_game_frame, text="Browse", 
                                                command=lambda: browse_folder(game_mods_path)
                                                )
    game_modable_mods_path_browse_btn.grid(column=2, row=6, sticky=W, pady=5)
    game_mods_path = ttk.Entry(add_game_frame, textvariable=game_mods_path)
    game_mods_path.grid(column=1, sticky=E,row=6, padx=5, pady=5)
    arg = {"cmd":"save_game", "modal": add_game_modal}
    global b_add_game
    b_add_game = ttk.Button(add_game_frame,
                            text="Add Game",
                            style="main_btn.TButton",
                            command=lambda: progress_thread(arg)
                            )
    b_add_game.grid(column=1, row=7, padx=5, pady=5)
    b_add_game.config(state="disabled")

    center_and_finalize_window(add_game_modal, root)

# Display for "add mod" modal
mod_src_path_e = StringVar()
mod_name_e = StringVar()
mod_url_e = StringVar()
mod_notes_modal_e = StringVar()

def open_add_mod_modal(game, modable_path):
    global mod_src_path_e, mod_name_e, mod_url_e, mod_notes_modal_e
    add_mod_modal = ttk.Toplevel(root)
    add_mod_modal.title("Add Mod")
    add_mod_modal.resizable(False, False)
    add_mod_modal.transient(root)
    add_mod_modal.grab_set()
    add_mod_modal.bind("<<CloseAddModModal>>", lambda event: add_mod_modal.destroy())

    selected_game_l = ttk.Label(add_mod_modal, text=f"Game: {game}")
    selected_game_l.grid(row=0, column=0, columnspan=2, padx=5, pady=10, sticky=W)
    
    modable = modable_path.rsplit("\\", 1)[-1]
    modable_asset_l = ttk.Label(add_mod_modal, 
                                    text=f"Modable Asset: {modable}")
    modable_asset_l.grid(row=1, column=0, columnspan=2, padx=5, pady=10, sticky=W)
    
    mod_src_path_l = ttk.Label(add_mod_modal, text='Folder of Downloaded Archive and Image:')
    mod_src_path_l.grid(row=2, column=0, columnspan=2, padx=5, pady=10, sticky=W)
    mod_src_path_browse_btn = ttk.Button(add_mod_modal,
                                            text="Browse",
                                            command= lambda: browse_folder(mod_src_path_e)
                                            )
    mod_src_path_browse_btn.grid(row=3, column=0, padx=5, pady=5, sticky=E)
    mod_src_path_e = ttk.Entry(add_mod_modal, textvariable=mod_src_path_e)
    mod_src_path_e.grid(row=3, column=1, columnspan=2, padx=5, pady=5, sticky=E)

    mod_name_l = ttk.Label(add_mod_modal, text="Mod Name (mod folder name):")
    mod_name_l.grid(row=4, column=0, padx=5, pady=10, sticky=W)
    mod_name_e = ttk.Entry(add_mod_modal, textvariable=mod_name_e)
    mod_name_e.grid(row=4, column=1, padx=5, pady=5, sticky=E)

    mod_url_l = ttk.Label(add_mod_modal, text="Mod URL (optional):")
    mod_url_l.grid(row=5, column=0, padx=5, pady=5, sticky=W)
    mod_url_e = ttk.Entry(add_mod_modal, textvariable=mod_url_e)
    mod_url_e.grid(row=5, column=1, padx=5, pady=5, sticky=E)

    mod_notes_modal_l = ttk.Label(add_mod_modal, text="Notes (toggles, install info, etc)(optional):")
    mod_notes_modal_l.grid(row=6, column=0, columnspan=2, padx=5, pady=5, sticky=W)
    mod_notes_modal_e = ttk.Text(add_mod_modal, width=25, height=14, wrap=ttk.WORD)
    mod_notes_modal_e.grid(row=7, column=0, columnspan=2, padx=5, pady=5, sticky=NSEW)
    
    arg = {"cmd":"add_mod_to_strg", "modal": add_mod_modal}
    submit_add_mod_modal_b = ttk.Button(add_mod_modal, text="Add Mod",
                                        command=lambda: progress_thread(arg)
                                        )
    submit_add_mod_modal_b.grid(row=8, column=0, columnspan=2, padx=20, pady=20, sticky=NSEW)

    center_and_finalize_window(add_mod_modal, root)

root.mainloop()
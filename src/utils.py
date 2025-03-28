from libraries import *

# Constants
ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
SRC_DIR = os.path.join(ROOT, 'src')
DATA_DIR = os.path.join(ROOT, 'data')
ENEMIES_DIR = os.path.join(DATA_DIR, 'enemies')
WEAPONS_DIR = os.path.join(DATA_DIR, 'weapons')
ATTACKS_DIR = os.path.join(WEAPONS_DIR, 'attacks')
LOGS_DIR = os.path.join(SRC_DIR, 'logs')

# Ensure directories exist
os.makedirs(LOGS_DIR, exist_ok=True)

# Set up logging for better debugging and monitoring
# To debug, open up a powershell terminal then type "Clear-Host; Get-Content ./src/logs/debug.log -Wait" and press enter
debug_handler = logging.FileHandler(os.path.join(LOGS_DIR, 'debug.log'), mode='w', encoding='utf-8')
debug_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
debug = logging.getLogger("debug")
debug.setLevel(logging.DEBUG)
debug.addHandler(debug_handler)

crash_handler = logging.FileHandler(os.path.join(LOGS_DIR, 'crash.log'), mode='a', encoding='utf-8')
crash_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
crash = logging.getLogger("crash")
crash.setLevel(logging.ERROR)
crash.addHandler(crash_handler)

# Convert string to integer without error
def int_str(string):
    try:
        integer = int(string)
        return integer
    except:
        return None
    
def roll_chance(chance):
    return random.randint(0, 100) <= chance

# Merge sort algorithm
def merge_sort(arr, key, ascending = True):
    if len(arr) <= 1:
        return arr

    # Split the array into two halves
    mid = len(arr) // 2
    left_half = merge_sort(arr[:mid], key, ascending)
    right_half = merge_sort(arr[mid:], key, ascending)

    # Merge the two sorted halves
    return merge(left_half, right_half, key, ascending)

def merge(left, right, key, ascending):
    sorted_array = []
    i = j = 0

    # Merge the two arrays by comparing the key
    while i < len(left) and j < len(right):
        if ascending:
            if left[i][key] < right[j][key]:
                sorted_array.append(left[i])
                i += 1
            else:
                sorted_array.append(right[j])
                j += 1
        else:
            if left[i][key] > right[j][key]:
                sorted_array.append(left[i])
                i += 1
            else:
                sorted_array.append(right[j])
                j += 1

    # Append any remaining elements
    sorted_array.extend(left[i:])
    sorted_array.extend(right[j:])

    return sorted_array

def is_terminal_in_focus():
    """Check if the terminal window is in focus."""
    active_window = gw.getActiveWindow()
    terminal_titles = ['Command Prompt', 'Terminal', 'Visual Studio Code']
    return active_window and any(t in active_window.title for t in terminal_titles)

def load_data_from_directory(directory, data_type):
    # Loads data from JSON files in a given directory.
    
    # Parameters:
    # directory (str): Path to the directory containing the JSON files.
    # data_type (str): Type of data being loaded (used for logging).
    
    # Returns:
    # list: List of dictionaries containing data from the loaded JSON files.
    data = []
    if os.path.exists(directory):
        for file_name in os.listdir(directory):
            if file_name.endswith('json'):
                file_path = os.path.join(directory, file_name)
                try:
                    with open(file_path, 'r') as file:
                        data.append(json.load(file))
                except Exception as e:
                    debug.error(f'Error loading {data_type} data from {file_name}: {e}')
    else:
        debug.warning(f'Directory {directory} does not exist.')
    return data

def load_file_from_directory(directory, name, extension='.json', backup=False):
    # Loads data from JSON (or other files) files in a given directory.
    
    # Parameters:
    # directory (str): Path to the directory containing the JSON files.
    # name (str): Name of file.
    # extension (str): Extension of file, default is .json.
    # backup (bool): If a backup of a file is allowed to be saved after load
    
    # Returns:
    # dict: Dictionary consisting of data
    data = {}
    if os.path.exists(directory):
        file_name = f'{name}{extension}' if not name.endswith(extension) else name
        file_path = os.path.join(directory, file_name)
        try:
            if extension == '.json':
                with open(file_path, 'r') as file:
                    data = json.load(file)
                    debug.debug(f'Successfully loaded {file_name}')
            save_backup(file_path, file_name)
        except FileNotFoundError:
            debug.warning(f'File {file_name} does not exist.')
            return None
        except Exception as e:
            debug.error(f'Error loading {file_name}: {e}')
            return None
    else:
        debug.error(f'Directory {directory} does not exist.')
    return data

def save_backup(file_path, file_name):
    allow_backup = True
    if os.path.exists(file_path) and os.stat(file_path).st_size > 0:
        if file_path.endswith('.json'):
            try:
                with open(file_path, 'r') as file:
                    data = json.load(file)
                    if not data: backup = False # If current data is empty then it shouldn't save a backup of that empty file
            except Exception as e:
                allow_backup = False
                debug.error(f'Error saving backup of {file_name}: {e}')

        if allow_backup: 
            backup_file_path = file_path + '.bak'
            try: shutil.copy(file_path, backup_file_path)
            except Exception as e: debug.error(f'Error saving backup of {file_name}: {e}')

def save_file_from_directory(directory, name, data, extension='.json', backup = True, debugging=True):
    # Saves data to JSON files from a given directory.
    
    # Parameters:
    # directory (str): Path to the directory containing the JSON files.
    # name (str): Name of data.
    # data (anything): Content of the data
    # extension (str): Extension of file, default is .json.
    # backup (bool): If a backup of a file is allowed to be saved
    # debugging (bool): If it should print debug logs


    if os.path.exists(directory):
        file_name = f'{name}{extension}' if not name.endswith(extension) else name
        file_path = os.path.join(directory, file_name)
        try:
            if backup: save_backup(file_path, file_name)
            if extension == '.json':
                with open(file_path, 'w') as file:
                    json.dump(data, file, indent=4)
            if debugging: debug.debug(f'Successfully saved {file_name}:\n{str(data)}')
        except Exception as e:
            debug.error(f'Error saving {file_name}: {e}')
    else:
        debug.error(f'Directory {directory} does not exist.')
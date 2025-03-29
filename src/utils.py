from libraries import *

# Constants: Directory paths for various project assets
ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
SRC_DIR = os.path.join(ROOT, 'src')
DATA_DIR = os.path.join(ROOT, 'data')
ENEMIES_DIR = os.path.join(DATA_DIR, 'enemies')
WEAPONS_DIR = os.path.join(DATA_DIR, 'weapons')
ATTACKS_DIR = os.path.join(WEAPONS_DIR, 'attacks')
LOGS_DIR = os.path.join(SRC_DIR, 'logs')

# Ensure the logs directory exists, if not, create it
os.makedirs(LOGS_DIR, exist_ok=True)

# Set up logging for better debugging and error monitoring
# The debug log will capture all debug-level messages
# To debug, open up a powershell terminal then type "Clear-Host; Get-Content ./src/logs/debug.log -Wait" and press enter
debug_handler = logging.FileHandler(os.path.join(LOGS_DIR, 'debug.log'), mode='w', encoding='utf-8')
debug_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
debug = logging.getLogger("debug")
debug.setLevel(logging.DEBUG)
debug.addHandler(debug_handler)

# The crash log will capture errors and critical crashes
crash_handler = logging.FileHandler(os.path.join(LOGS_DIR, 'crash.log'), mode='a', encoding='utf-8')
crash_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
crash = logging.getLogger("crash")
crash.setLevel(logging.ERROR)
crash.addHandler(crash_handler)

def int_str(string):
    """
    Converts a string to an integer safely.
    
    If the string is a valid integer, returns the integer value.
    If the conversion fails, returns None.
    """
    try:
        integer = int(string)
        return integer
    except:
        return None

def roll_chance(chance):
    """
    Simulates a chance roll.
    
    Returns True if a random number between 0 and 100 is less than or equal to the chance.
    The chance is expressed as an integer percentage (e.g., 50 for 50%).
    """
    return random.randint(0, 100) <= chance

def roll_percentage(chance):
    """
    Simulates a precise percentage roll, handles decimal chances like 0.25 for 0.25%.
    
    Parameters:
        chance (float): The percentage chance (e.g., 0.25 for 0.25%).
    
    Returns:
        bool: True if the roll succeeds, False otherwise.
    """
    chance_str = format(chance, '.10f').rstrip('0').rstrip('.')  # e.g., "0.025"
    decimals = len(chance_str.split('.')[1]) if '.' in chance_str else 0
    precision = 10 ** (decimals + 2)  # +2 because percentages are ×100
    scaled_chance = int(chance * (10 ** decimals))  # 0.025 → 25
    roll = random.randint(1, precision)  # 1-1000 for 0.025%
    
    return roll <= scaled_chance

def merge_sort(arr, key, ascending=True):
    """
    Sorts a list of dictionaries or objects using the merge sort algorithm based on a specified key.
    
    Parameters:
        arr (list): The list to be sorted.
        key (str): The key to sort by.
        ascending (bool): Whether to sort in ascending or descending order (default is True).
    
    Returns:
        list: The sorted list.
    """
    if len(arr) <= 1:
        return arr

    mid = len(arr) // 2
    left_half = merge_sort(arr[:mid], key, ascending)
    right_half = merge_sort(arr[mid:], key, ascending)

    return merge(left_half, right_half, key, ascending)

def merge(left, right, key, ascending):
    """
    Merges two sorted lists based on a specified key and order.
    
    Parameters:
        left (list): The first sorted list.
        right (list): The second sorted list.
        key (str): The key to compare for sorting.
        ascending (bool): Whether to merge in ascending or descending order.
    
    Returns:
        list: The merged sorted list.
    """
    sorted_array = []
    i = j = 0

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

    sorted_array.extend(left[i:])
    sorted_array.extend(right[j:])
    
    return sorted_array

def is_terminal_in_focus():
    """
    Check if the terminal window is currently in focus.
    
    Returns:
        bool: True if the terminal window is in focus, False otherwise.
    """
    active_window = gw.getActiveWindow()
    terminal_titles = ['Command Prompt', 'Terminal', 'Visual Studio Code', 'PowerShell', 'generic terminal rpg']
    return active_window and any(t in active_window.title for t in terminal_titles)

def load_data_from_directory(directory, data_type):
    """
    Loads data from all JSON files in a specified directory.
    
    Parameters:
        directory (str): The directory containing the JSON files.
        data_type (str): The type of data being loaded (used for logging).
    
    Returns:
        list: A list of dictionaries containing the data from each file.
    """
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
    """
    Loads data from a single file in the specified directory.
    
    Parameters:
        directory (str): The directory containing the file.
        name (str): The name of the file to load.
        extension (str): The file extension (default is '.json').
        backup (bool): Whether to create a backup before loading the file.
    
    Returns:
        dict: The data loaded from the file, or None if an error occurred.
    """
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
    """
    Creates a backup of a file before modifying or overwriting it.
    
    Parameters:
        file_path (str): The path of the file to back up.
        file_name (str): The name of the file to back up.
    """
    allow_backup = True
    if os.path.exists(file_path) and os.stat(file_path).st_size > 0:
        if file_path.endswith('.json'):
            try:
                with open(file_path, 'r') as file:
                    data = json.load(file)
                    if not data: backup = False
            except Exception as e:
                allow_backup = False
                debug.error(f'Error saving backup of {file_name}: {e}')

        if allow_backup:
            backup_file_path = file_path + '.bak'
            try:
                shutil.copy(file_path, backup_file_path)
            except Exception as e:
                debug.error(f'Error saving backup of {file_name}: {e}')

def save_file_from_directory(directory, name, data, extension='.json', backup=True, debugging=True):
    """
    Saves data to a specified file in the given directory.
    
    Parameters:
        directory (str): The directory where the file will be saved.
        name (str): The name of the file to save.
        data (dict or list): The data to save to the file.
        extension (str): The file extension (default is '.json').
        backup (bool): Whether to create a backup of the file before saving (default is True).
        debugging (bool): Whether to log debug messages (default is True).
    """
    if os.path.exists(directory):
        file_name = f'{name}{extension}' if not name.endswith(extension) else name
        file_path = os.path.join(directory, file_name)
        try:
            if backup:
                save_backup(file_path, file_name)
            if extension == '.json':
                with open(file_path, 'w') as file:
                    json.dump(data, file, indent=4)
            if debugging:
                debug.debug(f'Successfully saved {file_name}:\n{str(data)}')
        except Exception as e:
            debug.error(f'Error saving {file_name}: {e}')
    else:
        debug.error(f'Directory {directory} does not exist.')

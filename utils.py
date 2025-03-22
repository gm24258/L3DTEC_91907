from libraries import *
from rich.logging import RichHandler

# Constants
DATA_DIR = './data'
ENEMIES_DIR = f'{DATA_DIR}/enemies'
WEAPONS_DIR = f'{DATA_DIR}/weapons'

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

# Set up logging for better debugging and monitoring
# To debug, open up a powershell terminal then type "Clear-Host; Get-Content debug.log -Wait" and press enter
debug_handler = logging.FileHandler('debug.log', mode='w')
debug_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
debug = logging.getLogger("debug")
debug.setLevel(logging.DEBUG)
debug.addHandler(debug_handler)

# Set up logging for crashes
crash_handler = logging.FileHandler('crash.log', mode='a')
crash_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
crash = logging.getLogger("crash")
crash.setLevel(logging.ERROR)
crash.addHandler(crash_handler)

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

def load_file_from_directory(directory, name, template_prefix=None):
    # Loads data from JSON files in a given directory.
    
    # Parameters:
    # directory (str): Path to the directory containing the JSON files.
    # name (str): Name of data.
    # template_prefix (str): 
    
    # Returns:
    # dict: Dictionary consisting of data
    data = {}
    if os.path.exists(directory):
        file_name = f'{name}.json' if not name.endswith('.json') else name
        file_path = os.path.join(directory, file_name)
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                debug.debug(f'Successfully loaded {file_name}')
        except FileNotFoundError:
            debug.warning(f'File {file_name} does not exist.')

            # If this save file has a template file, it will attempt to get the data from that template file and make it the new file
            if template_prefix:
                template_file = os.path.join(directory, template_prefix + file_name)
                try:
                    with open(template_file, 'r') as file:
                        data = json.load(file)
                        debug.debug(f'Successfully created new file from {template_prefix}{file_name}')
                        save_file_from_directory(directory, file_name, data)
                except Exception as e:
                    debug.error(f'Error loading {template_prefix}{file_name}: {e}')
        except Exception as e:
            debug.error(f'Error loading {file_name}: {e}')
    else:
        debug.error(f'Directory {directory} does not exist.')
    return data

def save_file_from_directory(directory, name, data, debugging):
    # Saves data to JSON files from a given directory.
    
    # Parameters:
    # directory (str): Path to the directory containing the JSON files.
    # name (str): Name of data.
    # data (anything): Content of the data
    if os.path.exists(directory):
        file_name = f'{name}.json' if not name.endswith('.json') else name
        file_path = os.path.join(directory, file_name)
        try:
            backup = True
            # Check if file exists and it isn't empty, otherwise don't backup
            if os.path.exists(file_path) and os.stat(file_path).st_size > 0:
                # Checks if file is JSON and isn't empty/correct, otherwise don't backup
                if file_path.endswith('.json'):
                    with open(file_path, 'r') as file:
                        backup_data = json.load(file) 
                        if not backup_data: backup+ False

                backup_file_path = file_path + ".bak"
                if backup: shutil.copy(file_path, backup_file_path)
            # Saving
            with open(file_path, 'w') as file:
                json.dump(data, file, indent=4)
                if debugging: debug.debug(f'Successfully saved {file_name}:\n{str(data)}')
        except Exception as e:
            debug.error(f'Error saving {file_name}: {e}')
    else:
        debug.error(f'Directory {directory} does not exist.')
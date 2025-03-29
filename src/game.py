from menus import *
from utils import *
from fight import initiate_fight
from keyboard_manager import keyboard_manager
from globals import player
import globals

# ========================
#        GAME DATA
# ========================
def load_enemy_data(enemy_directory):
    """
    Loads individual enemy data (main and attacks) into a single dictionary.

    Parameters:
    enemy_directory (str): Path of enemy_directory to load data from
    """
    # Load main data (stats)
    main_data = {}
    attacks_data = []

    main_file_path = os.path.join(enemy_directory, 'main.json')
    attacks_file_path = os.path.join(enemy_directory, 'attacks.json')

    if os.path.exists(main_file_path):
        with open(main_file_path, 'r') as main_file:
            main_data = json.load(main_file)

    if os.path.exists(attacks_file_path):
        with open(attacks_file_path, 'r') as attacks_file:
            attacks_data = json.load(attacks_file).get('attacks', [])

    # Merge the attacks data into the main data dictionary
    main_data['attacks'] = attacks_data

    return main_data

def load_enemies():
    """
    Loads enemy data from the ENEMIES_DIR and sorts by level requirement.
    """
    for enemy_folder in os.listdir(ENEMIES_DIR):
        enemy_path = os.path.join(ENEMIES_DIR, enemy_folder)
        if os.path.isdir(enemy_path):  # Ensure it's a directory for an enemy
            enemy_data = load_enemy_data(enemy_path)
            globals.enemies.append(enemy_data)
    
    # Assuming each enemy has a 'main' data containing 'level'
    globals.enemies = merge_sort(globals.enemies, 'level')
    debug.info(f'Loaded {len(globals.enemies)} enemies.')

def load_attacks(): 
    """
    Loads attack data from the ATTACKS_DIR (Inside the WEAPONS_DIR)
    """   
    globals.attacks = load_data_from_directory(ATTACKS_DIR, 'attack')

def load_weapons(): 
    """
    Loads weapon data from the WEAPONS_DIR and sorts the dictionary by level requirement. 
    """      

    globals.weapons = load_data_from_directory(WEAPONS_DIR, 'weapon')
    globals.weapons = merge_sort(globals.weapons, 'levelRequirement')
    load_attacks()
    debug.info(f'Loaded {len(globals.weapons)} weapons.')

    # Create a new list of globals.weapons from existing globals.weapons list but removes items that are not shop items
    globals.shop_weapons = [weapon['id'] for weapon in globals.weapons if weapon['inShop']]

def sort_displayed_weapons(key, order, weapons_list):
    """
    Sorts a list of weapons for display (like shop or inventory), with a given key and order.

    Parameters:
    key (str): Name of key.
    order (bool): False for descending order, True for ascending order.
    weapons_list (list): List of weapon IDs.
    """

    # Price needs to be sorted differently because some weapons are not in the shop and therefore don't have a price
    if key == 'price':
        # Weapons in shop are sorted by the price
        displayed_shop_weapons = sorted(
            [
                weapon_id for weapon_id in weapons_list
                if next((weapon for weapon in globals.weapons if weapon['id'] == weapon_id and weapon['inShop'] is True), None) is not None
            ], 
            key = lambda weapon_id: next((item[key] for item in globals.weapons if item['id'] == weapon_id), 0),
            reverse = not order
        )
        # Weapons not in shop are sorted by levelRequirement in default
        not_in_shop_weapons = sorted(
            [
                weapon_id for weapon_id in weapons_list
                if next((weapon for weapon in globals.weapons if weapon['id'] == weapon_id and weapon['inShop'] is False), None) is not None
            ], 
            key = lambda weapon_id: next((item['levelRequirement'] for item in globals.weapons if item['id'] == weapon_id), 0),
            reverse = not order
        )
        if order: return not_in_shop_weapons + displayed_shop_weapons # In ascending order, the non-shop weapons are always at the top
        else: return displayed_shop_weapons + not_in_shop_weapons # In descending order, the non-shop weapons are always at the bottom
    
    # Other keys (only levelRequirement exists) are sorted like normal
    else:
        weapons_list = sorted(
            weapons_list, 
            key = lambda weapon_id: next((item[key] for item in globals.weapons if item['id'] == weapon_id), 0),
            reverse = not order
        )
        return weapons_list

# ========================
#       GLOBAL STATE
# ========================

class MenuState:
    """Manages the state of the current menu, including options, pagination, sorting, and UI elements."""
    def __init__(self):
        # Core menu state
        self.current_menu = None               # Tracks the current active menu
        self.should_exit = False               # Determines whether the menu should exit

        # Menu option state
        self.selected = 0                      # Index of the currently selected option
        self.options = []                      # List of menu options
        self.title = None                      # Title displayed at the top of the menu
        self.info = None                       # Additional information displayed in the menu
        self.tooltip_before = None             # Tooltip displayed before the main tooltip (used for timers)
        self.tooltip = None                    # Main tooltip for the current menu
        self.menu_type = 'basic'               # Type of menu: 'basic', 'horizontal', or 'paged'

        # Pagination state
        self.page_size = 5                     # Number of options per page for paged menus
        self.current_page = 1                  # Current page number (1-based index)
        self.total_pages = 1                   # Total number of pages
        self.start_index = 0                   # Index of the first option on the current page

        # Sorting state
        self.sort_type = None                  # Type of sorting applied (e.g., alphabetical, value-based)
        self.sort_order = None                 # Order of sorting (e.g., ascending or descending)

# Initialize global state
menu_state = MenuState()

# ========================
#       CRASH HANDLER
# ========================

def crash_handling(error):
    """
    This function runs after an error happens which would stop the game.

    Parameters:
    error (Exception): Error that contains the main error
    """
    globals.crashed = True 
    keyboard_manager.stop() # Stops keyboard inputs
    
    # Log the crash
    crash_log_path = os.path.join(LOGS_DIR, 'crash.log')
    debug.error(f"An error was caught and crashed the game. Please check {crash_log_path}")
    crash.error(f"Error caught while running the game:\n{error}\n{traceback.format_exc()}") # Full traceback of error cause

    # Print crash statemment in game
    clear_terminal()
    print("The game unexpectedly crashed! Restarting in a second...")
    time.sleep(2)

    globals.crashed = False
    menu_state.should_exit = False
    keyboard_manager.start()  # Restart keyboard listener

# ========================
#       MENU FUNCTIONS
# ========================

def main_menu(selected=0):
    """
    Displays the nain menu at the start of the game where the player can select the main options of the game

    Parameters:
    selected (int): The index of the pre-selected option for this menu. 
                    Used to restore the player's selection when returning here from other menus or functions. 
                    Defaults to 0 if not set.
    """

    # Set up menu state for main menu
    menu_state.options = ['Play', 'Shop', 'Inventory', 'Settings', 'Exit']
    menu_state.menu_type = 'basic'
    menu_state.selected = selected
    menu_state.title = style_text({'style': 'bold'}, f'Main Menu | Lvl. ') + Text(str(player.level)) + style_text({'style': 'italic'}, f' ({player.xp}/{player.xp_goal})')
    menu_state.info = None
    menu_state.tooltip = style_text({'style': 'italic'}, 'Arrow Keys ↑/↓ to navigate | ENTER to select') if player.display_controls else None

    def on_press(key):
        """
        Handle key inputs required for the menu
        Basic-type menus use up and down keys
        
        Parameters:
        key (str): The key that was pressed by the player.
        """
        if key == ('up' if player.use_arrow_keys else 'w'): # Up arrow / W key
            update_selection(-1)
        elif key == ('down' if player.use_arrow_keys else 's'): # Down arrow / S key
            update_selection(1)
        elif key == 'enter':  # Enter key
            handle_enter()

    def update_selection(delta):
        """
        Update the selected option and redraw the menu.

        Parameters:
        delta (int): The change in selection (either +1 or -1 to move up or down).
        """
        menu_state.selected = (menu_state.selected + delta) % len(menu_state.options) # Allows wrap-around
        redraw_menu()

    def handle_enter():
        """Handle menu item selection"""
        if menu_state.selected == 0:  # Play
            play_selection_menu(old_selected=0)
        elif menu_state.selected == 1:  # Shop
            shop_menu(old_selected=1)
        elif menu_state.selected == 2:  # Inventory
            inventory_menu(old_selected=2)
        elif menu_state.selected == 3:  # Settings
            settings_menu(old_selected=3)
        elif menu_state.selected == 4:  # Exit
            exit_confirmation(4)

    # Set the keyboard handler to this menu's key-input handler
    keyboard_manager.set_handler(on_press)
    redraw_menu()

def exit_confirmation(old_selected):
    """
    Displays the exit confirmation menu when player selects 'Exit' from the main menu

    Parameters:
    old_selected (int): The index of the pre-selected option for the main menu. 
                        Used to restore the player's selection in the main menu when returning from here. 
                        Defaults to 0 if not set.
    """

    # Set up the menu state for exit confirmation menu
    menu_state.options = ['Go Back', 'Confirm']
    menu_state.menu_type = 'basic'
    menu_state.selected = 0
    menu_state.title = style_text({'style': 'bold'}, 'Are you sure you want to exit?')
    menu_state.info = None
    menu_state.tooltip = style_text({'style': 'italic'}, 'Arrow Keys ↑/↓ to navigate | ENTER to select') if player.display_controls else None

    def update_selection(new_selection):
        """
        Update the selected option and redraw the menu.

        Parameters:
        new_selection (int): The new selection value
        """
        # No wrap around in here
        menu_state.selected = new_selection
        redraw_menu()

    def on_press(key):
        """
        Handle key inputs required for the menu
        Basic-type menus use up and down keys
        
        Parameters:
        key (str): The key that was pressed by the player.
        """
        if key == ('up' if player.use_arrow_keys else 'w'): # Up arrow / W key
            update_selection(0)
        elif key == ('down' if player.use_arrow_keys else 's'): # Down arrow / S key
            update_selection(1)
        elif key == 'enter':  # Enter key
            if menu_state.selected == 0:
                main_menu(old_selected) # Go back to main menu with the old_selected value
            elif menu_state.selected == 1: 
                player.save()
                print('\nExiting game...')
                menu_state.should_exit = True
        elif key == 'esc':  # Escape key
            main_menu(old_selected) # Go back to main menu with the old_selected value

    # Set the keyboard handler to this menu's key-input handler
    keyboard_manager.set_handler(on_press)
    redraw_menu()

def play_selection_menu(selected=0, old_selected=0):
    """
    Displays the play selection menu when player selects 'Play' from the main menu.
    Players can navigate enemies for information and prompt to fight them if they meet requirements.

    Parameters:
    selected (int): The index of the pre-selected option for this menu. 
                    Used to restore the player's selection when returning here from other menus or functions. 
                    Defaults to 0 if not set.

    old_selected (int): The index of the pre-selected option for the main menu. 
                        Used to restore the player's selection in the main menu when returning from here. 
                        Defaults to 0 if not set.
    """

    # Set up the menu state for the play selection menu
    menu_state.menu_type = 'horizontal'
    menu_state.selected = selected 
    menu_state.title = style_text({'style': 'bold'}, f'Play | Lvl. ') + Text(str(player.level)) + style_text({'style': 'italic'}, f' ({player.xp}/{player.xp_goal})')

    def on_press(key):
        """
        Handle key inputs required for the menu
        Horizontal-type menus use left and right keys
        
        Parameters:
        key (str): The key that was pressed by the player.
        """
        if key == ('left' if player.use_arrow_keys else 'a'): # Left arrow / A key
            update_selection(-1)
        elif key == ('right' if player.use_arrow_keys else 'd'): # Right arrow / D key
            update_selection(1)
        elif key == 'enter':
            handle_enter()
        elif key == 'esc': # Escape key
            main_menu(old_selected) # Go back to main menu with the old_selected value

    def update_selection(delta):
        """
        Update the selected option and redraw the menu.

        Parameters:
        delta (int): The change in selection (either +1 or -1 to move up or down).
        """
        new_selected = menu_state.selected + delta
        # No wrap around in here
        if 0 <= new_selected < len(globals.enemies):
            menu_state.selected = new_selected
            update_menu_info()  # Update the displayed info and tooltip

    def handle_enter():
        """Handle enemy selection for confirmation"""
        current_enemy = globals.enemies[menu_state.selected]
        if player.level >= current_enemy['level']:
            play_confirm_fight(
                current_enemy,
                style_text(current_enemy['title'], current_enemy['name']),
                current_enemy['id'],
                old_selected=menu_state.selected
            ) # Sends player to the a fight confirmation menu for the current enemy if player meets requirements

    def update_menu_info():
        """Update the info and tooltip based on the selected enemy"""

        # Get data of selected enemy
        current_enemy = globals.enemies[menu_state.selected]
        level_requirement = current_enemy['level']
        correct_level = player.level >= level_requirement # Condition if player meets enemy level requirement

        # ===========================
        # Enemy info to be displayed:
        # ===========================

        # Styled enemy name
        enemy_name = style_text(current_enemy['title'], current_enemy['name']) 
        # Displayed health with bold label and colored green value
        health_text = style_text({'style': 'bold'}, 'Health: ') + style_text({"color": [201, 237, 154]}, f"{current_enemy['health']}")
        # Start displayed level with bold label
        level_info = style_text({'style': 'bold'}, 'Level required: ') 
        # Set level required value color: green if level requirement met, red if not
        level_color = [201, 237, 154] if correct_level else [227, 104, 104] 
        # Append styled level requirement value with label 
        level_info += style_text({'color': level_color}, f"{level_requirement}")
        # Show lock symbol, or italic 'Locked' label if player prefers text labels over symbols
        locked_text = style_text({'style': 'italic'}, ' (Locked)') if player.display_text else Text(" 🔒")
        # Add lock indicator if level requirement is not met
        level_info += Text() if correct_level else locked_text

        # Combine and display enemy info 
        menu_state.info = enemy_name + '\n ' + health_text + '\n ' + level_info

        # ========================
        # Tooltip to be displayed:
        # ========================

        # Get data of enemy before selected enemy if it exists
        prev_enemy = globals.enemies[menu_state.selected - 1] if menu_state.selected > 0 else None
        # Get data of enemy after selected enemy if it exists
        next_enemy = globals.enemies[menu_state.selected + 1] if menu_state.selected < len(globals.enemies) - 1 else None
        # Style previous enemy name if it exists, otherwise display NONE
        prev_enemy_name = style_text(prev_enemy['title'], prev_enemy['name']) if prev_enemy else Text('NONE')
        # Style next enemy name if it exists, otherwise display NONE
        next_enemy_name = style_text(next_enemy['title'], next_enemy['name']) if next_enemy else Text('NONE')

        # Prepare enter substring for tooltip based on level requirement and player settings
        enter_string = ''
        # If player meets the level requirement
        if correct_level: 
            # If text display is disabled, add a sword symbol
            if not player.display_text: 
                enter_string += '⚔️  '
            # If control tooltips are enabled, add control instruction
            if player.display_controls: 
                enter_string += 'ENTER to '

            # Append action description
            enter_string += 'Fight'
        # If player doesn't meet the level requirement
        else:  
            # Display bold-italc warning message
            enter_string = style_text({'style': 'bold italic'}, 'You cannot fight this enemy yet!')

        # If control toolips are enabled, display navigation controls
        controls_tooltip = '\nArrow Keys ←/→ to navigate | ESC to go back' if player.display_controls else ''
        # Finalize and display tooltip
        menu_state.tooltip = style_text({'style': 'italic'}, enter_string, ' | ', prev_enemy_name, ' ← | → ', next_enemy_name, controls_tooltip)
        
        # Redraw menu to update displayed output
        redraw_menu()
    
    # Set the keyboard handler to this menu's key-input handler
    keyboard_manager.set_handler(on_press)
    update_menu_info()

def play_confirm_fight(enemy, enemy_name, enemy_id, old_selected=0):
    """
    Displays the play confirm fight menu when player selects an enemy from the play selection menu.
    Players can select 'Yes' if they want to initiate combat, otherwise 'No' goes back to the play selection menu.

    Parameters:
    enemy (dictionary): Data of the selected enemy
    enemy_name (str or Text): (Styled) name of the selected enemy
    enemy_id (str): ID of the selected enemy
    
    old_selected (int): The index of the pre-selected option for the play selection menu. 
                        Used to restore the player's selection in the play selection menu when returning from here. 
                        Defaults to 0 if not set.
    """
    # Set up the menu state for the play confirm menu
    menu_state.options = [style_text({'style': 'bold'}, 'No'), style_text({'style': 'bold'}, 'Yes')]
    menu_state.menu_type = 'basic'
    menu_state.selected = 0 
    menu_state.title = style_text({'style': 'bold'}, f"Are you sure you want to fight ", enemy_name, "?\n")
    menu_state.tooltip = style_text({'style': 'italic'}, 'Arrow Keys ↑/↓ to navigate | ENTER to select | ESC to go back' if player.display_controls else '')

    # =====================================
    # Enemy and player comparison info setup
    # ======================================

    # Display enemy health with bold label and colored green value
    enemy_health_info = style_text({'style': 'bold'}, ' Health: ') + style_text({'color': [201, 237, 154]}, str(enemy['health']))
    # Display enemy level with bold label and colored green value
    enemy_level_info = style_text({'style': 'bold'}, '\n Level requirement: ') + style_text({'color': [201, 237, 154]}, str(enemy['level']))
    # Display player health with bold label and colored green value
    player_level_info = style_text({'style': 'bold'}, '\n Your health: ') + style_text({'color': [201, 237, 154]}, str(player.health))
    # Display player level with bold label and colored green value
    player_level_info = style_text({'style': 'bold'}, '\n Your level: ') + style_text({'color': [201, 237, 154]}, str(player.level))
    # Set and display info
    menu_state.info = enemy_health_info + enemy_level_info + player_level_info

    def update_selection(new_selection):
        """
        Update the selected option and redraw the menu.

        Parameters:
        new_selection (int): The new selection value
        """
        menu_state.selected = new_selection
        redraw_menu()

    def handle_exit():
        """Return to selection menu without fighting"""
        debug.info(Text(f"Did not fight ") + enemy_name)
        play_selection_menu(selected=old_selected)

    async def handle_yes():
        """Initiate combat sequence"""
        debug.info(Text(f"Fighting ") + enemy_name)
        globals.in_combat = True # Set global combat variable to true
        try:
            # Initiate fight handled in fight.py
            await initiate_fight(enemy, enemy_name, enemy_id)
        except Exception as e:
            # If a crash occurs in fight.py, it is handled here
            crash_handling(e)
        finally:
            # Go back to play selection menu after the player successfully ends the fight, or crashes during it
            play_selection_menu(selected=old_selected)

    def on_press(key):
        """
        Handle key inputs required for the menu
        Basic-type menus use up and down keys
        
        Parameters:
        key (str): The key that was pressed by the player.
        """
        if key == ('up' if player.use_arrow_keys else 'w'): # Up arrow / W key
            update_selection(0)
        elif key == ('down' if player.use_arrow_keys else 's'): # Down arrow / S key
            update_selection(1)
        elif key == 'enter':
            if menu_state.selected == 0: # Selects 'No'
                handle_exit()
            else: # Selects 'Yes'
                asyncio.run(handle_yes())
        elif key == 'esc':
            handle_exit()
            
    # Set the keyboard handler to this menu's key-input handler
    keyboard_manager.set_handler(on_press)
    redraw_menu()

def shop_menu(selected=0, old_selected=0):
    """
    Displays the shop menu when player selects 'Shop' from the main menu.
    Shows the player's balance, level, and available weapons' names with labels indicating level requirement eligibility.
    Selection of a weapon sends the player to the shop weapon inspection menu.

    Parameters:
    selected (int): The index of the pre-selected option for this menu. 
                    Used to restore the player's selection when returning here from other menus or functions. 
                    Defaults to 0 if not set.

    old_selected (int): The index of the pre-selected option for the main menu. 
                        Used to restore the player's selection in the main menu when returning from here. 
                        Defaults to 0 if not set.
    """

    # Set sorting state
    menu_state.sort_type = player.settings.get('shopSortType', 'price')
    menu_state.sort_order = player.settings.get('shopSortAscending', True)

    # Get sort keybinds from player
    sort_type_keybind = player.settings['primarySortKeybind']
    sort_order_keybind = player.settings['secondarySortKeybind']

    # Store old sort_type and sort_order
    sort_type = menu_state.sort_type
    sort_order = menu_state.sort_order
    # Initialize displayed shop options
    displayed_shop = sort_displayed_weapons(sort_type, sort_order, globals.shop_weapons)

    # Set up the menu state for the shop menu
    menu_state.menu_type = 'paged'
    menu_state.selected = selected
    menu_state.title = style_text({'style':'bold'}, 'Shop | Balance: ', style_text({'color':[201, 237, 154]}, f"${player.balance}"), f" | Level: ") + Text(str(player.level))
    menu_state.info = None 
    menu_state.page_size = 5

    current_option = None # Initialize selected option

    def on_press(key):
        """
        Handle key inputs required for the menu
        Paged-type menus use up and down keys for navigating options in the current page
        and use left and right keys for switching pages in the menu
        
        Parameters:
        key (str): The key that was pressed by the player.
        """
        nonlocal current_option
        if key == ('up' if player.use_arrow_keys else 'w'): # Up arrow / W key
            update_selection(-1)
        elif key == ('down' if player.use_arrow_keys else 's'): # Down arrow / S key
            update_selection(1)
        # Left arrow / A key
        elif key == ('left' if player.use_arrow_keys else 'a') and menu_state.current_page > 0:
            # Switch to previous page if current page isn't the first one
            menu_state.current_page -= 1  # Move to the previous page
            menu_state.selected = menu_state.current_page * menu_state.page_size  # Set selected to the first item of the page
            redraw_menu()
        # Right arrow / D key
        elif key == ('right' if player.use_arrow_keys else 'd') and menu_state.current_page < menu_state.total_pages - 1: 
            # Switch to next page if current page isn't the last one
            menu_state.current_page += 1  # Move to the next page
            menu_state.selected = menu_state.current_page * menu_state.page_size  # Set selected to the first item of the page
            redraw_menu()
        elif key == 'enter': 
            if current_option:
                current_weapon_id = current_option[0] # Get ID of selected weapon
                current_weapon = current_option[1] # Get data of selected weapon
                current_weapon_name = style_text(current_weapon['title'], current_weapon['name']) # Get and style name of selected weapon
                # Sends player to the shop weapon inspection menu of the selected weapon
                shop_view_weapon(current_weapon, current_weapon_name, current_weapon_id, old_selected=menu_state.selected)
        elif key == 'esc':  # Escape key
            main_menu(old_selected) # Go back to the main menu with old selected value
        elif key == sort_type_keybind: # Key set for the sort type keybind
            keys = ['levelRequirement', 'price'] # Existing types to sort
            player.settings['shopSortType'] = keys[(keys.index(menu_state.sort_type) + 1) % len(keys)] # Set the sort type to the next key
            update_menu_info() # Update displayed menu
            player.save(debugging=False) # Save player data to save file
        elif key == sort_order_keybind: # Key set for the sort order keybind
            player.settings['shopSortAscending'] = not player.settings['shopSortAscending'] # Set to opposite sort type
            update_menu_info()
            player.save(debugging=False)

    def update_selection(delta):
        """
        Update the selected option and redraw the menu.

        Parameters:
        delta (int): The change in selection (either +1 or -1 to move up or down).
        """
        valid_indices = list(range(menu_state.start_index, min(menu_state.start_index + menu_state.page_size, len(menu_state.options))))
        if delta < 0:  # Moving up (previous selection)
            if menu_state.selected == valid_indices[0]:  # If at the top, loop to the bottom
                menu_state.selected = valid_indices[-1]
            else:
                menu_state.selected = valid_indices[valid_indices.index(menu_state.selected) + delta]
        else:  # Moving down (next selection)
            if menu_state.selected == valid_indices[-1]:  # If at the bottom, loop to the top
                menu_state.selected = valid_indices[0]
            else:
                menu_state.selected = valid_indices[valid_indices.index(menu_state.selected) + delta]
        update_menu_info()

    def update_menu_info():
        """Update options and tooltip based on sort order/type"""

        nonlocal current_option
        nonlocal displayed_shop
        nonlocal sort_type
        nonlocal sort_order

        # If sort type and sort order was changed, re-sort and display shop
        if menu_state.sort_type != sort_type or menu_state.sort_order != sort_order:
            sort_type = menu_state.sort_type
            sort_order = menu_state.sort_order
            displayed_shop = sort_displayed_weapons(sort_type, sort_order, globals.shop_weapons)

        # ==================
        # Menu options setup
        # ==================

        options = [] # Initialize options
        # Iterate through the displayed shop weapons to generate menu options
        for weapon_id in displayed_shop:
            weapon = next((item for item in globals.weapons if item['id'] == weapon_id), None) # Get weapon from weapons data based on weapon's ID
            if weapon:
                # Style weapon name for displayed option
                option_text = style_text(weapon['title'], weapon['name'])

                # Check if player already owns the weapon
                if weapon_id in player.inventory:
                    owned_text = style_text({'style': 'italic'}, ' (Owned)') if player.display_text else Text(" ✅")
                    option_text += owned_text
                # If the player does not meet level requirement
                elif player.level < weapon['levelRequirement']:
                    # Add a label beside the option: lock symbol, or italic 'Locked' text if player prefers text labels over symbols
                    locked_text = style_text({'style': 'italic'}, ' (Locked)') if player.display_text else Text(" 🔒")
                    option_text += locked_text  
                # Add weapon id, weapon data, and option text to the options list
                options.append((weapon_id, weapon, option_text))
            else: # If no data was found for given weapon ID
                debug.warning(f"Error trying to find weapon with ID: {weapon_id}")
        # Get selected option
        current_option = options[menu_state.selected]  
        # Update the menu options to display the option texts
        menu_state.options = [option[2] for option in options]
        
        # ==================
        # Menu tooltips setup
        # ==================

        # Determine the order of sorting (ascending or descending)
        displayed_order = 'Ascending' if sort_order else "Descending"
        # Initialize the sort type display text as an empty string
        displayed_type = ""
        # Determine the sorting type and set the corresponding display text
        if sort_type == 'levelRequirement': 
            displayed_type = "Level"  # If sorting by level requirement
        elif sort_type == 'price': 
            displayed_type = "Price"  # If sorting by price

        # Create the tooltip for sorting information
        # This includes the sorting type and the sorting order (Ascending/Descending)
        # It also adds keybind hints if the player is configured to display controls
        sort_tooltip = f"Sorted by: {displayed_type}{f' ({sort_type_keybind.upper()})' if player.display_controls else ''} | {displayed_order}{f' ({sort_order_keybind.upper()})' if player.display_controls else ''}"
        # Create the control tooltip for navigation instructions
        # These will only appear if the player is configured to see controls
        control_tooltip =  '\nArrow Keys ↑/↓ to navigate items | Arrow Keys ←/→ to navigate pages | ENTER to select | ESC to go back' if player.display_controls else ''
        # Create the extra tooltip for item statuses (Purchased or Locked)
        # It will show "✅" for purchased items and "🔒" for locked items, based on player settings
        extra_tooltip = '\n✅ = Purchased | 🔒 = Locked' if player.display_extra else ''
        # Combine all the tooltips into one, with italic styling applied
        menu_state.tooltip = style_text({'style':'italic'}, sort_tooltip, control_tooltip, extra_tooltip)  
        
        redraw_menu()

    # Set the keyboard handler to this menu's key-input handler
    keyboard_manager.set_handler(on_press)
    update_menu_info() 

def shop_view_weapon(weapon, weapon_name, weapon_id, selected=0, old_selected=0):
    """
    Displays the shop weapon inspection menu when player selects a weapon from the shop menu.
    Shows the player's balance and level at the title.
    Shows selected weapon's information, such as description, price, level requirement, and abilities
    Pressing ENTER sends the player to the shop buy weapon menu if player meets requirements.

    Parameters:
    weapon (dictionary): Data of the selected weapon
    weapon_name (str or Text): (Styled) name of the selected weapon
    weapon_id (str): ID of the selected weapon
    
    selected (int): The index of the pre-selected option for this menu. 
                    Used to restore the player's selection when returning here from the shop buy weapon menu. 
                    Defaults to 0 if not set.

    old_selected (int): The index of the pre-selected option for the shop menu. 
                        Used to restore the player's selection in the shop menu when returning from here. 
                        Defaults to 0 if not set.
    """

    # Set up the menu state for the shop weapon inspection menu
    menu_state.menu_type = 'horizontal'
    menu_state.selected = selected 
    menu_state.title = style_text({'style': 'bold'}, 'Inspeacting Weapon | Shop | Balance: ', style_text({'color':[201, 237, 154]}, f"${player.balance}"), f" | Level: ") + Text(str(player.level))

    # Checks player's balance, weapon's price
    balance = player.balance
    price = weapon['price']
    # If player has equal or more money than the price, or the weapon is free
    afford = balance >= price or price == 0 

    # Checks player's level and if it meets level requirement
    level = player.level
    level_requirement = weapon['levelRequirement']
    correct_level = level >= level_requirement
    # If player has weapon in their inventory
    owned = weapon_id in player.inventory

    # Get weapon's abilities
    abilities = weapon['abilities']

    def on_press(key):
        """
        Handle key inputs required for the menu
        Horizontal-type menus use left and right keys for navigation
        
        Parameters:
        key (str): The key that was pressed by the player.
        """
        nonlocal owned
        nonlocal afford
        nonlocal correct_level

        if key == ('left' if player.use_arrow_keys else 'a'):  # Left arrow / A key
            update_selection(-1)
        elif key == ('right' if player.use_arrow_keys else 'd'):  # Right arrow / D key
            update_selection(1)
        elif key == 'enter': 
            # If player meets level requirement, can afford it, and doesn't own it already
            if afford and correct_level and not owned:
                # Sends player to weapon purchase confirmation menu
                shop_buy_weapon(weapon, weapon_name, weapon_id, price, menu_state.selected)
        elif key == 'esc':
            shop_menu(old_selected)  # Go back to the shop menu with old_selected 

    def update_selection(delta):
        """
        Update the selected option and redraw the menu.

        Parameters:
        delta (int): The change in selection (either +1 or -1 to move up or down).
        """
        nonlocal abilities
        # Update the selected ability index
        new_selected = menu_state.selected + delta
        if 0 <= new_selected < len(abilities):
            menu_state.selected = new_selected
            update_menu_info()  # Update the displayed info and tooltip
            redraw_menu()

    def update_menu_info():
        """Update the info and tooltip based on the selected enemy"""
        nonlocal owned
        nonlocal afford
        nonlocal correct_level
        nonlocal abilities

        # ===================
        # Set up weapon info:
        # ===================

        # Start displayed price with bold label
        price_info = style_text({'style': 'bold'}, 'Price: ')
        # Set price value color: green if player can afford weapon, red if not
        price_color = [201, 237, 154] if afford else [227, 104, 104]
        # Append styled price value with label and finalize price info
        price_info += style_text({'color': price_color}, f"${price}")

        # Start displayed level with bold label
        level_info = style_text({'style': 'bold'}, 'Level required: ') 
        # Set level required value color: green if level requirement met, red if not
        level_color = [201, 237, 154] if correct_level else [227, 104, 104] 
        # Append styled level requirement value with label 
        level_info += style_text({'color': level_color}, f"{level_requirement}")
        # Show lock symbol, or italic 'Locked' label if player prefers text labels over symbols
        locked_text = style_text({'style': 'italic'}, ' (Locked)') if player.display_text else Text(" 🔒")
        # Add lock indicator if level requirement is not met, and finalize level info
        level_info += Text() if correct_level else locked_text

        # Combine weapon name, description, price, and level info
        weapon_info = Text(" ") + weapon_name + Text(f" \n{wrap_text(weapon['description'], indent="  ")}") + Text(f"\n  ") + price_info + Text(f"\n  ") + level_info

        # ===================
        # Set up ability info:
        # ===================
        
        # Get selected ability stats (e.g. damage, hit chance)
        ability_stats = abilities[menu_state.selected]
        # Get information of selected ability (e.g. name, description) from attacks data
        ability_info = next((att for att in globals.attacks if att['id'] == ability_stats['id']), None) 

        # Create ability title, including selected ability's index and total abilities
        ability_title = Text(f'\n == ABILITIES ({menu_state.selected + 1}/{len(abilities)}) ==\n')
        # Style ability's name
        ability_name = style_text(ability_info['title'], f" {ability_info['name']}")
        # Format the ability description, replacing placeholders with actual values for damage and hit chance
        ability_description = ability_info['description'].format(minDamage = ability_stats['minDamage'], maxDamage = ability_stats['maxDamage'], missChance = 100 - ability_stats['hitChance'])
        # Combine the title, name, and formatted description into the full ability info display
        ability_info = ability_title + ability_name + Text(f"\n{wrap_text(ability_description, indent="  ")}")
        
        # Combine the weapon info and ability info into the full menu information for display
        menu_state.info = weapon_info + ability_info
        
        # ====================
        # Set up tooltip info:
        # ====================

        # Prepare the tooltip for navigating abilities, displayed only if there are multiple abilities and if the player has controls enabled
        ability_tooltip = 'Arrow Keys ←/→ to navigate abilities\n' if len(abilities) > 1 and player.display_controls else ''

        # Prepare the text for the 'enter' action based on the player's status with the weapon
        enter_string = '' 
        if owned:
            # If the player already owns the weapon, display warning
            enter_string = style_text({'style':'bold italic'}, 'You already own this weapon!')
        elif not correct_level:
            # If the player does not meet weapon's level requirement, display warning
            enter_string = style_text({'style':'bold italic'}, 'You cannot purchase this weapon yet!')
        elif not afford:
            # If the player cannot afford the weapon, display warning
            enter_string = style_text({'style':'bold italic'}, 'You cannot afford this weapon yet!')
        else:
            # If the player can purchase the weapon, show the option to press 'ENTER' to purchase
            enter_string = 'ENTER to purchase'
        # Set the tooltip with the ability-specific navigation instructions, enter action prompt, and escape to go back if controls are enabled
        menu_state.tooltip =  style_text({'style':'italic'}, ability_tooltip, enter_string, ' | ESC to go back' if player.display_controls else '')

        redraw_menu()

    # Set the keyboard handler to this menu's key-input handler
    keyboard_manager.set_handler(on_press)
    update_menu_info() 

def shop_buy_weapon(weapon, weapon_name, weapon_id, price, old_selected=0):
    """
    Displays the (selected) weapon purchase confirmation menu when player presses ENTER in the shop (selected) weapon inspection menu.
    Players can select 'Yes' if they want to purchase the selected weapon, otherwise 'No' goes back to the shop (selected) weapon inspection menu.

    Parameters:
    weapon (dictionary): Data of the selected weapon
    weapon_name (str or Text): (Styled) name of the selected weapon
    weapon_id (str): ID of the selected weapon
    price (int)": Price of the selected weapon
    
    old_selected (int): The index of the pre-selected option for the shop weapon inspection menu. 
                        Used to restore the player's selection in the shop weapon inspection menu when returning from here. 
                        Defaults to 0 if not set.
    """

    # Set up the menu state for the weapon purchase confirmation menu
    menu_state.options = [style_text({'style': 'bold'}, 'No'), style_text({'style': 'bold'}, 'Yes')]
    menu_state.menu_type = 'basic'
    menu_state.selected = 0
    menu_state.title = style_text({'style': 'bold'}, f"Are you sure you want to purchase ", weapon_name, "?")
    menu_state.info = style_text({'style': 'bold'}, ' Price: ') + style_text({'color': [201, 237, 154]}, f"${weapon['price']}") + style_text({'style': 'bold'}, '\n Your balance: ') + style_text({'color': [201, 237, 154]}, f"${player.balance}")
    menu_state.tooltip = style_text({'style': 'italic'}, 'Arrow Keys ↑/↓ to navigate | ENTER to select | ESC to go back' if player.display_controls else '')
    
    def update_selection(new_selection):
        """Update selection and redraw menu"""
        # No wrap around in here
        menu_state.selected = new_selection
        redraw_menu()
    
    def on_press(key):
        """
        Handle key inputs required for the menu
        Basic-type menus use up and down keys for navigation
        
        Parameters:
        key (str): The key that was pressed by the player.
        """
        if key == ('up' if player.use_arrow_keys else 'w'):  # Up arrow / W key
            update_selection(0)
        elif key == ('down' if player.use_arrow_keys else 's'):  # Down arrow / S key
            update_selection(1)
        elif key == 'enter': 
            if menu_state.selected == 0: # Selects 'No'
                debug.info(f"Did not purchase {weapon_name}")
            elif menu_state.selected == 1: # Selects 'Yes'
                player.inventory.append(weapon_id) # Add weapon to inventory
                player.balance -= price # Subtract player's balance with price
                debug.info(f"Purchased {weapon_name}")
                player.save()
            # Go back to shop weapon inspection menu with the old_selected value
            shop_view_weapon(weapon, weapon_name, weapon_id, old_selected)
        elif key == 'esc': 
            # Go back to shop weapon inspection with the old_selected value
            shop_view_weapon(weapon, weapon_name, weapon_id, old_selected)

    # Set the keyboard handler to this menu's key-input handler
    keyboard_manager.set_handler(on_press)
    redraw_menu()

def inventory_menu(selected=0, old_selected=0):
    """
    Displays the inventory menu when player selects 'Inventory' from the main menu.
    Shows the player's balance, level, and available weapons' names with labels indicating level requirement eligibility.
    Selection of a weapon sends the player to the inventory weapon inspection menu.

    Parameters:
    selected (int): The index of the pre-selected option for this menu. 
                    Used to restore the player's selection when returning here from other menus or functions. 
                    Defaults to 0 if not set.

    old_selected (int): The index of the pre-selected option for the main menu. 
                        Used to restore the player's selection in the main menu when returning from here. 
                        Defaults to 0 if not set.
    """
    
    # Set sorting state
    menu_state.sort_type = player.settings.get('invSortType', 'levelRequirement')
    menu_state.sort_order = player.settings.get('invSortAscending', True)

    # Get sort keybinds from player
    sort_type_keybind = player.settings['primarySortKeybind']
    sort_order_keybind = player.settings['secondarySortKeybind']

    # Set up the menu state for the inventory menu
    menu_state.menu_type = 'paged'
    menu_state.selected = selected 
    menu_state.title = style_text({'style':'bold'}, f"Inventory | Level ") + Text(str(player.level))
    menu_state.info = None 
    menu_state.page_size = 5 

    current_option = None # Initialize selected option

    # Sort inventory by level requirement
    player.inventory = sorted(
        player.inventory, 
        key = lambda weapon_id: next((item['levelRequirement'] for item in globals.weapons if item['id'] == weapon_id), 0)
    )

    # Store old sort_type and sort_order
    sort_type = menu_state.sort_type
    sort_order = menu_state.sort_order
    # Initialize displayed inventory options
    displayed_inventory = sort_displayed_weapons(sort_type, sort_order, player.inventory)

    def on_press(key):
        """
        Handle key inputs required for the menu
        Paged-type menus use up and down keys for navigating options in the current page
        and use left and right keys for switching pages in the menu
        
        Parameters:
        key (str): The key that was pressed by the player.
        """
        nonlocal current_option
        if key == ('up' if player.use_arrow_keys else 'w'):  # Left arrow / W key
            update_selection(-1)
        elif key == ('down' if player.use_arrow_keys else 's'):  # Right arrow / S key
            update_selection(1)
        # Left arrow / A key
        elif key == ('left' if player.use_arrow_keys else 'a') and menu_state.current_page > 0:
            # Switch to previous page if current page isn't the first one
            menu_state.current_page -= 1  # Move to the previous page
            menu_state.selected = menu_state.current_page * menu_state.page_size  # Set selected to the first item of the page
            redraw_menu()
        # Right arrow / D key
        elif key == ('right' if player.use_arrow_keys else 'd') and menu_state.current_page < menu_state.total_pages - 1: 
            # Switch to next page if current page isn't the last one
            menu_state.current_page += 1  # Move to the next page
            menu_state.selected = menu_state.current_page * menu_state.page_size  # Set selected to the first item of the page
            redraw_menu()
        elif key == 'enter': 
            if current_option:
                current_weapon_id = current_option[0] # Get ID of selected weapon
                current_weapon = current_option[1] # Get data of selected weapon
                current_weapon_name = style_text(current_weapon['title'], current_weapon['name']) # Get and style name of selected weapon
                # Sends player to the inventory weapon inspection menu of the selected weapon
                inv_view_weapon(current_weapon, current_weapon_name, current_weapon_id, menu_state.selected)
        elif key == 'esc': 
            main_menu(old_selected)  # Go back to the main menu
        elif key == sort_type_keybind: # Key set for the sort type keybind
            keys = ['levelRequirement', 'price'] # Existing types to sort
            player.settings['invSortType'] = keys[(keys.index(menu_state.sort_type) + 1) % len(keys)] # Set the sort type to the next key
            update_menu_info() # Update displayed menu
            player.save(debugging=False) # Save player data to save file
        elif key == sort_order_keybind: # Key set for the sort order keybind
            player.settings['invSortAscending'] = not player.settings['invSortAscending'] # Set to opposite sort type
            update_menu_info()
            player.save(debugging=False)

    def update_selection(delta):
        """
        Update the selected option and redraw the menu.

        Parameters:
        delta (int): The change in selection (either +1 or -1 to move up or down).
        """
        valid_indices = list(range(menu_state.start_index, min(menu_state.start_index + menu_state.page_size, len(menu_state.options))))
        if delta < 0:  # Moving up (previous selection)
            if menu_state.selected == valid_indices[0]:  # If at the top, loop to the bottom
                menu_state.selected = valid_indices[-1]
            else:
                menu_state.selected = valid_indices[valid_indices.index(menu_state.selected) + delta]
        else:  # Moving down (next selection)
            if menu_state.selected == valid_indices[-1]:  # If at the bottom, loop to the top
                menu_state.selected = valid_indices[0]
            else:
                menu_state.selected = valid_indices[valid_indices.index(menu_state.selected) + delta]
        update_menu_info()

    def update_menu_info():
        """Update options and tooltip based on sort order/type"""

        nonlocal current_option
        nonlocal displayed_inventory
        nonlocal sort_type
        nonlocal sort_order

        # If sort type and sort order was changed, re-sort and display inventory
        if menu_state.sort_type != sort_type or menu_state.sort_order != sort_order:
            sort_type = menu_state.sort_type
            sort_order = menu_state.sort_order
            displayed_inventory = sort_displayed_weapons(sort_type, sort_order, player.inventory)

        # ==================
        # Menu options setup
        # ==================

        options = [] # Initialize options
        old_inventory = list(player.inventory) # Get old inventory to compare with updated inventory
        # Iterate through the displayed shop weapons to generate menu options
        for weapon_id in displayed_inventory:
            weapon = next((item for item in globals.weapons if item['id'] == weapon_id), None) # Get weapon from weapons data based on weapon's ID
            if weapon:
                # Style weapon name for displayed option
                option_text = style_text(weapon['title'], weapon['name'])

                # Check if player already equipped the weapon
                if player.equipped == weapon_id :
                    owned_text = style_text({'style': 'italic'}, ' (Equipped)') if player.display_text else Text(" ✅")
                    option_text += owned_text
                # If the player does not meet level requirement
                elif player.level < weapon['levelRequirement']:
                    # Add a label beside the option: lock symbol, or italic 'Locked' text if player prefers text labels over symbols
                    locked_text = style_text({'style': 'italic'}, ' (Locked)') if player.display_text else Text(" 🔒")
                    option_text += locked_text  
                # Add weapon id, weapon data, and option text to the options list
                options.append((weapon_id, weapon, option_text))
            else: # If no data was found for given weapon ID
                debug.warning(f"Error trying to find weapon with ID: {weapon_id}, removing item off inventory.")
                player.inventory.remove(weapon_id)
        # If the inventory had removed weapons, the save to player
        if len(old_inventory) != len(player.inventory): player.save(debugging=False)
        # Get selected option
        current_option = options[menu_state.selected]  
        # Update the menu options to display the option texts
        menu_state.options = [option[2] for option in options]
        
        # ==================
        # Menu tooltips setup
        # ==================

        # Determine the order of sorting (ascending or descending)
        displayed_order = 'Ascending' if sort_order else "Descending"
        # Initialize the sort type display text as an empty string
        displayed_type = ""
        # Determine the sorting type and set the corresponding display text
        if sort_type == 'levelRequirement': 
            displayed_type = "Level"  # If sorting by level requirement
        elif sort_type == 'price': 
            displayed_type = "Price"  # If sorting by price

        # Create the tooltip for sorting information
        # This includes the sorting type and the sorting order (Ascending/Descending)
        # It also adds keybind hints if the player is configured to display controls
        sort_tooltip = f"Sorted by: {displayed_type}{f' ({sort_type_keybind.upper()})' if player.display_controls else ''} | {displayed_order}{f' ({sort_order_keybind.upper()})' if player.display_controls else ''}"
        # Create the control tooltip for navigation instructions
        # These will only appear if the player is configured to see controls
        control_tooltip =  '\nArrow Keys ↑/↓ to navigate items | Arrow Keys ←/→ to navigate pages | ENTER to select | ESC to go back' if player.display_controls else ''
        # Create the extra tooltip for item status, it will show "✅" for equipped items
        extra_tooltip = '\n✅ = Equipped' if player.display_extra else ''
        # Combine all the tooltips into one, with italic styling applied
        menu_state.tooltip = style_text({'style':'italic'}, sort_tooltip, control_tooltip, extra_tooltip)  

        redraw_menu()

    # Set the keyboard handler to this menu's key-input handler
    keyboard_manager.set_handler(on_press)
    update_menu_info() 

def inv_view_weapon(weapon, weapon_name, weapon_id, old_selected=0):
    """
    Displays the inventpry weapon inspection menu when player selects a weapon from the shop menu.
    Shows the player's balance and level at the title.
    Shows selected weapon's information, such as description, price, level requirement, and abilities
    Pressing ENTER equips the selected weapon.

    Parameters:
    weapon (dictionary): Data of the selected weapon
    weapon_name (str or Text): (Styled) name of the selected weapon
    weapon_id (str): ID of the selected weapon

    old_selected (int): The index of the pre-selected option for the inventory menu. 
                        Used to restore the player's selection in the inventory menu when returning from here. 
                        Defaults to 0 if not set.
    """

    # Set up the menu state for the shop weapon inspection menu
    menu_state.menu_type = 'horizontal'
    menu_state.selected = 0 
    menu_state.title = style_text({'style': 'bold'}, f"Inspeacting Weapon | Inventory | Level ") + Text(str(player.level))

    # Checks player's level and if it meets this weapon's level requirement
    level = player.level
    level_requirement = weapon['levelRequirement']
    correct_level = level >= level_requirement
    # Check if player has this weapon equipped
    equipped = player.equipped == weapon_id

    abilities = weapon['abilities']

    def on_press(key):
        """
        Handle key inputs required for the menu
        Horizontal-type menus use left and right keys for navigation
        
        Parameters:
        key (str): The key that was pressed by the player.
        """
        nonlocal correct_level
        nonlocal equipped

        if key == ('left' if player.use_arrow_keys else 'a'):  # Left arrow / A key
            update_selection(-1)
        elif key == ('right' if player.use_arrow_keys else 'd'):  # Right arrow / D key
            update_selection(1)
        elif key == 'enter': 
            # If player meets level requirement, and doesn't have it equipped already
            if not equipped and correct_level:
                player.equipped = weapon_id # Set equipped weapon 
                player.save(debugging=False) # Save to player

                debug.info(f"Equipped {weapon_name}")
                equipped = True  
                update_menu_info() 
        elif key == 'esc':
            inventory_menu(selected=old_selected)  # Go back to the inventory menu with old_selected value

    def update_selection(delta):
        """
        Update the selected option and redraw the menu.

        Parameters:
        delta (int): The change in selection (either +1 or -1 to move up or down).
        """
        nonlocal abilities
        # Update the selected ability index
        new_selected = menu_state.selected + delta
        if 0 <= new_selected < len(abilities):
            menu_state.selected = new_selected
            update_menu_info()

    def update_menu_info():
        nonlocal correct_level
        nonlocal equipped
        nonlocal abilities

        # ===================
        # Set up weapon info:
        # ===================

        # Set up equip label next to weapon name
        equipped_text = style_text({'style': 'italic'}, ' (Equipped)') if player.display_text else Text(" ✅")
        equipped_string = equipped_text if equipped else Text()

        # Initialize price info
        price_info = Text()
        # If weapp
        if weapon.get('price'):
            price = weapon['price']
            price_info = style_text({'style': 'bold'}, '\n  Price from shop: ') + style_text({'color': [201, 237, 154]}, f"${price}")

        # Start displayed level with bold label
        level_info = style_text({'style': 'bold'}, 'Level required: ') 
        # Set level required value color: green if level requirement met, red if not
        level_color = [201, 237, 154] if correct_level else [227, 104, 104] 
        # Append styled level requirement value with label 
        level_info += style_text({'color': level_color}, f"{level_requirement}")
        # Show lock symbol, or italic 'Locked' label if player prefers text labels over symbols
        locked_text = style_text({'style': 'italic'}, ' (Locked)') if player.display_text else Text(" 🔒")
        # Add lock indicator if level requirement is not met, and finalize level info
        level_info += Text() if correct_level else locked_text

        # Combine weapon name, description, price, and level info
        weapon_info = Text(" ") + weapon_name + equipped_string + Text(f" \n{wrap_text(weapon['description'], indent="  ")}") + price_info + Text(f"\n  ") + level_info

        # ===================
        # Set up ability info:
        # ===================
        
        # Get selected ability stats (e.g. damage, hit chance)
        ability_stats = abilities[menu_state.selected]
        # Get information of selected ability (e.g. name, description) from attacks data
        ability_info = next((att for att in globals.attacks if att['id'] == ability_stats['id']), None) 

        # Create ability title, including selected ability's index and total abilities
        ability_title = Text(f'\n == ABILITIES ({menu_state.selected + 1}/{len(abilities)}) ==\n')
        # Style ability's name
        ability_name = style_text(ability_info['title'], f" {ability_info['name']}")
        # Format the ability description, replacing placeholders with actual values for damage and hit chance
        ability_description = ability_info['description'].format(minDamage = ability_stats['minDamage'], maxDamage = ability_stats['maxDamage'], missChance = 100 - ability_stats['hitChance'])
        # Combine the title, name, and formatted description into the full ability info display
        ability_info = ability_title + ability_name + Text(f"\n{wrap_text(ability_description, indent="  ")}")
        
        # Combine the weapon info and ability info into the full menu information for display
        menu_state.info = weapon_info + ability_info
        
        # ====================
        # Set up tooltip info:
        # ====================

        # Prepare the tooltip for navigating abilities, displayed only if there are multiple abilities and if the player has controls enabled
        ability_tooltip = 'Arrow Keys ←/→ to navigate abilities\n' if len(abilities) > 1 and player.display_controls else ''

        # Prepare the text for the 'enter' action based on the player's status with the weapon
        enter_string = '' 
        if equipped:
            # If the player already equipped the weapon, display warning
            enter_string = style_text({'style':'bold italic'}, 'You already equipped this weapon!')
        elif not correct_level:
            # If the player does not meet weapon's level requirement, display warning
            enter_string = style_text({'style':'bold italic'}, 'You cannot equip this weapon yet!')
        else:
            # If the player can equip the weapon, show the option to press 'ENTER' to equip
            enter_string = 'ENTER to equip'
        # Set the tooltip with the ability-specific navigation instructions, enter action prompt, and escape to go back if controls are enabled
        menu_state.tooltip =  style_text({'style':'italic'}, ability_tooltip, enter_string, ' | ESC to go back' if player.display_controls else '')

        redraw_menu()

    # Set the keyboard handler to this menu's key-input handler
    keyboard_manager.set_handler(on_press)
    update_menu_info() 

def settings_menu(selected=0, old_selected=0):
    """
    Displays the settings menu when player selects 'Settings' from the main menu.
    Shows the settings...

    Parameters:
    selected (int): The index of the pre-selected option for this menu. 
                    Used to restore the player's selection when returning here from other menus or functions. 
                    Defaults to 0 if not set.

    old_selected (int): The index of the pre-selected option for the main menu. 
                        Used to restore the player's selection in the main menu when returning from here. 
                        Defaults to 0 if not set.
    """
    options = [
        TwoStateSetting(style_text({'style': 'bold italic'}, 'Show keyboard controls on tooltips:'), 'displayControls'),
        TwoStateSetting(style_text({'style': 'bold italic'}, 'Show text instead of symbols for labels:'), 'displayTextTooltips'),
        TwoStateSetting(style_text({'style': 'bold italic'}, 'Show additional tooltips for symbols:'), 'displayExtraTooltips', None, {'displayTextTooltips': False}, False),
        TwoStateSetting(style_text({'style': 'bold italic'}, 'Switch navigation controls:'), 'useArrowKeys', ['WASD', 'Arrow Keys']),
        TwoStateSetting(style_text({'style': 'bold italic'}, 'Faster battle logs'), 'fasterBattleLogs'),
        KeyBindSetting(style_text({'style': 'bold italic'}, 'Set keybind for sort key:'), 'primarySortKeybind', ['secondarySortKeybind']),
        KeyBindSetting(style_text({'style': 'bold italic'}, 'Set keybind for sort order:'), 'secondarySortKeybind', ['primarySortKeybind']),
    ]

    # Set up the menu state for the settings menu
    menu_state.menu_type = 'paged'
    menu_state.selected = selected 
    menu_state.title = style_text({'style':'bold'}, 'Settings')
    menu_state.info = None 
    menu_state.page_size = 5 

    def on_press(key):
        """
        Handle key inputs required for the menu
        Paged-type menus use up and down keys for navigating options in the current page
        and use left and right keys for switching pages in the menu
        
        Parameters:
        key (str): The key that was pressed by the player.
        """
        if key == ('up' if player.use_arrow_keys else 'w'): # Up arrow / W key
            update_selection(-1)
        elif key == ('down' if player.use_arrow_keys else 's'): # Down arrow / S key
            update_selection(1)
        # Left arrow / A key
        elif key == ('left' if player.use_arrow_keys else 'a') and menu_state.current_page > 0:
            # Switch to previous page if current page isn't the first one
            menu_state.current_page -= 1  # Move to the previous page
            menu_state.selected = menu_state.current_page * menu_state.page_size  # Set selected to the first item of the page
            redraw_menu()
        # Right arrow / D key
        elif key == ('right' if player.use_arrow_keys else 'd') and menu_state.current_page < menu_state.total_pages - 1: 
            # Switch to next page if current page isn't the last one
            menu_state.current_page += 1  # Move to the next page
            menu_state.selected = menu_state.current_page * menu_state.page_size  # Set selected to the first item of the page
            redraw_menu()
        elif key == 'enter':
            handle_enter()
        elif key == 'esc':  
            main_menu(old_selected)  # Go back to the main menu with old_selected value

    def update_selection(delta):
        """
        Update the selected option and redraw the menu.

        Parameters:
        delta (int): The change in selection (either +1 or -1 to move up or down).
        """
        valid_indices = list(range(menu_state.start_index, min(menu_state.start_index + menu_state.page_size, len(menu_state.options))))
        if delta < 0:  # Moving up (previous selection)
            if menu_state.selected == valid_indices[0]:  # If at the top, loop to the bottom
                menu_state.selected = valid_indices[-1]
            else:
                menu_state.selected = valid_indices[valid_indices.index(menu_state.selected) + delta]
        else:  # Moving down (next selection)
            if menu_state.selected == valid_indices[-1]:  # If at the bottom, loop to the top
                menu_state.selected = valid_indices[0]
            else:
                menu_state.selected = valid_indices[valid_indices.index(menu_state.selected) + delta]
        update_menu_info()

    def handle_enter():
        """
        Handles the action when the Enter key is pressed.
        Toggles or updates the setting based on the selected option.
        If the selected option is a two-state setting, it toggles its state.
        If the selected option is a keybind setting, it opens the keybind configuration menu.
        """
        nonlocal options
        
        # Get the selected option and its ID
        selected_option = options[menu_state.selected]
        id = selected_option.id
        setting = player.settings.get(id)

        if setting is not None: # If the setting exists
        # Check if the selected option is a two-state setting
            if isinstance(selected_option, TwoStateSetting):
            # Toggle the setting value (True/False)
                player.settings[id] = not player.settings[id]
                player.save()
                debug.info(f"{'Enabled' if player.settings[id] is True else 'Disabled'} setting: {id}")

                update_menu_info() 
            # If it's a keybind setting, open the keybind configuration menu
            elif isinstance(selected_option, KeyBindSetting):
                set_keybind_menu(selected_option, menu_state.selected)
        else:
            debug.warning(f"Error finding setting: {id}")

    def update_menu_info():
        """
        Updates the menu options based on the player's settings.
        Disables options if certain dependencies aren't met.
        Updates the display text to reflect the state of each setting.
        """
        nonlocal options

        displayed_options = []

        # Iterate over each option in the menu
        for option in options:
            text = option.text
            id = option.id
            setting = player.settings.get(id, None)

            # Check if the setting has dependencies and if they are satisfied
            dependencies = option.dependencies
            disabled = False
            
            # Check if the dependencies are met
            if dependencies and isinstance(dependencies, dict):
                for dep_id, dep_value in dependencies.items():
                    if player.settings.get(dep_id) != dep_value:
                        disabled = True
                        break
            
            # If any dependency is not met, disable the option
            if disabled:
                player.settings[option.id] = option.disabled_value
                player.save(debugging=False)
                continue

            # If the option is a TwoStateSetting, display it with On/Off states
            if isinstance(option, TwoStateSetting):
                states = list(option.states)
                if player.display_text and option.states == ['', '✅']:
                    states[0] = style_text({'style': 'italic'}, 'Off')
                    states[1] = style_text({'style': 'italic'}, 'On')
                displayed_options.append(text + Text(f" {states[1] if setting else states[0]}"))

            # If the option is a KeyBindSetting, display the keybinding or "Unassigned"
            elif isinstance(option, KeyBindSetting):
                setting = 'Unassigned' if setting is None else setting
                displayed_options.append(text + Text(f" {setting.upper()}"))

        # Update the menu options to reflect changes
        menu_state.options = displayed_options

        # Tooltip instructing controls (if enabled)
        menu_state.tooltip = style_text({'style': 'italic'}, 'Arrow Keys ↑/↓ to navigate items | ←/→ to navigate pages | ENTER to select | ESC to go back') if player.display_controls else None
        
        redraw_menu()

    # Set the keyboard handler to this menu's key-input handler
    keyboard_manager.set_handler(on_press)
    update_menu_info() 

def set_keybind_menu(selected_option, old_selected):
    """
    Handles keybinding for a selected option in the settings menu. 
    This function listens for key presses and assigns the key to the selected option if it is valid.

    Parameters:
    selected_option (TwoStateSetting/KeyBindSetting): The selected setting option to bind a key.

    old_selected (int): The index of the pre-selected option for the settings menu. 
                        Used to restore the player's selection in the settings menu when returning from here. 
    """
    blacklisted_keybind = None  # Track if a key is blacklisted

    def on_press(key):
        nonlocal blacklisted_keybind

        # Check for keys that are blacklisted because they are used for game navigation
        if key in ['up', 'down', 'left', 'right', 'enter', 'w', 'a', 's', 'd']: 
            blacklisted_keybind = key
            update_menu()  # Refresh menu to show the conflict message

        # Check for conflicts with other keybinds (from dependencies)
        elif key in [player.settings[other_keybind] for other_keybind in selected_option.dependencies or [] if other_keybind in player.settings]:
            blacklisted_keybind = key
            update_menu()  # Refresh menu to show the conflict message

        # Handle the ESC key to cancel and return to the settings menu
        elif key == 'esc':  
            settings_menu(old_selected)  # Go back to the settings menu

        # Otherwise, set the keybind if no conflicts or blacklist
        else:
            player.settings[selected_option.id] = key
            player.save(debugging=False)  # Save the keybind
            settings_menu(old_selected)  # Go back to the settings menu

    def update_menu():
        """Update tooltip based on settings"""
        nonlocal blacklisted_keybind

        # Clear terminal and display updated menu information
        clear_terminal()
        console.print(style_text({'style': 'bold'}, f"Settings | ", str(selected_option.text)))  # Title of the option
        if player.display_controls:
            console.print(style_text({'style': 'italic'}, 'Press any key to set | ESC to cancel'))  # Instructions for controls
        if blacklisted_keybind:
            console.print(style_text({'style': 'bold italic'}, f'You cannot set your keybind to {blacklisted_keybind.upper()}!'))  # Show conflict message
    
    keyboard_manager.set_handler(on_press)
    update_menu() 

# ========================
#       REDRAW LOGIC
# ========================

def redraw_menu(clear=True):
    """Redraw the menu."""
    if clear: clear_terminal()
    if menu_state.menu_type == 'basic':
        print_basic_menu(
            menu_state.options,
            menu_state.selected,
            menu_state.title,
            menu_state.info,
            menu_state.tooltip_before,
            menu_state.tooltip
        )
    elif menu_state.menu_type == 'horizontal':
        print_horizontal_menu(
            menu_state.info,
            menu_state.title,
            menu_state.tooltip
        )
    elif menu_state.menu_type == 'paged':
        # Call print_paged_menu and store the returned values
        current_page, total_pages, start_index = print_paged_menu(
            menu_state.options,
            menu_state.selected,
            menu_state.title,
            menu_state.tooltip,
            menu_state.page_size
        )
        # Update the menu state with paging information
        menu_state.current_page = current_page
        menu_state.total_pages = total_pages
        menu_state.start_index = start_index

# ========================
#     INITIALIZE GAME
# ========================

def load_game_data():
    """Loads game data including enemies, weapons, and player data."""
    load_enemies()
    load_weapons()
    player.load()

def main_loop():
    """Main game loop to display the menu and handle game flow."""
    main_menu()  # Display the main menu
    
    # Keep the game running until the exit option is selected
    while not menu_state.should_exit:
        time.sleep(0.1)  # Prevent CPU overload

keyboard_manager.start()  # Start keyboard listener
while True:
    """Main game loop with crash handling and restart"""
    try:
        globals.in_combat = False

        load_game_data() # Load game data
        main_loop() # Start the game

        break # If the game exits normally, break the loop
    except Exception as e:
        crash_handling(e) # Handle crash

        # ==========
        # Reset data
        # ==========

        # Reset global data
        globals.enemies = []
        globals.weapons = []
        globals.attacks = []
        globals.shop_weapons = []

        # Re-initialize player to reset player values to default
        player.__init__()

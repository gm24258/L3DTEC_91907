from menus import *
from utils import *
from fight import initiate_fight
from keyboard_manager import keyboard_manager
from globals import save_player
import globals

def load_enemy_data(enemy_directory):
    # Loads enemy data (main and attacks) into a single dictionary.
    
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
    # Loads enemy data from the ENEMIES_DIR and sorts by level requirement.
    for enemy_folder in os.listdir(ENEMIES_DIR):
        enemy_path = os.path.join(ENEMIES_DIR, enemy_folder)
        if os.path.isdir(enemy_path):  # Ensure it's a directory for an enemy
            enemy_data = load_enemy_data(enemy_path)
            globals.enemies.append(enemy_data)
    
    # Assuming each enemy has a 'main' data containing 'levelRequirement'
    globals.enemies = merge_sort(globals.enemies, 'levelRequirement')
    debug.info(f'Loaded {len(globals.enemies)} enemies.')

def load_attacks(): 
    # Loads weapon data from the WEAPONS_DIR and sorts by level requirement.    
    globals.attacks = load_data_from_directory(ATTACKS_DIR, 'attack')

def load_weapons(): 
    # Loads weapon data from the WEAPONS_DIR and sorts by level requirement.    
    globals.weapons = load_data_from_directory(WEAPONS_DIR, 'weapon')
    globals.weapons = merge_sort(globals.weapons, 'levelRequirement')
    load_attacks()
    debug.info(f'Loaded {len(globals.weapons)} weapons.')

    # Create a new list of globals.weapons from exisiting globals.weapons list but removes items that are not shop items
    globals.shop_weapons = [weapon['id'] for weapon in globals.weapons if weapon['inShop']]
    
# Player data
def load_player():
    globals.player = load_file_from_directory(DATA_DIR, 'save_file', 'template_')
    globals.settings = globals.player['settings']
    globals.display_controls = globals.settings['displayControls']
    globals.display_text = globals.settings['displayTextTooltips']
    globals.display_extra = globals.settings['displayExtraTooltips']
    debug.info('Loaded globals.player data:\n' + str(globals.player))

def sort_displayed_weapons(key, order, weapons_list):
    if key == 'price':
        displayed_shop_weapons = sorted(
            [
                weapon_id for weapon_id in weapons_list
                if next((weapon for weapon in globals.weapons if weapon['id'] == weapon_id and weapon['inShop'] is True), None) is not None
            ], 
            key = lambda weapon_id: next((item[key] for item in globals.weapons if item['id'] == weapon_id), 0),
            reverse = not order
        )
        not_in_shop_weapons = sorted(
            [
                weapon_id for weapon_id in weapons_list
                if next((weapon for weapon in globals.weapons if weapon['id'] == weapon_id and weapon['inShop'] is False), None) is not None
            ], 
            key = lambda weapon_id: next((item['levelRequirement'] for item in globals.weapons if item['id'] == weapon_id), 0),
            reverse = not order
        )
        if order: return displayed_shop_weapons + not_in_shop_weapons 
        else: return not_in_shop_weapons + displayed_shop_weapons
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
    def __init__(self):
        self.current_menu = None
        self.should_exit = False

        self.selected = 0
        self.options = []
        self.title = None
        self.info = None  # Used for horizontal menus
        self.tooltip_before = None
        self.tooltip = None
        self.menu_type = 'basic'  # Can be 'basic', 'horizontal', or 'paged'

        self.page_size = 5  # Used for paged menus
        self.current_page = 1
        self.total_pages = 1
        self.start_index = 0

        self.sort_type = None
        self.sort_order = None

# Initialize global state
menu_state = MenuState()

def crash_handling(e):
    globals.crashed = True
    keyboard_manager.stop()
    
    # Log the crash
    crash_log_path = os.path.join(LOGS_DIR, 'crash.log')
    debug.error(f"An error was caught and crashed the game. Please check {crash_log_path}")
    crash.error(f"Error caught while running the game:\n{e}\n{traceback.format_exc()}")

    clear_terminal()
    print("The game unexpectedly crashed! Restarting in a second...")
    time.sleep(2)

    globals.crashed = False
    menu_state.should_exit = False
    keyboard_manager.start()  # Start keyboard listener

# ========================
#       MENU FUNCTIONS
# ========================
def main_menu(selected=0):
    menu_state.options = ['Play', 'Shop', 'Inventory', 'Settings', 'Exit']
    menu_state.menu_type = 'basic'
    menu_state.selected = selected
    menu_state.title = style_text({'style': 'bold'}, 'Main Menu')
    menu_state.info = None
    menu_state.tooltip = style_text({'style': 'italic'}, 'Arrow Keys ↑/↓ to navigate | ENTER to select') if globals.display_controls else None

    def update_selection(delta):
        """Update the selected option and redraw the menu."""
        menu_state.selected = (menu_state.selected + delta) % len(menu_state.options)
        redraw_menu()
    
    def on_press(key):
        if key == 'up':  # Up arrow
            update_selection(-1)
        elif key == 'down':  # Down arrow
            update_selection(1)
        elif key == 'enter':  # Enter key
            handle_enter()

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

    # Register the keyboard handler
    keyboard_manager.set_handler(on_press)
    redraw_menu()

def exit_confirmation(old_selected):
    # Set up the menu state for the exit confirmation menu
    menu_state.options = ['Go Back', 'Confirm']
    menu_state.menu_type = 'basic'
    menu_state.selected = 0
    menu_state.title = style_text({'style': 'bold'}, 'Are you sure you want to exit?')
    menu_state.info = None
    menu_state.tooltip = style_text({'style': 'italic'}, 'Arrow Keys ↑/↓ to navigate | ENTER to select') if globals.display_controls else None

    def on_press(key):
        if key == 'up':  # Up arrow
            menu_state.selected = 0
            redraw_menu()
        elif key == 'down':  # Down arrow
            menu_state.selected = 1
            redraw_menu()
        elif key == 'enter':  # Enter key
            if menu_state.selected == 0:
                # Go back to main menu with the old_selected value
                main_menu(old_selected)
            elif menu_state.selected == 1: 
                save_player()
                print('\nExiting game...')
                menu_state.should_exit = True
        elif key == 'esc':  # ESC key
            # Go back to main menu with the old_selected value
            main_menu(old_selected)

    # Set the current menu handler
    keyboard_manager.set_handler(on_press)
    redraw_menu()

def play_selection_menu(selected=0, old_selected=0):
    # Set up the menu state for the play selection menu
    menu_state.menu_type = 'horizontal'
    menu_state.selected = selected  # Start with the first enemy selected
    menu_state.title = "Play"
    menu_state.tooltip = None  # Will be updated dynamically
    menu_state.info = None  # Will be updated dynamically

    def on_press(key):
        if key == 'left':
            update_selection(-1)
        elif key == 'right':
            update_selection(1)
        elif key == 'enter':
            handle_enter()
        elif key == 'esc':
            handle_escape()

    def update_selection(delta):
        # Update the selected enemy index
        new_selected = menu_state.selected + delta
        if 0 <= new_selected < len(globals.enemies):
            menu_state.selected = new_selected
            update_menu_info()  # Update the displayed info and tooltip
            redraw_menu()

    def handle_enter():
        """Handle enemy selection for combat"""
        current_enemy = globals.enemies[menu_state.selected]
        if globals.player['level'] >= current_enemy['levelRequirement']:
            play_confirm_fight(
                current_enemy,
                style_text(current_enemy['title'], current_enemy['name']),
                current_enemy['id'],
                old_selected=menu_state.selected
            )

    def handle_escape():
        """Return to main menu"""
        main_menu(old_selected)

    def update_menu_info():
        # Update the info and tooltip based on the selected enemy
        current_enemy = globals.enemies[menu_state.selected]
        level_requirement = current_enemy['levelRequirement']
        correct_level = globals.player['level'] >= level_requirement

        # Enemy info
        enemy_name = style_text(current_enemy['title'], current_enemy['name'])
        health_text = style_text({'style': 'bold'}, ' Health: ') + style_text({"color": [201, 237, 154]}, f"{current_enemy['health']}")
        level_info = style_text({'style': 'bold'}, ' Level required: ')
        level_color = [201, 237, 154] if correct_level else [227, 104, 104]  # Green if meeting level requirement, else red
        level_info += style_text({'color': level_color}, f"{level_requirement}")
        locked_text = style_text({'style': 'italic'}, ' (Locked)') if globals.display_text else Text(" 🔒")
        level_info += Text() if correct_level else locked_text

        menu_state.info = enemy_name + '\n' + health_text + '\n' + level_info

        # Tooltip
        prev_enemy = globals.enemies[menu_state.selected - 1] if menu_state.selected > 0 else None
        next_enemy = globals.enemies[menu_state.selected + 1] if menu_state.selected < len(globals.enemies) - 1 else None

        prev_enemy_name = style_text(prev_enemy['title'], prev_enemy['name']) if prev_enemy else Text('NONE')
        next_enemy_name = style_text(next_enemy['title'], next_enemy['name']) if next_enemy else Text('NONE')

        enter_string = f"{'' if globals.display_text else '⚔️  ' }{'ENTER to ' if globals.display_controls else ''}Fight" if correct_level else style_text({'style': 'bold italic'}, 'You cannot fight this enemy yet!')
        menu_state.tooltip = style_text({'style': 'italic'}, enter_string, ' | ', prev_enemy_name, ' ← | → ', next_enemy_name, '\nArrow Keys ←/→ to navigate | ESC to go back' if globals.display_controls else '')
    
    # Register the keyboard handler
    keyboard_manager.set_handler(on_press)
    update_menu_info()
    redraw_menu()

def play_confirm_fight(enemy, enemy_name, enemy_id, old_selected=0):
    # Set up info
    health_info = style_text({'style': 'bold'}, ' Health: ') + style_text({'color': [201, 237, 154]}, str(enemy['health']))
    enemy_level_info = style_text({'style': 'bold'}, '\n Level requirement: ') + style_text({'color': [201, 237, 154]}, str(enemy['levelRequirement']))
    player_level_info = style_text({'style': 'bold'}, '\n Your health: ') + style_text({'color': [201, 237, 154]}, str(globals.player['health']))
    player_level_info = style_text({'style': 'bold'}, '\n Your level: ') + style_text({'color': [201, 237, 154]}, str(globals.player['level']))

    # Set up the menu state
    menu_state.options = [style_text({'style': 'bold'}, 'No'), style_text({'style': 'bold'}, 'Yes')]
    menu_state.menu_type = 'basic'
    menu_state.selected = 0 
    menu_state.title = style_text({'style': 'bold'}, f"Are you sure you want to fight ", enemy_name, "?\n")
    menu_state.tooltip = style_text({'style': 'italic'}, 'Arrow Keys ↑/↓ to navigate | ENTER to select | ESC to go back' if globals.display_controls else '')
    menu_state.info = health_info + enemy_level_info + player_level_info

    def handle_selection_change(new_selection):
        """Update selection and redraw menu"""
        menu_state.selected = new_selection
        redraw_menu()

    def handle_no():
        """Return to selection menu without fighting"""
        debug.info(Text(f"Did not fight ") + enemy_name)
        play_selection_menu(selected=old_selected)

    async def handle_yes():
        """Initiate combat sequence"""
        debug.info(Text(f"Fighting ") + enemy_name)
        globals.in_combat = True
        try:
            await initiate_fight(enemy, enemy_name, enemy_id)
        except Exception as e:
            crash_handling(e)
        finally:
            play_selection_menu(selected=old_selected)
            
    def handle_escape():
        """Return to selection menu"""
        play_selection_menu(selected=old_selected)

    def on_press(key):
        if key == 'up':
            handle_selection_change(0)
        elif key == 'down':
            handle_selection_change(1)
        elif key == 'enter':
            if menu_state.selected == 0:
                handle_no()
            else:
                asyncio.run(handle_yes())
        elif key == 'esc':
            handle_escape()
            
    # Register the keyboard handler
    keyboard_manager.set_handler(on_press)
    redraw_menu()

def shop_menu(selected=0, old_selected=0):
    menu_state.sort_type = globals.settings.get('shopSortType', 'price')
    menu_state.sort_order = globals.settings.get('shopSortAscending', True)

    sort_type_keybind = globals.settings['primarySortKeybind']
    sort_order_keybind = globals.settings['secondarySortKeybind']

    # Store old sort_type and sort_order
    sort_type = menu_state.sort_type
    sort_order = menu_state.sort_order
    displayed_shop = sort_displayed_weapons(sort_type, sort_order, globals.shop_weapons)

    # Set up the menu state for the shop menu
    menu_state.menu_type = 'paged'
    menu_state.selected = selected
    menu_state.title = style_text({'style':'bold'}, 'Shop (Balance: ', style_text({'color':[201, 237, 154]}, f"${globals.player['money']}"), ')')
    menu_state.tooltip = None # Will be updated dynamically
    menu_state.info = None 
    menu_state.page_size = 5 

    current_option = None

    def on_press(key):
        nonlocal current_option
        if key == 'up':  # Left arrow
            update_selection(-1)
        elif key == 'down':  # Right arrow
            update_selection(1)
        elif key == 'left' and menu_state.current_page > 0:
            menu_state.selected = max(0, selected + menu_state.page_size)
            redraw_menu()
        elif key == 'right' and menu_state.current_page < menu_state.total_pages - 1: 
            menu_state.selected = min(len(menu_state.options) - 1, selected + menu_state.page_size)
            redraw_menu()
        elif key == 'enter':  # Enter key
            if current_option:
                current_weapon_id = current_option[0]
                current_weapon = current_option[1]
                current_weapon_name = style_text(current_weapon['title'], current_weapon['name'])
                shop_view_weapon(current_weapon, current_weapon_name, current_weapon_id, old_selected=menu_state.selected)
        elif key == 'esc':  # ESC key
            main_menu(old_selected)  # Go back to the main menu
        elif key == sort_type_keybind:
            keys = ['levelRequirement', 'price']
            menu_state.sort_type = keys[(keys.index(menu_state.sort_type) + 1) % len(keys)]
            update_menu_info() 
            redraw_menu()
            globals.settings['shopSortType'] = sort_type
            globals.player['settings'] = globals.settings
            save_player(debug=False)
        elif key == sort_order_keybind:
            menu_state.sort_order = not menu_state.sort_order
            globals.settings['shopSortAscending'] = menu_state.sort_order
            globals.player['settings'] = globals.settings
            update_menu_info() 
            redraw_menu()
            save_player(debug=False)

    def update_selection(delta):
        valid_indices = list(range(menu_state.start_index, min(menu_state.start_index + menu_state.page_size, len(menu_state.options))))
        if delta < 0: # Negative 
            if menu_state.selected == valid_indices[0]:
                menu_state.selected = valid_indices[-1]
            else:
                menu_state.selected = valid_indices[valid_indices.index(menu_state.selected) + delta]
        else: # Positive
            if menu_state.selected == valid_indices[-1]:
                menu_state.selected = valid_indices[0]
            else:
                menu_state.selected = valid_indices[valid_indices.index(menu_state.selected) + delta]
        update_menu_info()
        redraw_menu()

    def update_menu_info():
        nonlocal current_option
        nonlocal displayed_shop
        nonlocal sort_type
        nonlocal sort_order

        # Compare new sort type so that the shop isn't sorted all the time
        if menu_state.sort_type != sort_type or menu_state.sort_order != sort_order:
            sort_type = menu_state.sort_type
            sort_order = menu_state.sort_order
            displayed_shop = sort_displayed_weapons(sort_type, sort_order, globals.shop_weapons)

        options = []  
        for weapon_id in displayed_shop:
            weapon = next((item for item in globals.weapons if item['id'] == weapon_id), None)
            if weapon:
                option_text = style_text(weapon['title'], weapon['name'])
                if weapon_id in globals.player['inventory']:
                    owned_text = style_text({'style': 'italic'}, ' (Owned)') if globals.display_text else Text(" ✅")
                    option_text += owned_text
                elif globals.player['level'] < weapon['levelRequirement']:
                    locked_text = style_text({'style': 'italic'}, ' (Locked)') if globals.display_text else Text(" 🔒")
                    option_text += locked_text  
                options.append((weapon_id, weapon, option_text))
            else:
                debug.warning(f"Error trying to find weapon with ID: {weapon_id}")
        current_option = options[menu_state.selected]  
        
        displayed_order = 'Ascending' if sort_order else "Descending"
        displayed_type = ""
        if sort_type == 'levelRequirement': displayed_type = "Level"
        elif sort_type == 'price': displayed_type = "Price"
        sort_tooltip = f"Sorted by: {displayed_type}{f' ({sort_type_keybind.upper()})' if globals.display_controls else ''} | {displayed_order}{f' ({sort_order_keybind.upper()})' if globals.display_controls else ''}"
        control_tooltip =  '\nArrow Keys ↑/↓ to navigate items | Arrow Keys ←/→ to navigate pages | ENTER to select | ESC to go back' if globals.display_controls else ''
        extra_tooltip = '\n✅ = Purchased | 🔒 = Locked' if globals.display_extra else ''

        menu_state.tooltip = style_text({'style':'italic'}, sort_tooltip, control_tooltip, extra_tooltip)  
        menu_state.options = [option[2] for option in options]

    # Set the current menu handler
    keyboard_manager.set_handler(on_press)
    update_menu_info() 
    redraw_menu()

def shop_view_weapon(weapon, weapon_name, weapon_id, selected=0, old_selected=0):
    # Set up the menu state for the weapon inspection menu for shop
    menu_state.menu_type = 'horizontal'
    menu_state.selected = selected 
    menu_state.title = style_text({'style': 'bold'}, 'Inspeacting Weapon | Shop (Balance: ', style_text({'color':[201, 237, 154]}, f"${globals.player['money']}"), ')')
    menu_state.tooltip = None  # Will be updated dynamically
    menu_state.info = None  # Will be updated dynamically

    # Checks player's balance and if player can afford
    balance = globals.player['money']
    price = weapon['price']
    afford = balance >= price or price == 0 # If player has equal or more money than the price, or the weapon is free
    # Checks player's level and if it meets level requirement
    level = globals.player['level']
    level_requirement = weapon['levelRequirement']
    correct_level = level >= level_requirement
    # If player has weapon in their inventory
    owned = weapon_id in globals.player['inventory']

    abilities = weapon['abilities']

    def on_press(key):
        nonlocal owned
        nonlocal afford
        nonlocal correct_level

        if key == 'left':  # Left arrow
            update_selection(-1)
        elif key == 'right':  # Right arrow
            update_selection(1)
        elif key == 'enter':  # Enter key
            if afford and correct_level and not owned:
                shop_buy_weapon(weapon, weapon_name, weapon_id, price, menu_state.selected)
        elif key == 'esc':  # ESC key
            shop_menu(old_selected)  # Go back to the main menu

    def update_selection(delta):
        nonlocal abilities
        # Update the selected enemy index
        new_selected = menu_state.selected + delta
        if 0 <= new_selected < len(abilities):
            menu_state.selected = new_selected
            update_menu_info()  # Update the displayed info and tooltip
            redraw_menu()

    def update_menu_info():
        nonlocal owned
        nonlocal afford
        nonlocal correct_level
        nonlocal abilities

        # Price
        price_info = style_text({'style': 'bold'}, 'Price: ')
        price_color = [201, 237, 154] if afford else [227, 104, 104] # Green if afford else red
        price_info += style_text({'color': price_color}, f"${price}")

        # Level
        level_info = style_text({'style': 'bold'}, 'Level required: ')
        level_color = [201, 237, 154] if correct_level else [227, 104, 104] # Green if meeting level requirement else red
        level_info += style_text({'color': level_color}, f"{level_requirement}")
        locked_text = style_text({'style': 'italic'}, ' (Locked)') if globals.display_text else Text(" 🔒")
        level_info += Text() if correct_level else locked_text
        
        # ability: where the weapon's ability's stats are stored
        ability = abilities[menu_state.selected]
        # attack: where the weapon's ability's info is stored
        attack = next((att for att in globals.attacks if att['id'] == ability['id']), None) 

        # Info should be displayed like this:
        # Title
        #  Weapon Name
        #   Weapon description
        #  Weapon price: number
        #  Weapon level requirement: number
        #  == ABILITIES ==
        #  Ability name
        #   Ability description
        weapon_info = Text(" ") + weapon_name + Text(f" \n  {weapon['description']}") + Text(f"\n  ") + price_info + Text(f"\n  ") + level_info
        ability_title = Text(f'\n == ABILITIES ({menu_state.selected + 1}/{len(abilities)}) ==\n')
        ability_name = style_text(attack['title'], f" {attack['name']}")
        ability_description = attack['description'].format(minDamage = ability['minDamage'], maxDamage = ability['maxDamage'], hitChance = 100 - ability['hitChance'])
        ability_info = ability_title + ability_name + Text(f"\n  {ability_description}")

        enter_string = '' 
        if owned:
            enter_string = style_text({'style':'bold italic'}, 'You already own this weapon!')
        elif not correct_level:
            enter_string = style_text({'style':'bold italic'}, 'You cannot purchase this weapon yet!')
        elif not afford:
            enter_string = style_text({'style':'bold italic'}, 'You cannot afford this weapon yet!')
        else:
            enter_string = 'ENTER to purchase'
        ability_tooltip = 'Arrow Keys ←/→ to navigate abilities\n' if len(abilities) > 1 and globals.display_controls else ''

        menu_state.info = weapon_info + ability_info
        menu_state.tooltip =  style_text({'style':'italic'}, ability_tooltip, enter_string, ' | ESC to go back' if globals.display_controls else '')

    # Set the current menu handler
    keyboard_manager.set_handler(on_press)
    update_menu_info() 
    redraw_menu()

def shop_buy_weapon(weapon, weapon_name, weapon_id, price, old_selected=0):
    menu_state.options = [style_text({'style': 'bold'}, 'No'), style_text({'style': 'bold'}, 'Yes')]
    menu_state.menu_type = 'basic'
    menu_state.selected = 0
    menu_state.title = style_text({'style': 'bold'}, f"Are you sure you want to purchase ", weapon_name, "?")
    menu_state.info = style_text({'style': 'bold'}, ' Price: ') + style_text({'color': [201, 237, 154]}, f"${weapon['price']}") + style_text({'style': 'bold'}, '\n Your balance: ') + style_text({'color': [201, 237, 154]}, f"${globals.player['money']}")
    menu_state.tooltip = style_text({'style': 'italic'}, 'Arrow Keys ↑/↓ to navigate | ENTER to select | ESC to go back' if globals.display_controls else '')
        
    def on_press(key):
        if key == 'up':  # Up arrow
            menu_state.selected = 0
            redraw_menu()
        elif key == 'down':  # Down arrow
            menu_state.selected = 1
            redraw_menu()
        elif key == 'enter':  # Enter key
            if menu_state.selected == 0:
                debug.info(f"Did not purchase {weapon_name}")
            elif menu_state.selected == 1: 
                globals.player['inventory'].append(weapon_id)
                globals.player['money'] -= price
                debug.info(f"Purchased {weapon_name}")
                save_player()
            # Go back to shop weapon inspection with the old_selected value
            shop_view_weapon(weapon, weapon_name, weapon_id, old_selected)
        elif key == 'esc':  # ESC key
            # Go back to shop weapon inspection with the old_selected value
            shop_view_weapon(weapon, weapon_name, weapon_id, old_selected)

    # Set the current menu handler
    keyboard_manager.set_handler(on_press)
    redraw_menu()

def inventory_menu(selected=0, old_selected=0):
    menu_state.sort_type = globals.settings.get('invSortType', 'levelRequirement')
    menu_state.sort_order = globals.settings.get('invSortAscending', True)

    sort_type_keybind = globals.settings['primarySortKeybind']
    sort_order_keybind = globals.settings['secondarySortKeybind']

    # Set up the menu state for the inventory menu
    menu_state.menu_type = 'paged'
    menu_state.selected = selected 
    menu_state.title = style_text({'style':'bold'}, 'Inventory')
    menu_state.tooltip = None # Will be updated dynamically
    menu_state.info = None 
    menu_state.page_size = 5 

    current_option = None

    globals.player['inventory'] = sorted(
        globals.player['inventory'], 
        key = lambda weapon_id: next((item['levelRequirement'] for item in globals.weapons if item['id'] == weapon_id), 0)
    )

    # Store old sort_type and sort_order
    sort_type = menu_state.sort_type
    sort_order = menu_state.sort_order
    displayed_inventory = sort_displayed_weapons(sort_type, sort_order, globals.player['inventory'])

    def on_press(key):
        nonlocal current_option
        if key == 'up':  # Left arrow
            update_selection(-1)
        elif key == 'down':  # Right arrow
            update_selection(1)
        elif key == 'left' and menu_state.current_page > 0:
            menu_state.selected = max(0, selected + menu_state.page_size)
            redraw_menu()
        elif key == 'right' and menu_state.current_page < menu_state.total_pages - 1: 
            menu_state.selected = min(len(menu_state.options) - 1, selected + menu_state.page_size)
            redraw_menu()
        elif key == 'enter':  # Enter key
            if current_option:
                current_weapon_id = current_option[0]
                current_weapon = current_option[1]
                current_weapon_name = style_text(current_weapon['title'], current_weapon['name'])
                inv_view_weapon(current_weapon, current_weapon_name, current_weapon_id, menu_state.selected)
        elif key == 'esc':  # ESC key
            main_menu(old_selected)  # Go back to the main menu
        elif key == sort_type_keybind:
            keys = ['levelRequirement', 'price']
            menu_state.sort_type = keys[(keys.index(menu_state.sort_type) + 1) % len(keys)]
            update_menu_info() 
            redraw_menu()
            globals.settings['shopSortType'] = sort_type
            globals.player['settings'] = globals.settings
            save_player(debug=False)
        elif key == sort_order_keybind:
            menu_state.sort_order = not menu_state.sort_order
            globals.settings['shopSortAscending'] = menu_state.sort_order
            globals.player['settings'] = globals.settings
            update_menu_info() 
            redraw_menu()
            save_player(debug=False)

    def update_selection(delta):
        valid_indices = list(range(menu_state.start_index, min(menu_state.start_index + menu_state.page_size, len(menu_state.options))))
        if delta < 0: # Negative 
            if menu_state.selected == valid_indices[0]:
                menu_state.selected = valid_indices[-1]
            else:
                menu_state.selected = valid_indices[valid_indices.index(menu_state.selected) + delta]
        else: # Positive
            if menu_state.selected == valid_indices[-1]:
                menu_state.selected = valid_indices[0]
            else:
                menu_state.selected = valid_indices[valid_indices.index(menu_state.selected) + delta]
        update_menu_info()
        redraw_menu()

    def update_menu_info():
        nonlocal current_option
        nonlocal displayed_inventory
        nonlocal sort_type
        nonlocal sort_order

        # Compare new sort type so that the shop isn't sorted all the time
        if menu_state.sort_type != sort_type or menu_state.sort_order != sort_order:
            sort_type = menu_state.sort_type
            sort_order = menu_state.sort_order
            displayed_inventory = sort_displayed_weapons(sort_type, sort_order, globals.player['inventory'])

        options = [] 
        old_inventory = list(globals.player['inventory'])
        for weapon_id in displayed_inventory:
            weapon = next((item for item in globals.weapons if item['id'] == weapon_id), None)
            if weapon:
                option_text = style_text(weapon['title'], weapon['name'])
                equipped_text = style_text({'style': 'italic'}, ' (Equipped)') if globals.display_text else Text(" ✅")
                option_text += equipped_text if globals.player['equipped'] == weapon_id else Text()
                options.append((weapon_id, weapon, option_text))
            else:
                debug.warning(f"Error trying to find weapon with ID: {weapon_id}, removing item off inventory.")
                globals.player['inventory'].remove(weapon_id)
        if len(old_inventory) != globals.player['inventory']: save_player()
        current_option = options[menu_state.selected]  
        
        displayed_order = 'Ascending' if sort_order else "Descending"
        displayed_type = ""
        if sort_type == 'levelRequirement': displayed_type = "Level"
        elif sort_type == 'price': displayed_type = "Price"
        sort_tooltip = f"Sorted by: {displayed_type}{f' ({sort_type_keybind.upper()})' if globals.display_controls else ''} | {displayed_order}{f' ({sort_order_keybind.upper()})' if globals.display_controls else ''}"
        control_tooltip =  '\nArrow Keys ↑/↓ to navigate items | Arrow Keys ←/→ to navigate pages | ENTER to select | ESC to go back' if globals.display_controls else ''
        extra_tooltip = '\n✅ = Equipped' if globals.display_extra else ''

        menu_state.tooltip = style_text({'style':'italic'}, sort_tooltip, control_tooltip, extra_tooltip)  
        menu_state.options = [option[2] for option in options]

    # Set the current menu handler
    keyboard_manager.set_handler(on_press)
    update_menu_info() 
    redraw_menu()

def inv_view_weapon(weapon, weapon_name, weapon_id, old_selected=0):
    # Set up the menu state for the weapon inspection menu for inventory
    menu_state.menu_type = 'horizontal'
    menu_state.selected = 0 
    menu_state.title = style_text({'style': 'bold'}, 'Inspeacting Weapon | Inventory')
    menu_state.tooltip = None  # Will be updated dynamically
    menu_state.info = None  # Will be updated dynamically

    # Checks player's level and if it meets this weapon's level requirement
    level = globals.player['level']
    level_requirement = weapon['levelRequirement']
    correct_level = level >= level_requirement
    # Check if player has this weapon equipped
    equipped = globals.player['equipped'] == weapon_id

    abilities = weapon['abilities']

    def on_press(key):
        nonlocal correct_level
        nonlocal equipped

        if key == 'left':  # Left arrow
            update_selection(-1)
        elif key == 'right':  # Right arrow
            update_selection(1)
        elif key == 'enter':  # Enter key
            if not equipped and correct_level:

                globals.player['equipped'] = weapon_id
                save_player(debug=False)
                debug.info(f"Equipped {weapon_name}")

                equipped = True
                update_menu_info() 
                redraw_menu()
        elif key == 'esc':  # ESC key
            inventory_menu(selected=old_selected)  # Go back to the main menu

    def update_selection(delta):
        nonlocal abilities
        # Update the selected enemy index
        new_selected = menu_state.selected + delta
        if 0 <= new_selected < len(abilities):
            menu_state.selected = new_selected
            update_menu_info()  # Update the displayed info and tooltip
            redraw_menu()

    def update_menu_info():
        nonlocal correct_level
        nonlocal equipped
        nonlocal abilities
        
        equipped_text = style_text({'style': 'italic'}, ' (Equipped)') if globals.display_text else Text(" ✅")
        equipped_string = equipped_text if equipped else Text()

        # Price
        price_info = Text()
        if weapon.get('price'):
            price = weapon['price']
            price_info = style_text({'style': 'bold'}, '  Price from shop: ') + style_text({'color': [201, 237, 154]}, f"${price}\n")

        # Level
        level_info = style_text({'style': 'bold'}, 'Level required: ')
        level_color = [201, 237, 154] if correct_level else [227, 104, 104] # Green if meeting level requirement else red
        level_info += style_text({'color': level_color}, f"{level_requirement}")
        locked_text = style_text({'style': 'italic'}, ' (Locked)') if globals.display_text else Text(" 🔒")
        level_info += Text() if correct_level else locked_text
        
        # ability: where the weapon's ability's stats are stored
        ability = abilities[menu_state.selected]
        # attack: where the weapon's ability's info is stored
        attack = next((att for att in globals.attacks if att['id'] == ability['id']), None) 

        # Info should be displayed like this:
        # Title
        #  Weapon Name
        #   Weapon description
        #  Weapon price: number
        #  Weapon level requirement: number
        #  == ABILITIES ==
        #  Ability name
        #   Ability description

        weapon_info = Text(" ") + weapon_name + equipped_string + Text(f" \n  {weapon['description']}") + Text(f"\n  ") + price_info + Text(f"  ") + level_info
        ability_title = Text(f'\n == ABILITIES ({menu_state.selected + 1}/{len(abilities)}) ==\n')
        ability_name = style_text(attack['title'], f" {attack['name']}")
        ability_description = attack['description'].format(minDamage = ability['minDamage'], maxDamage = ability['maxDamage'], hitChance = 100 - ability['hitChance'])
        ability_info = ability_title + ability_name + Text(f"\n  {ability_description}")

        enter_string = '' 
        if equipped:
            enter_string = style_text({'style':'bold italic'}, 'You already equipped this weapon!')
        elif not correct_level:
            enter_string = style_text({'style':'bold italic'}, 'You cannot equip this weapon!')
        else:
            enter_string = 'ENTER to equip'
        ability_tooltip = 'Arrow Keys ←/→ to navigate abilities\n' if len(abilities) > 1 and globals.display_controls else ''

        menu_state.info = weapon_info + ability_info
        menu_state.tooltip =  style_text({'style':'italic'}, ability_tooltip, enter_string, ' | ESC to go back' if globals.display_controls else '')

    # Set the current menu handler
    keyboard_manager.set_handler(on_press)
    update_menu_info() 
    redraw_menu()

def settings_menu(selected=0, old_selected=0):
    options = [
        # Options/globals.settings:
        # (Styled text for setting name, id of setting, ['what to display beside text if off', 'what to display beside text if on'], {setting(s) that this one depends on: what state it has to be})
        TwoStateSetting(style_text({'style': 'bold italic'}, 'Show keyboard controls on tooltips:'), 'displayControls'),
        TwoStateSetting(style_text({'style': 'bold italic'}, 'Show text instead of symbols for labels:'), 'displayTextTooltips'),
        TwoStateSetting(style_text({'style': 'bold italic'}, 'Show additional tooltips for symbols:'), 'displayExtraTooltips', None, {'displayTextTooltips': False}, False),
        KeyBindSetting(style_text({'style': 'bold italic'}, 'Set keybind for sort key:'), 'primarySortKeybind', ['secondarySortKeybind']),
        KeyBindSetting(style_text({'style': 'bold italic'}, 'Set keybind for sort order:'), 'secondarySortKeybind', ['primarySortKeybind']),
    ]
    # Set up the menu state for the inventory menu
    menu_state.menu_type = 'paged'
    menu_state.selected = selected 
    menu_state.title = style_text({'style':'bold'}, 'Settings')
    menu_state.tooltip = None # Will be updated dynamically
    menu_state.info = None 
    menu_state.options = None # Will be updated dynamically
    menu_state.page_size = 5 

    def on_press(key):
        if key == 'up':  # Left arrow
            update_selection(-1)
        elif key == 'down':  # Right arrow
            update_selection(1)
        elif key == 'left' and menu_state.current_page > 0:
            menu_state.selected = max(0, selected + menu_state.page_size)
            redraw_menu()
        elif key == 'right' and menu_state.current_page < menu_state.total_pages - 1: 
            menu_state.selected = min(len(menu_state.options) - 1, selected + menu_state.page_size)
            redraw_menu()
        elif key == 'enter':  # Enter key
            handle_enter()
        elif key == 'esc':  # ESC key
            main_menu(old_selected)  # Go back to the main menu

    def update_selection(delta):
        valid_indices = list(range(menu_state.start_index, min(menu_state.start_index + menu_state.page_size, len(menu_state.options))))
        if delta < 0: # Negative 
            if menu_state.selected == valid_indices[0]:
                menu_state.selected = valid_indices[-1]
            else:
                menu_state.selected = valid_indices[valid_indices.index(menu_state.selected) + delta]
        else: # Positive
            if menu_state.selected == valid_indices[-1]:
                menu_state.selected = valid_indices[0]
            else:
                menu_state.selected = valid_indices[valid_indices.index(menu_state.selected) + delta]
        update_menu_info()
        redraw_menu()

    def handle_enter():
        nonlocal options
        
        selected_option = options[menu_state.selected]
        id = selected_option.id
        setting = globals.settings.get(id)

        if setting is not None: # If setting exists
            if isinstance(selected_option, TwoStateSetting):
                globals.settings[id] = not globals.settings[id]
                globals.player['settings'] = globals.settings
                save_player()
                debug.info(f"{'Enabled' if globals.settings[id] is True else 'Disabled'} setting: {id}")

                update_menu_info() 
                redraw_menu()
            elif isinstance(selected_option, KeyBindSetting):
                set_keybind_menu(selected_option, menu_state.selected)
        else:
            debug.warning(f"Error finding setting: {id}")

    def update_menu_info():
        nonlocal options

        
        displayed_options = []

        for option in options:
            text = option.text
            id = option.id
            setting = globals.settings[id] or None
            
            # Checks if user prefers text than symbols to indicate something

            # Checks if other setting(s) this setting depends on is the right value for it, if at least one value is incorrect, the setting is disabled
            dependencies = option.dependencies
            disabled = False
            if dependencies and isinstance(dependencies, dict):
                for i,v in dependencies.items():
                    if globals.settings[i] != v:
                        disabled = True
                        break
            
            # This option is skipped and no longer displayed
            if disabled:
                globals.settings[option.id] = option.disabled_value
                globals.player['settings'] = globals.settings
                save_player(debug=False)
                continue

            if isinstance(option, TwoStateSetting):
                states = list(option.states)
                if globals.display_text and option.states == ['', '✅']:
                    states[0] = style_text({'style': 'italic'}, 'Off')
                    states[1] = style_text({'style': 'italic'}, 'On')
                displayed_options.append(text + Text(f" {states[1] if setting is True else states[0]}"))
            elif isinstance(option, KeyBindSetting):
                setting = 'Unassigned' if setting is None else setting
                displayed_options.append(text + Text(f" {setting.upper()}"))
            # Placeholder for globals.settings with more than 3 options 
            # else:

        menu_state.tooltip = style_text({'style': 'italic'}, 'Arrow Keys ↑/↓ to navigate items | ←/→ to navigate pages | ENTER to select | ESC to go back') if globals.display_controls else None
        menu_state.options = displayed_options

    # Set the current menu handler
    keyboard_manager.set_handler(on_press)
    update_menu_info() 
    redraw_menu()

def set_keybind_menu(selected_option, old_selected):
    blacklisted_keybind = None

    def on_press(key):
        nonlocal blacklisted_keybind

        # Keys cannot be binded to these as these are required for navigating the game's UI
        if key in ['up', 'down', 'left', 'right', 'enter']: 
            blacklisted_keybind = key
            update_menu()
        # Keys cannot be binded to conflicting keybinds (inside dependencies)
        elif key in [globals.settings[other_keybind] for other_keybind in selected_option.dependencies or [] if other_keybind in globals.settings]:
            blacklisted_keybind = key
            update_menu()
        elif key == 'esc':  # ESC key
            settings_menu(old_selected)  # Go back to settings menu
        # Set keybind to key if no conflicts
        else:
            globals.settings[selected_option.id] = key
            globals.player['settings'] = globals.settings
            save_player(debug=False)

            settings_menu(old_selected)  # Go back to settings menu


    def update_menu():
        nonlocal blacklisted_keybind

        clear_terminal()
        console.print(style_text({'style':'bold'}, f"Settings | ", str(selected_option.text))) # title
        if globals.display_controls:
            console.print(style_text({'style':'italic'}, 'Press any key to set | ESC to cancel')) # tooltip
        if blacklisted_keybind:
            console.print(style_text({'style':'bold italic'}, f'You cannot set your keybind to {blacklisted_keybind}!'))
    
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

# Load data
def load_game_data():
    load_enemies()
    load_weapons()
    load_player()

def main_loop():
    main_menu()
    
    # Keep the game running until exit is selected
    while not menu_state.should_exit:
        time.sleep(0.1)  # Prevent CPU overload

# Main game loop with crash handling and restart
keyboard_manager.start()  # Start keyboard listener
while True:
    try:
        globals.in_combat = False

        # Load game data
        load_game_data()
        
        # Start the game
        main_loop()

        # If the game exits normally, break the loop
        break

    except Exception as e:
        crash_handling(e)
        # Reset data in globals to reload them
        ## Data loaded from game
        globals.enemies = []
        globals.weapons = []
        globals.attacks = []
        globals.shop_weapons = []

        ## Player data
        globals.player = []
        globals.settings = []
        globals.display_controls = True
        globals.display_extra = True
        globals.display_text = False

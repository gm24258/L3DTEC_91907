from menus import *
from utils import *
from data import *
from fight import *
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
    
# Tuesday March 11 12:15PM
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

def main_menu():
    # Main menu displayed at the start of the game that handles user selection

    options = ['Play', 'Shop', 'Inventory', 'Settings', 'Exit'] # Menu options in order
    selected = 0 # Tracks selected option

    while True:
        tooltip = style_text({'style': 'italic'}, 'Arrow Keys (↑/↓) to navigate | ENTER to select') if globals.display_controls else None
        print_basic_menu(options, selected, style_text({'style': 'bold'}, 'Main Menu'), tooltip) # Selected is saved so that the last option is selected when you go back to the main menu
        key = readchar.readkey()

        if key == readchar.key.UP:
            debug.debug("Pressed UP arrow key")
            selected = (selected - 1) % len(options)
        elif key == readchar.key.DOWN:
            debug.debug("Pressed DOWN arrow key")
            selected = (selected + 1) % len(options)
        elif key == readchar.key.ENTER:
            debug.debug('Pressed ENTER key')
            if selected == 0: # Play
                play_selection_menu()
            elif selected == 1: # Shop
                shop_menu()
            elif selected == 2: # Inventory
                inventory_menu()
            elif selected == 3: # Settings  
                settings_menu()
            elif selected == 4: # Exit
                global exit
                exit = exit_confirmation()
                if exit is True: break

def exit_confirmation():
    # Confirmation menu for exiting game. Returns True if globals.player confirms exit, False otherwise

    tooltip = style_text({'style': 'italic'}, 'Arrow Keys (↑/↓) to navigate | ENTER to select | ESC to go back') if globals.display_controls else ''
    selected = 0

    while True:
        print_basic_menu(['Go Back', 'Confirm'], selected, style_text({'style': 'bold'}, 'Are you sure you want to exit?'), tooltip)
        key = readchar.readkey()
        if key == readchar.key.UP:
            debug.debug("Pressed UP arrow key")
            selected = 0
        elif key == readchar.key.DOWN:
            debug.debug("Pressed DOWN arrow key")
            selected = 1
        elif key == readchar.key.ENTER:
            debug.debug('Pressed ENTER key')
            if selected == 0:
                return
            elif selected == 1: 
                save_player()
                print ('\nExiting game...')
                return True 
        elif key == readchar.key.ESC:
            debug.debug("Pressed ESC key")
            return

def play_selection_menu():
    # Checks list of globals.enemies then puts info in a string to be printed later
    locked_text = style_text({'style': 'italic'}, ' (Locked)') if globals.display_text else Text(" 🔒")

    enemy_info_strings = []
    for enemy in globals.enemies:
        # Create a rich Text object for each part
        enemy_name = style_text(enemy['title'], enemy['name'])
        health_text = style_text({'style': 'bold'}, ' Health: ') + style_text({"color":[201, 237, 154]}, f"{enemy['health']}")

        level_requirement = enemy['levelRequirement']
        correct_level = globals.player['level'] >= level_requirement

        level_info = style_text({'style': 'bold'}, ' Level required: ')
        level_color = [201, 237, 154] if correct_level else [227, 104, 104] # Green if meeting level requirement else red
        level_info += style_text({'color': level_color}, f"{level_requirement}")
        level_info += Text() if correct_level else locked_text

        # Append them to the list
        enemy_info_strings.append(enemy_name + '\n' + health_text + '\n' + level_info)

    selected = 0

    while True:
        current_enemy = globals.enemies[selected]
        current_enemy_name = style_text(current_enemy['title'], current_enemy['name'])
        level_requirement = current_enemy['levelRequirement']
        correct_level = globals.player['level'] >= level_requirement

        # Checks if there's previous enemy
        prev_enemy = globals.enemies[selected - 1] if selected > 0 else None
        prev_enemy_name = Text('NONE')
        if prev_enemy:
            enemy_title = prev_enemy['title']
            if enemy_title.get('style'):
                if not 'italic' in enemy_title['style']:
                    enemy_title['style'] += ' italic'
            else:
                enemy_title['style'] = 'italic'

            prev_enemy_name = style_text(enemy_title, prev_enemy['name'])
            prev_enemy_name += Text() if globals.player['level'] >= prev_enemy['levelRequirement'] else locked_text

        # Checks if there's next enemy
        next_enemy = globals.enemies[selected + 1] if selected < len(globals.enemies) - 1 else None
        next_enemy_name = Text('NONE')
        if next_enemy:
            enemy_title = next_enemy['title']
            if enemy_title.get('style'):
                if not 'italic' in enemy_title['style']:
                    enemy_title['style'] += ' italic'
            else:
                enemy_title['style'] = 'italic'

            next_enemy_name = style_text(enemy_title, next_enemy['name'])
            next_enemy_name += Text() if globals.player['level'] >= next_enemy['levelRequirement'] else locked_text

        enter_string = f'{'' if globals.display_text else '⚔️  ' }{'ENTER to ' if globals.display_controls else ''}Fight' if correct_level else style_text({'style': 'bold italic'}, 'You cannot fight this enemy yet!')
        tooltip = style_text({'style':'italic'}, enter_string,  ' | ', prev_enemy_name, ' ← | → ', next_enemy_name, '\nArrow Keys (←/→) to navigate | ESC to go back' if globals.display_controls else '')

        print_horizontal_menu(enemy_info_strings[selected], style_text({'style': 'bold'}, 'Play'), tooltip)
        key = readchar.readkey()

        if key == readchar.key.LEFT:
            debug.debug('Pressed LEFT arrow key')
            if selected > 0:
                selected -= 1
        elif key == readchar.key.RIGHT:
            debug.debug('Pressed RIGHT arrow key')
            if selected < len(globals.enemies) - 1:
                selected += 1
        elif key == readchar.key.ENTER:
            debug.debug('Pressed ENTER key')
            if correct_level:
                play_confirm_fight(current_enemy, current_enemy_name, current_enemy['id'])
        elif key == readchar.key.ESC:
            debug.debug("Pressed ESC key")
            return

def play_confirm_fight(enemy, enemy_name, enemy_id):
    health_info = style_text({'style': 'bold'}, ' Health: ') + style_text({'color': [201, 237, 154]}, str(enemy['health']))
    enemy_level_info = style_text({'style': 'bold'}, '\n Level requirement: ') + style_text({'color': [201, 237, 154]}, str(enemy['levelRequirement']))
    player_level_info = style_text({'style': 'bold'}, '\n Your health: ') + style_text({'color': [201, 237, 154]}, str(globals.player['health']))
    player_level_info = style_text({'style': 'bold'}, '\n Your level: ') + style_text({'color': [201, 237, 154]}, str(globals.player['level']))
    info = health_info + enemy_level_info + player_level_info

    options = [style_text({'style': 'bold'}, 'No'), style_text({'style': 'bold'}, 'Yes')]
    tooltip = style_text({'style': 'italic'}, 'Arrow Keys (↑/↓) to navigate | ENTER to select | ESC to go back' if globals.display_controls else '')
    selected = 0

    while True:
        print_basic_menu(options, selected, style_text({'style': 'bold'}, f"Are you sure you want to fight ", enemy_name, "?\n") + info, tooltip)
        key = readchar.readkey()
        if key == readchar.key.UP:
            debug.debug("Pressed UP arrow key")
            selected = 0
        elif key == readchar.key.DOWN:
            debug.debug("Pressed DOWN arrow key")
            selected = 1
        elif key == readchar.key.ENTER:
            debug.debug('Pressed ENTER key')
            if selected == 0:
                debug.info(Text(f"Did not fight ") + enemy_name)
                return
            elif selected == 1: 
                debug.info(Text(f"Fighting ") + enemy_name)
                battle(enemy, enemy_name, enemy_id)
                break
        elif key == readchar.key.ESC:
            debug.debug("Pressed ESC key")
            return

def shop_menu(selected=0):
    # Wednesday March 5 10:10AM
    # Shop menu for viewing and purchasing globals.weapons

    # Parameters
    # selected (int): Selected number to determine selected option. Default is 0.

    old_sort_type = globals.settings.get('shopSortType', 'price')
    old_sort_order = globals.settings.get('shopSortAscending', True)
    displayed_shop = sort_displayed_weapons(old_sort_type, old_sort_order, globals.shop_weapons)

    while True:
        sort_type = globals.settings.get('shopSortType', 'price')
        sort_order = globals.settings.get('shopSortAscending', True)
        sort_type_keybind = globals.settings['primarySortKeybind']
        sort_order_keybind = globals.settings['secondarySortKeybind']

        if sort_type != old_sort_type or sort_order != old_sort_order:
            old_sort_type = sort_type
            old_sort_order = sort_order
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
        page_size = 5

        current_option = options[selected]
        current_weapon_id = current_option[0]
        current_weapon = current_option[1]
        current_weapon_name = style_text(current_weapon['title'], current_weapon['name'])

        title = style_text({'style':'bold'}, 'Shop (Balance: ', style_text({'color':[201, 237, 154]}, f"${globals.player['money']}"), ')')
        
        displayed_type = ""
        if sort_type == 'levelRequirement': displayed_type = "Level"
        elif sort_type == 'price': displayed_type = "Price"
        displayed_order = 'Ascending' if sort_order else "Descending"
        sort_tooltip = f"Sorted by: {displayed_type}{f' ({sort_type_keybind.upper()})' if globals.display_controls else ''} | {displayed_order}{f' ({sort_order_keybind.upper()})' if globals.display_controls else ''}"
        
        control_tooltip =  '\nArrow Keys (↑/↓) to navigate items | Arrow Keys (←/→) to navigate pages | ENTER to select | ESC to go back\n' if globals.display_controls else ''
        extra_tooltip = '✅ = Purchased | 🔒 = Locked' if globals.display_extra else ''
        tooltip = style_text({'style':'italic'}, sort_tooltip, control_tooltip, extra_tooltip)
        current_page, total_pages, start_index = print_paged_menu([option[2] for option in options], selected, title, tooltip, page_size)
        key = readchar.readkey()

        # Ensure selected index points to a valid weapon (ignores empty slots)
        valid_indices = list(range(start_index, min(start_index + page_size, len(options))))

        if key == readchar.key.UP:
            debug.debug("Pressed UP arrow key")
            selected = valid_indices[-1] if selected == valid_indices[0] else valid_indices[valid_indices.index(selected) - 1]
        elif key == readchar.key.DOWN:
            debug.debug("Pressed DOWN arrow key")
            selected = valid_indices[0] if selected == valid_indices[-1] else valid_indices[valid_indices.index(selected) + 1]
        elif key == readchar.key.LEFT and current_page > 0:
            debug.debug('Pressed LEFT arrow key')
            selected = max(0, selected - page_size)  # Move to previous page
        elif key == readchar.key.RIGHT and current_page < total_pages - 1:
            debug.debug('Pressed RIGHT arrow key')
            selected = min(len(options) - 1, selected + page_size)  # Move to next page
        elif key == readchar.key.ENTER:
            debug.debug('Pressed ENTER key')
            shop_view_weapon(current_weapon, current_weapon_name, current_weapon_id, selected)
            break
        elif key == readchar.key.ESC:
            debug.debug("Pressed ESC key")
            return
        elif str(key) == sort_type_keybind or key == settings_keybinds.get(sort_type_keybind):
            debug.debug(f"Pressed {sort_type_keybind.upper()} key")
            keys = ['levelRequirement', 'price']
            sort_type = keys[(keys.index(sort_type) + 1) % len(keys)]
            globals.settings['shopSortType'] = sort_type
            globals.player['settings'] = globals.settings
            save_player(debug=False)
        elif str(key) == sort_order_keybind or key == settings_keybinds.get(sort_order_keybind):
            debug.debug(f"Pressed {sort_order_keybind.upper()} key")
            sort_order = not sort_order
            globals.settings['shopSortAscending'] = sort_order
            globals.player['settings'] = globals.settings
            save_player(debug=False)
        
def shop_view_weapon(weapon, weapon_name, weapon_id, old_selected):
    # Saturday March 8 10:04AM
    # Tuesday March 11 11:36AM
    # View stats of a selected weapon from shop

    # Parameters:
    # weapon (dict): Data of viewed weapon to display information
    # weapon_name (Text object): Styled weapon name string
    # weapon_id (str): Weapon ID used to handle if globals.player owns the weapon
    # old_selected (int): Selected number from shop_menu() function used when going back to shop
    
    debug.debug(f"Viewing from shop: {weapon_name}")
    selected = 0
    
    while True:
        # Checks globals.player's balance and if globals.player can afford
        balance = globals.player['money']
        price = weapon['price']
        afford = balance >= price or price == 0 # If globals.player has equal or more money than the price, or the weapon is free and somehow the globals.player has negative balance

        # Checks globals.player's level and if it meets level requirement
        level = globals.player['level']
        level_requirement = weapon['levelRequirement']
        correct_level = level >= level_requirement

        owned = weapon_id in globals.player['inventory'] # If globals.player has weapon in their inventory

        # Price
        price_info = style_text({'style': 'bold'}, '  Price: ')
        price_color = [201, 237, 154] if afford else [227, 104, 104] # Green if afford else red
        price_info += style_text({'color': price_color}, f"${price}\n")

        # Level
        level_info = style_text({'style': 'bold'}, '  Level required: ')
        level_color = [201, 237, 154] if correct_level else [227, 104, 104] # Green if meeting level requirement else red
        level_info += style_text({'color': level_color}, f"{level_requirement}")
        locked_text = style_text({'style': 'italic'}, ' (Locked)') if globals.display_text else Text(" 🔒")
        level_info += Text() if correct_level else locked_text

        weapon_info = weapon_name + Text(f"\n  {weapon['description']}\n") + price_info + level_info

        # Abilities
        abilities = weapon['abilities']
        ability = abilities[selected] # Selected ability

        true_title = style_text({'style': 'bold'}, 'Inspeacting Weapon | Shop (Balance: ', style_text({'color':[201, 237, 154]}, f"${globals.player['money']}"), ')\n ') # Actual title at the top
        title = true_title + weapon_info + Text(f'\n  == ABILITIES ({selected + 1}/{len(abilities)}) ==') # All the information stored in "title" to not conflict with actual options
        ability_info = style_text(ability['title'], f"   {ability['name']}\n   ") + Text(ability['description'])
        
        enter_string = '' 
        if owned:
            enter_string = style_text({'style':'bold italic'}, 'You already own this weapon!')
        elif not correct_level:
            enter_string = style_text({'style':'bold italic'}, 'You cannot purchase this weapon yet!')
        elif not afford:
            enter_string = style_text({'style':'bold italic'}, 'You cannot afford this weapon yet!')
        else:
            enter_string = 'ENTER to purchase' if globals.display_controls else ''

        ability_tooltip = 'Arrow Keys (←/→) to navigate abilities\n' if len(abilities) > 1 and globals.display_controls else ''
        tooltip =  style_text({'style':'italic'}, ability_tooltip, enter_string, ' | ESC to go back' if globals.display_controls else '')
        print_horizontal_menu(ability_info, title, tooltip)

        key = readchar.readkey()
        if key == readchar.key.LEFT:
            debug.debug('Pressed LEFT arrow key')
            if selected > 0:
                selected -= 1
        elif key == readchar.key.RIGHT:
            debug.debug('Pressed RIGHT arrow key')
            if selected < len(abilities) - 1:
                selected += 1
        elif key == readchar.key.ENTER:
            debug.debug('Pressed ENTER key')
            if afford and correct_level and not owned:
                shop_buy_weapon(weapon, weapon_name, weapon_id, price)
        elif key == readchar.key.ESC:
            debug.debug("Pressed ESC key")
            shop_menu(old_selected)
            break

def shop_buy_weapon(weapon, weapon_name, weapon_id, price):
    # Tuesday 11 March 11:53AM
    # Confirmation prompt of buying a weapon from shop
    # When successful purchase, will add weapon to globals.player's inventory, subtract money from globals.player with price, and then save globals.player file.

    # Parameters:
    # weapon (dict): Data of viewed weapon to display information
    # weapon_name (Text object): Styled weapon name string
    # weapon_id (str): Weapon ID used to handle to give globals.player's inventory the weapon
    # price (int): Number used to subtract off the globals.player's balance after purchase
    
    info = style_text({'style': 'bold'}, ' Price: ') + style_text({'color': [201, 237, 154]}, f"${weapon['price']}") + style_text({'style': 'bold'}, '\n Your balance: ') + style_text({'color': [201, 237, 154]}, f"${globals.player['money']}")
    options = [style_text({'style': 'bold'}, 'No'), style_text({'style': 'bold'}, 'Yes')]
    tooltip = style_text({'style': 'italic'}, 'Arrow Keys (↑/↓) to navigate | ENTER to select | ESC to go back' if globals.display_controls else '')
    selected = 0

    while True:
        print_basic_menu(options, selected, style_text({'style': 'bold'}, f"Are you sure you want to purchase ", weapon_name, "?\n") + info, tooltip)
        key = readchar.readkey()
        if key == readchar.key.UP:
            debug.debug("Pressed UP arrow key")
            selected = 0
        elif key == readchar.key.DOWN:
            debug.debug("Pressed DOWN arrow key")
            selected = 1
        elif key == readchar.key.ENTER:
            debug.debug('Pressed ENTER key')
            if selected == 0:
                debug.info(f"Did not purchase {weapon_name}")
                return
            elif selected == 1: 
                globals.player['inventory'].append(weapon_id)
                globals.player['money'] -= price
                debug.info(f"Purchased {weapon_name}")
                save_player()
                return 
        elif key == readchar.key.ESC:
            debug.debug("Pressed ESC key")
            return
        
def inventory_menu(selected=0):
    # Sunday 16 March 2025
    # Inventory menu for viewing and equipping globals.weapons

    # Weapon IDs are stored in inventory
    # Scans globals.weapons list for weapon with matching ID

    # Plans for Wednesday 19 March
    # Make search function or sort system (by key and ascending/descending order)
    globals.player['inventory'] = sorted(
        globals.player['inventory'], 
        key = lambda weapon_id: next((item['levelRequirement'] for item in globals.weapons if item['id'] == weapon_id), 0)
    )

    old_sort_type = globals.settings.get('invSortType', 'levelRequirement')
    old_sort_order = globals.settings.get('invSortAscending', True)
    displayed_inventory = sort_displayed_weapons(old_sort_type, old_sort_order, globals.player['inventory'])

    while True:
        sort_type = globals.settings.get('invSortType', 'levelRequirement')
        sort_order = globals.settings.get('invSortAscending', True)
        sort_type_keybind = globals.settings['primarySortKeybind']
        sort_order_keybind = globals.settings['secondarySortKeybind']

        if sort_type != old_sort_type or sort_order != old_sort_order:
            old_sort_type = sort_type
            old_sort_order = sort_order
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
        page_size = 5
        title = style_text({'style':'bold'}, 'Inventory')

        displayed_type = ""
        if sort_type == 'levelRequirement': displayed_type = "Level"
        elif sort_type == 'price': displayed_type = "Price"
        displayed_order = 'Ascending' if sort_order else "Descending"
        sort_tooltip = f"Sorted by: {displayed_type}{f' ({sort_type_keybind.upper()})' if globals.display_controls else ''} | {displayed_order}{f' ({sort_order_keybind.upper()})' if globals.display_controls else ''}"
        
        control_tooltip = '\nArrow Keys (↑/↓) to navigate items | Arrow Keys (←/→) to navigate pages | ENTER to select | ESC to go back\n' if globals.display_controls else ''
        extra_tooltip = '✅ = Equipped' if globals.display_extra else ''
        tooltip = style_text({'style':'italic'}, sort_tooltip, control_tooltip, extra_tooltip)

        current_page, total_pages, start_index = print_paged_menu([option[2] for option in options], selected, title, tooltip, page_size)
        # Ensure selected index points to a valid weapon (ignores empty slots)
        valid_indices = list(range(start_index, min(start_index + page_size, len(options))))

        key = readchar.readkey()
        if key == readchar.key.UP:
            debug.debug("Pressed UP arrow key")
            selected = valid_indices[-1] if selected == valid_indices[0] else valid_indices[valid_indices.index(selected) - 1]
        elif key == readchar.key.DOWN:
            debug.debug("Pressed DOWN arrow key")
            selected = valid_indices[0] if selected == valid_indices[-1] else valid_indices[valid_indices.index(selected) + 1]
        elif key == readchar.key.LEFT and current_page > 0:
            debug.debug('Pressed LEFT arrow key')
            selected = max(0, selected - page_size)  # Move to previous page
        elif key == readchar.key.RIGHT and current_page < total_pages - 1:
            debug.debug('Pressed RIGHT arrow key')
            selected = min(len(options) - 1, selected + page_size)  # Move to next page
        elif key == readchar.key.ENTER:
            debug.debug('Pressed ENTER key')
            current_option = options[selected]
            current_weapon_id = current_option[0]
            current_weapon = current_option[1]
            current_weapon_name = style_text(current_weapon['title'], current_weapon['name'])
            inv_view_weapon(current_weapon, current_weapon_name, current_weapon_id, selected)
            break
        elif key == readchar.key.ESC:
            debug.debug("Pressed ESC key")
            break
        elif str(key) == sort_type_keybind or key == settings_keybinds.get(sort_type_keybind):
            debug.debug(f"Pressed {sort_type_keybind.upper()} key")
            keys = ['levelRequirement', 'price']
            sort_type = keys[(keys.index(sort_type) + 1) % len(keys)]
            globals.settings['invSortType'] = sort_type
            globals.player['settings'] = globals.settings
            save_player(debug=False)
        elif str(key) == sort_order_keybind or key == settings_keybinds.get(sort_order_keybind):
            debug.debug(f"Pressed {sort_order_keybind.upper()} key")
            sort_order = not sort_order
            globals.settings['invSortAscending'] = sort_order
            globals.player['settings'] = globals.settings
            save_player(debug=False)
        
def inv_view_weapon(weapon, weapon_name, weapon_id, old_selected):
    # Saturday March 8 10:04AM
    # Tuesday March 11 11:36AM
    # View stats of a selected weapon from shop

    # Parameters:
    # weapon (dict): Data of viewed weapon to display information
    # weapon_name (Text object): Styled weapon name string
    # weapon_id (str): Weapon ID used to handle if globals.player owns the weapon
    # old_selected (int): Selected number from shop_menu() function used when going back to shop
    
    debug.debug(f"Viewing from inventory: {weapon_name}")
    selected = 0
    while True:
        # Checks globals.player's balance and if globals.player can afford

        # Checks globals.player's level and if it meets level requirement
        level = globals.player['level']
        level_requirement = weapon['levelRequirement']
        correct_level = level >= level_requirement

        equipped = globals.player['equipped'] == weapon_id
        equipped_text = style_text({'style': 'italic'}, ' (Equipped)') if globals.display_text else Text(" ✅")
        equipped_string = equipped_text if equipped else Text()

        # Price
        price_info = Text()
        if weapon.get('price'):
            price = weapon['price']
            price_info = style_text({'style': 'bold'}, '  Price from shop: ') + style_text({'color': [201, 237, 154]}, f"${price}\n")

        # Level
        level_info = style_text({'style': 'bold'}, '  Level required: ')
        level_color = [201, 237, 154] if correct_level else [227, 104, 104] # Green if meeting level requirement else red
        level_info += style_text({'color': level_color}, f"{level_requirement}")
        locked_text = style_text({'style': 'italic'}, ' (Locked)') if globals.display_text else Text(" 🔒")
        level_info += Text() if correct_level else locked_text


        weapon_info = weapon_name + equipped_string + Text(f"\n  {weapon['description']}\n") + price_info + level_info

        # Abilities
        abilities = weapon['abilities']
        ability = abilities[selected] # Selected ability

        true_title = style_text({'style': 'bold'}, 'Inspeacting Weapon | Inventory\n ') # Actual title at the top
        title = true_title + weapon_info + Text(f'\n  == ABILITIES ({selected + 1}/{len(abilities)}) ==') # All the information stored in "title" to not conflict with actual options
        ability_info = style_text(ability['title'], f"  {ability['name']}\n   ") + Text(ability['description'])
        
        enter_string = '' 
        if equipped:
            enter_string = style_text({'style':'bold italic'}, 'You already equipped this weapon!')
        elif not correct_level:
            enter_string = style_text({'style':'bold italic'}, 'You cannot equip this weapon!')
        else:
            enter_string = 'ENTER to equip'

        ability_tooltip = 'Arrow Keys (←/→) to navigate abilities\n' if len(abilities) > 1 and globals.display_controls else ''
        tooltip =  style_text({'style':'italic'}, ability_tooltip, enter_string, ' | ESC to go back' if globals.display_controls else '')
        print_horizontal_menu(ability_info, title, tooltip)

        key = readchar.readkey()
        if key == readchar.key.LEFT:
            debug.debug('Pressed LEFT arrow key')
            if selected > 0:
                selected -= 1
        elif key == readchar.key.RIGHT:
            debug.debug('Pressed RIGHT arrow key')
            if selected < len(abilities) - 1:
                selected += 1
        elif key == readchar.key.ENTER:
            debug.debug('Pressed ENTER key')
            if not equipped and correct_level:
                debug.info(f"Equipped {weapon_name}")
                globals.player['equipped'] = weapon_id
                save_player()
        elif key == readchar.key.ESC:
            debug.debug("Pressed ESC key")
            inventory_menu(old_selected)
            break

def settings_menu():
    options = [
        # Options/globals.settings:
        # (Styled text for setting name, id of setting, ['what to display beside text if off', 'what to display beside text if on'], {setting(s) that this one depends on: what state it has to be})
        TwoStateSetting(style_text({'style': 'bold italic'}, 'Show keyboard controls on tooltips:'), 'displayControls'),
        TwoStateSetting(style_text({'style': 'bold italic'}, 'Show text instead of symbols for labels:'), 'displayTextTooltips'),
        TwoStateSetting(style_text({'style': 'bold italic'}, 'Show additional tooltips for symbols:'), 'displayExtraTooltips', None, {'displayTextTooltips': False}, False),
        KeyBindSetting(style_text({'style': 'bold italic'}, 'Set keybind for sort key:'), 'primarySortKeybind', ['secondarySortKeybind']),
        KeyBindSetting(style_text({'style': 'bold italic'}, 'Set keybind for sort order:'), 'secondarySortKeybind', ['primarySortKeybind']),
    ]

    selected = 0

    while True:
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
                save_player()
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
        
        tooltip = style_text({'style': 'italic'}, 'Arrow Keys (↑/↓) to navigate | ENTER to select | ESC to go back') if globals.display_controls else ''
        print_basic_menu(displayed_options, selected, style_text({'style': 'bold'}, 'Settings'), tooltip)

        key = readchar.readkey()
        if key == readchar.key.UP:
            debug.debug("Pressed UP arrow key")
            selected = (selected - 1) % len(options)
        elif key == readchar.key.DOWN:
            debug.debug("Pressed DOWN arrow key")
            selected = (selected + 1) % len(options)
        elif key == readchar.key.ENTER:
            debug.debug('Pressed ENTER key')
            selected_option = options[selected]
            id = selected_option.id
            setting = globals.settings.get(id)

            if setting is not None: # If setting exists
                if isinstance(selected_option, TwoStateSetting):
                    globals.settings[id] = not globals.settings[id]
                    globals.player['settings'] = globals.settings
                    save_player()
                    debug.info(f"{'Enabled' if globals.settings[id] is True else 'Disabled'} setting: {id}")
                elif isinstance(selected_option, KeyBindSetting):
                    blacklisted_keybind = None
                    while True:
                        clear_terminal()
                        console.print(style_text({'style':'bold'}, f"Settings | {str(selected_option.text)}")) # title
                        if globals.display_controls:
                            console.print(style_text({'style':'italic'}, 'Press any key to set | ESC to cancel')) # tooltip
                        if blacklisted_keybind:
                            console.print(style_text({'style':'bold italic'}, 'You cannot set your keybind to that'))
                        keybind = readchar.readkey()
                        debug.info(selected_option.dependencies)
                        # Keys in this list are required to navigate through menus, so these keys should not be used when setting keybinds
                        if keybind in [readchar.key.ENTER, readchar.key.UP, readchar.key.DOWN, readchar.key.LEFT, readchar.key.RIGHT]:
                            blacklisted_keybind = keybind
                            continue
                        elif keybind in [globals.settings[other_keybind] for other_keybind in selected_option.dependencies or []if other_keybind in globals.settings]:
                            blacklisted_keybind = keybind
                            continue
                        elif keybind == readchar.key.ESC: break
                        elif keybind in settings_keybinds.values():
                            globals.settings[id] = next((k for k, v in settings_keybinds.items() if v == keybind), None)
                            globals.player['settings'] = globals.settings
                            save_player()
                        else:
                            globals.settings[id] = str(keybind)
                            globals.player['ettings'] = globals.settings
                            save_player()
                        debug.debug(f"Set keybind for {id}: {globals.settings[id]}")
                        break
                    
            else:
                debug.warning(f"Error finding setting: {id}")
        elif key == readchar.key.ESC:
            debug.debug("Pressed ESC key")
            break

# Load data
load_enemies()
load_weapons()
load_player()

# Start game
script_dir = os.path.dirname(os.path.abspath(__file__))
crash_log_path = os.path.join(script_dir, 'crash.log')

while True:
    if exit is True: break
    try:
        main_menu()  
    except Exception as e:
        debug.error(f"An error was caught and crashed game.py, please check {crash_log_path}")
        crash.error(f"Error caught while running game.py:\n{e}\n{traceback.format_exc()}")
        

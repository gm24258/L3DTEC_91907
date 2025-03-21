from menus import *
from utils import *
from data import *

enemies = []
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
    global enemies
    # Loads enemy data from the ENEMIES_DIR and sorts by level requirement.
    for enemy_folder in os.listdir(ENEMIES_DIR):
        enemy_path = os.path.join(ENEMIES_DIR, enemy_folder)
        if os.path.isdir(enemy_path):  # Ensure it's a directory for an enemy
            enemy_data = load_enemy_data(enemy_path)
            enemies.append(enemy_data)
    
    # Assuming each enemy has a 'main' data containing 'levelRequirement'
    enemies = merge_sort(enemies, 'levelRequirement')
    debug.info(f'Loaded {len(enemies)} enemies.')

weapons = []
shop_weapons = []
def load_weapons(): 
    global weapons
    global shop_weapons
    # Loads weapon data from the WEAPONS_DIR and sorts by level requirement.    
    weapons = load_data_from_directory(WEAPONS_DIR, 'weapon')
    weapons = merge_sort(weapons, 'levelRequirement')
    debug.info(f'Loaded {len(weapons)} weapons.')

    # Create a new list of weapons from exisiting weapons list but removes items that are not shop items
    shop_weapons = [weapon['id'] for weapon in weapons if weapon['inShop']]
    
# Tuesday March 11 12:15PM
# Player data
player = []

settings = []
display_controls = True
display_text = False
display_extra = True

def load_player():
    global player
    global settings
    global display_controls
    global display_text
    global display_extra

    player = load_file_from_directory(DATA_DIR, 'save_file', 'template_')
    settings = player['settings']
    display_controls = settings['displayControls']
    display_text = settings['displayTextTooltips']
    display_extra = settings['displayExtraTooltips']
    debug.info('Loaded player data:\n' + str(player))

def save_player(debug=True):
    global display_controls
    global display_text
    global display_extra

    display_controls = settings['displayControls']
    display_text = settings['displayTextTooltips']
    display_extra = settings['displayExtraTooltips']
    save_file_from_directory(DATA_DIR, 'save_file', player, debug)

def sort_displayed_weapons(key, order, weapons_list):
    if key == 'price':
        displayed_shop_weapons = sorted(
            [
                weapon_id for weapon_id in weapons_list
                if next((weapon for weapon in weapons if weapon['id'] == weapon_id and weapon['inShop'] is True), None) is not None
            ], 
            key = lambda weapon_id: next((item[key] for item in weapons if item['id'] == weapon_id), 0),
            reverse = not order
        )
        not_in_shop_weapons = sorted(
            [
                weapon_id for weapon_id in weapons_list
                if next((weapon for weapon in weapons if weapon['id'] == weapon_id and weapon['inShop'] is False), None) is not None
            ], 
            key = lambda weapon_id: next((item['levelRequirement'] for item in weapons if item['id'] == weapon_id), 0),
            reverse = not order
        )
        if order: return displayed_shop_weapons + not_in_shop_weapons 
        else: return not_in_shop_weapons + displayed_shop_weapons
    else:
        weapons_list = sorted(
            weapons_list, 
            key = lambda weapon_id: next((item[key] for item in weapons if item['id'] == weapon_id), 0),
            reverse = not order
        )
        return weapons_list

def main_menu():
    # Main menu displayed at the start of the game that handles user selection

    options = ['Play', 'Shop', 'Inventory', 'Settings', 'Exit'] # Menu options in order
    selected = 0 # Tracks selected option

    while True:
        tooltip = style_text({'style': 'italic'}, 'Arrow Keys (↑/↓) to navigate | ENTER to select') if display_controls else ''
        print_basic_menu(style_text({'style': 'bold'}, 'Main Menu'), options, tooltip, selected) # Selected is saved so that the last option is selected when you go back to the main menu
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
    # Confirmation menu for exiting game. Returns True if player confirms exit, False otherwise

    tooltip = style_text({'style': 'italic'}, 'Arrow Keys (↑/↓) to navigate | ENTER to select | ESC to go back') if display_controls else ''
    selected = 0

    while True:
        print_basic_menu(style_text({'style': 'bold'}, 'Are you sure you want to exit?'), ['Go Back', 'Confirm'], tooltip, selected)
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
    # Checks list of enemies then puts info in a string to be printed later
    locked_text = style_text({'style': 'italic'}, ' (Locked)') if display_text else Text(" 🔒")

    enemy_info_strings = []
    for enemy in enemies:
        # Create a rich Text object for each part
        enemy_name = style_text(enemy['title'], enemy['name'])
        health_text = style_text({'style': 'bold'}, ' Health: ') + style_text({"color":[201, 237, 154]}, f"{enemy['health']}")

        level_requirement = enemy['levelRequirement']
        correct_level = player['level'] >= level_requirement

        level_info = style_text({'style': 'bold'}, ' Level required: ')
        level_color = [201, 237, 154] if correct_level else [227, 104, 104] # Green if meeting level requirement else red
        level_info += style_text({'color': level_color}, f"{level_requirement}")
        level_info += Text() if correct_level else locked_text

        # Append them to the list
        enemy_info_strings.append(enemy_name + '\n' + health_text + '\n' + level_info)

    selected = 0

    while True:
        current_enemy = enemies[selected]
        current_enemy_name = style_text(current_enemy['title'], current_enemy['name'])
        level_requirement = current_enemy['levelRequirement']
        correct_level = player['level'] >= level_requirement

        # Checks if there's previous enemy
        prev_enemy = enemies[selected - 1] if selected > 0 else None
        prev_enemy_name = Text('NONE')
        if prev_enemy:
            enemy_title = prev_enemy['title']
            if enemy_title.get('style'):
                if not 'italic' in enemy_title['style']:
                    enemy_title['style'] += ' italic'
            else:
                enemy_title['style'] = 'italic'

            prev_enemy_name = style_text(enemy_title, prev_enemy['name'])
            prev_enemy_name += Text() if player['level'] >= prev_enemy['levelRequirement'] else locked_text

        # Checks if there's next enemy
        next_enemy = enemies[selected + 1] if selected < len(enemies) - 1 else None
        next_enemy_name = Text('NONE')
        if next_enemy:
            enemy_title = next_enemy['title']
            if enemy_title.get('style'):
                if not 'italic' in enemy_title['style']:
                    enemy_title['style'] += ' italic'
            else:
                enemy_title['style'] = 'italic'

            next_enemy_name = style_text(enemy_title, next_enemy['name'])
            next_enemy_name += Text() if player['level'] >= next_enemy['levelRequirement'] else locked_text

        enter_string = f'{'' if display_text else '⚔️  ' }{'ENTER to ' if display_controls else ''}Fight' if correct_level else style_text({'style': 'bold italic'}, 'You cannot fight this enemy yet!')
        tooltip = style_text({'style':'italic'}, enter_string,  ' | ', prev_enemy_name, ' ← | → ', next_enemy_name, '\nArrow Keys (←/→) to navigate | ESC to go back' if display_controls else '')

        print_horizontal_menu(style_text({'style': 'bold'}, 'Play'), enemy_info_strings[selected], tooltip)
        key = readchar.readkey()

        if key == readchar.key.LEFT:
            debug.debug('Pressed LEFT arrow key')
            if selected > 0:
                selected -= 1
        elif key == readchar.key.RIGHT:
            debug.debug('Pressed RIGHT arrow key')
            if selected < len(enemies) - 1:
                selected += 1
        elif key == readchar.key.ENTER:
            debug.debug('Pressed ENTER key')
            debug.info(f"You chose to fight {current_enemy_name}.")
            break
        elif key == readchar.key.ESC:
            debug.debug("Pressed ESC key")
            return

def shop_menu(selected=0):
    # Wednesday March 5 10:10AM
    # Shop menu for viewing and purchasing weapons

    # Parameters
    # selected (int): Selected number to determine selected option. Default is 0.

    old_sort_type = settings.get('shopSortType', 'price')
    old_sort_order = settings.get('shopSortAscending', True)
    displayed_shop = sort_displayed_weapons(old_sort_type, old_sort_order, shop_weapons)

    while True:
        sort_type = settings.get('shopSortType', 'price')
        sort_order = settings.get('shopSortAscending', True)
        sort_type_keybind = settings['primarySortKeybind']
        sort_order_keybind = settings['secondarySortKeybind']

        if sort_type != old_sort_type or sort_order != old_sort_order:
            old_sort_type = sort_type
            old_sort_order = sort_order
            displayed_shop = sort_displayed_weapons(sort_type, sort_order, shop_weapons)

        options = []
        for weapon_id in displayed_shop:
            weapon = next((item for item in weapons if item['id'] == weapon_id), None)
            if weapon:
                option_text = style_text(weapon['title'], weapon['name'])
                if weapon_id in player['inventory']:
                    owned_text = style_text({'style': 'italic'}, ' (Owned)') if display_text else Text(" ✅")
                    option_text += owned_text
                elif player['level'] < weapon['levelRequirement']:
                    locked_text = style_text({'style': 'italic'}, ' (Locked)') if display_text else Text(" 🔒")
                    option_text += locked_text  
                options.append((weapon_id, weapon, option_text))
            else:
                debug.warning(f"Error trying to find weapon with ID: {weapon_id}")
        page_size = 5

        current_option = options[selected]
        current_weapon_id = current_option[0]
        current_weapon = current_option[1]
        current_weapon_name = style_text(current_weapon['title'], current_weapon['name'])

        title = style_text({'style':'bold'}, 'Shop (Balance: ', style_text({'color':[201, 237, 154]}, f"${player['money']}"), ')')
        
        displayed_type = ""
        if sort_type == 'levelRequirement': displayed_type = "Level"
        elif sort_type == 'price': displayed_type = "Price"
        displayed_order = 'Ascending' if sort_order else "Descending"
        sort_tooltip = f"Sorted by: {displayed_type}{f' ({sort_type_keybind.upper()})' if display_controls else ''} | {displayed_order}{f' ({sort_order_keybind.upper()})' if display_controls else ''}"
        
        control_tooltip =  '\nArrow Keys (↑/↓) to navigate items | Arrow Keys (←/→) to navigate pages | ENTER to select | ESC to go back\n' if display_controls else ''
        extra_tooltip = '✅ = Purchased | 🔒 = Locked' if display_extra else ''
        tooltip = style_text({'style':'italic'}, sort_tooltip, control_tooltip, extra_tooltip)
        current_page, total_pages, start_index = print_paged_menu(title, [option[2] for option in options], tooltip, selected, page_size)
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
            settings['shopSortType'] = sort_type
            player['settings'] = settings
            save_player(debug=False)
        elif str(key) == sort_order_keybind or key == settings_keybinds.get(sort_order_keybind):
            debug.debug(f"Pressed {sort_order_keybind.upper()} key")
            sort_order = not sort_order
            settings['shopSortAscending'] = sort_order
            player['settings'] = settings
            save_player(debug=False)
        
def shop_view_weapon(weapon, weapon_name, weapon_id, old_selected):
    # Saturday March 8 10:04AM
    # Tuesday March 11 11:36AM
    # View stats of a selected weapon from shop

    # Parameters:
    # weapon (dict): Data of viewed weapon to display information
    # weapon_name (Text object): Styled weapon name string
    # weapon_id (str): Weapon ID used to handle if player owns the weapon
    # old_selected (int): Selected number from shop_menu() function used when going back to shop
    
    debug.debug(f"Viewing from shop: {weapon_name}")
    selected = 0
    
    while True:
        # Checks player's balance and if player can afford
        balance = player['money']
        price = weapon['price']
        afford = balance >= price or price == 0 # If player has equal or more money than the price, or the weapon is free and somehow the player has negative balance

        # Checks player's level and if it meets level requirement
        level = player['level']
        level_requirement = weapon['levelRequirement']
        correct_level = level >= level_requirement

        owned = weapon_id in player['inventory'] # If player has weapon in their inventory

        # Price
        price_info = style_text({'style': 'bold'}, '  Price: ')
        price_color = [201, 237, 154] if afford else [227, 104, 104] # Green if afford else red
        price_info += style_text({'color': price_color}, f"${price}\n")

        # Level
        level_info = style_text({'style': 'bold'}, '  Level required: ')
        level_color = [201, 237, 154] if correct_level else [227, 104, 104] # Green if meeting level requirement else red
        level_info += style_text({'color': level_color}, f"{level_requirement}")
        locked_text = style_text({'style': 'italic'}, ' (Locked)') if display_text else Text(" 🔒")
        level_info += Text() if correct_level else locked_text

        weapon_info = weapon_name + Text(f"\n  {weapon['description']}\n") + price_info + level_info

        # Abilities
        abilities = weapon['abilities']
        ability = abilities[selected] # Selected ability

        true_title = style_text({'style': 'bold'}, 'Inspeacting Weapon | Shop (Balance: ', style_text({'color':[201, 237, 154]}, f"${player['money']}"), ')\n ') # Actual title at the top
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
            enter_string = 'ENTER to purchase' if display_controls else ''

        ability_tooltip = 'Arrow Keys (←/→) to navigate abilities\n' if len(abilities) > 1 and display_controls else ''
        tooltip =  style_text({'style':'italic'}, ability_tooltip, enter_string, ' | ESC to go back' if display_controls else '')
        print_horizontal_menu(title, ability_info, tooltip)

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
    # When successful purchase, will add weapon to player's inventory, subtract money from player with price, and then save player file.

    # Parameters:
    # weapon (dict): Data of viewed weapon to display information
    # weapon_name (Text object): Styled weapon name string
    # weapon_id (str): Weapon ID used to handle to give player's inventory the weapon
    # price (int): Number used to subtract off the player's balance after purchase
    
    info = style_text({'style': 'bold'}, 'Price: ') + style_text({'color': [201, 237, 154]}, f"${weapon['price']}") + style_text({'style': 'bold'}, '\nYour balance: ') + style_text({'color': [201, 237, 154]}, f"${player['money']}")
    options = [style_text({'style': 'bold'}, 'No'), style_text({'style': 'bold'}, 'Yes')]
    tooltip = style_text({'style': 'italic'}, 'Arrow Keys (↑/↓) to navigate | ENTER to select | ESC to go back' if display_controls else '')
    selected = 0

    while True:
        print_basic_menu(style_text({'style': 'bold'}, f"Are you sure you want to purchase ", weapon_name, "?\n") + info, options, tooltip, selected)
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
                player['inventory'].append(weapon_id)
                player['money'] -= price
                debug.info(f"Purchased {weapon_name}")
                save_player()
                return 
        elif key == readchar.key.ESC:
            debug.debug("Pressed ESC key")
            return
        
def inventory_menu(selected=0):
    # Sunday 16 March 2025
    # Inventory menu for viewing and equipping weapons

    # Weapon IDs are stored in inventory
    # Scans weapons list for weapon with matching ID

    # Plans for Wednesday 19 March
    # Make search function or sort system (by key and ascending/descending order)
    player['inventory'] = sorted(
        player['inventory'], 
        key = lambda weapon_id: next((item['levelRequirement'] for item in weapons if item['id'] == weapon_id), 0)
    )

    old_sort_type = settings.get('invSortType', 'levelRequirement')
    old_sort_order = settings.get('invSortAscending', True)
    displayed_inventory = sort_displayed_weapons(old_sort_type, old_sort_order, player['inventory'])

    while True:
        sort_type = settings.get('invSortType', 'levelRequirement')
        sort_order = settings.get('invSortAscending', True)
        sort_type_keybind = settings['primarySortKeybind']
        sort_order_keybind = settings['secondarySortKeybind']

        if sort_type != old_sort_type or sort_order != old_sort_order:
            old_sort_type = sort_type
            old_sort_order = sort_order
            displayed_inventory = sort_displayed_weapons(sort_type, sort_order, player['inventory'])

        options = []
        for weapon_id in displayed_inventory:
            weapon = next((item for item in weapons if item['id'] == weapon_id), None)
            if weapon:
                option_text = style_text(weapon['title'], weapon['name'])
                equipped_text = style_text({'style': 'italic'}, ' (Equipped)') if display_text else Text(" ✅")
                option_text += equipped_text if player['equipped'] == weapon_id else Text()
                options.append((weapon_id, weapon, option_text))
            else:
                debug.warning(f"Error trying to find weapon with ID: {weapon_id}")
        page_size = 5
        title = style_text({'style':'bold'}, 'Inventory')

        displayed_type = ""
        if sort_type == 'levelRequirement': displayed_type = "Level"
        elif sort_type == 'price': displayed_type = "Price"
        displayed_order = 'Ascending' if sort_order else "Descending"
        sort_tooltip = f"Sorted by: {displayed_type}{f' ({sort_type_keybind.upper()})' if display_controls else ''} | {displayed_order}{f' ({sort_order_keybind.upper()})' if display_controls else ''}"
        
        control_tooltip = '\nArrow Keys (↑/↓) to navigate items | Arrow Keys (←/→) to navigate pages | ENTER to select | ESC to go back\n' if display_controls else ''
        extra_tooltip = '✅ = Equipped' if display_extra else ''
        tooltip = style_text({'style':'italic'}, sort_tooltip, control_tooltip, extra_tooltip)

        current_page, total_pages, start_index = print_paged_menu(title, [option[2] for option in options], tooltip, selected, page_size)
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
            settings['invSortType'] = sort_type
            player['settings'] = settings
            save_player(debug=False)
        elif str(key) == sort_order_keybind or key == settings_keybinds.get(sort_order_keybind):
            debug.debug(f"Pressed {sort_order_keybind.upper()} key")
            sort_order = not sort_order
            settings['invSortAscending'] = sort_order
            player['settings'] = settings
            save_player(debug=False)
        
def inv_view_weapon(weapon, weapon_name, weapon_id, old_selected):
    # Saturday March 8 10:04AM
    # Tuesday March 11 11:36AM
    # View stats of a selected weapon from shop

    # Parameters:
    # weapon (dict): Data of viewed weapon to display information
    # weapon_name (Text object): Styled weapon name string
    # weapon_id (str): Weapon ID used to handle if player owns the weapon
    # old_selected (int): Selected number from shop_menu() function used when going back to shop
    
    debug.debug(f"Viewing from inventory: {weapon_name}")
    selected = 0
    while True:
        # Checks player's balance and if player can afford

        # Checks player's level and if it meets level requirement
        level = player['level']
        level_requirement = weapon['levelRequirement']
        correct_level = level >= level_requirement

        equipped = player['equipped'] == weapon_id
        equipped_text = style_text({'style': 'italic'}, ' (Equipped)') if display_text else Text(" ✅")
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
        locked_text = style_text({'style': 'italic'}, ' (Locked)') if display_text else Text(" 🔒")
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

        ability_tooltip = 'Arrow Keys (←/→) to navigate abilities\n' if len(abilities) > 1 and display_controls else ''
        tooltip =  style_text({'style':'italic'}, ability_tooltip, enter_string, ' | ESC to go back' if display_controls else '')
        print_horizontal_menu(title, ability_info, tooltip)

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
                player['equipped'] = weapon_id
                save_player()
        elif key == readchar.key.ESC:
            debug.debug("Pressed ESC key")
            inventory_menu(old_selected)
            break

def settings_menu():
    global display_controls
    options = [
        # Options/settings:
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
            setting = settings[id] or None
            
            # Checks if user prefers text than symbols to indicate something

            # Checks if other setting(s) this setting depends on is the right value for it, if at least one value is incorrect, the setting is disabled
            dependencies = option.dependencies
            disabled = False
            if dependencies and isinstance(dependencies, dict):
                for i,v in dependencies.items():
                    if settings[i] != v:
                        disabled = True
                        break
            
            # This option is skipped and no longer displayed
            if disabled:
                settings[option.id] = option.disabled_value
                player['settings'] = settings
                save_player()
                continue

            if isinstance(option, TwoStateSetting):
                states = list(option.states)
                if display_text and option.states == ['', '✅']:
                    states[0] = style_text({'style': 'italic'}, 'Off')
                    states[1] = style_text({'style': 'italic'}, 'On')
                displayed_options.append(text + Text(f" {states[1] if setting is True else states[0]}"))
            elif isinstance(option, KeyBindSetting):
                setting = 'Unassigned' if setting is None else setting
                displayed_options.append(text + Text(f" {setting.upper()}"))
            # Placeholder for settings with more than 3 options 
            # else:
        
        tooltip = style_text({'style': 'italic'}, 'Arrow Keys (↑/↓) to navigate | ENTER to select | ESC to go back') if display_controls else ''
        print_basic_menu(style_text({'style': 'bold'}, 'Settings'), displayed_options, tooltip, selected)

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
            setting = settings.get(id)

            if setting is not None: # If setting exists
                if isinstance(selected_option, TwoStateSetting):
                    settings[id] = not settings[id]
                    player['settings'] = settings
                    save_player()
                    debug.info(f"{'Enabled' if settings[id] is True else 'Disabled'} setting: {id}")
                elif isinstance(selected_option, KeyBindSetting):
                    blacklisted_keybind = None
                    while True:
                        clear_terminal()
                        console.print(style_text({'style':'bold'}, f"Settings | {str(selected_option.text)}")) # title
                        if display_controls:
                            console.print(style_text({'style':'italic'}, 'Press any key to set | ESC to cancel')) # tooltip
                        if blacklisted_keybind:
                            console.print(style_text({'style':'bold italic'}, 'You cannot set your keybind to that'))
                        keybind = readchar.readkey()
                        debug.info(selected_option.dependencies)
                        # Keys in this list are required to navigate through menus, so these keys should not be used when setting keybinds
                        if keybind in [readchar.key.ENTER, readchar.key.UP, readchar.key.DOWN, readchar.key.LEFT, readchar.key.RIGHT]:
                            blacklisted_keybind = keybind
                            continue
                        elif keybind in [settings[other_keybind] for other_keybind in selected_option.dependencies or []if other_keybind in settings]:
                            blacklisted_keybind = keybind
                            continue
                        elif keybind == readchar.key.ESC: break
                        elif keybind in settings_keybinds.values():
                            settings[id] = next((k for k, v in settings_keybinds.items() if v == keybind), None)
                            player['settings'] = settings
                            save_player()
                        else:
                            settings[id] = str(keybind)
                            player['settings'] = settings
                            save_player()
                        debug.debug(f"Set keybind for {id}: {settings[id]}")
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
        

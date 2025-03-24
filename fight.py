from libraries import *
from menus import *
from utils import *
import globals

player_health = None
previous_player_attack = ['', '']
previous_player_hit = None
previous_player_crit = None
weapon = None

previous_enemy_attack = ['', '']
previous_enemy_crit = None
enemy_health = None

def print_top_info(enemy, enemy_name, show='both'):
    show_player = True
    show_enemy = True

    if show == 'player': show_enemy = False
    elif show == 'enemy': show_player = False

    player_max_health = globals.player.get('health')
    enemy_max_health = enemy.get('health')
    if (player_max_health or enemy_max_health) is None:
        raise Exception(f"Error fighting {enemy_name}: Couldn't load data properly")

    total_width = 50
    spaces = max((total_width - 3 - len(str(enemy_name))), 1)
    console.print(style_text({'style':'bold'}, 'You' if show_player else '   ', ' '*spaces) + (enemy_name if show_enemy else ''))

    player_min_health_color = [201, 237, 154] # Green if greater than 2/3 of health or full
    if (1/3) * player_max_health  < player_health <= (2/3) * player_max_health: 
        player_min_health_color = [237, 198, 154] # Orange if greater than 1/3 of health but lesser than 2/3
    elif player_health <= (1/3) * player_max_health:
        player_min_health_color = [227, 104, 104] # Red if lesser than 1/3 of health

    enemy_min_health_color = [201, 237, 154] # Green if greater than 2/3 of health or full
    if (1/3) * enemy_max_health  < enemy_health <= (2/3) * enemy_max_health: 
        enemy_min_health_color = [237, 198, 154] # Orange if greater than 1/3 of health but lesser than 2/3
    elif enemy_health <= (1/3) * enemy_max_health:
        enemy_min_health_color = [227, 104, 104] # Red if lesser than 1/3 of health

    player_min_health_string = style_text({'color': player_min_health_color}, str(player_health))
    player_max_health_string = style_text({'color': [201, 237, 154]}, str(player_max_health))
    enemy_min_health_string = style_text({'color': enemy_min_health_color}, str(enemy_health))
    enemy_max_health_string = style_text({'color': [201, 237, 154]}, str(enemy_max_health))

    player_health_string = player_min_health_string + Text("/") + player_max_health_string 
    enemy_health_string = enemy_min_health_string + Text("/") + enemy_max_health_string 
    health_spaces = max((total_width - len(str(player_health_string)) - len(str(enemy_health_string))), 1)
    console.print((player_health_string if show_player else ' '*len(player_health_string)) + Text(' '*health_spaces) + (enemy_health_string if show_enemy else Text()))

def flee_confirm(enemy_name):
    # 

    # Parameters:
    # enemy_name (Text): 
    
    options = [style_text({'style': 'bold'}, 'No'), style_text({'style': 'bold'}, 'Yes')]
    tooltip = style_text({'style': 'italic'}, 'Arrow Keys (↑/↓) to navigate | ENTER to select | ESC to go back' if globals.display_controls else '')
    selected = 0

    while True:
        print_basic_menu(options, selected, style_text({'style': 'bold'}, f"Are you sure you want to flee from ", enemy_name, "?"), tooltip)
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
                debug.info(f"Did not flee from {enemy_name}")
                return False
            elif selected == 1: 
                debug.info(f"Fleed from {enemy_name}")
                return True
        elif key == readchar.key.ESC:
            debug.debug("Pressed ESC key")
            return False

def determine_attack(attack, player=True):
    global previous_player_attack
    global previous_player_hit
    global previous_player_crit

    global previous_enemy_attack
    global previous_enemy_crit

    damage = random.randint(attack['minDamage'], attack['maxDamage'])
    hit_chance = (previous_player_hit if player else 100) or attack.get('hitChance', 100)
    crit_chance = (previous_player_crit if player else previous_enemy_crit) or attack['critChance']

    # If previous player/enemy attack different from this one, reset to this' default chances
    if (player and previous_player_attack[0] != attack['id']) or (not player and previous_enemy_attack[0] != attack['id']):
        hit_chance = attack.get('hitChance', 100)
        crit_chance = attack['critChance']

    # Streak prevention
    ## Increasse hit chance by 5% if player missed previously
    if player and previous_player_attack[1] == 'miss':
        hit_chance = min(hit_chance + 5, 100)
    ## Increasse crit chance by 1% if player didn't crit previously
    elif (player and previous_player_attack[1] == 'normal') or (not player and previous_enemy_attack[1] == 'normal'):
        crit_chance = min(crit_chance + 1, 100)
    
    # Missed
    if hit_chance < 100 and roll_chance(100 - hit_chance):
        previous_player_attack = [attack['id'], 'miss']
        previous_player_hit = hit_chance
        previous_player_crit = attack['critChance']
        return 'miss', damage
    # Crit
    elif roll_chance(crit_chance):
        crit_damage = max(round(damage * (1 + attack['critMulti'])), attack['maxDamage'] + 1)
        if player:
            previous_player_attack = [attack['id'], 'crit']
            previous_player_hit = attack['hitChance']
            previous_player_crit = attack['critChance']
        else:
            previous_enemy_attack = [attack['id'], 'crit']
            previous_enemy_crit = attack['critChance']
        return 'crit', crit_damage
    # Normal
    else:
        if player:
            previous_player_attack = [attack['id'], 'normal']
            previous_player_hit = attack['hitChance']
            previous_player_crit = crit_chance
        else:
            previous_enemy_attack = [attack['id'], 'normal']
            previous_enemy_crit = crit_chance
        return 'normal', damage

def get_random_message(messages, format):
    message = random.choice(messages)
    message_substrings = [message]  # Start with the whole message as the first part

    for substring, styled_substring in format.items():
        split_substring = f"{{{substring}}}"

        # Create a new list to hold the split substrings and the formatted substrings
        new_message_substrings = []

        # Iterate through the current substrings
        for part in message_substrings:
            if split_substring in part:
                # Split the part where the placeholder is
                split_message_substring = part.split(split_substring)
                new_message_substrings.append(split_message_substring[0])  # Add the part before the placeholder
                new_message_substrings.append(styled_substring)  # Add the styled substring
                new_message_substrings.append(split_message_substring[1])  # Add the part after the placeholder
            else:
                # If no placeholder is found, just add the part unchanged
                new_message_substrings.append(part)

        # Update the list of substrings after processing
        message_substrings = new_message_substrings

    # Combine all parts into a final message
    styled_message = Text()
    for substring in message_substrings:
        styled_message += Text(substring) if not isinstance(substring, Text) else substring
    return styled_message

def player_turn(enemy, enemy_name):
    # 

    # Parameters:
    # enemy (dict): Enemy data
    # enemy_name (Text): Enemy name in rich text

    global player_health
    global enemy_health
    global weapon
    abilities = weapon['abilities']

    options = []
    for ability in abilities:
        attack = next((att for att in globals.attacks if att['id'] == ability['id']), None)
        if attack is None: raise Exception(f"Error fighting {enemy_name}: Couldn't load data properly")
        index = len(options) + 1 
        if index == 10: index = 0  # Number key list from 1-9 and then 0 so index becomes 0
        elif index > 10: break  # Weapon should not have more than 10 attacks, it will skip those extra ones if it does
        options.append(Text(f'[{index}]: ') + style_text(attack['title'], attack['name']))
    options.append(f'{'[ESC]: ' if globals.display_controls else ''}Flee')

    selected = 0
    ignore_input = False  # Flag to ignore input during sleep

    while True:
        clear_terminal()
        print_top_info(enemy, enemy_name)
        print_basic_menu(options, selected, clear=False)
        
        ability = None

        # Block keypresses during the time.sleep period
        if not ignore_input:  # If we are not ignoring input, allow keypresses
            key = readchar.readkey()  # Block until a key is pressed
            key_int = int_key(key)
        else:
            # If ignoring input, consume any keys in the buffer
            while readchar.keypress():
                pass  # This consumes any keypress that was already made during sleep

            key = None  # No key is immediately read
        
        if key == readchar.key.UP:
            debug.debug("Pressed UP arrow key")
            selected = (selected - 1) % len(options)
        elif key == readchar.key.DOWN:
            debug.debug("Pressed DOWN arrow key")
            selected = (selected + 1) % len(options)
        elif key == readchar.key.ENTER:
            debug.debug('Pressed ENTER key')
            if selected == len(options) - 1:  # Last option is always exit
                exit = flee_confirm(enemy_name)
                if exit is True:
                    return False
            else:
                ability = abilities[selected]
                break
        elif key == readchar.key.ESC:
            debug.debug('Pressed ESC key')
            exit = flee_confirm(enemy_name)
            if exit is True:
                return False
        elif key_int is not None and key_int < len(options):
            debug.debug(f'Pressed {key_int} key')
            ability = abilities[key_int - 1]
            break
        
    if ability:
        attack = next((att for att in globals.attacks if att['id'] == ability['id']), None)
        attack_title = attack.get('title', None)
        attack_name = attack.get('name', None)
        attack_type, damage = determine_attack(ability)

        # Starting attack section
        clear_terminal()
        print_top_info(enemy, enemy_name, show='player')
        messages = attack.get('messages', None)

        if (attack or attack_type or attack_name or attack_title or messages) is None:
            raise Exception(f"Error fighting {enemy_name}: Couldn't load data properly")

        styled_attack_name = style_text(attack_title, attack_name)
        start_message = get_random_message(messages['start'], {"attack_name": styled_attack_name})
        console.print(style_text({'style':'italic'}, start_message))

        time.sleep(2)  # Simulate some delay
        
        # Hit or miss attack section
        clear_terminal()
        # If attack is miss
        if attack_type == 'miss':
            print_top_info(enemy, enemy_name)
            # Get random message to print then format, and finally print it
            miss_message = get_random_message(messages['miss'], {"enemy_name": enemy_name})
            console.print(style_text({'style':'italic'}, miss_message))
        # If attack is hit or crit
        else:
            enemy_health = max(enemy_health - damage, 0)
            print_top_info(enemy, enemy_name)

            # Get random message to print then format, and finally print it
            is_crit = attack_type == 'crit'
            styled_damage = style_text({'color': [252, 144, 3] if is_crit else [201, 237, 154]}, str(damage))  # Orange damage if critical damage else green
            hit_message = get_random_message(messages['crit' if is_crit else 'hit'], {"attack_name": styled_attack_name, "damage": styled_damage})
            console.print(style_text({'style':'italic'}, hit_message))

def battle(enemy, enemy_name, enemy_id):
    global player_health
    global enemy_health
    global weapon

    player_health = globals.player.get('health')
    enemy_health = enemy.get('health')
    weapon = next((item for item in globals.weapons if item['id'] == globals.player['equipped']), None)
    for ability in weapon['abilities']:
        if ability.get('cooldown', 0) > 0 and 'timer' not in ability:
            ability['timer'] = ability['cooldown']

    if (player_health or enemy_health or weapon) is None:
        raise Exception(f"Error fighting {enemy_name}: Couldn't load data properly")
    while True:
        player_attack = player_turn(enemy, enemy_name)
        if player_attack is False: return
        time.sleep(2)
        

from libraries import *
from menus import *
from utils import *
from keyboard_manager import keyboard_manager
import globals

class Weapon:
    def __init__(self):
        self.name = None
        self.id = None
        self.chosen_attack = None
        self.abilities = []

class Player:
    def __init__(self):
        self.health = None
        self.max_health = None
        self.previous_attack_id = None
        self.previous_attack_type = None
        self.previous_hit_success = None
        self.previous_crit_success = None

class Enemy:
    def __init__(self):
        self.name = None
        self.id = None
        self.health = None
        self.max_health = None
        self.attacks = None


        self.previous_attack = None
        self.previous_attack_id = None
        self.previous_attack_type = None
        self.previous_hit_success = None
        self.previous_crit_success = None

class MenuState:
    def __init__(self):
        self.current_menu = None

        self.selected = 0
        self.options = []
        self.title = None
        self.info = None 
        self.tooltip = None
        self.menu_type = 'basic' 

        self.chosen_attack = None
        self.timer = 0
        self.timer_tooltip = None

# Initialize global state
menu_state = MenuState()
fighting_player =  Player()
fighting_enemy = Enemy()
equipped_weapon = Weapon()

idle_messages = [
    "The {enemy_name} watches your stillness like a hawk, two of them perhaps.",
    "Your clench your hands around your {weapon_name}.",
    "The clash of steel echoes, but you stand unmoved.",
    "The {enemy_name} grumbles, impatient for your next move.",
    "You lock eyes with the {enemy_name}, their eyes ",
    "A ball of hay passes by.",
    "Your stance is steady, but the moment stretches.",
    "A drop of sweat rolls down your wrist onto your {weapon_name}.",
    "The smell of iron and dirt hangs in the air.",
    "Distant cries of other fights remind you: time flows onward.",
    "The {enemy_name} tests your patience with a feinted lunge.",
    "Your muscles coil, but the strike remains unthrown.",
    "Every second you stand still is a second the {enemy_name} studies you."
]

enemy_attack_messages = {
    "hit": [
        "The enemy unleashes a savage {attack_name}, dealing {damage} damage!",
        "With a guttural roar, the enemy strikes with {attack_name}, hitting for {damage} damage!",
        "The enemy lashes out with a vicious {attack_name}, inflicting {damage} damage!",
        "The enemy charges and delivers a brutal {attack_name}, causing {damage} damage!",
        "With deadly intent, the enemy attacks with {attack_name}, dealing {damage} damage!",
        "The enemy focuses its malice into a powerful {attack_name}, striking for {damage} damage!"
    ],
    "crit": [
        "The enemy lands a devastating critical {attack_name}, dealing massive {damage} damage!",
        "A monstrous critical strike! The enemy's {attack_name} hits for {damage} damage!",
        "The enemy scores a perfect critical hit with {attack_name}, inflicting {damage} damage!",
        "The enemy's {attack_name} strikes with unnatural force - CRITICAL HIT for {damage} damage!",
        "A bone-crushing critical! The enemy's {attack_name} deals {damage} damage!"
    ]
}

attack_cooldowns = {}

def set_cooldown_timer(attack):
    id = attack['id']
    if id not in attack_cooldowns:
        attack_cooldowns[id] = attack['cooldown']  + 1
    elif attack_cooldowns[id] <= 0:
        del attack_cooldowns[id]
        set_cooldown_timer(attack)

def update_cooldown_timers():
    old_cooldowns = dict(attack_cooldowns)
    for id in old_cooldowns.keys():
        cooldown = attack_cooldowns.get(id)
        if cooldown:
            if cooldown > 0: 
                attack_cooldowns[id] -= 1

def get_timer():
    timer_color = [201, 237, 154]
    if 5 < menu_state.timer <= 10:
        timer_color = [237, 198, 154]
    elif menu_state.timer <= 5:
        timer_color = [227, 104, 104]

    return style_text({'color': timer_color}, f'{menu_state.timer}s')

def print_top_info(enemy_first=False):
    first_name = fighting_enemy.name if enemy_first else 'You' 
    first_health = fighting_enemy.health if enemy_first else fighting_player.health
    first_max_health = fighting_enemy.max_health if enemy_first else fighting_player.max_health
    second_name = 'You' if enemy_first else fighting_enemy.name
    second_health = fighting_player.health if enemy_first else fighting_enemy.health
    second_max_health = fighting_player.max_health if enemy_first else fighting_enemy.max_health

    total_width = 50
    spaces = max(total_width - len(str(first_name)) - len(str(second_name)), 1)

    first_health_color = [201, 237, 154] # Green if greater than 2/3 of health or full
    if (1/3) * first_max_health  < first_health <= (2/3) * first_max_health: 
        first_health_color = [237, 198, 154] # Orange if greater than 1/3 of health but lesser than 2/3
    elif first_health <= (1/3) * first_max_health:
        first_health_color = [227, 104, 104] # Red if lesser than 1/3 of health

    second_health_color = [201, 237, 154] # Green if greater than 2/3 of health or full
    if (1/3) * second_max_health  < second_health <= (2/3) * second_max_health: 
        second_health_color = [237, 198, 154] # Orange if greater than 1/3 of health but lesser than 2/3
    elif second_health <= (1/3) * second_max_health:
        second_health_color = [227, 104, 104] # Red if lesser than 1/3 of health

    first_min_health_string = style_text({'color': first_health_color}, str(first_health))
    first_max_health_string = style_text({'color': [171, 201, 131]}, str(first_max_health))
    second_min_health_string = style_text({'color': second_health_color}, str(second_health))
    second_max_health_string = style_text({'color': [171, 201, 131]}, str(second_max_health))

    first_health_string = first_min_health_string + Text("/") + first_max_health_string 
    second_health_string = second_min_health_string + Text("/") + second_max_health_string 
    health_spaces = max(total_width - len(str(first_health_string)) - len(str(second_health_string)), 1)

    clear_terminal()
    console.print(style_text({'style':'bold'}, first_name, ' '*spaces) + second_name)
    console.print(first_health_string + Text(' '*health_spaces) + second_health_string)

def determine_attack(attack, player=True):
    damage = random.randint(attack['minDamage'], attack['maxDamage'])
    hit_chance = (fighting_player.previous_hit_success if player else 100) or attack.get('hitChance', 100)
    crit_chance = (fighting_player.previous_crit_success if player else fighting_enemy.previous_crit_success) or attack['critChance']

    # If previous player/enemy attack different from this one, reset to this' default chances
    if (player and fighting_player.previous_attack_id != attack['id']) or (not player and fighting_enemy.previous_attack_id != attack['id']):
        hit_chance = attack.get('hitChance', 100)
        crit_chance = attack['critChance']

    # Streak prevention
    ## Increasse hit chance by 5% if player missed previously
    if player and fighting_player.previous_attack_type == 'miss':
        hit_chance = min(hit_chance + 5, 100)
    ## Increasse crit chance by 1% if player didn't crit previously
    elif (player and fighting_player.previous_attack_type == 'normal') or (not player and fighting_enemy.previous_attack_type == 'normal'):
        crit_chance = min(crit_chance + 1, 100)
    
    if player:
        fighting_player.previous_attack_id = attack['id']
    else: 
        fighting_enemy.previous_attack_id = attack['id']

    # Missed
    if hit_chance < 100 and roll_chance(100 - hit_chance):
        fighting_player.previous_attack_type = 'miss'
        fighting_player.previous_hit_success = hit_chance
        fighting_player.previous_crit_success = attack['critChance']
        return 'miss', damage
    # Crit
    elif roll_chance(crit_chance):
        crit_damage = max(round(damage * (1 + attack['critMulti'])), attack['maxDamage'] + 1)
        if player:
            fighting_player.previous_attack_type = 'crit'
            fighting_player.previous_hit_success = attack['hitChance']
            fighting_player.previous_crit_success = attack['critChance']
        else:
            fighting_enemy.previous_attack_type = 'crit'
            fighting_enemy.previous_crit_success = attack['critChance']
        return 'crit', crit_damage
    # Normal
    else:
        if player:
            fighting_player.previous_attack_type = 'normal'
            fighting_player.previous_hit_success = attack['hitChance']
            fighting_player.previous_crit_success = crit_chance
        else:
            fighting_enemy.previous_attack_type = 'normal'
            fighting_enemy.previous_crit_success = crit_chance
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

def flee_confirm(old_selected):
    # Set up the menu state for the flee confirm menu
    menu_state.current_menu = 'flee_confirm'
    menu_state.options = [style_text({'style': 'bold'}, 'No'), style_text({'style': 'bold'}, 'Yes')]
    menu_state.menu_type = 'basic'
    menu_state.selected = 0 
    menu_state.title = style_text({'style': 'bold'}, f"Are you sure you want to flee from ", fighting_enemy.name, "?")
    menu_state.info = None
    menu_state.tooltip = style_text({'style': 'italic'}, 'Arrow Keys ↑/↓ to navigate | ENTER to select | ESC to go back') if globals.display_controls else None

    original_menu = menu_state.current_menu

    def on_press(key):
        if key == 'up':  # Up arrow
            menu_state.selected = 0
            redraw_menu()
        elif key == 'down':  # Down arrow
            menu_state.selected = 1
            redraw_menu()
        elif key == 'enter':  # Enter key
            debug.debug('Pressed ENTER key')
            if menu_state.selected == 0:
                debug.info(f"Did not flee from {fighting_enemy.name}")
                player_turn(old_selected)
            elif menu_state.selected == 1: 
                debug.info(f"Fleed from {fighting_enemy.name}")
                globals.in_combat = False
        elif key == 'esc':  # ESC key
            player_turn(old_selected)

    def update_timer_display():
        if menu_state.current_menu == original_menu:
            menu_state.timer_tooltip = style_text({'style': 'bold'}, f'Time left: ', get_timer())
            redraw_menu()

    def flee_confirm_timer():
        old_timer = menu_state.timer
        while menu_state.timer > 0 and globals.in_combat and menu_state.current_menu == original_menu:
            if menu_state.timer != old_timer:
                old_timer = menu_state.timer
                update_timer_display()
            time.sleep(0.1)

    # Set the current menu handler
    keyboard_manager.set_handler(on_press)
    redraw_menu()
    threading.Thread(target=flee_confirm_timer, daemon=True).start()

def player_turn(selected=None):
    # Set up the menu state for the player's turn
    menu_state.current_menu = 'player_turn'
    menu_state.menu_type = 'basic'
    menu_state.selected = selected or 0
    menu_state.title = None
    menu_state.info = None
    menu_state.timer_tooltip = None # Will be updated dynamically
    menu_state.tooltip = None # Will be updated dynamically

    original_menu = menu_state.current_menu

    # Set up options for the menu of player's turrn
    menu_state.options = []
    for ability in equipped_weapon.abilities:
        index = len(menu_state.options) + 1 
        if index == 10: index = 0  # Number key list from 1-9 and then 0 so index becomes 0
        elif index > 10: break  # Weapon should not have more than 10 attacks, it will skip those extra ones if it does
        option_name = ability['name']
        cooldown = attack_cooldowns.get(ability['id'])
        if cooldown and cooldown > 0:
            option_name = style_text({'color': [173, 173, 173]}, option_name) + Text(f' ({cooldown} turns left)')
            debug.info(option_name)
        menu_state.options.append(Text(f'[{index}]: ') + option_name)
    menu_state.options.append(f"{'[ESC]: ' if globals.display_controls else ''}Flee")

    def on_press(key):
        key_int = int_str(key)

        if key == 'up':  # Left arrow
            update_selection(-1)
        elif key == 'down':  # Right arrow
            update_selection(1)
        elif key == 'enter':  # Enter key
            if menu_state.selected == len(menu_state.options) - 1:  # Last option is always exit
                exit = flee_confirm(menu_state.selected)
                if exit: globals.in_combat = False
                return False
            else:
                chosen_attack = equipped_weapon.abilities[menu_state.selected]
                if not attack_cooldowns.get(chosen_attack['id']):
                    menu_state.chosen_attack = chosen_attack
        elif key == 'esc':  # ESC key
            exit = flee_confirm()
            if exit: globals.in_combat = False
            return False
        elif key_int and key_int < len(menu_state.options):
            debug.debug(f'Pressed {key_int} key')
            chosen_attack = equipped_weapon.abilities[key_int - 1]
            if not attack_cooldowns.get(chosen_attack['id']):
                menu_state.chosen_attack = chosen_attack

    def update_selection(delta):
        # Update the selected option and redraw the menu.
        menu_state.selected = (menu_state.selected + delta) % len(menu_state.options)
        update_menu_info()
        redraw_menu(clear=False)
    
    def update_menu_info():
        print_top_info()

        menu_state.timer_tooltip = style_text({'style': 'bold'}, f'Time left: ', get_timer())
        menu_state.tooltip = style_text({'style': 'italic'}, 'Arrow Keys ↑/↓ to navigate | ENTER to select | ESC to go back') if globals.display_controls else None

    def player_turn_timer():
        old_timer = menu_state.timer
        while globals.in_combat and menu_state.current_menu == original_menu:
            if menu_state.timer != old_timer and menu_state.timer >= 0:
                old_timer = menu_state.timer
                update_menu_info()
                redraw_menu(clear=False)

            if menu_state.timer <= 0: 
                time.sleep(1)
                menu_state.current_menu = None
                menu_state.title = None
                menu_state.info = None
                menu_state.timer_tooltip = None
                menu_state.tooltip = None
            time.sleep(0.1)

    keyboard_manager.set_handler(on_press)
    update_menu_info()
    redraw_menu(clear=False)
    threading.Thread(target=player_turn_timer, daemon=True).start()

    while globals.in_combat and menu_state.current_menu is not None and not menu_state.chosen_attack:
        time.sleep(0.1)

def battle():
    def timer():
        while globals.in_combat and menu_state.timer > 0 and not menu_state.chosen_attack:
            time.sleep(1)
            menu_state.timer -= 1

    # Turn-based mechanics
    while fighting_enemy.health > 0 and fighting_player.health > 0:
        try:
            menu_state.chosen_attack = None
            menu_state.timer = 15

            timer_task = threading.Thread(target=timer, daemon=True)
            timer_task.start()
            player_turn()

            if not globals.in_combat: return

            menu_state.current_menu = 'initiate_attack'
            keyboard_manager.set_handler(None)

            attack_output, damage = 'miss', 0
            if menu_state.chosen_attack:
                set_cooldown_timer(menu_state.chosen_attack)
                update_cooldown_timers()
                
                attack_output, damage = determine_attack(menu_state.chosen_attack)

            print_top_info()
            if menu_state.chosen_attack:
                attack_name =  menu_state.chosen_attack['name']
                messages = menu_state.chosen_attack['messages']
                # Initate attack message
                start_message = get_random_message(messages['start'], {"attack_name": attack_name})
                console.print(style_text({'style':'italic'}, " ", start_message))

                time.sleep(2)  
                clear_terminal()

                # If attack missed
                if attack_output == 'miss':
                    print_top_info()
                    # Get random message to print then format, and finally print it
                    miss_message = get_random_message(messages['miss'], {"enemy_name": fighting_enemy.name})
                    console.print(style_text({'style':'italic'}, " ",  miss_message))
                # If attack hit normally or critically
                else:
                    fighting_enemy.health = max(fighting_enemy.health - damage, 0) # Subtract enemy health with damage
                    print_top_info()

                    # Get random message to print then format, and finally print it
                    is_crit = attack_output == 'crit'
                    styled_damage = style_text({'color': [252, 144, 3] if is_crit else [201, 237, 154]}, str(damage))  # Orange damage if critical damage else green
                    hit_message = get_random_message(messages['crit' if is_crit else 'hit'], {"attack_name": attack_name, "damage": styled_damage})
                    console.print(style_text({'style':'italic'}, " ", hit_message))
            else:
                idle_message = get_random_message(idle_messages, {"enemy_name": fighting_enemy.name, "weapon_name": equipped_weapon.name})
                console.print(style_text({'style':'italic'}, " ", idle_message))

            time.sleep(2)

            enemy_attack = random.choices(fighting_enemy.attacks, weights=[att['attackChance'] for att in fighting_enemy.attacks], k=1)[0]
            enemy_attack_output, enemy_damage = determine_attack(enemy_attack, player=False)

            fighting_player.health = max(fighting_player.health - enemy_damage, 0) # Subtract player health with enemy damage

            print_top_info(enemy_first=True)

            # Get random message to print then format, and finally print it
            attack_name =  style_text(enemy_attack['title'], enemy_attack['name'])
            messages = menu_state.chosen_attack['messages']
            is_crit = enemy_attack_output == 'crit'
            styled_enemy_damage = style_text({'color': [252, 144, 3] if is_crit else [201, 237, 154]}, str(enemy_damage))  # Orange damage if critical damage else green
            enemy_message = get_random_message(enemy_attack_messages['crit' if is_crit else 'hit'], {"attack_name": attack_name, "damage": styled_enemy_damage})
            console.print(style_text({'style':'italic'}, " ", enemy_message))

            time.sleep(3)  
        except Exception as e:
            raise
        
    globals.in_combat = False
        
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
            menu_state.timer_tooltip,
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
#       MAIN LOOP
# ========================
async def main_loop():
    global menu_state
    global fighting_player
    global fighting_enemy
    global equipped_weapon

    while True:
        if not globals.in_combat or globals.crashed:
            # Reset value
            menu_state.__init__()
            fighting_player.__init__()
            fighting_enemy.__init__()
            equipped_weapon.__init__()
            return True
        await asyncio.sleep(0.01)

# Function for game.py
async def initiate_fight(enemy, enemy_name, enemy_id):
    fighting_player.health = globals.player['health']
    fighting_player.max_health = globals.player['health']

    fighting_enemy.health = enemy['health']
    fighting_enemy.max_health = enemy['health']
    fighting_enemy.name = enemy_name
    fighting_enemy.id = enemy_id
    fighting_enemy.attacks = enemy['attacks']

    weapon = next((item for item in globals.weapons if item['id'] == globals.player['equipped']), None)
        
    if (fighting_player.health or fighting_enemy.health or weapon) is None:
        raise Exception(f"Error fighting {enemy_name}: Couldn't load data properly")
    
    equipped_weapon.name = style_text(weapon['title'], weapon['name'])
    
    for ability in weapon['abilities']:
        attack = next((att for att in globals.attacks if att['id'] == ability['id']), None)

        if attack is None:
            raise Exception(f"Error fighting {enemy_name}: Couldn't load data properly")
        
        ability_info = {}
        for key, value in ability.items():
            ability_info[key] = value

        for key, value in attack.items():
            if key in ['id', 'description']:
                continue # Skip id because we already fetched it before, skip description because it's not needed
            ability_info[key] = value

        # Important keys required for fight mechanics
        important_keys = ['name', 'title', 'id', 'messages', 'minDamage', 'maxDamage', 'critMulti', 'critChance', 'hitChance', 'cooldown'] 
        for key in important_keys:
            if key not in ability_info:
                raise Exception(f"Error fighting {enemy_name}: Couldn't load data properly")
        debug.info(ability['id'])

        # Store name as styled text and remove title because it's not needed
        ability_info['name'] = style_text(ability_info['title'], ability_info['name'])
        del ability_info['title']

        equipped_weapon.abilities.append(ability_info)

    debug.info(f'Initiated fight for {enemy_name}')

    asyncio.create_task(main_loop())

    battle()

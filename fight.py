from libraries import *
from menus import *
from utils import *
import globals

player_health = None
enemy_health = None
weapon = None

def int_key(key):
    try:
        integer = int(str(key))
        return integer
    except:
        return None

def print_top_info(enemy, enemy_name):
    player_max_health = globals.player.get('health')
    enemy_max_health = enemy.get('health')
    if (player_max_health or enemy_max_health) is None:
        raise Exception(f"Error fighting {enemy_name}: Couldn't load data properly")

    total_width = 50
    spaces = max((total_width - 3 - len(str(enemy_name))), 1)
    console.print(style_text({'style':'bold'}, f'You{' '*spaces}') + enemy_name)

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
    console.print(player_health_string + Text(' '*health_spaces) + enemy_health_string)

def player_turn(enemy, enemy_name):
    global player_health
    global enemy_health
    global weapon
    abilities = weapon['abilities']
    options = []
    for ability in abilities:
        index = len(options) + 1 
        # 
        if index == 10: index = 0
        elif index > 10: break # Weapon should not have more than 10 attacks, it will skip those extra ones if it does
        options.append(Text(f'[{index}]: ') + style_text(ability['title'], ability['name']))
    options.append(f'{'[ESC]: ' if globals.display_controls else ''}Flee')
    debug.info(options)
    selected = 0
    while True:
        clear_terminal()
        print_top_info(enemy, enemy_name)
        print_basic_menu(options, selected, clear=False)

        key = readchar.readkey()
        key_int = int_key(key)
        if key == readchar.key.UP:
            debug.debug("Pressed UP arrow key")
            selected = (selected - 1) % len(options)
        elif key == readchar.key.DOWN:
            debug.debug("Pressed DOWN arrow key")
            selected = (selected + 1) % len(options)
        elif key == readchar.key.ENTER:
            debug.debug('Pressed ENTER key')
        elif key == readchar.key.ESC:
            debug.debug('Pressed ESC key')
        elif key_int is not None and key_int < len(options):
            debug.debug(f'Pressed {key_int} key')



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
    player_attack = player_turn(enemy, enemy_name) 

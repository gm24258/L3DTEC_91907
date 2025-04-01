from .menus import *
from .utils import *
from .keyboard_manager import keyboard_manager
from .globals import player
from . import globals

# ========================
# CLASSES AND GLOBAL STATE
# ========================
class Weapon:
    def __init__(self):
        self.name = None              # Name of the weapon
        self.id = None                # Unique identifier for the weapon
        self.chosen_attack = None     # ID of the chosen attack (or None if not set)
        self.abilities = []           # List of abilities (could be a list of Attack objects)

class Player:
    def __init__(self):
        self.health = 100             # Default health (example value)
        self.max_health = 100         # Default max health (example value)
        self.faster_logs = False      # Whether faster battle logs are enabled

        self.previous_attack_id = None    # ID of the last attack used
        self.previous_attack_type = None  # Type of the last attack used
        self.previous_hit_success = None  # Whether the last attack hit
        self.previous_crit_success = None # Whether the last attack was a critical hit

class Enemy:
    def __init__(self):
        self.name = None              # Name of the enemy
        self.id = None                # Unique identifier for the enemy
        self.health = 100             # Default health (example value)
        self.max_health = 100         # Default max health (example value)
        self.attacks = []             # List of attacks (could be a list of Attack objects)
        self.rewards = []             # List of rewards (e.g., items, money)
        self.level = 1                # Default level (example value)

        self.previous_attack = None          # Last attack used by the enemy
        self.previous_attack_id = None       # ID of the last attack used
        self.previous_attack_type = None     # Type of the last attack used
        self.previous_hit_success = None     # Whether the last attack hit
        self.previous_crit_success = None    # Whether the last attack was a critical hit

class MenuState:
    """Manages the state of the current menu, including options, navigation, etc."""
    def __init__(self):
        self.current_menu = None            # Currently displayed menu (e.g., 'main', 'settings')
        self.selected = 0                   # Index of the currently selected option
        self.options = []                   # List of available menu options
        self.title = None                   # Title of the menu
        self.info = None                    # Additional information for the menu (e.g., descriptions)
        self.tooltip = None                 # Tooltip for menu controls or options
        self.menu_type = 'basic'            # Type of menu (could be 'basic', 'detailed', etc.)

        self.chosen_attack = None           # The attack chosen by the player (or None)
        self.timer = 0                      # Timer for any time-limited actions or effects
        self.timer_tooltip = None           # Tooltip for the timer or any time-related info

# Initialize global state
menu_state = MenuState() # Tracks the state of the current menu
fighting_player = Player() # Represents the player in combat
fighting_enemy = Enemy() # Represents the enemy in combat
equipped_weapon = Weapon() # Holds the currently equipped weapon

# ========================
#     ATTACK COOLDOWN
# ========================

attack_cooldowns = {}  # Holds cooldowns for attacks by attack ID

def set_cooldown_timer(attack):
    """Function to set a cooldown timer for an attack"""
    id = attack['id']  # Unique ID for the attack
    if id not in attack_cooldowns:  # If the attack isn't already on cooldown
        attack_cooldowns[id] = attack['cooldown']  + 1  # Set the cooldown timer
    elif attack_cooldowns[id] <= 0:  # If the cooldown has ended
        del attack_cooldowns[id]  # Remove the cooldown
        set_cooldown_timer(attack)  # Reset the cooldown timer

def update_cooldown_timers():
    """Function to update cooldown timers for all active attacks"""
    old_cooldowns = dict(attack_cooldowns)  # Make a copy of the current cooldowns
    for id in old_cooldowns.keys():  # Loop through each attack ID
        cooldown = attack_cooldowns.get(id)  # Get the cooldown for the current attack ID
        if cooldown:  # If there is a valid cooldown
            if cooldown > 0:  # If the cooldown is greater than 0
                attack_cooldowns[id] -= 1  # Decrease the cooldown by 1 second

def get_timer():
    """Function to return the remaining cooldown time as a formatted string"""
    timer_color = [201, 237, 154]  # Default color for the timer (greenish)
    if 3 < menu_state.timer <= 6:  # Change color to yellow if timer is between 3 and 6
        timer_color = [237, 198, 154]
    elif menu_state.timer <= 3:  # Change color to red if timer is less than or equal to 3
        timer_color = [227, 104, 104]

    return style_text({'color': timer_color}, f'{menu_state.timer}s')  # Return the styled timer with color

# =======================
#     PRINT TOP INFO
# =======================

def print_top_info(enemy_first=False, victory=None):
    """
    Function to print the top info (player and enemy stats) on the screen.

    Parameters:
    - enemy_first (bool): If True, the enemy's stats will be printed first. Defaults to False (player first).
    - victory (bool, optional): If provided, determines whether the player won or lost the battle. 
                                 If True, the player's victory status is highlighted.
                                 If False, the player's defeat status is highlighted.
    """
    # Determine the names and health of the player and enemy based on whether the enemy goes first
    first_name = fighting_enemy.name + Text(f' Lvl. {fighting_enemy.level}') if enemy_first else style_text({'style':'bold'}, 'You') + Text(f' Lvl. {player.level}')
    first_health = fighting_enemy.health if enemy_first else fighting_player.health
    first_max_health = fighting_enemy.max_health if enemy_first else fighting_player.max_health

    second_name = style_text({'style':'bold'}, 'You') + Text(f' Lvl. {player.level}') if enemy_first else fighting_enemy.name + Text(f' Lvl. {fighting_enemy.level}')
    second_health = fighting_player.health if enemy_first else fighting_enemy.health
    second_max_health = fighting_player.max_health if enemy_first else fighting_enemy.max_health
    
    total_width = 60  # Total width of the display
    spaces = max(total_width - len(str(first_name)) - len(str(second_name)), 1)  # Calculate space between player and enemy names

    # Determine the health color for both player and enemy based on current health status
    first_health_color = [201, 237, 154]  # Green for healthy
    if (1/3) * first_max_health < first_health <= (2/3) * first_max_health:
        first_health_color = [237, 198, 154]  # Orange for moderate health
    elif first_health <= (1/3) * first_max_health:
        first_health_color = [227, 104, 104]  # Red for low health

    second_health_color = [201, 237, 154]  # Green for healthy
    if (1/3) * second_max_health < second_health <= (2/3) * second_max_health:
        second_health_color = [237, 198, 154]  # Orange for moderate health
    elif second_health <= (1/3) * second_max_health:
        second_health_color = [227, 104, 104]  # Red for low health

    # Style the health values with appropriate colors
    first_min_health_string = style_text({'color': first_health_color}, str(first_health))
    first_max_health_string = style_text({'color': [201, 93, 93] if victory is False else [171, 201, 131]}, str(first_max_health))
    second_min_health_string = style_text({'color': second_health_color}, str(second_health))
    second_max_health_string = style_text({'color': [201, 93, 93] if victory else [171, 201, 131]}, str(second_max_health))

    # Combine health values into strings to be displayed
    first_health_string = first_min_health_string + Text("/") + first_max_health_string
    second_health_string = second_min_health_string + Text("/") + second_max_health_string
    health_spaces = max(total_width - len(str(first_health_string)) - len(str(second_health_string)), 1)

    # Clear terminal and print the stats
    clear_terminal()
    console.print(first_name + ' ' * spaces + second_name)
    console.print(first_health_string + Text(' ' * health_spaces) + second_health_string)

# ========================
#     BATTLE MESSAGES
# ========================

# Idle messages during combat when player idles after timer
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

# Messages for enemy attacks (normal hit and critical hit)
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

def get_random_message(messages, format):
    """
    Function to get a random message from a list and format it with dynamic values.

    Parameters:
    - messages (list of str): List of messages to choose from.
    - format (dict): Dictionary with placeholders as keys and corresponding formatted text as values.

    Returns:
    - Text: A styled message with formatted values applied to it.
    """
    message = random.choice(messages)  # Pick a random message from the list
    message_substrings = [message]  # Start with the whole message as the first part

    # Iterate over the formatting options and apply them to the message
    for substring, styled_substring in format.items():
        split_substring = f"{{{substring}}}"  # Find the placeholder to replace

        # Create a new list to hold the split substrings and formatted substrings
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
                new_message_substrings.append(part)  # If no placeholder is found, just add the part unchanged

        message_substrings = new_message_substrings  # Update the list of substrings

    # Combine all parts into a final styled message
    styled_message = Text()
    for substring in message_substrings:
        styled_message += Text(substring) if not isinstance(substring, Text) else substring
    return styled_message

# =======================
#   DAMAGE CALCULATION
# =======================

def determine_attack(attack, player=True):
    """
    Function to determine the outcome of an attack (hit, crit, or miss).

    Parameters:
    - attack (dict): The attack object containing details such as minDamage, maxDamage, hitChance, critChance, etc.
    - player (bool): A boolean to specify whether the attack is from the player (True) or the enemy (False). Defaults to True.

    Returns:
    - tuple: A tuple containing the attack result (hit, crit, or miss) and the damage dealt.
    """
    # Calculate damage based on the attack's min and max damage
    damage = random.randint(attack['minDamage'], attack['maxDamage'])
    # Set hit and crit chances based on player or enemy
    hit_chance = (fighting_player.previous_hit_success if player else 100) or attack.get('hitChance', 100)
    crit_chance = (fighting_player.previous_crit_success if player else fighting_enemy.previous_crit_success) or attack['critChance']

    # Reset hit and crit chances if the attack ID is different from the last one
    if (player and fighting_player.previous_attack_id != attack['id']) or (not player and fighting_enemy.previous_attack_id != attack['id']):
        hit_chance = attack.get('hitChance', 100)
        crit_chance = attack['critChance']

    # Streak prevention: Adjust chances based on previous attack outcomes
    if player and fighting_player.previous_attack_type == 'miss':
        hit_chance = min(hit_chance + 5, 100)  # Increase hit chance by 5% if player missed previously
    elif (player and fighting_player.previous_attack_type == 'normal') or (not player and fighting_enemy.previous_attack_type == 'normal'):
        crit_chance = min(crit_chance + 1, 100)  # Increase crit chance by 1% if player or enemy didn't crit previously

    # Update previous attack ID for both player and enemy
    if player:
        fighting_player.previous_attack_id = attack['id']
    else:
        fighting_enemy.previous_attack_id = attack['id']

    # Determine the outcome of the attack (miss, crit, or normal)
    if hit_chance < 100 and roll_chance(100 - hit_chance):  # Missed attack
        fighting_player.previous_attack_type = 'miss'
        fighting_player.previous_hit_success = hit_chance
        fighting_player.previous_crit_success = attack['critChance']
        return 'miss', damage
    elif roll_chance(crit_chance):  # Critical hit
        crit_damage = max(round(damage * (1 + attack['critMulti'])), attack['maxDamage'] + 1)
        if player:
            fighting_player.previous_attack_type = 'crit'
            fighting_player.previous_hit_success = attack['hitChance']
            fighting_player.previous_crit_success = attack['critChance']
        else:
            fighting_enemy.previous_attack_type = 'crit'
            fighting_enemy.previous_crit_success = attack['critChance']
        return 'crit', crit_damage
    else:  # Normal hit
        if player:
            fighting_player.previous_attack_type = 'normal'
            fighting_player.previous_hit_success = attack['hitChance']
            fighting_player.previous_crit_success = crit_chance
        else:
            fighting_enemy.previous_attack_type = 'normal'
            fighting_enemy.previous_crit_success = crit_chance
        return 'normal', damage

# ========================
#       MENU FUNCTIONS
# ========================

def flee_confirm(old_selected):
    """
    Initializes the flee confirmation menu, handles key presses for navigation and selection,
    and displays the current combat timer, allowing the player to decide whether to flee or not.
    
    Parameters:

    old_selected (int): The index of the pre-selected option for the player's turn. 
                        Used to restore the player's selection in the player's turn when returning from here. 
    """
    # Set up the menu state for the flee confirm menu
    menu_state.current_menu = 'flee_confirm'  # Identify this menu as the flee confirm screen
    menu_state.options = [style_text({'style': 'bold'}, 'No'), style_text({'style': 'bold'}, 'Yes')]  # Menu options: No and Yes
    menu_state.menu_type = 'basic'  # Simple menu type
    menu_state.selected = 0  # Default selection is 'No'
    menu_state.title = style_text({'style': 'bold'}, f"Are you sure you want to flee from ", fighting_enemy.name, "?")  # Title with enemy's name
    menu_state.info = None  # No additional information shown
    menu_state.tooltip = style_text({'style': 'italic'}, 'Arrow Keys ↑/↓ to navigate | ENTER to select | ESC to go back') if player.display_controls else None  # Tooltip for controls

    original_menu = menu_state.current_menu  # Store the original menu to track the current menu during the timer update

    def on_press(key):
        """
        Handle key inputs required for the menu
        Basic-type menus use up and down keys
        
        Parameters:
        key (str): The key that was pressed by the player.
        """
        if key == ('up' if player.use_arrow_keys else 'w'):  # Up arrow or 'w' for navigation
            menu_state.selected = 0  # Select 'No'
            redraw_menu()  # Redraw the menu to reflect the new selection
        elif key == ('down' if player.use_arrow_keys else 's'):  # Down arrow or 's' for navigation
            menu_state.selected = 1  # Select 'Yes'
            redraw_menu()  # Redraw the menu to reflect the new selection
        elif key == 'enter':  # Enter key
            if menu_state.selected == 0:  # If 'No' is selected
                debug.info(f"Did not flee from {fighting_enemy.name}")  # Log action
                player_turn(old_selected)  # Continue with the player's turn
            elif menu_state.selected == 1:  # If 'Yes' is selected
                debug.info(f"Fleed from {fighting_enemy.name}")  # Log action
                globals.in_combat = False  # Exit combat mode
        elif key == 'esc':  # ESC key
            player_turn(old_selected)  # Go back to the player's turn

    def update_timer_display():
        """
        Updates the display of the combat timer in the flee confirm menu.
        
        This function is responsible for refreshing the display of the time left for the player
        to make a decision on fleeing. The time left is based on the current combat timer.
        """
        if menu_state.current_menu == original_menu:  # If the menu is still active
            menu_state.timer_tooltip = style_text({'style': 'bold'}, f'Time left: ', get_timer())  # Update the timer tooltip with the current time left
            redraw_menu()  # Redraw the menu with updated timer display
    def flee_confirm_timer():
        """
        Handles the countdown timer for the flee confirm menu, which reflects the current combat timer.
        
        The timer decrements over time, and the menu display is updated whenever the timer changes.
        The loop will exit once the timer reaches 0 or the combat ends.
        """
        old_timer = menu_state.timer  # Store the current timer value
        while globals.in_combat and menu_state.current_menu == original_menu and menu_state.timer >= 0:  # While the timer is active and combat continues
            if menu_state.timer != old_timer:  # If the timer has changed
                old_timer = menu_state.timer  # Update the old timer value
                update_timer_display()  # Update the timer display

            if menu_state.timer < 0: break # If the timer runs out

            time.sleep(0.1)  # Sleep for a short time to avoid using too much CPU

    # Set the current menu handler for key presses
    keyboard_manager.set_handler(on_press)
    redraw_menu()  # Redraw the menu initially
    threading.Thread(target=flee_confirm_timer, daemon=True).start()  # Start the timer in a separate thread to avoid blocking

def player_turn(selected=0):
    """
    Sets up and handles the player's turn in combat. The menu allows the player to choose an attack
    or flee from combat. The player's options are dynamically updated based on the abilities of the
    equipped weapon and their cooldowns. The combat timer is also displayed.

    Parameters:
    selected (int): The index of the pre-selected option for this menu. 
                    Used to restore the player's selection when returning here from other menus or functions. 
                    Defaults to None if not set.
    """
    # Set up the menu state for the player's turn
    menu_state.current_menu = 'player_turn'  # Identify this menu as the player's turn menu
    menu_state.menu_type = 'basic'  # Simple menu type
    menu_state.selected = selected # Set the default selected option (either passed or first option)
    menu_state.title = None  # No title displayed for this menu
    menu_state.info = None  # No additional information shown
    menu_state.timer_tooltip = None  # Will be updated dynamically
    menu_state.tooltip = None  # Will be updated dynamically

    original_menu = menu_state.current_menu  # Store the original menu to track the current menu during the timer update

    # Set up options for the menu of player's turn
    menu_state.options = []
    for ability in equipped_weapon.abilities:
        """
        Populate the options list with the player's available abilities and cooldowns. If an ability
        is on cooldown, its name will be grayed out with the remaining cooldown time displayed.
        """
        index = len(menu_state.options) + 1
        if index == 10: index = 0  # Number key list from 1-9 and then 0 so index becomes 0
        elif index > 10: break  # Limit weapon abilities to a maximum of 10
        option_name = ability['name']
        cooldown = attack_cooldowns.get(ability['id'])
        if cooldown and cooldown > 0:
            option_name = style_text({'color': [173, 173, 173]}, option_name) + Text(f' ({cooldown} turns left)')
        menu_state.options.append(Text(f'[{index}]: ') + option_name)
    menu_state.options.append(f"{'[ESC]: ' if player.display_controls else ''}Flee")  # Add the flee option

    def on_press(key):
        """
        Handles key press events for the player's turn menu. This function determines how the player
        navigates the menu and selects an attack or chooses to flee.

        Parameters:
        key (str): The key pressed by the player.
        """
        key_int = int_str(key)

        if key == ('up' if player.use_arrow_keys else 'w'):  # Up arrow or 'w' for navigation
            update_selection(-1)  # Move up in the menu
        elif key == ('down' if player.use_arrow_keys else 's'):  # Down arrow or 's' for navigation
            update_selection(1)  # Move down in the menu
        elif key == 'enter':  # Enter key to select an option
            if menu_state.selected == len(menu_state.options) - 1:  # Last option is always flee
                exit = flee_confirm(menu_state.selected)  # Confirm flee action
                if exit: globals.in_combat = False  # Exit combat if confirmed
            else:
                # Select an attack from the weapon abilities
                chosen_attack = equipped_weapon.abilities[menu_state.selected]
                if not attack_cooldowns.get(chosen_attack['id']):  # Check if the attack is off cooldown
                    menu_state.chosen_attack = chosen_attack  # Set the chosen attack
        elif key == 'esc':  # ESC key to flee
            exit = flee_confirm(menu_state.selected)  # Confirm flee action
            if exit: globals.in_combat = False  # Exit combat if confirmed
        elif key_int and key_int < len(menu_state.options):  # If a valid number key is pressed
            debug.debug(f'Pressed {key_int} key')
            chosen_attack = equipped_weapon.abilities[key_int - 1]  # Select the attack based on key
            if not attack_cooldowns.get(chosen_attack['id']):  # Check if the attack is off cooldown
                menu_state.chosen_attack = chosen_attack  # Set the chosen attack

    def update_selection(delta):
        """
        Updates the selected option in the player's turn menu. It ensures the selection wraps around 
        when reaching the top or bottom of the menu.

        Parameters:
        delta (int): The change in selection (either +1 or -1 to move up or down).
        """
        menu_state.selected = (menu_state.selected + delta) % len(menu_state.options)  # Adjust the selected option
        update_menu_info()  # Update the menu info with the new selection

    def update_menu_info():
        """
        Updates the top info section and the tooltip display with the current combat timer and 
        control hints.
        """
        print_top_info()  # Print the top section info (e.g., health, etc.)

        menu_state.timer_tooltip = style_text({'style': 'bold'}, f'Time left: ', get_timer())  # Display the remaining time in the combat timer
        menu_state.tooltip = style_text({'style': 'italic'}, 'Arrow Keys ↑/↓ to navigate | ENTER to select | ESC to go back') if player.display_controls else None  # Display controls

        redraw_menu(clear=False)  # Redraw the menu 
    
    def player_turn_timer():
        """
        Handles the countdown for the player's turn timer. While the player's turn is active,
        it continually checks and updates the display based on the remaining time. Once the time
        runs out, it clears the menu and ends the turn.

        This function runs in a separate thread to avoid blocking the main game loop.
        """
        old_timer = menu_state.timer  # Store the current timer value
        while globals.in_combat and menu_state.current_menu == original_menu and menu_state.timer >= 0:  # Continue while combat is ongoing
            if menu_state.timer != old_timer:  # If the timer changes
                old_timer = menu_state.timer  # Update the old timer value
                update_menu_info()  # Update the menu info (timer, controls)

            if menu_state.timer < 0:  # If the timer runs out
                menu_state.current_menu = None  # Close the menu
                menu_state.title = None  # Remove the title
                menu_state.info = None  # Clear the info section
                menu_state.timer_tooltip = None  # Remove the timer tooltip
                menu_state.tooltip = None  # Remove the control tooltip
                break
            time.sleep(0.1)  # Sleep briefly to avoid using excessive CPU

    # Set the current menu handler for key presses
    keyboard_manager.set_handler(on_press)
    update_menu_info()  # Update the menu info initially
    threading.Thread(target=player_turn_timer, daemon=True).start()  # Start the timer in a separate thread

def battle():
    """
    Manages the entire combat sequence between the player and the enemy. This includes turn-based
    mechanics, where each side (player and enemy) takes turns attacking. The function also manages
    timers, messages, damage calculation, and handles the win/loss conditions.

    This function runs in a loop until either the player or enemy is defeated.
    """
    def timer():
        """
        A timer function that counts down from the initial time limit (10 seconds). The timer runs
        in a separate thread and decreases the menu timer by 1 each second. The timer stops when
        the turn ends or the player selects an attack.

        The timer is used to limit how long the player has to make a move during their turn.
        """
        while globals.in_combat and menu_state.timer >= 0 and not menu_state.chosen_attack:
            time.sleep(1)  # Wait for 1 second
            menu_state.timer -= 1  # Decrease the timer by 1 second

    # Turn-based mechanics
    while fighting_enemy.health > 0 and fighting_player.health > 0:  
        """
        The main combat loop runs as long as both the player and enemy are alive. Each iteration
        represents a player's turn followed by the enemy's turn.
        """
        try:
            # Reset menu state and set timer
            menu_state.chosen_attack = None
            menu_state.timer = 10  # Set a 10-second timer for the player's turn

            # Start the timer in a separate thread
            timer_task = threading.Thread(target=timer, daemon=True)
            timer_task.start()

            # Run the player's turn (choose an attack or flee)
            player_turn()

            # Loop until the timer is over and the player is at player's turn
            while globals.in_combat and not menu_state.chosen_attack:
                if menu_state.current_menu == 'player_turn' and menu_state.timer < 0: break
                # Wait for the player to make a selection or for the combat to end
                time.sleep(0.1)

            if not globals.in_combat: return  # Exit if combat has ended

            # End the player's turn and clear input handler
            menu_state.current_menu = None
            keyboard_manager.set_handler(None)

            # Determine the result of the player's attack
            attack_output, damage = 'miss', 0
            if menu_state.chosen_attack:
                set_cooldown_timer(menu_state.chosen_attack)  # Set cooldown for the attack
                update_cooldown_timers()  # Update the cooldown timers

                attack_output, damage = determine_attack(menu_state.chosen_attack)  # Execute the attack

            print_top_info()  # Print the top info (e.g., health, turn info)
            
            if menu_state.chosen_attack:  # If the player chose an attack
                attack_name =  menu_state.chosen_attack['name']
                messages = menu_state.chosen_attack['messages']
                start_message = get_random_message(messages['start'], {"attack_name": attack_name})  # Get attack start message
                console.print(style_text({'style':'italic'}, " ", start_message))
    
                time.sleep(0.5 if fighting_player.faster_logs else 1.5)  # Adjust log speed

                # Handle missed attack
                if attack_output == 'miss':
                    print_top_info()  # Print top info again for miss
                    miss_message = get_random_message(messages['miss'], {"attack_name": attack_name, "enemy_name": fighting_enemy.name})
                    console.print(style_text({'style':'italic'}, " ", miss_message))
                else:
                    # Handle successful or critical hit
                    fighting_enemy.health = max(fighting_enemy.health - damage, 0)  # Decrease enemy health
                    print_top_info()  # Update top info after hit

                    is_crit = attack_output == 'crit'
                    styled_damage = style_text({'color': [252, 144, 3] if is_crit else [201, 237, 154]}, str(damage))  # Style damage based on crit or normal hit
                    hit_message = get_random_message(messages['crit' if is_crit else 'hit'], {"attack_name": attack_name, "enemy_name": fighting_enemy.name, "damage": styled_damage})
                    console.print(style_text({'style':'italic'}, " ", hit_message))  # Print the hit message
            else:
                idle_message = get_random_message(idle_messages, {"enemy_name": fighting_enemy.name, "weapon_name": equipped_weapon.name})
                console.print(style_text({'style':'italic'}, " ", idle_message))  # If the player didn't attack, show idle message

            if fighting_enemy.health > 0:  # If the enemy is still alive, take its turn
                time.sleep(0.5 if fighting_player.faster_logs else 1.5)  # Adjust log speed

                # Determine the enemy's attack
                enemy_attack = random.choices(fighting_enemy.attacks, weights=[att['attackChance'] for att in fighting_enemy.attacks], k=1)[0]
                enemy_attack_output, enemy_damage = determine_attack(enemy_attack, player=False)  # Enemy attacks the player

                # Update player health after enemy's attack
                fighting_player.health = max(fighting_player.health - enemy_damage, 0)

                print_top_info(enemy_first=True)  # Print updated info for the enemy's attack

                # Print the message for the enemy's attack
                attack_name =  style_text(enemy_attack['title'], enemy_attack['name'])
                is_crit = enemy_attack_output == 'crit'
                styled_enemy_damage = style_text({'color': [252, 144, 3] if is_crit else [201, 237, 154]}, str(enemy_damage))
                enemy_message = get_random_message(enemy_attack_messages['crit' if is_crit else 'hit'], {"attack_name": attack_name, "enemy_name": fighting_enemy.name, "damage": styled_enemy_damage})
                console.print(style_text({'style':'italic'}, " ", enemy_message))

            time.sleep(1.5 if fighting_player.faster_logs else 2.5)  # Adjust log speed between turns
        except Exception as e:
            raise

    # Checks for loss/victory
    if globals.in_combat:
        menu_state.current_menu = None  # End the combat menu
        keyboard_manager.set_handler(None)  # Remove keyboard input handler

        # Check if the player or enemy won the battle
        victory = True if fighting_enemy.health <= 0 else False
        victory = False if fighting_player.health <= 0 else victory

        print_top_info(victory=victory)  # Print final battle info
        if victory:
            console.print(f'You defeated {fighting_enemy.name}! Victory is yours!')  # Victory message
            rewards = fighting_enemy.rewards
            xp_reward = random.randint(rewards['minXp'], rewards['maxXp'])  # Random XP reward
            money_reward = random.randint(rewards['minMoney'], rewards['maxMoney'])  # Random money reward

            time.sleep(0.5 if fighting_player.faster_logs else 2)

            player.balance += money_reward  # Add money to player's balance
            player.xp += xp_reward  # Add XP to player's total
            leveled_up = player.level_up()  # Check if player levels up
            console.print(Text(f"You've gained ") + style_text({'color': [201, 237, 154]}, str(xp_reward)) + Text(f" XP and ") + style_text({'color': [201, 237, 154]}, f'${money_reward}'))

            # If enemy has weapon rewards
            if rewards.get('weapons'):
                rolled_rewards = [] # Initialize won rewards
                # Iterate through weapon drops
                for drop, chance in rewards['weapons'].items():
                    # If successfully rolled chance
                    if roll_percentage(chance) and not drop in player.inventory:
                        rolled_rewards.append(drop) # Add reward to won rewards

                if len(rolled_rewards) > 0:
                    reward = rolled_rewards[len(rolled_rewards) - 1] # Get the latest won reward
                    player.inventory.append(reward) # Put won reward in inventory
                    
                    weapon = next((item for item in globals.weapons if item['id'] == drop), None) # Get weapon data of reward
                    console.print(Text("You have obtained: ") + style_text(weapon['title'], f"{weapon['name']} ({chance}%)"))

            player.save()  # Save player progress

            if leveled_up: 
                console.print(f"You leveled up to {player.level}!")  # Display level-up message
        else:
            console.print(f'You have been defeated. The {fighting_enemy.name} stands victorious.')  # Defeat message

        time.sleep(1.5 if fighting_player.faster_logs else 2)

        console.print(Text(f'Exiting battle from ') + fighting_enemy.name + Text('...'))

        time.sleep(0 if fighting_player.faster_logs else 0.5)

    globals.in_combat = False  # End the combat

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

# ========================
#    INITIALIZE BATTLE
# ========================

# Function for game.py
def initiate_fight(enemy, enemy_name, enemy_id):
    global attack_cooldowns

    # Reset values from previous battle
    attack_cooldowns = {}
    menu_state.__init__()
    fighting_player.__init__()
    fighting_enemy.__init__()
    equipped_weapon.__init__()

    clear_terminal()
    debug.info(f'Initiated fight for {enemy_name}...')
    console.print(Text(f'Loading battle for ') + enemy_name + Text('...'))

    fighting_player.health = player.health
    fighting_player.max_health = player.health
    fighting_player.faster_logs = player.settings['fasterBattleLogs']

    fighting_enemy.health = enemy['health']
    fighting_enemy.max_health = enemy['health']
    fighting_enemy.name = enemy_name
    fighting_enemy.id = enemy_id
    fighting_enemy.level = enemy['level']
    fighting_enemy.attacks = enemy['attacks']
    fighting_enemy.rewards = enemy['rewards']

    weapon = next((item for item in globals.weapons if item['id'] == player.equipped), None)
        
    if (fighting_player.health or fighting_enemy.health or weapon) is None:
        raise Exception(f"Error fighting {enemy_name}: Couldn't load data properly, player/enemy health or weapon data is missing")
    
    equipped_weapon.name = style_text(weapon['title'], weapon['name'])
    
    for ability in weapon['abilities']:
        attack = next((att for att in globals.attacks if att['id'] == ability['id']), None)

        if attack is None:
            raise Exception(f"Error fighting {enemy_name}: Couldn't load data properly, weapon ability is missing a corresponding attack")
        
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
                raise Exception(f"Error fighting {enemy_name}: Couldn't load data properly, ability is missing key: {key}")

        # Store name as styled text and remove title because it's not needed
        ability_info['name'] = style_text(ability_info['title'], ability_info['name'])
        del ability_info['title']

        equipped_weapon.abilities.append(ability_info)

    debug.info(f'Initiated fight for {enemy_name}')

    battle()
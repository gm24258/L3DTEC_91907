# Example ChatGPT script:
import readchar
import time

# Text formatting
bold = "\033[1m"
italic = "\033[3m"
reset = "\033[0m"

def mainMenu():
    buttons = ["Play", "Shield", "Potion", "Bow", "Exit"]
    selected = 0

    # Main sceen
    def print_menu():
        # Clears terminal screen
        print("\033c", end="")  
        # Title
        print(f"{bold}MAIN MENU:{reset}")

        # Printing buttons
        for i, item in enumerate(buttons):
            prefix = "> " if i == selected else "  "
            print(prefix + item)

        # Tooltip
        print(f"\n{italic}Use Arrow Keys (↑/↓) to navigate, Enter to select.{reset}") 

    # First start
    print_menu()

    # Handling arrow Kkeys
    while True:
        key = readchar.readkey()
        
        if key == readchar.key.UP:
            selected = (selected - 1) % len(buttons) 
        elif key == readchar.key.DOWN:
            selected = (selected + 1) % len(buttons) 
        elif key == readchar.key.ENTER:
            print(f"\nYou selected: {buttons[selected]}")
            break
        
        print_menu()

mainMenu()
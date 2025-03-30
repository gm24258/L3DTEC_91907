# generic terminal rpg
*A random Python RPG game intended to be played on the terminal. Made for a school project.*

## Features
- Menu system: Navigate through game options and menus using
- Turn based combat: Engage in battles using weapons with different stats and abilities.
- Level progression: Gain experience from your battles to unlock new weapons and more challenging but rewarding enemies.
- Inventory & shop: View, purchase and manage weapons which get better stats the higher level requirements they need.
- Text-based UI: Uses the terminal and uses `rich` module to display colors.

## Installation 
- Recommended to use Python 3.11+
- It is recommended that you use Windows Terminal or Visual Studio Code's integrated terminal because other terminals have limited font style, color and emoji support.
- Go to the latest [release](https://github.com/gm24258/L3DTEC_91907/releases) and install the `generic_terminal_rpg.zip`
- Extract the zip somewhere like Documents, and ensure the only thing extracted is the "generic terminal rpg" folder.

### Dependencies
- PyGetWindow: `0.0.9`
- pynput: `1.8.1`
- rich: `13.9.4`
- Run the following command to install required libraries: `pip install -r requirements.txt`

## How to Play
- Run `main.py` in the folder.
- Control instructions are shown in tooltips to help you navigate the game.
- 'Play' leads you to the play menu, where you can select and choose to fight enemies. These enemies have level requirements so while you can view the stats of them, if you don't meet the level requirement, you cannot fight them.
- 'Shop' leads you to a menu where you can view available weapons and their stats and abilities. If you meet their price and level requirements, you can purchase them.
- 'Inventory' leads you to a menu where you can view your owned/purchased weapons and equip them.
- 'Settings' leads you to a menu where you can toggle and change setttings and keybinds for customisation and preference.
- 'Exit' makes you exit to the game once you confirm.
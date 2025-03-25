from utils import *

# Data loaded from game
enemies = []
weapons = []
attacks = []
shop_weapons = []

# Player data
player = []
settings = []
display_controls = True
display_extra = True
display_text = False

in_combat = False

def save_player(debug=True):
    global display_controls
    global display_text
    global display_extra

    display_controls = settings['displayControls']
    display_text = settings['displayTextTooltips']
    display_extra = settings['displayExtraTooltips']
    save_file_from_directory(DATA_DIR, 'save_file', player, debug)
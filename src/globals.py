from utils import *
from libraries import *

# Data loaded from game
enemies = []
weapons = []
attacks = []
shop_weapons = []

# Global conditions
in_combat = False
crashed = False

# Player data
class Player():
    def __init__(self):
        self.health = 100
        self.balance = 0
        self.level = 0
        self.xp = 0
        self.xp_goal = 100
        self.equipped = 'default'
        self.inventory = ['default']

        self.display_controls = True
        self.display_extra = True
        self.display_text = False
        self.settings = {
            'shopSortType': 'levelRequirement',
            'shopSortAscending': True,
            'invSortType': 'levelRequirement',
            'invSortAscending': True,
            'primarySortKeybind': 'z',
            'secondarySortKeybind': 'x',
            'displayControls': self.display_controls,
            'displayTextTooltips': self.display_text,
            'displayExtraTooltips': self.display_extra,
            'fasterBattleLogs': False
        }

    def level_up(self):
        scale_factor = 1.2
        base = 100
        
        leveled_up = False
        
        if self.xp >= self.xp_goal:
            left_over_xp = max(0, self.xp - self.xp_goal)

            self.level += 1
            self.xp = left_over_xp
            self.xp_goal = round(base * ((self.level + 1) ** scale_factor)) 
            self.scale_health()
            leveled_up = True
        else:
            new_goal_xp = round(base * ((self.level + 1) ** scale_factor)) 
            if self.xp_goal != new_goal_xp: # If new goal is diferent after level was changed but not the xp
                self.xp = 0
                self.xp_goal = new_goal_xp 
                self.scale_health()
                self.save()
        
        
        return leveled_up

    def scale_health(self):
        scale_factor = 0.05
        base = 100
        self.health = round(base *(1 + scale_factor * self.level**2))

    # Player loading/saving
    def load(self):
        data = load_file_from_directory(DATA_DIR, 'save_file', backup=True)
        if data:
            self.health = data['health']
            self.balance = data['money']
            self.level = data['level']
            self.xp = data['xp']['current']
            self.xp_goal = data['xp']['max']
            self.inventory = data['inventory'] 

            self.settings = data['settings']
            self.display_controls = self.settings['displayControls']
            self.display_text = self.settings['displayTextTooltips']
            self.display_extra = self.settings['displayExtraTooltips']

            self.level_up()
            self.scale_health()
            debug.info('Loaded player data:\n' + str(data))
        else:
            debug.info('Loaded default player data.')
            self.save(debugging=False)

    def save(self, debugging=True):
        self.display_controls = self.settings['displayControls']
        self.display_text = self.settings['displayTextTooltips']
        self.display_extra = self.settings['displayExtraTooltips']

        data = {
            'health': self.health,
            'money': self.balance,
            'level': self.level,
            'xp': {
                'current': self.xp,
                'max': self.xp_goal
            },
            'inventory': self.inventory,
            'equipped': self.equipped,
            'settings': self.settings
        }
        save_file_from_directory(DATA_DIR, 'save_file', data, debugging=debugging)

player = Player()
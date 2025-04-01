from .utils import *
from .libraries import *

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
        self.use_arrow_keys = True
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
            'useArrowKeys': self.use_arrow_keys,
            'fasterBattleLogs': False
        }

    def level_up(self):
        """Scale and update health and XP goal based on level. Uses exponential formula"""
        scale_factor = 1.1
        base = 100
        
        leveled_up = False # Flag to indicate if player has leveled up
        
        if self.xp >= self.xp_goal: # If the player has enough XP to level up
            left_over_xp = max(0, self.xp - self.xp_goal) # Remaining XP after leveling up

            self.level += 1 # Increase level
            self.xp = left_over_xp # Set remaining XP
            self.xp_goal = round(base * ((self.level + 1) ** scale_factor)) # Calculate and set new XP goal
            self.scale_health() # Update health for new level
            leveled_up = True
        else:
            new_goal_xp = round(base * ((self.level + 1) ** scale_factor)) # Calculate the XP goal for current level
            # If XP goal is changed (e.g., level was modified externally but not  XP)
            if self.xp_goal != new_goal_xp: 
                self.xp = 0 # Reset XP
                self.xp_goal = new_goal_xp # Set new/correct XP goal
                self.scale_health() # Update the health based on level
                self.save() # Save to player data
        
        return leveled_up

    def scale_health(self):
        """Scale and update health based on level. Uses quadratic formula"""
        scale_factor = 0.05
        base = 100
        self.health = round(base *(1 + scale_factor * self.level**2))

    def update_self_settings(self):
        """Get settings value of the individual settings or their default value if it doesn't exist inside settings"""
        self.display_controls = self.settings.get('displayControls',  self.display_controls)
        self.display_text = self.settings.get('displayTextTooltips',  self.display_text)
        self.display_extra = self.settings.get('displayExtraTooltips',  self.display_extra)
        self.use_arrow_keys = self.settings.get('useArrowKeys',  self.use_arrow_keys)

    def update_saved_settings(self):
        """Set settings values to the individual settings' values"""
        self.settings['displayControls'] = self.display_controls
        self.settings['displayTextTooltips'] = self.display_text
        self.settings['displayExtraTooltips'] = self.display_extra
        self.settings['useArrowKeys'] = self.use_arrow_keys

    # Player loading/saving
    def load(self):
        data = load_file_from_directory(DATA_DIR, 'save_file', backup=True)
        if data:
            self.health = data.get('health', self.health)
            self.balance = data.get('money', self.balance)
            self.level = data.get('level', self.level)
            if data.get('xp'):
                self.xp = data['xp'].get('current', self.xp)
                self.xp_goal = data['xp'].get('max', self.xp_goal)
            self.equipped = data.get('equipped', self.equipped)
            self.inventory = data.get('inventory', self.inventory)

            self.settings = data.get('settings', self.settings)
            self.update_self_settings()
            self.update_saved_settings() # Set settings in case some settings were missing in the settings dictionary

            self.level_up() 
            self.scale_health()
            debug.info('Loaded player data:\n' + str(data))
        else:
            debug.info('Loaded default player data.')
            self.save(debugging=False)

    def save(self, debugging=True):
        self.update_self_settings()


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
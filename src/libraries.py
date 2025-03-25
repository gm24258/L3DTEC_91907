# Saturday March 1 10AM

import os
import logging # Debugging
import traceback # Error
import json
import shutil
import random
import time

# Auto install modules if user doesn't have it already
import sys
import subprocess
def auto_install_module(module_name, package_name=None):
    # Automatically installs a Python module if it is not already installed.

    # Args:
    #   module_name (str): The name of the module to import.
    #   package_name (str, optional): The name of the package to install (if different from module_name).
    if package_name is None:
        package_name = module_name

    try:
        # Try to import the module
        __import__(module_name)
    except ImportError:
        print(f"{module_name} is not installed. Attempting to install it now...")
        
        try:
            # Use pip to install the module
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            print(f"{module_name} has been successfully installed.")
        except subprocess.CalledProcessError:
            print(f"Failed to install {module_name}. Please install it manually using: pip install {package_name}")
            sys.exit(1)  # Exit the program if installation fails

# Third-party module used to read arrow keys
# Insert license
auto_install_module("keyboard")
import keyboard

# Third-party module used to check if window is active for keyboard input
# Insert license
auto_install_module("pygetwindow")
import pygetwindow as gw

# Third-party module used to format text in terminal
# Insert license
auto_install_module("rich")
import rich

"""# Settings:
settings_keybinds = {
    'ENTER': readchar.key.ENTER,
    'ESC': readchar.key.ESC,
    'UP': readchar.key.UP,
    'DOWN': readchar.key.DOWN,
    'LEFT': readchar.key.LEFT,
    'RIGHT': readchar.key.RIGHT,
    'SPACE': readchar.key.SPACE,
    'BACKSPACE': readchar.key.BACKSPACE,
    'TAB': readchar.key.TAB,
    'F1': readchar.key.F1,
    'F2': readchar.key.F2,
    'F3': readchar.key.F3,
    'F4': readchar.key.F4,
    'F5': readchar.key.F5,
    'F6': readchar.key.F6,
    'F7': readchar.key.F7,
    'F8': readchar.key.F8,
    'F9': readchar.key.F9,
    'F10': readchar.key.F10,
    'F11': readchar.key.F11,
    'F12': readchar.key.F12
}"""

class GameSetting:
    def __init__(self, text, id, dependencies=None, disabled_value=None):
        self.text = text
        self.id = id
        self.dependencies = dependencies
        self.disabled_value = disabled_value

class TwoStateSetting(GameSetting):
    def __init__(self, text, id, states=None, dependencies=None, disabled_value=None):
        super().__init__(text, id, dependencies, disabled_value)
        self.states = states or ['', '✅']

class KeyBindSetting(GameSetting):
    def __init__(self, text, id, dependencies=None, disabled_value=None):
        super().__init__(text, id, dependencies, disabled_value)
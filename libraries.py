# Saturday March 1 10AM

import os
import logging # Debugging
import traceback # Error
import json
import shutil

# Auto install modules if user doesn't have it already
import sys
import subprocess

def install_package(package):
    # Attempts to install a package if it's not found.

    # Parameters:
    # package (str): name of package/module
    try:
        __import__(package)
    except ImportError:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Third-party module used to read arrow keys
# MIT License for readchar (MIT Licence Copyright (c) 2022 Miguel Angel Garcia Permission is hereby granted, free of charge, t...)
install_package("readchar")
import readchar

# Third-party module used to format text in terminal
# Insert license
install_package("rich")
import rich

# Settings:
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
}

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
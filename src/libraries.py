import os
import logging  # For debugging purposes
import traceback  # For error handling and tracebacks
import json
import shutil
import random
import time
import asyncio
import threading
import math
import ctypes
import platform
import sys
import subprocess


# Third-party module used to listen to key inputs
# GNU Lesser General Public License v3.0 - https://github.com/moses-palmer/pynput/blob/master/COPYING.LGPL
import pynput

# Third-party module used to check if window is active for keyboard input
# BSD 3-Clause "New" or "Revised" License - https://github.com/asweigart/PyGetWindow/blob/master/LICENSE.txt
import pygetwindow as gw

# Third-party module used to format text in terminal
# MIT License - https://github.com/Textualize/rich/blob/master/LICENSE
import rich

def set_window_title(title):
    """
    Set the terminal window title based on the operating system.

    Args:
        title (str): The title to set for the terminal window.
    """
    if platform.system() == "Windows":
        ctypes.windll.kernel32.SetConsoleTitleW(title)  # Set title for Windows OS
    elif platform.system() == "Darwin":  # macOS
        print(f"\033]0;{title}\a", end="")  # Set title for macOS
    elif platform.system() == "Linux":
        print(f"\033]0;{title}\a", end="")  # Set title for Linux OS

# Set initial window title
set_window_title("generic terminal rpg")

# Define a class for game settings
class GameSetting:
    """
    Base class to represent a generic game setting.

    Args:
        text (str): The display text for the setting.
        id (str): Unique identifier for the setting.
        dependencies (list, optional): A list of other settings that depend on this one.
        disabled_value (str, optional): The value to use when the setting is disabled.
    """
    def __init__(self, text, id, dependencies=None, disabled_value=None):
        self.text = text
        self.id = id
        self.dependencies = dependencies
        self.disabled_value = disabled_value

# Define a class for settings with two states (on/off, etc.)
class TwoStateSetting(GameSetting):
    """
    Represents a game setting with two possible states (e.g., 'Enabled' or 'Disabled').

    Args:
        text (str): The display text for the setting.
        id (str): Unique identifier for the setting.
        states (list, optional): List of states the setting can have (e.g., ['Off', 'On']).
        dependencies (list, optional): A list of other settings that depend on this one.
        disabled_value (str, optional): The value to use when the setting is disabled.
    """
    def __init__(self, text, id, states=None, dependencies=None, disabled_value=None):
        super().__init__(text, id, dependencies, disabled_value)
        self.states = states or ['', '✅']  # Default states if not provided

# Define a class for key binding settings
class KeyBindSetting(GameSetting):
    """
    Represents a game setting for key bindings (e.g., a specific key press for an action).

    Args:
        text (str): The display text for the setting.
        id (str): Unique identifier for the setting.
        dependencies (list, optional): A list of other settings that depend on this one.
        disabled_value (str, optional): The value to use when the setting is disabled.
    """
    def __init__(self, text, id, dependencies=None, disabled_value=None):
        super().__init__(text, id, dependencies, disabled_value)
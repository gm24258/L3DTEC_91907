# Saturday March 1 10:07AM

from formatting import *

def print_basic_menu(options, selected, title=None, info=None, tooltip=None, clear=True):
    # Displays a vertical menu with options that can be navigated using UP/DOWN arrow keys.
    
    # Parameters:
    # title (str): Title of the menu.
    # options (list): List of menu options.
    # selected (int): Index of the currently selected option.
    if clear is True: clear_terminal()
    if title: console.print(title)
    if info: console.print(info)
    for i, option in enumerate(options):
        prefix = '> ' if i == selected else '  '
        console.print(Text(prefix) + option)
    if tooltip: console.print(Text('\n') + tooltip)

def print_horizontal_menu(info, title=None, tooltip=None):
    # Displays a horizontal menu, where the player can navigate between previous and next options.
    
    # Parameters:
    # title (str): Title of the menu.
    # info (str): Information about the selected item.
    # prev (str): Name of the previous option.
    # next (str): Name of the next option.

    clear_terminal()
    console.print(title)
    console.print(info)
    if len(tooltip) > 0:
        console.print(Text('\n') + tooltip)

def print_paged_menu(options, selected, title=None, tooltip=None, page_size=5):
    # Displays a vertical paged menu, where options can be navigated using UP/DOWN keys.
    # Pages can be navigated using LEFT/RIGHT keys.
    
    # Parameters:
    # title (str): Title of the menu.
    # options (list): List of menu options.
    # selected (int): Index of the currently selected option.

    clear_terminal()

    total_pages = (len(options) + page_size - 1) // page_size
    current_page = selected // page_size

    start_index = current_page * page_size
    end_index = min(start_index + page_size, len(options))
    displayed_options = options[start_index:end_index]

    # Fill remaining slots with empty spaces
    while len(displayed_options) < page_size:
        displayed_options.append(Text(''))

    console.print(title)
    for i, option in enumerate(displayed_options):
        index = start_index + i  # Adjust index for selection tracking
        prefix = '> ' if index == selected and option else '  '
        console.print(Text(prefix) + option)

    previous_string = '← Prev | ' if current_page > 0 else '       | '
    next_string = ' | Next →' if current_page < total_pages - 1 else ' |       '

    console.print(style_text({'style':'italic'}, f'\n{previous_string}Page {current_page + 1}/{total_pages}{next_string}'))
    if tooltip: console.print(tooltip)

    return current_page, total_pages, start_index
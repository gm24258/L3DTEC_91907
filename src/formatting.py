from libraries import *
from rich.console import Console
from rich.text import Text

# Initialize Console for rich text, which allows us to print styled text
global console
console = Console()

def clear_terminal():
    """
    Clears the terminal screen, ensuring compatibility with different operating systems.

    If the OS is Windows ('nt'), it uses the 'cls' command. Otherwise, it uses 
    ANSI escape codes to clear the terminal screen.
    """
    if os.name == 'nt':
        os.system('cls')  # Windows system command to clear terminal
    else:
        # Use ANSI escape code for clearing the terminal screen on Unix-based systems
        print("\033[2J\033[H", end="", flush=True)
    console.clear()  # Clears the console using the `rich` console

def style_text(styles, *substrings):
    """
    Applies styles and colors to multiple substrings using `rich` module.

    Args:
        styles (dict): A dictionary containing 'style' and/or 'color' keys.
        substrings (str/Text): Substrings (or Text objects) to which styles will be applied.

    Returns:
        Text: A `rich.text.Text` object with the applied styles and colors.
    """
    rich_text = Text()  # Initialize an empty `Text` object to hold the final result

    for substring in substrings:
        # If the substring is already a Text object, copy it to preserve its styles
        sub_text = substring.copy() if isinstance(substring, Text) else Text(substring)

        # Apply additional styles while keeping existing ones
        if styles.get("style"):
            sub_text.stylize(styles["style"], 0, len(sub_text))  # Apply style to the entire substring

        if styles.get("color"):
            color = styles["color"]
            # If the color is in RGB format (list of 3 integers), apply it
            if isinstance(color, list) and len(color) == 3:
                sub_text.stylize(f"rgb({color[0]},{color[1]},{color[2]})", 0, len(sub_text))
            elif isinstance(color, str):  # If the color is a string (e.g., "red"), apply it
                sub_text.stylize(color, 0, len(sub_text))

        rich_text.append(sub_text)  # Add the styled substring to the final text

    return rich_text

def wrap_text(text, width=60, indent=""):
    """
    Wraps the text to a specific width and indents each line after the first.

    Args:
        text (str): The input text to be wrapped.
        width (int): The maximum width for each line.
        indent (str): The string used for indenting each wrapped line.

    Returns:
        str: A string with the wrapped and indented text.
    """
    words = text.split(" ")  # Split the text into individual words
    lines = []
    current_line = words[0]  # Start with the first word in the current line

    # Loop through the remaining words
    for word in words[1:]:
        # If adding this word does not exceed the line width, add it to the current line
        if len(current_line + " " + word) <= width:
            current_line += " " + word
        else:
            # If the line is too long, add the current line to the list of lines and start a new line
            lines.append(current_line)
            current_line = word
    
    lines.append(current_line)  # Add the last line
    # Return the lines with the specified indent applied to each line
    return "\n".join([indent + line for line in lines])

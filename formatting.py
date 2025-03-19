from libraries import *
from rich.console import Console
from rich.text import Text

# Initialize Console for rich text
global console
console = Console()

def clear_terminal():
    print("\033c", end="")
    console.clear()
    os.system("cls" if os.name == "nt" else "clear")

def style_text(styles, *substrings):
    # Apply styles and colors to multiple substrings using `rich`.
    
    rich_text = Text()

    for substring in substrings:
        # If the substring is already a Text object, copy it to preserve its styles
        sub_text = substring.copy() if isinstance(substring, Text) else Text(substring)

        # Apply additional styles while keeping existing ones
        if styles.get("style"):
            sub_text.stylize(styles["style"], 0, len(sub_text))

        if styles.get("color"):
            color = styles["color"]
            if isinstance(color, list) and len(color) == 3:  # RGB format
                sub_text.stylize(f"rgb({color[0]},{color[1]},{color[2]})", 0, len(sub_text))
            elif isinstance(color, str):  # Named color (e.g., "red")
                sub_text.stylize(color, 0, len(sub_text))

        rich_text.append(sub_text)

    return rich_text

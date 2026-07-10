"""Shared file selectors used by the ComicScreen backends.

``terminal_select`` is used by the terminal/desktop screens; the Inky backend
selects with its buttons instead (no keyboard).
"""
from pathlib import Path
from typing import List, Optional

import questionary


def terminal_select(options: List[str], title: str = "Choose a file") -> Optional[str]:
    """Interactive terminal picker (questionary). Returns the chosen option or None."""
    if not options:
        return None
    choices = [questionary.Choice(title=Path(option).name, value=option) for option in options]
    choices += [questionary.Separator(), questionary.Choice(title="Cancel", value=None)]
    return questionary.select(title, choices=choices).ask()

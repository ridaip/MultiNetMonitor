import os

THEMES = {
    "cyberpunk": {
        "name": "Cyberpunk Neon (Dark)",
        "file": "cyberpunk_theme.qss",
        "is_dark": True,
        "primary": "#00E5FF",
        "secondary": "#FF007F",
        "bg": "#090d16",
        "card_bg": "#111827",
        "grid": "#1f293d",
        "text": "#F3F4F6"
    },
    "midnight": {
        "name": "Midnight Indigo (Dark)",
        "file": "midnight_theme.qss",
        "is_dark": True,
        "primary": "#6366F1",
        "secondary": "#10B981",
        "bg": "#0b0f19",
        "card_bg": "#1e293b",
        "grid": "#334155",
        "text": "#F8FAFC"
    },
    "dracula": {
        "name": "Dracula Purple (Dark)",
        "file": "dracula_theme.qss",
        "is_dark": True,
        "primary": "#CBA6F7",
        "secondary": "#94E2D5",
        "bg": "#181825",
        "card_bg": "#1e1e2e",
        "grid": "#313244",
        "text": "#CDD6F4"
    },
    "nord": {
        "name": "Nordic Frost (Dark)",
        "file": "nord_theme.qss",
        "is_dark": True,
        "primary": "#88C0D0",
        "secondary": "#A3BE8C",
        "bg": "#2e3440",
        "card_bg": "#3b4252",
        "grid": "#4c566a",
        "text": "#ECEFF4"
    },
    "light": {
        "name": "Crisp Slate (Light)",
        "file": "light_theme.qss",
        "is_dark": False,
        "primary": "#0284C7",
        "secondary": "#059669",
        "bg": "#F8FAFC",
        "card_bg": "#FFFFFF",
        "grid": "#E2E8F0",
        "text": "#0F172A"
    }
}

def load_theme(theme_key="cyberpunk"):
    if isinstance(theme_key, bool):
        theme_key = "cyberpunk" if theme_key else "light"
        
    if theme_key not in THEMES:
        theme_key = "cyberpunk"
        
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, THEMES[theme_key]["file"])
    
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read()
    return ""

def get_theme_info(theme_key="cyberpunk"):
    if isinstance(theme_key, bool):
        theme_key = "cyberpunk" if theme_key else "light"
    return THEMES.get(theme_key, THEMES["cyberpunk"])

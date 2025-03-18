# Texture Checker Rules
# Define texture type rules based on suffix

TEXTURE_RULES = {
    "BC": {
        "compression_settings": "TC_DEFAULT", 
        "srgb": True,
        "brightness_curve": 1.0
    },
    "D": {
        "compression_settings": "TC_DEFAULT", 
        "srgb": True,
        "brightness_curve": 1.0
    },
    "E": {
        "compression_settings": "TC_DEFAULT", 
        "srgb": True,
        "brightness_curve": 1.0
    },
    "PBR": {
        "compression_settings": "TC_MASKS", 
        "srgb": False,
        "brightness_curve": 1.0
    },
    "L": {
        "compression_settings": "TC_MASKS", 
        "srgb": False,
        "brightness_curve": 1.0
    },
    "M": {
        "compression_settings": "TC_ALPHA", 
        "srgb": False,
        "brightness_curve": 2.2
    },
    "MASK": {
        "compression_settings": "TC_ALPHA", 
        "srgb": False,
        "brightness_curve": 1.0
    },
    "IC_M": {
        "compression_settings": "TC_ALPHA", 
        "srgb": False,
        "brightness_curve": 1.0
    },
    "N": {
        "compression_settings": "TC_NORMALMAP", 
        "srgb": False,
        "brightness_curve": 1.0
    }
}

# Define suffix priority for matching
# Order from most specific to least specific to avoid substring matching issues
SUFFIX_PRIORITY = ["IC_M", "PBR", "BC", "E", "N", "M", "D", "L", "MASK"]

# Define regular expression patterns for each suffix type
# These patterns ensure more precise matching
SUFFIX_PATTERNS = {
    "IC_M": r"ic_m(?:\d+)?$",  # "ic_m" at the end, possibly followed by numbers
    "PBR": r"pbr(?:\d+)?$",    # "pbr" at the end, possibly followed by numbers
    "BC": r"bc(?:\d+)?$",      # "bc" at the end, possibly followed by numbers
    "E": r"e(?:\d+)?$",        # "e" at the end, possibly followed by numbers
    "N": r"n(?:\d+)?$",        # "n" at the end, possibly followed by numbers
    "M": r"m(?:\d+)?$" ,        # "m" at the end, possibly followed by numbers
    "D": r"d(?:\d+)?$" ,
    "L": r"l(?:\d+)?$" ,
    "MASK": r"mask(?:\d+)?$"
}
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
    "CLEARCOAT_MASK": {
        "compression_settings": "TC_MASKS", 
        "srgb": False,
        "brightness_curve": 1.0
    },
    "DIRT_MASK": {
        "compression_settings": "TC_MASKS", 
        "srgb": False,
        "brightness_curve": 1.0
    },
    "AO_MASK": {
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
# Longer, more specific patterns should come first
SUFFIX_PRIORITY = [
    "CLEARCOAT_MASK", "DIRT_MASK", "AO_MASK",  # Most specific mask types first
    "IC_M",  # Special case
    "PBR", 
    "BC", 
    "E", 
    "N", 
    "M", 
    "D", 
    "L"
]

# Define regular expression patterns for each suffix type with improved specificity
SUFFIX_PATTERNS = {
    # For mask types, look for the specific prefix before "mask"
    "CLEARCOAT_MASK": r"(?:^|_)clearcoat(?:_)?mask(?:\d+)?$",  # Matches "clearcoat_mask" or "clearcoatmask"
    "DIRT_MASK": r"(?:^|_)dirt(?:_)?mask(?:\d+)?$",            # Matches "dirt_mask" or "dirtmask"
    "AO_MASK": r"(?:^|_)ao(?:_)?mask(?:\d+)?$",                # Matches "ao_mask" or "aomask"
    
    # Handle IC_M special case with more precision
    "IC_M": r"(?:^|_)ic(?:_)?m(?:\d+)?$",                      # Matches "ic_m" or "icm"
    
    # Standard texture types with word boundary awareness
    "PBR": r"(?:^|_)pbr(?:\d+)?$",                             # Must be at word start or after underscore
    "BC": r"(?:^|_)bc(?:\d+)?$",
    "E": r"(?:^|_)e(?:\d+)?$",
    "N": r"(?:^|_)n(?:\d+)?$",
    "M": r"(?:^|_)m(?:\d+)?$",
    "D": r"(?:^|_)d(?:\d+)?$",
    "L": r"(?:^|_)l(?:\d+)?$"
}
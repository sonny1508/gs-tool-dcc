# Texture Checker Rules
# Define texture type rules based on suffix and project

import unreal
import os
import re

def get_current_project_directory():
    """
    Returns the path of the current Unreal Engine 5 project directory.
    """
    try:
        # Get the current project file path
        project_file_path = unreal.Paths.get_project_file_path()
        
        # Get the project directory (parent directory of the project file)
        project_directory = unreal.Paths.get_path(project_file_path)
        
        return project_directory
    except Exception as e:
        print(f"Error getting project directory: {e}")
        return None

def get_project_name_from_path(project_path):
    """
    Extracts the project name from the project path.
    """
    if not project_path:
        return None
        
    # Split the path and get the last directory name
    path_parts = project_path.replace("\\", "/").split("/")
    # Filter out empty parts and get the last non-empty part
    filtered_parts = [p for p in path_parts if p]
    if filtered_parts:
        return filtered_parts[-1].lower()
    return None

# Default texture rules that apply to all projects
DEFAULT_TEXTURE_RULES = {
    "BC": {
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
    "M": {
        "compression_settings": "TC_ALPHA", 
        "srgb": False,
        "brightness_curve": 2.2
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

# Default suffix priority list
DEFAULT_SUFFIX_PRIORITY = [
    "IC_M",  # Special case
    "PBR", 
    "BC", 
    "E", 
    "N", 
    "M"
]

# Default suffix patterns
DEFAULT_SUFFIX_PATTERNS = {
    # Handle IC_M special case with more precision
    "IC_M": r"(?:^|_)ic(?:_)?m(?:\d+)?$",                      # Matches "ic_m" or "icm"
    
    # Standard texture types with word boundary awareness
    "PBR": r"(?:^|_)pbr(?:\d+)?$",                             # Must be at word start or after underscore
    "BC": r"(?:^|_)bc(?:\d+)?$",
    "E": r"(?:^|_)e(?:\d+)?$",
    "N": r"(?:^|_)n(?:\d+)?$",
    "M": r"(?:^|_)m(?:\d+)?$"
}

# Project-specific rules

# MotoGP25 extended rule set with conditional logic
MOTOGP25_TEXTURE_RULES = {
    "CLEARCOAT_MASK": {
        "compression_settings": "TC_MASKS", 
        "srgb": False,
        "brightness_curve": 1.0,
        "texture_group": "VehicleSpecular",
        "size": (2048, 2048)
    },
    "DIRT_MASK": {
        "compression_settings": "TC_MASKS", 
        "srgb": False,
        "brightness_curve": 1.0,
        "texture_group": "VehicleDirtMask",
        "size": (2048, 2048),
        "special_cases": [
            {
                "pattern": r"(?:glass)",
                "override": {
                    "texture_group": "VehicleSpecular",
                    "size": (2048, 1024)
                },
            }
        ]
    },
    "AO_MASK": {
        "compression_settings": "TC_ALPHA", 
        "srgb": False,
        "brightness_curve": 1.0,
        "texture_group": "VehicleAOMap",
        "size": (1024, 1024)
    },
    "D": {
        "compression_settings": "TC_DEFAULT", 
        "srgb": True,
        "brightness_curve": 1.0,
        "texture_group": "Vehicle",
        "size": (2048, 2048),
        # Special case handling for D suffix
        "special_cases": [
            {
                "pattern": r"(?:livery|mechanics)",  # Matches livery or mechanics in the name
                "override": {
                    "texture_group": "VehicleHighRes",
                    "size": (4096, 4096)
                }
            },
            {
                "pattern": r"(?:glass)",
                "override": {
                    "size": (2048, 1024)
                }
            },
            {
                "pattern": r"(?:rim|brake)",
                "override": {
                    "size": (1024, 1024)
                }
            },
            {
                "pattern": r"(?:gauge)",
                "override": {
                    "size": (512, 512)
                }
            },

        ]
    },
    "L": {
        "compression_settings": "TC_MASKS", 
        "srgb": False,
        "brightness_curve": 1.0,
        "texture_group": "VehicleSpecular",
        "size": (2048, 2048),
        "special_cases": [
            {
                "pattern": r"(?:gauge)",
                "override": {
                    "size": (512, 512)
                }
            },
            {
                "pattern": r"(?:glass)",
                "override": {
                    "size": (2048, 1024)
                }
            },
            {
                "pattern": r"(?:brake|rim)",
                "override": {
                    "size": (1024, 1024)
                }
            }
        ]
    },
    "N": {
        "compression_settings": "TC_NORMALMAP", 
        "srgb": False,
        "brightness_curve": 1.0,
        "texture_group": "VehicleNormalMap",
        "size": (2048, 2048),
        "special_cases": [
            {
                "pattern": r"(?:brake|rim)",
                "override": {
                    "size": (1024, 1024)
                },
            }
        ]
    }
}

MOTOGP25_SUFFIX_PRIORITY = [
    "CLEARCOAT_MASK", "DIRT_MASK", "AO_MASK",  # Most specific mask types first
    "D",
    "L",
    "N"
]

MOTOGP25_SUFFIX_PATTERNS = {
    # For mask types, look for the specific prefix before "mask"
    "CLEARCOAT_MASK": r"(?:^|_)clearcoat(?:_)?mask(?:\d+)?$",  # Matches "clearcoat_mask" or "clearcoatmask"
    "DIRT_MASK": r"(?:^|_)dirt(?:_)?mask(?:\d+)?$",            # Matches "dirt_mask" or "dirtmask"
    "AO_MASK": r"(?:^|_)ao(?:_)?mask(?:\d+)?$",                # Matches "ao_mask" or "aomask"
    
    # Standard texture types with word boundary awareness
    "D": r"(?:^|_)d(?:\d+)?$",
    "L": r"(?:^|_)l(?:\d+)?$",
    "N": r"(?:^|_)n(?:\d+)?$"
}

# Screamer1 extended rule set with texture group-based sizing
SCREAMER1_TEXTURE_RULES = {
    "BC": {
        "compression_settings": "TC_DEFAULT", 
        "srgb": True,
        "brightness_curve": 1.0,

        # Special flag to indicate size should be determined by texture group
        "group_based_size": True,

        # Dictionary mapping texture groups to lists of approved sizes
        "group_size_map": {
            "WorldLow": [(512, 512), (2048, 2048)],
            "World": [(1024, 1024), (2048, 2048)],
            "Runnable": (4096, 4096),
            "Sponsor": (2048, 2048),
            "Landscape": (1024, 1024),
            "Character": (1024, 1024),
        }
    },
    "E": {
        "compression_settings": "TC_DEFAULT", 
        "srgb": True,
        "brightness_curve": 1.0,
        "texture_group": "InteriorMap",

        "group_based_size": True,
        "group_size_map": {
            "InteriorMap": [(256, 256), (1024, 1024)],
        }
    },
    "N": {
        "compression_settings": "TC_NORMALMAP", 
        "srgb": False,
        "brightness_curve": 1.0,

        "group_based_size": True,
        "group_size_map": {
            "WorldLowNrmMap": [(1024, 1024), (4096, 4096)],
            "WorldNormalMap": [(1024, 1024), (2048, 2048)],
            "RunnableNrmMap": [(4096, 4096)],
            "LandscapeNormalMap": [(1024, 1024)],
            "CharacterNormalMap": [(1024, 1024)],
        }
    },
    "PBR": {
        "compression_settings": "TC_MASKS", 
        "srgb": False,
        "brightness_curve": 1.0,

        "group_based_size": True,
        "group_size_map": {
            "WorldLowSpecular": [(512, 512)],
            "WorldSpecular": [(1024, 1024), (2048, 2048)],
            "RunnableSpecular": [(4096, 4096)],
            "LandscapeSpecular": [(1024, 1024)],
            "CharacterSpecular": [(1024, 1024)],
        }
    },
    "M": {
        "compression_settings": "TC_ALPHA", 
        "srgb": False,
        "brightness_curve": 2.2,

        "group_based_size": True,
        "group_size_map": {
            "OpacityMaskr": [(1024, 1024), (2048, 2048)],
            "RunnableMask": [(1024, 1024), (2048, 2048)],
        }
    },
    "IC_M": {
        "compression_settings": "TC_ALPHA", 
        "srgb": False,
        "brightness_curve": 1.0,
        "texture_group": "OpacityMask",
    },
}

SCREAMER1_SUFFIX_PRIORITY = [
    "BC", "E", "N", "PBR", "M", "IC_M"
]

SCREAMER1_SUFFIX_PATTERNS = {
    # Standard texture types with word boundary awareness
    "BC": r"(?:^|_)bc(?:\d+)?$",
    "E": r"(?:^|_)e(?:\d+)?$",
    "N": r"(?:^|_)n(?:\d+)?$",
    "PBR": r"(?:^|_)pbr(?:\d+)?$",  
    "M": r"(?:^|_)m(?:\d+)?$",

    # Handle IC_M special case with more precision
    "IC_M": r"(?:^|_)ic(?:_)?m(?:\d+)?$",                      # Matches "ic_m" or "icm"
}

# Template for adding a new project (copy and modify as needed)
"""
# PROJECT2 complete rule set
PROJECT2_TEXTURE_RULES = {
    "TYPE1": {
        "compression_settings": "TC_DEFAULT", 
        "srgb": True,
        "brightness_curve": 1.0,
        "texture_group": "Group1",
        "size": (1024, 1024),
        "special_cases": [
            {
                "pattern": r"some_pattern",
                "override": {
                    "texture_group": "SpecialGroup",
                    "size": (2048, 2048)
                }
            }
        ]
    },
    # Add more type rules as needed
}
"""

def get_rules_for_current_project():
    """
    Returns the appropriate texture rules, suffix priority, and suffix patterns
    based on the current project.
    """
    project_dir = get_current_project_directory()
    project_name = get_project_name_from_path(project_dir)
    
    print(f"Current project directory: {project_dir}")
    print(f"Detected project name: {project_name}")
    
    # Match project name to specific rules
    if project_name == "motogp25":
        print("Using MotoGP25 specific texture rules")
        return (MOTOGP25_TEXTURE_RULES, MOTOGP25_SUFFIX_PRIORITY, MOTOGP25_SUFFIX_PATTERNS)
    elif project_name == "screamer":
        print("Using SCREAMER1 specific texture rules")
        return (SCREAMER1_TEXTURE_RULES, SCREAMER1_SUFFIX_PRIORITY, SCREAMER1_SUFFIX_PATTERNS)
    # Add more project matches as needed
    # elif project_name == "project2":
    #     return (PROJECT2_TEXTURE_RULES, PROJECT2_SUFFIX_PRIORITY, PROJECT2_SUFFIX_PATTERNS)
    
    # Default fallback
    print("No project-specific rules found, using default texture rules")
    return (DEFAULT_TEXTURE_RULES, DEFAULT_SUFFIX_PRIORITY, DEFAULT_SUFFIX_PATTERNS)

def get_final_rule_for_texture(rules, suffix, texture_name, current_texture_group=None):
    """
    Apply any conditional logic to get the final rule for a specific texture.
    This handles special cases based on texture name patterns or texture groups.
    
    Args:
        rules (dict): The base rule dictionary for the matching suffix
        suffix (str): The texture suffix that matched
        texture_name (str): The full texture name
        current_texture_group (str or UE enum, optional): The current texture group of the texture
        
    Returns:
        dict: The final rule dictionary with any special case overrides applied
    """
    # Make a copy of the base rule to avoid modifying the original
    final_rule = rules.copy()
    
    # Handle group-based sizing for SCREAMER1 project
    if "group_based_size" in final_rule and final_rule["group_based_size"] and current_texture_group:
        group_size_map = final_rule.get("group_size_map", {})
        
        # Get the display name for the current texture group
        # Convert to string to ensure it's hashable
        try:
            # First try to get display name (for Unreal enum objects)
            if hasattr(current_texture_group, 'get_display_name'):
                group_display_name = current_texture_group.get_display_name()
            else:
                # If it's already a string or another object, convert to string
                group_display_name = str(current_texture_group)
                
            print(f"Processing texture group: '{group_display_name}' for texture '{texture_name}'")
        except Exception as e:
            print(f"Error getting texture group display name: {e}")
            group_display_name = "Unknown"
        
        # Look up the approved sizes for this texture group
        if group_display_name in group_size_map:
            # Store the approved sizes list
            sizes = group_size_map[group_display_name]
            # Ensure sizes is a list, not a single tuple
            if isinstance(sizes, tuple) and len(sizes) == 2 and isinstance(sizes[0], int):
                # Convert single tuple to a list with one tuple
                sizes = [sizes]
                
            final_rule["approved_sizes"] = sizes
            print(f"Found approved sizes for '{texture_name}' with group '{group_display_name}': {sizes}")
        else:
            # If no approved sizes for this group, create an empty list
            final_rule["approved_sizes"] = []
            print(f"No approved sizes found for '{texture_name}' with group '{group_display_name}'")
        
        # Remove the special flags from the final rule
        if "group_based_size" in final_rule:
            del final_rule["group_based_size"]
        if "group_size_map" in final_rule:
            del final_rule["group_size_map"]
    
    # Process normal special cases based on name patterns
    if "special_cases" in final_rule:
        texture_name_lower = texture_name.lower()
        
        # Check each special case pattern
        for special_case in final_rule["special_cases"]:
            pattern = special_case.get("pattern")
            if pattern and re.search(pattern, texture_name_lower):
                # Found a matching special case, apply the overrides
                overrides = special_case.get("override", {})
                for key, value in overrides.items():
                    final_rule[key] = value
                print(f"Applied special case for '{texture_name}' matching pattern '{pattern}'")
                break
                
        # Remove the special_cases list from the final rule
        del final_rule["special_cases"]
                
    return final_rule

# These variables will be imported by the main texture checker script
TEXTURE_RULES, SUFFIX_PRIORITY, SUFFIX_PATTERNS = get_rules_for_current_project()
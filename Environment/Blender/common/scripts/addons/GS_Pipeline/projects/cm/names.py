"""The CM naming contract: reading LOD and custom-part tokens out of object
names, and the names Check Names requires on every car.

Plain string rules, no bpy: shared by the switching (variants.py) and Check
Names (name_check.py). They come from the client's spec ("Specifications for
car production v.3") and their example car (AudiR8_Example_optimized.blend):

    <part>_<material>_LOD<n>              default mesh        hood_carpaint_LOD0
    anchor_<part>_LOD<n>                  default anchor      anchor_hood_LOD0
    anchor_<part>_part_<X>_LOD<n>         custom part         anchor_hood_part_B_LOD0
    <part>_<material>_part_<X>_LOD<n>     its meshes          hood_carbon_part_B_LOD0
    <car>_<wheel part>_LOD<n>             wheels              audi_r8_rims_LOD0

Every CM car has LOD0, LOD1 and LOD2; any other number is a mistake. The LOD
token isn't always last (l_door_handle_LOD0_highlight, l_sunvisor_LOD0_a): it
is _LOD<n> followed by the end of the name, "_" or ".".
"""
from __future__ import annotations

import re

# The LODs a CM car has.
LODS = (0, 1, 2)

# _LOD0, _LOD0_highlight, _LOD0.001. Any case, so a stray "_lod1" still
# switches; Check Names asks for capitals.
_LOD = re.compile(r"_(LOD)(\d+)(?=$|[_.])", re.IGNORECASE)

# _part_A. Any letters, so a look-alike from another alphabet (a Cyrillic С)
# still groups, and Check Names reports it. Never "_part_LOD0".
_PART = re.compile(r"_(part)_(?!LOD\d)([^_.]+)(?=$|[_.])", re.IGNORECASE)

# Blender's rename-on-collision suffix: .001, .002...
_DUPLICATE = re.compile(r"\.\d{3,}$")


def lod_of(name):
    """The LOD number in ``name`` (its last _LOD<n>), or None."""
    matches = _LOD.findall(name)
    return int(matches[-1][1]) if matches else None


def part_of(name):
    """The custom part letter in ``name`` (A in anchor_hood_part_A_LOD0), or None."""
    match = _PART.search(name)
    return match.group(2) if match else None


def default_name(part_name):
    """The default object a custom part replaces: anchor_hood_part_B_LOD0 -> anchor_hood_LOD0."""
    return _PART.sub("", strip_duplicate(part_name), count=1)


def slot_key(part_name):
    """The part a custom part is a version of, without LOD: anchor_hood_part_B_LOD0 -> anchor_hood."""
    name = default_name(part_name)
    matches = list(_LOD.finditer(name))
    return name[:matches[-1].start()] if matches else name


def slot_label(key):
    """What the panel calls a part: anchor_front_bumper -> Front Bumper."""
    if key.lower().startswith("anchor_"):
        key = key[len("anchor_"):]
    return key.replace("_", " ").strip().title() or key


def with_lod(name, lod):
    return "{}_LOD{}".format(name, lod)


# ----------------------------------------------------------------------------
# Spelling (Check Names)
# ----------------------------------------------------------------------------
def strip_duplicate(name):
    return _DUPLICATE.sub("", name)


def duplicate_suffix(name):
    """'.001' when Blender renamed ``name`` to avoid a duplicate, else None."""
    match = _DUPLICATE.search(name)
    return match.group(0) if match else None


def bad_characters(name):
    """Characters other than English letters, digits and _ (a .001 suffix aside), in order."""
    bad = []
    for ch in strip_duplicate(name):
        if not (ch.isascii() and (ch.isalnum() or ch == "_")) and ch not in bad:
            bad.append(ch)
    return bad


def lod_misspelled(name):
    """The LOD token as written ('_lod1') when it isn't in capitals, else None."""
    matches = list(_LOD.finditer(name))
    if matches and matches[-1].group(1) != "LOD":
        return matches[-1].group(0)
    return None


def part_misspelled(name):
    """The part token as written ('_Part_a') when it isn't _part_ with a capital letter, else None.

    A letter from another alphabet is left to bad_characters().
    """
    match = _PART.search(name)
    if match is None or not match.group(2).isascii():
        return None
    if match.group(1) != "part" or not match.group(2).isupper():
        return match.group(0)
    return None


# ----------------------------------------------------------------------------
# What every car needs (Check Names)
# ----------------------------------------------------------------------------
# The LODs each half of the car is delivered at (spec v.3): exterior all;
# interior LOD0 in full, LOD1 as one mesh under anchor_interior_LOD1; wheels 0-1.
EXTERIOR_LODS = LODS
INTERIOR_LODS = (0,)
WHEEL_LODS = (0, 1)

# (LODs, anchor, parent), names without _LOD<n>. Each anchor is required at
# every LOD listed, under its parent at the same LOD (None: anywhere). Some
# parents are meshes, as in the example (anchor_l_paddle sits on the steering
# wheel mesh).
# Drawn from the Audi R8 example: drop what isn't on every car.
ESSENTIAL_ANCHORS = (
    # Exterior
    (EXTERIOR_LODS, "anchor_exterior", None),
    (EXTERIOR_LODS, "anchor_body", "anchor_exterior"),
    (EXTERIOR_LODS, "anchor_front_bumper", "anchor_exterior"),
    (EXTERIOR_LODS, "anchor_headlights", "anchor_exterior"),
    (EXTERIOR_LODS, "anchor_hood", "anchor_exterior"),
    (EXTERIOR_LODS, "anchor_l_door_exterior", "anchor_exterior"),
    (EXTERIOR_LODS, "anchor_l_rearview_mirror_exterior", "anchor_l_door_exterior"),
    (EXTERIOR_LODS, "anchor_l_side_window_exterior", "anchor_l_door_exterior"),
    (EXTERIOR_LODS, "anchor_l_wiper", "anchor_exterior"),
    (EXTERIOR_LODS, "anchor_r_door_exterior", "anchor_exterior"),
    (EXTERIOR_LODS, "anchor_r_rearview_mirror_exterior", "anchor_r_door_exterior"),
    (EXTERIOR_LODS, "anchor_r_side_window_exterior", "anchor_r_door_exterior"),
    (EXTERIOR_LODS, "anchor_r_wiper", "anchor_exterior"),
    (EXTERIOR_LODS, "anchor_rear_bumper", "anchor_exterior"),
    (EXTERIOR_LODS, "anchor_skirts", "anchor_exterior"),
    (EXTERIOR_LODS, "anchor_spoiler", "anchor_exterior"),
    (EXTERIOR_LODS, "anchor_trunk", "anchor_exterior"),
    # Interior
    ((0, 1), "anchor_interior", None),
    (INTERIOR_LODS, "anchor_l_door", "anchor_interior"),
    (INTERIOR_LODS, "anchor_l_door_handle", "anchor_l_door"),
    (INTERIOR_LODS, "anchor_l_side_window", "anchor_l_door"),
    (INTERIOR_LODS, "anchor_l_door_buttons", "l_door"),
    (INTERIOR_LODS, "anchor_button_window_l_driver", "anchor_l_door_buttons"),
    (INTERIOR_LODS, "anchor_button_window_l_passenger", "anchor_l_door_buttons"),
    (INTERIOR_LODS, "anchor_l_sunvisor", "anchor_interior"),
    (INTERIOR_LODS, "anchor_r_door", "anchor_interior"),
    (INTERIOR_LODS, "anchor_r_side_window", "anchor_r_door"),
    (INTERIOR_LODS, "anchor_r_door_buttons", "r_door"),
    (INTERIOR_LODS, "anchor_button_window_r_passenger", "anchor_r_door_buttons"),
    (INTERIOR_LODS, "anchor_r_sunvisor", "anchor_interior"),
    (INTERIOR_LODS, "anchor_rearview_mirror", "anchor_interior"),
    (INTERIOR_LODS, "anchor_seat", "anchor_interior"),
    (INTERIOR_LODS, "anchor_seat_passenger", "anchor_interior"),
    (INTERIOR_LODS, "anchor_shift_stick", "anchor_interior"),
    (INTERIOR_LODS, "anchor_gear_stick_knob", "anchor_shift_stick"),
    (INTERIOR_LODS, "anchor_steering_wheel", "anchor_interior"),
    (INTERIOR_LODS, "anchor_l_paddle", "steering_wheel"),
    (INTERIOR_LODS, "anchor_r_paddle", "steering_wheel"),
    (INTERIOR_LODS, "anchor_steering_wheel_cover", "steering_wheel"),
    (INTERIOR_LODS, "anchor_tach", "anchor_interior"),
    (INTERIOR_LODS, "anchor_tach_arrow_rev", "anchor_tach"),
    (INTERIOR_LODS, "anchor_tach_arrow_speed", "anchor_tach"),
    (INTERIOR_LODS, "anchor_tach_indicators", "anchor_tach"),
    (INTERIOR_LODS, "anchor_pedals", "interior"),
    (INTERIOR_LODS, "anchor_hazard_button", "front_panel"),
    (INTERIOR_LODS, "anchor_l_console_stick", "front_panel"),
    (INTERIOR_LODS, "anchor_r_console_stick", "front_panel"),
)

# Wheel meshes, <car>_<wheel part>_LOD<n> (audi_r8_rims_LOD0), at WHEEL_LODS.
WHEELS = ("caliper_b", "caliper_f", "rims", "rotor_b", "rotor_f")

_WHEEL = re.compile(r"^(?P<car>.+)_(?P<wheel>{})_LOD(?P<lod>\d+)$".format("|".join(WHEELS)))


def wheel_of(name):
    """(car, wheel part, LOD) for a wheel mesh name (audi_r8_rims_LOD0), else None."""
    match = _WHEEL.match(name)
    if match is None:
        return None
    return match.group("car"), match.group("wheel"), int(match.group("lod"))

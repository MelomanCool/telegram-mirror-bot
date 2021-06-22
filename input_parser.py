import re


class NoMatchError(ValueError):
    pass


class InvalidSideError(ValueError):
    pass


def parse_input(text):
    text = text.strip().lower()

    mode_side_center = '^(c?)(l|left|r|right)(\d*|a|auto)$'
    found = re.match(mode_side_center, text)
    if not found:
        raise NoMatchError(text)

    mode, side, center = found.groups()

    if side in ('l', 'left'):
        left_mode = True
    elif side in ('r', 'right'):
        left_mode = False
    else:
        raise InvalidSideError(side)

    is_chat = (mode == 'c')

    try:
        center_pos = float(center) / 100
    except ValueError:
        center_pos = center

    return is_chat, left_mode, center_pos

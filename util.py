from collections import namedtuple

import telegram

from named_bytesio import NamedBytesIO


def mirrored_indices(center_pos: int):
    orig_size = center_pos

    for i in reversed(range(0, orig_size)):
        lx = center_pos - i - 1
        rx = center_pos + i

        yield lx, rx


Pos = namedtuple('Pos', ['left', 'right', 'center'])


def get_indices(width: int, left_mode=True, center_mult=0.5):
    orig = Pos(
        left=0,
        right=width,
        center=int(width * center_mult)
    )

    if left_mode:
        original_indices = range(orig.left, orig.center)
        new_center = orig.center
    else:
        original_indices = reversed(range(orig.center, orig.right))
        new_center = width - orig.center

    mirror_indices = mirrored_indices(new_center)
    return zip(original_indices, mirror_indices)


class NoPhotoError(ValueError):
    pass


def extract_image_id(message):
    if message.sticker:
        return message.sticker.file_id
    elif message.photo:
        return message.photo[-1].file_id
    else:
        raise NoPhotoError(message)


def download_file(file_info: telegram.File) -> NamedBytesIO:
    file_name = file_info.file_path.split('/')[-1]

    image_file = NamedBytesIO(name=file_name)
    file_info.download(out=image_file)
    image_file.seek(0)

    return image_file


if __name__ == '__main__':
    indices = get_indices(width=10, left_mode=True, center_mult=0.6)
    # indices = get_indices(width=10, left_mode=False, center_mult=0.6)
    print(*indices, sep='\n')

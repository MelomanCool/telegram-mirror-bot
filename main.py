import logging
import shelve

import telegram
from PIL import Image
from telegram import Message, Bot, Update, ParseMode
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler

from config import TOKEN
from fr import find_face_center, NoFaceError
from named_bytesio import NamedBytesIO
from util import get_indices, extract_image_id, download_file
from input_parser import NoMatchError, parse_input


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def process_image(image_file: NamedBytesIO, image_func) -> NamedBytesIO:
    orig = Image.open(image_file)
    orig_format = orig.format
    processed = image_func(orig)
    orig.close()

    out_file = NamedBytesIO(name=image_file.name)
    logger.info(orig_format)
    processed.save(out_file, format=orig_format)
    processed.close()
    out_file.seek(0)

    return out_file


def ragign(image, left_mode=True, h_center_mult=0.5):
    assert 0 < h_center_mult < 1
    width, height = image.size

    top = 0
    bottom = height
    h_center = int(width * h_center_mult)

    if left_mode:
        mirror_width = h_center * 2
    else:
        mirror_width = (width - h_center) * 2
    mirror = Image.new(image.mode, size=(mirror_width, height))

    indices = get_indices(width, left_mode, h_center_mult)
    for orig_x, left_right in indices:
        lx, rx = left_right

        for y in range(top, bottom):
            pixel = image.getpixel((orig_x, y))
            mirror.putpixel((lx, y), pixel)
            mirror.putpixel((rx, y), pixel)

    return mirror


class MyBot(object):
    def __init__(self, image_func):
        self.last_user_photos = shelve.open('last_user_photos', writeback=True)
        self.last_chat_photos = shelve.open('last_chat_photos', writeback=True)
        self.image_func = image_func

    def __del__(self):
        self.last_user_photos.close()

    def remember_photo(self, bot: Bot, update: Update):
        message = update.message  # type: telegram.Message
        image_id = extract_image_id(message)

        user_id = str(message.from_user.id)
        self.last_user_photos[user_id] = image_id
        self.last_user_photos.sync()

        chat_id = str(message.chat.id)
        self.last_chat_photos[chat_id] = image_id
        self.last_chat_photos.sync()

    def cmd_mirror(self, bot: Bot, update: Update):
        message = update.message  # type: Message

        try:
            is_chat, left_mode, center_pos = parse_input(message.text)
        except NoMatchError:
            return

        if is_chat:
            chat_id = str(message.chat.id)
            file_info = bot.get_file(self.last_chat_photos[chat_id])
        else:
            user_id = str(message.from_user.id)
            file_info = bot.get_file(self.last_user_photos[user_id])

        if center_pos:
            self.send(file_info, message, left_mode, center_pos)
        else:
            self.send(file_info, message, left_mode)

    def send(self, file_info: telegram.File, message, left_mode, center_pos=0.5):
        image_file = download_file(file_info)

        if center_pos in ('a', 'auto'):
            try:
                center_pos = find_face_center(image_file)
                logger.info('Recognized face center: %s', center_pos)
            except NoFaceError:
                center_pos = 0.5
        else:
            center_pos = float(center_pos)

        image_func = lambda img: self.image_func(img, left_mode, center_pos)
        processed_image_file = process_image(image_file, image_func)

        file_ext = file_info.file_path.split('.')[-1]
        if file_ext == 'webp':
            message.reply_sticker(processed_image_file, quote=False)
        else:
            message.reply_photo(processed_image_file, quote=False)


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"' % (update, error))


def cmd_help(bot, update):
    message = update.message  # type: Message
    message.reply_text(
        'This bot can mirror images. Send a sticker or a photo, then send '
        'a side — `left` or `right` to mirror it.\n'
        '\n'
        'You can also set center of symmetry — just write a number between'
        '0 and 100 right after the side (e.g. `left40`). Also, there is '
        'auto-mode, just write `auto` after side (e.g. `rightauto`).\n'
        '\n'
        'Also, there are short versions of keywords:\n'
        '`l` – `left`\n'
        '`r` – `right`\n'
        '`a` – `auto`\n'
        '\n'
        'Example commands:\n'
        '`left` – mirror left\n'
        '`right` – mirror right\n'
        '`left40` – mirror right, center 40%\n'
        '`l40` – same as above\n'
        '`rightauto` – mirror right, center is automatically set\n'
        '`righta` – same as above\n'
        '`rauto` – same as above\n'
    , parse_mode=ParseMode.MARKDOWN, quote=False)


if __name__ == '__main__':
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    bot = MyBot(image_func=ragign)

    dp.add_handler(CommandHandler('help', cmd_help))
    dp.add_handler(MessageHandler(Filters.photo | Filters.sticker, bot.remember_photo))
    dp.add_handler(MessageHandler(Filters.text, bot.cmd_mirror))

    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()

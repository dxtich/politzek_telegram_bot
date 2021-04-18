import requests
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, executor, types
from math import ceil
import os

API_TOKEN = os.getenv("API_TOKEN")
LOG_FILE = os.getenv("LOG_FILE")
# DEBUG_LEVEL = logging.INFO

if LOG_FILE:
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO)
else:
    logging.basicConfig(level=logging.DEBUG)

log = logging.getLogger("bot")

cached_prisoners = dict()
bulk = 25

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

keyboard_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
btns_text = ("5", "10", "15")
keyboard_markup.row(*(types.KeyboardButton(text) for text in btns_text))


def get_prisoners():
    req_url = "https://politzek.me/api/prisoners?" \
              "fields[]=name&" \
              "fields[]=shortName&" \
              "fields[]=friendsCount&" \
              "filterByFormula=AND(isVisible, releasedAt='')&" \
              "sort[0][field]=friendsCount"
    try:
        response = requests.get(req_url)
    except requests.exceptions.SSLError as e:
        if "certificate has expired" in str(e):
            response = requests.get(req_url, verify=False)
        else:
            log.info(str(e))
            raise e
    prisoners = response.json()['body']['records']
    return prisoners


def cache_prisoners():
    now = datetime.now()
    if 'time' not in cached_prisoners or cached_prisoners['time'] < now - timedelta(minutes=1):
        cached_prisoners['prisoners'] = get_prisoners()
        cached_prisoners['time'] = now
        log.info(f"cache updated {now.time()}")


def escape(s: str):
    es = s.replace("(", "\\(").replace(")", "\\)").replace('-', '\\-')
    return es


def format_prisoner(prisoner):
    friends_count = prisoner['fields']['friendsCount']
    name = escape(str(prisoner['fields']['name']))
    short_name = escape(str(prisoner['fields']['shortName']))
    s = f"{friends_count} друзей [{name}](https://politzek.me/details/{short_name})"
    return s


def get_prisoners_by_count(n=10):
    cache_prisoners()
    filtered_prisons = list()
    filtered_prisons.extend(x for x in cached_prisoners['prisoners'][:n])
    for i in range(ceil(len(filtered_prisons) / bulk)):
        s = '\n'.join(format_prisoner(x) for x in filtered_prisons[i * bulk:i * bulk + bulk])
        yield s


def get_prisoners_by_friends_count(friends_count=1):
    cache_prisoners()
    filtered_prisons = list()
    filtered_prisons.extend(x for x in cached_prisoners['prisoners'] if x['fields']['friendsCount'] < friends_count)
    for i in range(ceil(len(filtered_prisons) / bulk)):
        s = '\n'.join(format_prisoner(x) for x in filtered_prisons[i * bulk:i * bulk + bulk])
        yield s


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply("Выберите или введите количество политзаключенных с минимальным количеством друзей",
                        reply_markup=keyboard_markup)


@dp.message_handler(regexp='^[0-9]')
async def by_count(message: types.Message):
    log.info(message)
    for answer in get_prisoners_by_count(int(message.text)):
        await message.answer(answer, parse_mode='MarkdownV2', disable_web_page_preview=True,
                             reply_markup=keyboard_markup)


@dp.message_handler(regexp='^<[0-9]')
async def by_friends(message: types.Message):
    log.info(message)
    for answer in get_prisoners_by_friends_count(int(message.text[1:])):
        await message.answer(answer, parse_mode='MarkdownV2', disable_web_page_preview=True,
                             reply_markup=keyboard_markup)


@dp.message_handler()
async def empty(message: types.Message):
    log.info(message)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

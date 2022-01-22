import requests
import logging
import random
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, executor, types
from math import ceil
import os
import re

BASE_URL = 'https://www.politzek.me'
API_TOKEN = os.getenv("API_TOKEN")
LOG_FILE = os.getenv("LOG_FILE")
# DEBUG_LEVEL = logging.INFO
log_format = '%(asctime)s|%(levelname)s|%(message)s'
datefmt='%Y-%m-%d %H:%M:%S'
p_url = "https://mzpyd51e32.execute-api.us-east-2.amazonaws.com/prod/prisoners"

if LOG_FILE:
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                        format=log_format,
                        datefmt=datefmt)
else:
    logging.basicConfig(level=logging.DEBUG,
                        format=log_format,
                        datefmt=datefmt)

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
    try:
        response = requests.get(p_url)
    except requests.exceptions.ConnectionError:
        get_api_url()
        try:
            response = requests.get(p_url)
        except Exception as e:
            log.warning(str(e))
            raise e
    except requests.exceptions.SSLError as e:
        if "certificate has expired" in str(e):
            log.warning("Certificate has expired")
            response = requests.get(p_url, verify=False)
        else:
            log.info(str(e))
            raise e
    prisoners = response.json()
    return prisoners


def shuffle_prisoners():
    cache_prisoners()
    current_prisoners = cached_prisoners['prisoners']
    current_friends_count = current_prisoners[0]['fields']['friendsCount']
    temp_prisoners = list()
    shuufled_prisoners = list()
    for prisoner in current_prisoners:
        prisoner_friends_count = prisoner['fields']['friendsCount']
        if prisoner_friends_count == current_friends_count:
            temp_prisoners.append(prisoner)
        else:
            random.shuffle(temp_prisoners)
            shuufled_prisoners.extend(temp_prisoners)
            temp_prisoners = [prisoner]
            current_friends_count = prisoner_friends_count
    random.shuffle(temp_prisoners)
    shuufled_prisoners.extend(temp_prisoners)
    cached_prisoners['prisoners'] = shuufled_prisoners


def sort_prisoners(prisoners: dict):
    sorted_prisoners = sorted(prisoners, key=lambda k: k['fields']['friendsCount'])
    return sorted_prisoners


def get_api_url():
    try:
        response = requests.get(f"{BASE_URL}/js/index.js")
        rt = response.text
        apiBase = re.search('apiBase:"(.+?)"', rt).group(1)
        global p_url
        p_url = f"{apiBase}/prisoners"
        log.info(f"api url updated to: {p_url}")
    except AttributeError as e:
        log.warning("not found apiBase")
        raise e
    except Exception as e:
        log.warning(str(e))
        raise e




def cache_prisoners():
    now = datetime.now()
    if 'time' not in cached_prisoners or cached_prisoners['time'] < now - timedelta(minutes=1):
        prisoners = get_prisoners()
        sorted_prisoners = sort_prisoners(prisoners)
        cached_prisoners['prisoners'] = sorted_prisoners
        cached_prisoners['time'] = now
        log.info(f"cache updated {now.time()}")


def escape(s: str):
    es = s.replace("(", "\\(").replace(")", "\\)").replace('-', '\\-')
    return es


def format_prisoner(prisoner):
    friends_count = prisoner['fields']['friendsCount']
    name = escape(str(prisoner['fields']['name']))
    short_name = escape(str(prisoner['fields']['shortName']))
    s = f"{friends_count} друзей [{name}]({BASE_URL}/friends/{short_name})"
    return s


def get_prisoners_by_count(n=10):
    shuffle_prisoners()
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
    await message.reply("Бот помогает найти политзаключённых, у которых меньше всего друзей и, соответственно, писем. "
                        "При нажатии кнопки «5» бот выдает 5 человек с самого конца списка, «10» - 10 человек "
                        "соответственно по данным сайта Politzek.me\n"
                        "Выберите или введите количество политзаключенных",
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

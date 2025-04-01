import logging
import random
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

API_TOKEN = '8031461614:AAG5nEy2LtWtmcjomroTnCQcAl6eTOYbwyQ'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# Хранилище мест в памяти
places = []

# Шаги для добавления места
class AddPlace(StatesGroup):
    name = State()
    category = State()
    description = State()
    location = State()

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    await message.reply("Привет! Я помогу тебе выбрать место для свидания 💘\n\nДоступные команды:\n/add — добавить место\n/list — посмотреть все\n/filter — выбрать по категории\n/random — случайное место")

@dp.message_handler(commands=['add'])
async def cmd_add(message: types.Message):
    await AddPlace.name.set()
    await message.reply("Как называется место?")

@dp.message_handler(state=AddPlace.name)
async def add_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await AddPlace.next()
    await message.reply("Какая категория? (кафе, парк, бар, выставка и т.п.)")

@dp.message_handler(state=AddPlace.category)
async def add_category(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text)
    await AddPlace.next()
    await message.reply("Краткое описание?")

@dp.message_handler(state=AddPlace.description)
async def add_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await AddPlace.next()
    await message.reply("Где находится место? (адрес или ссылка на карту)")

@dp.message_handler(state=AddPlace.location)
async def add_location(message: types.Message, state: FSMContext):
    data = await state.get_data()
    place = {
        'name': data['name'],
        'category': data['category'],
        'description': data['description'],
        'location': message.text
    }
    places.append(place)
    await state.finish()
    await message.reply("Место добавлено! ❤️")

@dp.message_handler(commands=['list'])
async def cmd_list(message: types.Message):
    if not places:
        await message.reply("Пока что мест нет. Добавь что-нибудь с помощью /add")
    else:
        text = "\n\n".join([
            f"📍 *{p['name']}* ({p['category']})\n_{p['description']}_\n{p['location']}"
            for p in places
        ])
        await message.reply(text, parse_mode="Markdown")

@dp.message_handler(commands=['filter'])
async def cmd_filter(message: types.Message):
    categories = list(set([p['category'] for p in places]))
    if not categories:
        await message.reply("Категорий пока нет. Добавь места через /add")
        return
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for c in categories:
        kb.add(KeyboardButton(c))
    await message.reply("Выбери категорию:", reply_markup=kb)

@dp.message_handler(lambda message: message.text in [p['category'] for p in places])
async def filtered_places(message: types.Message):
    selected = [p for p in places if p['category'] == message.text]
    text = "\n\n".join([
        f"📍 *{p['name']}*\n_{p['description']}_\n{p['location']}"
        for p in selected
    ])
    await message.reply(text, parse_mode="Markdown", reply_markup=types.ReplyKeyboardRemove())

@dp.message_handler(commands=['random'])
async def cmd_random(message: types.Message):
    if not places:
        await message.reply("Пока нет мест. Добавь что-нибудь через /add")
    else:
        p = random.choice(places)
        text = f"❤️ *{p['name']}* ({p['category']})\n_{p['description']}_\n{p['location']}"
        await message.reply(text, parse_mode="Markdown")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

import logging
import random
import sqlite3
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

API_TOKEN = '8031461614:AAG5nEy2LtWtmcjomroTnCQcAl6eTOYbwyQ'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# SQLite setup
conn = sqlite3.connect("places.db")
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS places (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    category TEXT,
    description TEXT,
    location TEXT,
    visited INTEGER DEFAULT 0
)
''')
conn.commit()

CATEGORIES = [
    "Еда 🍕", "Животные 🙉", "Учеба 📚", "Выставки 🏛️",
    "Погулять 🚶‍♂️🚶‍♀️", "Клубы 🪩", "Концерты 🎤", "Кино 🍿", "Театры 🎭"
]

class AddPlace(StatesGroup):
    name = State()
    category = State()
    description = State()
    location = State()

def reply_category_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for cat in CATEGORIES:
        kb.add(KeyboardButton(cat))
    return kb

def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton('Добавить'), KeyboardButton('Показать все'))
    kb.row(KeyboardButton('Категории'), KeyboardButton('Рандом'))
    return kb

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    await message.reply(
        "Привет! Я помогу тебе выбрать место для свидания 💘",
        reply_markup=main_menu()
    )

@dp.message_handler(lambda message: message.text == 'Добавить')
async def cmd_add(message: types.Message):
    await AddPlace.name.set()
    await message.reply("Как называется место?")

@dp.message_handler(state=AddPlace.name)
async def add_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await AddPlace.next()
    await message.reply("Выбери категорию:", reply_markup=reply_category_keyboard())

@dp.message_handler(state=AddPlace.category)
async def add_category(message: types.Message, state: FSMContext):
    category = message.text
    if category not in CATEGORIES:
        await message.reply("Пожалуйста, выбери категорию из кнопок ниже:", reply_markup=reply_category_keyboard())
        return
    await state.update_data(category=category)
    await AddPlace.next()
    await message.reply("Краткое описание?", reply_markup=ReplyKeyboardRemove())

@dp.message_handler(state=AddPlace.description)
async def add_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await AddPlace.next()
    await message.reply("Ссылка на место")

@dp.message_handler(state=AddPlace.location)
async def add_location(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cursor.execute("INSERT INTO places (name, category, description, location) VALUES (?, ?, ?, ?)",
                   (data['name'], data['category'], data['description'], message.text))
    conn.commit()
    await state.finish()
    await message.reply("Место добавлено! ❤️", reply_markup=main_menu())

@dp.message_handler(lambda message: message.text == 'Показать все')
async def cmd_list(message: types.Message):
    cursor.execute("SELECT name, category, description, location, visited FROM places")
    records = cursor.fetchall()
    if not records:
        await message.reply("Пока что мест нет. Добавь что-нибудь с помощью 'Добавить'")
    else:
        text = "\n\n".join([
            f"📍 *{r[0]}* ({r[1]}) {'✅' if r[4] else ''}\n_{r[2]}_\n{r[3]}"
            for r in records
        ])
        await message.reply(text, parse_mode="Markdown")

@dp.message_handler(lambda message: message.text == 'Категории')
async def cmd_filter(message: types.Message):
    cursor.execute("SELECT DISTINCT category FROM places")
    categories = [row[0] for row in cursor.fetchall()]
    if not categories:
        await message.reply("Категорий пока нет. Добавь места через 'Добавить'")
        return
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for c in categories:
        kb.add(KeyboardButton(c))
    await message.reply("Выбери категорию:", reply_markup=kb)

@dp.message_handler(lambda message: message.text in CATEGORIES)
async def filtered_places(message: types.Message):
    category = message.text
    cursor.execute("SELECT name, description, location FROM places WHERE category = ?", (category,))
    selected = cursor.fetchall()
    if selected:
        text = "\n\n".join([
            f"📍 *{r[0]}*\n_{r[1]}_\n{r[2]}"
            for r in selected
        ])
        await message.reply(text, parse_mode="Markdown", reply_markup=main_menu())
    else:
        await message.reply("Ничего не найдено в этой категории", reply_markup=main_menu())

@dp.message_handler(lambda message: message.text == 'Рандом')
async def cmd_random(message: types.Message):
    cursor.execute("SELECT name, category, description, location FROM places")
    records = cursor.fetchall()
    if not records:
        await message.reply("Пока нет мест. Добавь что-нибудь через 'Добавить'")
    else:
        r = random.choice(records)
        text = f"❤️ *{r[0]}* ({r[1]})\n_{r[2]}_\n{r[3]}"
        await message.reply(text, parse_mode="Markdown")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

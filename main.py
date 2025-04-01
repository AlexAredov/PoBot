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

class EditPlace(StatesGroup):
    place_id = State()
    field = State()
    new_value = State()

def reply_category_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for cat in CATEGORIES:
        kb.add(KeyboardButton(cat))
    return kb

def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton('Добавить'), KeyboardButton('Показать все'))
    kb.row(KeyboardButton('Категории'), KeyboardButton('Рандом'))
    kb.row(KeyboardButton('Удалить'), KeyboardButton('Изменить'))
    kb.add(KeyboardButton('Посетили'))
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
    cursor.execute("SELECT id, name, category, description, location, visited FROM places")
    records = cursor.fetchall()
    if not records:
        await message.reply("Пока что мест нет. Добавь что-нибудь с помощью 'Добавить'")
    else:
        text = "\n\n".join([
            f"📍 *{r[1]}* ({r[2]}) {'✅' if r[5] else ''}\n_{r[3]}_\n{r[4]}\nID: {r[0]}"
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

@dp.message_handler(lambda message: message.text == 'Удалить')
async def delete_prompt(message: types.Message):
    await message.reply("Введи ID места, которое нужно удалить")

@dp.message_handler(lambda message: message.text.startswith('Удалить '))
async def delete_place(message: types.Message):
    place_id = message.text.replace('Удалить ', '').strip()
    cursor.execute("DELETE FROM places WHERE id = ?", (place_id,))
    conn.commit()
    await message.reply("Место удалено, если ID был корректным.")

@dp.message_handler(lambda message: message.text == 'Посетили')
async def visit_prompt(message: types.Message):
    await message.reply("Введи ID места, которое ты посетил")

@dp.message_handler(lambda message: message.text.startswith('visit '))
async def mark_visited(message: types.Message):
    place_id = message.text.replace('visit ', '').strip()
    cursor.execute("UPDATE places SET visited = 1 WHERE id = ?", (place_id,))
    conn.commit()
    await message.reply("Место отмечено как посещенное ✅")

@dp.message_handler(lambda message: message.text == 'Изменить')
async def edit_start(message: types.Message):
    await EditPlace.place_id.set()
    await message.reply("Введи ID места, которое хочешь изменить")

@dp.message_handler(state=EditPlace.place_id)
async def edit_field_prompt(message: types.Message, state: FSMContext):
    await state.update_data(place_id=message.text)
    await EditPlace.next()
    await message.reply("Что изменить? (name, category, description, location)")

@dp.message_handler(state=EditPlace.field)
async def edit_value_prompt(message: types.Message, state: FSMContext):
    await state.update_data(field=message.text)
    await EditPlace.next()
    await message.reply("На что заменить?")

@dp.message_handler(state=EditPlace.new_value)
async def edit_apply(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cursor.execute(f"UPDATE places SET {data['field']} = ? WHERE id = ?", (message.text, data['place_id']))
    conn.commit()
    await state.finish()
    await message.reply("Изменения сохранены ✅", reply_markup=main_menu())

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

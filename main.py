import logging
import random
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

API_TOKEN = 'YOUR_BOT_TOKEN_HERE'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

places = []
CATEGORIES = ["кафе", "парк", "бар", "выставка", "кино", "другое"]

class AddPlace(StatesGroup):
    name = State()
    category = State()
    description = State()
    location = State()

def category_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    buttons = [InlineKeyboardButton(text=c, callback_data=f"cat_{c}") for c in CATEGORIES]
    kb.add(*buttons)
    return kb

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
    await message.reply("Выбери категорию:", reply_markup=category_keyboard())

@dp.callback_query_handler(lambda c: c.data.startswith("cat_"), state=AddPlace.category)
async def process_category(callback_query: types.CallbackQuery, state: FSMContext):
    category = callback_query.data[4:]
    await state.update_data(category=category)
    await AddPlace.next()
    await bot.send_message(callback_query.from_user.id, "Краткое описание?", reply_markup=ReplyKeyboardRemove())
    await callback_query.answer()

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
    kb = InlineKeyboardMarkup(row_width=2)
    buttons = [InlineKeyboardButton(text=c, callback_data=f"filter_{c}") for c in categories]
    kb.add(*buttons)
    await message.reply("Выбери категорию:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("filter_"))
async def filtered_places(callback_query: types.CallbackQuery):
    selected_category = callback_query.data[7:]
    selected = [p for p in places if p['category'] == selected_category]
    text = "\n\n".join([
        f"📍 *{p['name']}*\n_{p['description']}_\n{p['location']}"
        for p in selected
    ])
    await bot.send_message(callback_query.from_user.id, text or "Ничего не найдено в этой категории", parse_mode="Markdown")
    await callback_query.answer()

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
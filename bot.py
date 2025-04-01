
# ✅ Railway-ready версия Telegram-бота (MindDrop Bot)
# Все переменные передаются через окружение (API_TOKEN)

import os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

API_TOKEN = os.getenv("API_TOKEN")

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Подключение к Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("google_credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("MindDropBotData").sheet1

# FSM для пошагового ввода
class Form(StatesGroup):
    thought = State()
    recency = State()
    ownership = State()
    quick_task = State()

@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    await message.reply("Привет! Я помогу тебе структурировать мысли. Напиши /new, чтобы начать.")

@dp.message_handler(commands='new')
async def cmd_new(message: types.Message):
    await Form.thought.set()
    await message.reply("Что за мысль пришла тебе в голову?")

@dp.message_handler(state=Form.thought)
async def process_thought(message: types.Message, state: FSMContext):
    await state.update_data(thought=message.text)
    await Form.next()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Сейчас", "Сегодня", "Давно", "Не помню")
    await message.reply("Когда эта мысль пришла тебе в голову?", reply_markup=markup)

@dp.message_handler(state=Form.recency)
async def process_recency(message: types.Message, state: FSMContext):
    await state.update_data(recency=message.text)
    await Form.next()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Моя", "Навязанная")
    await message.reply("Это твоя мысль или навязанная?", reply_markup=markup)

@dp.message_handler(state=Form.ownership)
async def process_ownership(message: types.Message, state: FSMContext):
    await state.update_data(ownership=message.text)
    await Form.next()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Да", "Нет")
    await message.reply("Можно ли выполнить за 5 минут?", reply_markup=markup)

@dp.message_handler(state=Form.quick_task)
async def process_quick_task(message: types.Message, state: FSMContext):
    await state.update_data(quick_task=message.text)
    data = await state.get_data()

    # Запись в таблицу
    sheet.append_row([
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data['thought'],
        data['recency'],
        data['ownership'],
        data['quick_task']
    ])

    await message.reply("Записал! Хочешь добавить ещё — введи /new", reply_markup=types.ReplyKeyboardRemove())
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

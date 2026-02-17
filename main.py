import logging
import sys
import os
import asyncio
import datetime
import random

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile
from aiogram.exceptions import TelegramBadRequest
from dotenv import load_dotenv

from models import init_db
import db_helper
import ai_helper
import schedule_gen

# Загрузка переменных
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    logger.error("Ошибка: TELEGRAM_BOT_TOKEN не найден")
    sys.exit(1)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Состояния FSM
class States(StatesGroup):
    waiting_task_subject = State()
    waiting_task_desc = State()
    waiting_task_deadline = State()
    waiting_edit_choice = State()
    waiting_edit_subject = State()
    waiting_edit_desc = State()
    waiting_edit_deadline = State()

# Главная клавиатура
def main_kb(user_id: int = None):
    kb = ReplyKeyboardBuilder()
    kb.button(text="📅 Расписание")
    kb.button(text="📝 Мои Задания")
    
    admin_id = os.getenv("ADMIN_ID")
    if str(user_id) == admin_id:
        kb.button(text="➕ Добавить ДЗ")
        
    kb.button(text="🤖 AI Помощник")
    kb.button(text="📊 Статистика")
    kb.button(text="🎮 Достижения")
    
    if str(user_id) == admin_id:
        kb.adjust(2, 2, 2)
    else:
        kb.adjust(2, 1, 2)
    return kb.as_markup(resize_keyboard=True)

# --- КОМАНДЫ ---

@dp.message(CommandStart())
async def start(message: types.Message):
    logger.info(f"User {message.from_user.id} started the bot")
    try:
        await db_helper.get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
        
        kb = InlineKeyboardBuilder()
        classes = ["6А", "6В", "7А", "7В", "7С", "8А", "8Б", "9А", "10А", "11А"]
        for c in classes:
            kb.button(text=c, callback_data=f"cls_{c}")
        kb.adjust(3)
        
        await message.answer(
            f"Привет, {message.from_user.first_name}! 👋\n\n"
            "Я твой умный школьный дневник 2.0. Я помогу тебе учиться эффективнее.\n\n"
            "Для начала выбери свой класс:", 
            reply_markup=kb.as_markup()
        )
    except Exception as e:
        logger.error(f"Error in start command: {e}")

@dp.callback_query(F.data.startswith("cls_"))
async def set_class(cb: types.CallbackQuery):
    cls = cb.data.split("_")[1]
    await db_helper.update_user_class(cb.from_user.id, cls)
    await cb.answer(f"Класс {cls} выбран! ✅")
    await cb.message.answer(
        f"Отлично! Теперь я знаю твое расписание для {cls}. 😎", 
        reply_markup=main_kb(cb.from_user.id)
    )

# --- РАСПИСАНИЕ ---

@dp.message(F.text == "📅 Расписание")
async def schedule_menu(message: types.Message):
    user = await db_helper.get_user(message.from_user.id)
    if not user or not user.class_name:
        await message.answer("Сначала выбери класс с помощью /start")
        return
    
    kb = InlineKeyboardBuilder()
    days = ["Пн", "Вт", "Ср", "Чт", "Пт"]
    for i, d in enumerate(days):
        kb.button(text=d, callback_data=f"sch_{i}")
    kb.adjust(5)
    
    await message.answer(f"На какой день показать расписание ({user.class_name})?", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("sch_"))
async def show_schedule(cb: types.CallbackQuery):
    user = await db_helper.get_user(cb.from_user.id)
    day_idx = int(cb.data.split("_")[1])
    
    from schedule_gen import РАСПИСАНИЕ
    
    if user.class_name not in РАСПИСАНИЕ or day_idx not in РАСПИСАНИЕ[user.class_name]:
        await cb.answer("Расписание для этого дня пока не заполнено.")
        return
    
    try:
        await cb.answer("Генерирую карточку...")
    except:
        pass
        
    schedule_data = РАСПИСАНИЕ[user.class_name][day_idx]
    img_path = schedule_gen.generate_schedule_image(user.class_name, day_idx, schedule_data)
    
    photo = FSInputFile(img_path)
    days_acc = ["понедельник", "вторник", "среду", "четверг", "пятницу"]
    await cb.message.answer_photo(photo, caption=f"Твоё расписание на {days_acc[day_idx]}")
    try:
        await cb.message.delete()
    except:
        pass

# --- ДОМАШНЕЕ ЗАДАНИЕ ---

@dp.message(F.text == "📝 Мои Задания")
async def list_tasks(message: types.Message):
    db_user = await db_helper.get_user(message.from_user.id)
    if not db_user:
        await message.answer("Сначала выбери класс с помощью /start")
        return
    tasks = await db_helper.get_user_tasks(db_user.id)
    
    if not tasks:
        await message.answer("У тебя пока нет активных заданий. Отдыхай! 🥳", reply_markup=main_kb(message.from_user.id))
        return
    
    admin_id = os.getenv("ADMIN_ID")
    for t in tasks:
        kb = InlineKeyboardBuilder()
        kb.button(text="✅ Выполнено", callback_data=f"done_{t.id}")
        kb.button(text="🤖 Разбить на шаги", callback_data=f"steps_{t.id}")
        kb.button(text="📚 Материалы", callback_data=f"mats_{t.id}")
        
        if str(message.from_user.id) == admin_id:
            kb.button(text="✏️ Редактировать", callback_data=f"edit_{t.id}")
            kb.button(text="🗑️ Удалить", callback_data=f"del_{t.id}")
            
        kb.adjust(1)
        deadline_str = t.deadline.strftime("%d.%m %H:%M")
        diff_emoji = {"easy": "🟢", "normal": "🟡", "hard": "🔴"}.get(t.difficulty, "⚪")
        
        text = f"{diff_emoji} *{t.subject}*\n\n{t.description}\n\n⏰ К занятию: {deadline_str}"
        await message.answer(text, reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("done_"))
async def complete_task_cb(cb: types.CallbackQuery):
    task_id = int(cb.data.split("_")[1])
    if await db_helper.complete_task(task_id):
        await cb.answer("Молодец! +XP 🌟")
        try:
            await cb.message.edit_text(f"✅ {cb.message.text}\n\n*ВЫПОЛНЕНО*")
        except:
            await cb.message.answer(f"✅ Задача выполнена!")
    else:
        await cb.answer("Ошибка или уже выполнено")

@dp.callback_query(F.data.startswith("mats_"))
async def get_materials(cb: types.CallbackQuery):
    try:
        await cb.answer("Ищу полезные ссылки...")
    except: pass
    
    task_text = cb.message.text
    prompt = f"Найди реальные ссылки на материалы (видео VK и статьи) по теме: {task_text}. Не выдумывай ссылки!"
    result = await ai_helper.solve_problem(prompt, system_prompt="Ты — эксперт по поиску образовательного контента.")
    await cb.message.answer(f"📚 *Материалы для подготовки:*\n\n{result}")

@dp.callback_query(F.data.startswith("steps_"))
async def get_steps(cb: types.CallbackQuery):
    try:
        await cb.answer("Генерирую план...")
    except: pass
    
    task_text = cb.message.text
    prompt = f"Разбей на конкретные шаги выполнение этого задания: {task_text}. Используй эмодзи."
    result = await ai_helper.solve_problem(prompt, system_prompt="Ты — эксперт-репетитор.")
    await cb.message.answer(f"📋 *Интеллектуальный план выполнения:*\n\n{result}")

# --- АДМИН-ФУНКЦИИ ---

@dp.message(F.text == "➕ Добавить ДЗ")
async def add_task_start(message: types.Message, state: FSMContext):
    admin_id = os.getenv("ADMIN_ID")
    if str(message.from_user.id) != admin_id:
        await message.answer("У вас нет прав администратора!")
        return
    await message.answer("По какому предмету задание?")
    await state.set_state(States.waiting_task_subject)

@dp.message(States.waiting_task_subject)
async def add_task_subject(message: types.Message, state: FSMContext):
    await state.update_data(subject=message.text)
    await message.answer("Что нужно сделать?")
    await state.set_state(States.waiting_task_desc)

@dp.message(States.waiting_task_desc)
async def add_task_desc(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Через сколько часов будет занятие? (введи число)")
    await state.set_state(States.waiting_task_deadline)

@dp.message(States.waiting_task_deadline)
async def add_task_deadline(message: types.Message, state: FSMContext):
    try:
        hours = int(message.text)
        data = await state.get_data()
        db_user = await db_helper.get_user(message.from_user.id)
        deadline = datetime.datetime.now() + datetime.timedelta(hours=hours)
        
        prompt = f"Определи сложность задания (easy, normal, hard) одним словом: {data['subject']} - {data['description']}"
        diff_res = await ai_helper.solve_problem(prompt, system_prompt="Отвечай только одним словом: easy, normal или hard")
        difficulty = diff_res.lower().strip() if diff_res else "normal"
        if difficulty not in ['easy', 'normal', 'hard']: difficulty = 'normal'
            
        await db_helper.add_task(user_id=db_user.id, subject=data['subject'], description=data['description'], deadline=deadline, difficulty=difficulty, class_name=db_user.class_name)
        await message.answer(f"✅ Задание добавлено! Сложность: {difficulty}", reply_markup=main_kb(message.from_user.id))
        await state.clear()
    except Exception as e:
        logger.error(f"Error adding task: {e}")
        await message.answer("Ошибка. Введи число часов.")

@dp.callback_query(F.data.startswith("del_"))
async def delete_task_cb(cb: types.CallbackQuery):
    admin_id = os.getenv("ADMIN_ID")
    if str(cb.from_user.id) != admin_id:
        await cb.answer("Нет прав!")
        return
    task_id = int(cb.data.split("_")[1])
    if await db_helper.delete_task(task_id):
        await cb.answer("Удалено!")
        try:
            await cb.message.delete()
        except: pass

# --- СТАТИСТИКА И ПРОЧЕЕ ---

@dp.message(F.text == "🤖 AI Помощник")
async def ai_menu(message: types.Message):
    await message.answer("Я тут! Спрашивай что угодно по учебе.")

@dp.message(F.text == "📊 Статистика")
async def stats(message: types.Message):
    db_user = await db_helper.get_user(message.from_user.id)
    tasks = await db_helper.get_user_tasks(db_user.id)
    text = f"📊 *Твоя статистика:*\n\nУровень: {db_user.level}\nXP: {db_user.xp}\nЗадач в работе: {len(tasks)}"
    await message.answer(text)

@dp.message(F.text == "🎮 Достижения")
async def achievements(message: types.Message):
    user = await db_helper.get_user(message.from_user.id)
    text = f"🏆 *Твои достижения:*\n\nУровень {user.level}\n"
    if user.xp > 100: text += "⭐ Продвинутый ученик\n"
    else: text += "🐣 Новичок\n"
    await message.answer(text)

@dp.message(F.text, ~F.text.startswith("/"))
async def process_ai_query(message: types.Message):
    if message.text in ["📅 Расписание", "📝 Мои Задания", "➕ Добавить ДЗ", "🤖 AI Помощник", "📊 Статистика", "🎮 Достижения"]:
        return
    await message.answer("⏳ Думаю...")
    response = await ai_helper.solve_problem(message.text)
    await message.answer(response)

async def main():
    await init_db()
    logger.info("Database initialized")
    print("Бот запущен!")
    # Удаляем вебхук перед запуском polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

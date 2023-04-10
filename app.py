import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging
import base64
from config import MY_TOKEN
from translations_dict import translations

logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=MY_TOKEN)
dp = Dispatcher(bot)

# Add logging middleware
dp.middleware.setup(LoggingMiddleware())
correct_answers = {}
scores = {}
total_answers = {}
options_per_chat = {}
selected_language = {}


async def choose_language_handler(message):
    chat_id = message.chat.id if isinstance(message, types.Message) else message.from_user.id
    markup = InlineKeyboardMarkup(row_width=2)
    en_button = InlineKeyboardButton("English", callback_data="language_en")
    ru_button = InlineKeyboardButton("Русский", callback_data="language_ru")
    markup.add(en_button, ru_button)

    await bot.send_message(chat_id, "Choose the interface language / Выберите язык интерфейса:", reply_markup=markup)


def generate_trivia_button(language: str):
    markup = InlineKeyboardMarkup()
    trivia_button = InlineKeyboardButton(translations[language]["get_trivia_question"], callback_data="get_trivia")
    end_game_button = InlineKeyboardButton(translations[language]["end_game"], callback_data="end_game")
    markup.add(trivia_button, end_game_button)
    return markup


async def fetch_trivia_question(difficulty: str):
    url = f"https://opentdb.com/api.php?amount=1&difficulty={difficulty}&type=multiple&encode=base64"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
    return data


async def format_question(data):
    question = base64.b64decode(data["results"][0]["question"]).decode('utf-8')
    correct_answer = base64.b64decode(data["results"][0]["correct_answer"]).decode('utf-8')
    incorrect_answers = [base64.b64decode(ans).decode('utf-8') for ans in data["results"][0]["incorrect_answers"]]

    formatted_question = f"<b>{question}</b>\n\n"
    options = [correct_answer] + incorrect_answers
    options.sort()

    return formatted_question, options, correct_answer


async def send_response_and_buttons(chat_id, text, language):
    markup = generate_trivia_button(language)
    await bot.send_message(chat_id, text, reply_markup=markup)


async def start_handler(message: types.Message):
    chat_id = message.chat.id

    if chat_id in total_answers:
        total_answers[chat_id] = 0
    if chat_id in scores:
        scores[chat_id] = 0

    await choose_language_handler(message)


async def trivia_handler(message: types.Message, difficulty: str = "easy"):
    data = await fetch_trivia_question(difficulty)
    question, options, correct_answer = await format_question(data)
    chat_id = message.chat.id
    correct_answers[chat_id] = correct_answer
    if chat_id not in total_answers:
        total_answers[chat_id] = 0
        scores[chat_id] = 0  # Initialize scores for the chat

    inline_keyboard = InlineKeyboardMarkup()
    for index, option in enumerate(options, start=1):
        button = InlineKeyboardButton(f"{index}. {option}", callback_data=f"answer_{index}")
        inline_keyboard.add(button)

    options_per_chat[chat_id] = options

    language = selected_language.get(message.chat.id, "en")
    await bot.send_message(chat_id, question, parse_mode=ParseMode.HTML, reply_markup=inline_keyboard)


async def end_game_handler(callback_query: types.CallbackQuery):
    message = callback_query.message
    chat_id = message.chat.id
    await bot.answer_callback_query(callback_query.id)
    if chat_id in scores:
        final_score = scores[chat_id]
        total = total_answers[chat_id]
        percentage = (final_score / total) * 100
    else:
        percentage = 0

    # Reset the counters
    total_answers[chat_id] = 0
    scores[chat_id] = 0

    language = selected_language.get(chat_id, "en")
    await bot.send_message(
        chat_id,
        translations[language]["thanks_for_playing"].format(score=final_score, total=total, percentage=percentage)
    )

    await bot.send_message(
        chat_id,
        translations[language]["click_button_to_start_new_test"],
        reply_markup=generate_start_button()
    )


@dp.callback_query_handler(
    lambda c: c.data.startswith("answer_") or c.data in ["get_trivia", "end_game"] or c.data.startswith(
        "difficulty_") or c.data == "start_test" or c.data.startswith("language_"))
async def answer_callback_handler(callback_query: types.CallbackQuery):
    message = callback_query.message

    if callback_query.data.startswith("answer_"):
        chat_id = message.chat.id
        user_answer_index = int(callback_query.data.split("_")[1])
        correct_answer = correct_answers[chat_id]
        total_answers[chat_id] += 1

        options = options_per_chat.get(chat_id, [])

        user_answer = options[user_answer_index - 1]

        language = selected_language.get(chat_id, "en")

        if user_answer.lower() == correct_answer.lower():
            scores[chat_id] += 1
            response_text = translations[language]["correct_well_done_score"].format(
                score=scores[chat_id],
                total=total_answers[chat_id]
            )
        else:
            response_text = translations[language]["sorry_correct_answer_was"].format(
                correct_answer=correct_answer,
                score=scores[chat_id],
                total=total_answers[chat_id]
            )

        await send_response_and_buttons(chat_id, response_text, language)

    elif callback_query.data.startswith("get_trivia"):
        await trivia_handler(message)

    elif callback_query.data.startswith("end_game"):
        await end_game_handler(callback_query)

    elif callback_query.data.startswith("language_"):
        language = callback_query.data.split("_")[1]
        selected_language[callback_query.message.chat.id] = language
        await start_test_handler(message)

    elif callback_query.data.startswith("difficulty_"):
        difficulty = callback_query.data.split("_")[1]
        await trivia_handler(message, difficulty)

    elif callback_query.data.startswith("start_test"):
        await start_test_handler(message)


def generate_start_button():
    markup = InlineKeyboardMarkup()
    start_test_button = InlineKeyboardButton("Start Test", callback_data="start_test")
    markup.add(start_test_button)
    return markup


async def start_test_handler(message, language=None):
    chat_id = message.chat.id if isinstance(message, types.Message) else message.from_user.id
    if language is None:
        language = selected_language.get(chat_id, "en")
    markup = InlineKeyboardMarkup(row_width=2)
    easy_button = InlineKeyboardButton(translations[language]["easy"], callback_data="difficulty_easy")
    medium_button = InlineKeyboardButton(translations[language]["medium"], callback_data="difficulty_medium")
    hard_button = InlineKeyboardButton(translations[language]["hard"], callback_data="difficulty_hard")
    markup.add(easy_button, medium_button, hard_button)

    await bot.send_message(chat_id, translations[language]["choose_difficulty"], reply_markup=markup)


def generate_language_buttons():
    markup = InlineKeyboardMarkup(row_width=2)
    en_button = InlineKeyboardButton("English", callback_data="language_en")
    ru_button = InlineKeyboardButton("Русский", callback_data="language_ru")
    markup.add(en_button, ru_button)
    return markup


dp.register_message_handler(start_handler, commands=["start", "help"])

# Start the bot
if __name__ == '__main__':
    executor.start_polling(dp)

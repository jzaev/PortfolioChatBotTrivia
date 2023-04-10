import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging
import base64
from config import MY_TOKEN

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


def generate_trivia_button():
    markup = InlineKeyboardMarkup()
    trivia_button = InlineKeyboardButton("Get Trivia Question", callback_data="get_trivia")
    end_game_button = InlineKeyboardButton("End Game", callback_data="end_game")
    markup.add(trivia_button, end_game_button)
    return markup


async def fetch_trivia_question():
    url = f"https://opentdb.com/api.php?amount=1&type=multiple&encode=base64"  # &key={TRIVIA_API_KEY}"
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


async def send_response_and_buttons(chat_id, text):
    markup = generate_trivia_button()
    await bot.send_message(chat_id, text, reply_markup=markup)


async def start_handler(message: types.Message):
    markup = generate_trivia_button()
    await message.reply("Welcome to the Trivia Bot! Click the button to get a trivia question.", reply_markup=markup)


async def trivia_handler(message: types.Message):
    data = await fetch_trivia_question()
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

    await message.reply(question, parse_mode=ParseMode.HTML, reply_markup=inline_keyboard)


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
    await bot.send_message(chat_id,
                           f"Thanks for playing! Your final score is: {final_score}. "
                           f"Your percentage of correct answers is: {percentage:.1f}%. Click the button to play again.")
    markup = generate_trivia_button()
    await bot.send_message(chat_id, "Click the button below to get a new trivia question.", reply_markup=markup)


@dp.callback_query_handler(lambda c: c.data.startswith("answer_") or c.data in ["get_trivia", "end_game"])
async def answer_callback_handler(callback_query: types.CallbackQuery):
    message = callback_query.message

    if callback_query.data.startswith("answer_"):
        chat_id = message.chat.id
        user_answer_index = int(callback_query.data.split("_")[1])
        correct_answer = correct_answers[chat_id]
        total_answers[chat_id] += 1

        options = options_per_chat.get(chat_id, [])

        user_answer = options[user_answer_index - 1]

        if user_answer.lower() == correct_answer.lower():
            scores[chat_id] += 1
            await send_response_and_buttons(chat_id, f"Correct! Well done! Your score is: {scores[chat_id]}")
        else:
            await send_response_and_buttons(chat_id,
                                            f"Sorry, the correct answer was: {correct_answer}."
                                            f" Your score is: {scores[chat_id]}")

        del correct_answers[chat_id]

    elif callback_query.data == "get_trivia":
        await trivia_handler(message)
    elif callback_query.data == "end_game":
        await end_game_handler(callback_query)


dp.register_message_handler(start_handler, commands=["start", "help"])

# Start the bot
if __name__ == '__main__':
    executor.start_polling(dp)

from aiogram import types
from trivia import Trivia

async def answer_callback_handler(callback_query: types.CallbackQuery, trivia: Trivia):
    await trivia.answer_callback_handler(callback_query)

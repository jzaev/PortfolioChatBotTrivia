from aiogram import types
from trivia import Trivia

async def start_handler(message: types.Message, trivia: Trivia):
    await trivia.start_handler(message)
